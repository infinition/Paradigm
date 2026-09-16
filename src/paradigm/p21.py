from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from .agent_scenarios import make_task
from .agent_vertical import AgentFeatureEncoder, ParadigmCodingAgent, ReferenceCodingDeliberator, summarize_episodes
from .online_learning import OnlineReflexCompiler, train_bounded_softmax_candidate


def make_online_stream(*, quick: bool = False) -> tuple[list, list[str]]:
    """Sequential task stream shared by the P2.1 and P2.3 online benchmarks.

    Returns the tasks and a parallel phase label per task: "A" repeated known
    workflows, "B" a genuinely unseen family, "C" mixed use after the new family
    has had a chance to be compiled.
    """
    known = ["missing_import", "wrong_constant", "renamed_symbol", "off_by_one"]
    tasks = []
    phases: list[str] = []
    if quick:
        for r in range(3):
            for i, family in enumerate(known):
                tasks.append(make_task(family, r * 10 + i))
                phases.append("A")
        for i in range(6):
            tasks.append(make_task("syntax_error", 100 + i))
            phases.append("B")
        for r in range(2):
            for i, family in enumerate(known + ["syntax_error"]):
                tasks.append(make_task(family, 200 + r * 10 + i))
                phases.append("C")
        return tasks, phases

    for r in range(8):
        for i, family in enumerate(known):
            tasks.append(make_task(family, r * 10 + i))
            phases.append("A")
    for i in range(12):
        tasks.append(make_task("syntax_error", 100 + i))
        phases.append("B")
    for r in range(5):
        for i, family in enumerate(known + ["syntax_error"]):
            tasks.append(make_task(family, 200 + r * 10 + i))
            phases.append("C")
    return tasks, phases


def _make_stream(*, quick: bool = False) -> list:
    return make_online_stream(quick=quick)[0]


def _window_metrics(episodes: list, start: int, size: int) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for offset in range(0, len(episodes), size):
        items = episodes[offset : offset + size]
        summary = summarize_episodes(items)
        windows.append(
            {
                "start_episode": start + offset + 1,
                "end_episode": start + offset + len(items),
                "success_rate": summary["success_rate"],
                "fast_path_coverage": summary["fast_path_coverage"],
                "deliberative_calls": summary["deliberative_calls"],
                "reflex_calls": summary["reflex_calls"],
                "families": sorted({e.family for e in items}),
            }
        )
    return windows


def run_p21_benchmark(*, quick: bool = False) -> dict[str, Any]:
    encoder = AgentFeatureEncoder()
    deliberator = ReferenceCodingDeliberator(analysis_rounds=10 if quick else 900)
    compiler = OnlineReflexCompiler(
        min_episodes=6 if quick else 8,
        compile_every=3 if quick else 4,
        validation_fraction=0.25,
        minimum_ood_acceptance=0.65,
        random_state=21,
    )
    stream = _make_stream(quick=quick)
    episodes = []
    promotion_events = []

    for idx, task in enumerate(stream, start=1):
        agent = compiler.make_agent(deliberator, encoder)
        episode = agent.run(task)
        episodes.append(episode)
        promotion = compiler.ingest(episode, stream_episode=idx)
        if promotion is not None:
            promotion_events.append(asdict(promotion))

    overall = summarize_episodes(episodes)
    known_eps = [e for e in episodes if e.family != "syntax_error"]
    syntax_eps = [e for e in episodes if e.family == "syntax_error"]
    first_syntax = next(i for i, e in enumerate(episodes) if e.family == "syntax_error")
    syntax_first_half = syntax_eps[: max(1, len(syntax_eps) // 2)]
    syntax_second_half = syntax_eps[max(1, len(syntax_eps) // 2) :]

    # Baseline cost for the exact same stream, using only the deliberative controller.
    baseline_agent = ParadigmCodingAgent(deliberator, encoder=encoder)
    baseline_episodes = [baseline_agent.run(task) for task in stream]
    baseline = summarize_episodes(baseline_episodes)

    train, validation = compiler.buffer.split(0.25)
    bounded: dict[str, Any]
    if train and validation:
        _, bounded_report = train_bounded_softmax_candidate(
            train,
            validation,
            epsilon=0.03,
            epochs=20 if quick else 70,
            batch_size=64,
            seed=21,
        )
        bounded = asdict(bounded_report)
    else:
        bounded = {"feasible": False, "reason": "insufficient_buffer"}

    # Explicit outcome-filter control. A failed episode must not enter the trusted buffer.
    class StallingDeliberator:
        def decide(self, state):
            if state.phase == "start":
                return "run_tests"
            return "inspect_file"

    before = compiler.buffer.trusted_trace_count
    failed = ParadigmCodingAgent(StallingDeliberator(), encoder=encoder).run(
        make_task("wrong_constant", 999), max_steps=4
    )
    compiler.buffer.ingest(failed)
    after = compiler.buffer.trusted_trace_count

    baseline_calls = int(baseline["deliberative_calls"])
    online_calls = int(overall["deliberative_calls"])
    result = {
        "phase": "P2.1",
        "scope": "outcome-filtered online supervised reflex compilation during agent use",
        "learning_mode": {
            "active_runtime": "immutable between promotions",
            "teacher_labels": "deliberative decisions from successful episodes only",
            "primary_compiler": "periodic supervised recompile with held-out shadow validation",
            "bounded_candidate": "linear softmax supervised fine-tuning with Drift Contract updates",
            "reinforcement_learning": False,
        },
        "stream": {
            "episodes": len(episodes),
            "first_novel_family_episode": first_syntax + 1,
            "families": sorted({e.family for e in episodes}),
        },
        "baseline": baseline,
        "online": overall,
        "known": summarize_episodes(known_eps),
        "novel_family": {
            "overall": summarize_episodes(syntax_eps),
            "first_half": summarize_episodes(syntax_first_half),
            "second_half": summarize_episodes(syntax_second_half) if syntax_second_half else {},
        },
        "learning_curve": _window_metrics(episodes, 0, 8 if quick else 10),
        "experience_buffer": {
            "trusted_episodes": len(compiler.buffer.episodes),
            "trusted_traces": compiler.buffer.trusted_trace_count,
            "rejected_failed_episodes": compiler.buffer.rejected_failed_episodes,
            "ignored_self_labels": compiler.buffer.ignored_self_labels,
            "failed_episode_success": failed.success,
            "failed_episode_added_traces": after - before,
        },
        "promotions": promotion_events,
        "active_version": compiler.state.version,
        "bounded_neural_candidate": bounded,
        "deliberative_calls_avoided": baseline_calls - online_calls,
        "deliberative_call_reduction": (baseline_calls - online_calls) / baseline_calls if baseline_calls else 0.0,
        "success_preserved": bool(overall["success_rate"] >= baseline["success_rate"]),
    }
    return result


def write_p21_results(root: Path, result: dict[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "core_p21_online_learning.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    online = result["online"]
    baseline = result["baseline"]
    novel = result["novel_family"]
    bounded = result["bounded_neural_candidate"]
    report = "# P2.1 Online Agent Learning Report\n\n"
    report += (
        "P2.1 tests supervised learning during normal agent use. The active runtime is never updated in place. "
        "Only deliberative decisions from successful episodes enter the trusted experience buffer. Candidates are "
        "compiled periodically, evaluated on held-out recent episodes, and promoted only when quality, calibration, "
        "and OOD shadow coverage pass.\n\n"
    )
    report += "## End-to-end result\n\n"
    report += f"- Episodes: {result['stream']['episodes']}\n"
    report += f"- Baseline success: {baseline['success_rate']:.1%}\n"
    report += f"- Online success: {online['success_rate']:.1%}\n"
    report += f"- Online fast-path coverage: {online['fast_path_coverage']:.1%}\n"
    report += f"- Deliberative calls avoided: {result['deliberative_calls_avoided']}\n"
    report += f"- Deliberative call reduction: {result['deliberative_call_reduction']:.1%}\n"
    report += f"- Active reflex version at end: {result['active_version']}\n\n"
    report += "## Novel family acquisition\n\n"
    report += (
        f"- Novel-family first-half fast-path coverage: {novel['first_half']['fast_path_coverage']:.1%}\n"
        f"- Novel-family second-half fast-path coverage: {novel['second_half'].get('fast_path_coverage', 0.0):.1%}\n"
        f"- Novel-family overall success: {novel['overall']['success_rate']:.1%}\n\n"
    )
    report += "The expected behavior is low fast-path coverage when the family first appears, followed by higher "
    report += "coverage only after enough successful fallback episodes have been admitted and a candidate passes shadow validation.\n\n"
    report += "## Outcome filtering\n\n"
    report += f"- Failed control episode success: {result['experience_buffer']['failed_episode_success']}\n"
    report += f"- Failed control episode admitted traces: {result['experience_buffer']['failed_episode_added_traces']}\n"
    report += "- Reflex self-labels are not used as teacher labels.\n\n"
    report += "## Bounded neural candidate\n\n"
    if bounded.get("feasible") is not None:
        report += f"- Feasible: {bounded.get('feasible')}\n"
        report += f"- Selective accuracy: {bounded.get('selective_accuracy', 0.0):.1%}\n"
        report += f"- Coverage: {bounded.get('coverage', 0.0):.1%}\n"
        report += f"- ECE: {bounded.get('ece', 0.0):.4f}\n"
        report += f"- Maximum measured update drift: {bounded.get('max_step_drift', 0.0):.6f}\n"
        report += f"- Epsilon: {bounded.get('epsilon', 0.0):.4f}\n\n"
    report += "## Interpretation\n\n"
    report += (
        "This phase is supervised imitation with outcome filtering, not RL. It fine-tunes a separate reflex candidate, "
        "not the deliberative controller. The primary fast path still prefers the simplest feasible compiled mechanism. "
        "The bounded softmax candidate exists to test whether Drift Contract can constrain neural reflex adaptation.\n"
    )
    (root / "REPORT.md").write_text(report, encoding="utf-8")
