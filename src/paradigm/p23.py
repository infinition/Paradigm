from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .agent_scenarios import make_task
from .agent_vertical import AgentFeatureEncoder, ParadigmCodingAgent, summarize_episodes
from .llm_controller import LLMUsage, OpenAICompatibleCodingDeliberator
from .online_learning import OnlineReflexCompiler
from .p21 import _window_metrics, make_online_stream

NOVEL_FAMILY = "syntax_error"


def _usage_dict(usage: LLMUsage) -> dict[str, Any]:
    data = asdict(usage)
    data["mean_latency_ms"] = usage.latency_ms / usage.calls if usage.calls else 0.0
    data["mean_tokens_per_call"] = usage.total_tokens / usage.calls if usage.calls else 0.0
    return data


class _StallingDeliberator:
    """Deterministic control that never repairs, so its episode must fail."""

    def decide(self, state):
        if state.phase == "start":
            return "run_tests"
        return "inspect_file"


def _novel_family(result: dict[str, Any]) -> str:
    return str(result.get("stream", {}).get("novel_family", NOVEL_FAMILY))


def derive_time_to_reflex(result: dict[str, Any]) -> dict[str, Any]:
    """Time-to-reflex for the novel family, derived from the recorded per-episode log.

    TTR counts validated novel-family episodes ingested before the promotion that first
    represented the family. Time-to-mature counts novel-family episodes before the point
    from which every remaining novel-family episode runs at >= 95% fast path with success
    and no invalid action.
    """
    novel_family = _novel_family(result)
    rows = [r for r in result["per_episode"] if r["family"] == novel_family]
    represented_from = result["novel_family"].get("represented_from_episode")
    rejected_before = sum(
        1
        for p in result["promotions"]
        if not p["promoted"]
        and novel_family in p.get("families_in_buffer", [])
        and (represented_from is None or p["stream_episode"] < represented_from)
    )
    if represented_from is None:
        novel_seen = sum(1 for r in rows if r["success"])
        # Distinguish a candidate that was compiled with the family and failed the gate from a family
        # that never accumulated enough buffered evidence to be compiled into a candidate at all.
        audit = derive_promotion_audit(result)
        compiled_with_novel = [a for a in audit if a["train_traces"]["novel"] > 0]
        outcome = "rejected" if compiled_with_novel else "insufficient_evidence"
        return {
            "validated_episodes": None,
            "validated_decisions": None,
            "learning_evidence": None,
            "certification_evidence": None,
            "candidates_rejected_before_representation": rejected_before,
            "time_to_mature_episodes": None,
            "outcome": outcome,
            "novel_episodes_observed": novel_seen,
            "candidates_with_novel_in_train": len(compiled_with_novel),
            "definition": "validated novel-family episodes before the first promotion representing the family",
        }
    validated = [r for r in rows if r["success"] and r["episode"] <= represented_from]
    promoting = next(
        (a for a in derive_promotion_audit(result) if a["promoted"] and a["stream_episode"] == represented_from), None
    )
    learning = (
        {"episodes": promoting["train_episodes"]["novel"], "decisions": promoting["train_traces"]["novel"]}
        if promoting
        else None
    )
    certification = (
        {"episodes": promoting["validation_episodes"]["novel"], "decisions": promoting["validation_traces"]["novel"]}
        if promoting
        else None
    )
    mature_from = None
    for i in range(len(rows)):
        tail = rows[i:]
        if all(
            r["success"]
            and r["invalid_reflex_actions"] == 0
            and r["invalid_llm_actions"] == 0
            and r["reflex_calls"] / max(1, r["reflex_calls"] + r["llm_calls"]) >= 0.95
            for r in tail
        ):
            mature_from = i
            break
    return {
        "validated_episodes": len(validated),
        "validated_decisions": sum(r["llm_calls"] for r in validated),
        "learning_evidence": learning,
        "certification_evidence": certification,
        "candidates_rejected_before_representation": rejected_before,
        "time_to_mature_episodes": mature_from,
        "outcome": "promoted",
        "definition": (
            "validated novel-family episodes before the first promotion representing the family; "
            "learning evidence is the novel share of that candidate's train split, certification evidence "
            "the novel share of its validation split"
        ),
    }


def derive_promotion_audit(result: dict[str, Any], validation_fraction: float = 0.25) -> list[dict[str, Any]]:
    """Reconstruct the train/validation family composition of every promotion attempt.

    The online buffer is deterministic: successful episodes with at least one deliberative
    decision, in stream order, with the most recent 25% of episodes held out for validation.
    Each buffered episode contributes as many traces as it had deliberative decisions. This
    lets the split composition be audited from the per-episode log even for runs recorded
    before per-family acceptance was stored on the promotion record.
    """
    rows = result["per_episode"]
    novel_family = _novel_family(result)
    audit = []
    for attempt in result["promotions"]:
        upto = attempt["stream_episode"]
        buffered = [r for r in rows if r["episode"] <= upto and r["success"] and r["llm_calls"] > 0]
        if len(buffered) < 2:
            train_eps, val_eps = buffered, []
        else:
            n_val = max(1, int(round(len(buffered) * validation_fraction)))
            n_val = min(n_val, len(buffered) - 1)
            train_eps, val_eps = buffered[:-n_val], buffered[-n_val:]

        def composition(eps):
            out: dict[str, int] = {}
            for r in eps:
                key = "novel" if r["family"] == novel_family else "known"
                out[key] = out.get(key, 0) + r["llm_calls"]
            return {"known": out.get("known", 0), "novel": out.get("novel", 0)}

        def episodes(eps):
            novel = sum(1 for r in eps if r["family"] == novel_family)
            return {"known": len(eps) - novel, "novel": novel}

        train_c = composition(train_eps)
        val_c = composition(val_eps)
        audit.append(
            {
                "stream_episode": upto,
                "candidate_version": attempt["version"] + (0 if attempt["promoted"] else 1),
                "promoted": attempt["promoted"],
                "reason": attempt["reason"],
                "train_traces": {"known": train_c["known"], "novel": train_c["novel"]},
                "validation_traces": {"known": val_c["known"], "novel": val_c["novel"]},
                "train_episodes": episodes(train_eps),
                "validation_episodes": episodes(val_eps),
                "validation_novel_share": (
                    val_c["novel"] / (val_c["known"] + val_c["novel"]) if (val_c["known"] + val_c["novel"]) else 0.0
                ),
                "overall_shadow_acceptance": attempt["ood_acceptance"],
                "novel_shadow_acceptance": (attempt.get("ood_acceptance_by_family") or {}).get(novel_family),
                "recorded_train_traces": attempt["train_traces"],
                "recorded_validation_traces": attempt["validation_traces"],
                "reconstruction_matches_record": (
                    train_c["known"] + train_c["novel"] == attempt["train_traces"]
                    and val_c["known"] + val_c["novel"] == attempt["validation_traces"]
                ),
            }
        )
    return audit


def derive_signature_metrics(result: dict[str, Any]) -> dict[str, Any]:
    """Time-to-reflex, acquisition debt, and reflex dividend from the per-episode log.

    Acquisition debt is the deliberation spent on the novel family before its first
    fast-path use. Reflex dividend is what the online run saved relative to the
    LLM-only baseline on novel-family episodes after representation, and overall.
    """
    rows = result["per_episode"]
    novel_family = _novel_family(result)
    novel_rows = [r for r in rows if r["family"] == novel_family]
    first_fast = next((r["episode"] for r in novel_rows if r["reflex_calls"] > 0), None)
    represented_from = result["novel_family"].get("represented_from_episode")
    debt_rows = [r for r in novel_rows if first_fast is None or r["episode"] < first_fast]
    after_rows = [r for r in novel_rows if represented_from is not None and r["episode"] > represented_from]
    debt_tokens = sum(r["tokens"] for r in debt_rows)
    dividend_tokens = sum(r["baseline_tokens"] - r["tokens"] for r in after_rows)
    return {
        "time_to_reflex": derive_time_to_reflex(result),
        "acquisition_debt": {
            "episodes": len(debt_rows),
            "decisions": sum(r["llm_calls"] for r in debt_rows),
            "tokens": debt_tokens,
            "llm_latency_ms": sum(r["llm_latency_ms"] for r in debt_rows),
            "reflex_reached": first_fast is not None,
        },
        "reflex_dividend": {
            "novel_episodes_after_representation": len(after_rows),
            "novel_tokens_saved": dividend_tokens,
            "novel_llm_calls_saved": sum(r["baseline_llm_calls"] - r["llm_calls"] for r in after_rows),
            "novel_llm_latency_saved_ms": sum(r["baseline_llm_latency_ms"] - r["llm_latency_ms"] for r in after_rows),
            "novel_fast_path_after_representation": (
                sum(r["reflex_calls"] for r in after_rows)
                / max(1, sum(r["reflex_calls"] + r["llm_calls"] for r in after_rows))
            ) if after_rows else None,
            "total_tokens_saved": rows[-1]["cumulative_tokens_saved"] if rows else 0,
            "total_llm_latency_saved_ms": rows[-1]["cumulative_llm_latency_saved_ms"] if rows else 0.0,
        },
        # Fraction of the novel family's acquisition tokens recovered by its own reflex within the stream.
        # The debt was deliberation the baseline also paid, so this measures how fast deliberation
        # turns into reusable competence, not a net training cost.
        "debt_recovery_ratio_tokens": (dividend_tokens / debt_tokens) if debt_tokens and first_fast else None,
    }


def run_p23_live_online_benchmark(
    controller: OpenAICompatibleCodingDeliberator,
    *,
    quick: bool = False,
    stream: list | None = None,
    phases: list[str] | None = None,
    random_state: int = 21,
    arrival: str = "burst",
    compiler_options: dict[str, Any] | None = None,
    return_compiler: bool = False,
    novel_family: str = NOVEL_FAMILY,
    encoder: AgentFeatureEncoder | None = None,
) -> dict[str, Any]:
    """P2.1 online acquisition with the deterministic teacher replaced by a real LLM.

    Compiler thresholds, stream, and outcome filter are identical to P2.1 so the only
    experimental change is the deliberative controller. ``stream`` and ``phases`` can be
    supplied to test other arrival orders; ``random_state`` seeds the compiler.
    """
    encoder = encoder or AgentFeatureEncoder()
    compiler = OnlineReflexCompiler(
        min_episodes=6 if quick else 8,
        compile_every=3 if quick else 4,
        validation_fraction=0.25,
        minimum_ood_acceptance=0.65,
        random_state=random_state,
        **(compiler_options or {}),
    )
    if stream is None or phases is None:
        stream, phases = make_online_stream(quick=quick)

    episodes = []
    per_episode: list[dict[str, Any]] = []
    promotion_events: list[dict[str, Any]] = []
    compile_wallclock_ms = 0.0
    novel_represented_from: int | None = None

    online_before = controller.snapshot()
    for idx, (task, phase) in enumerate(zip(stream, phases), start=1):
        version_before = compiler.state.version
        before = controller.snapshot()
        agent = compiler.make_agent(controller, encoder)
        episode = agent.run(task)
        usage = controller.snapshot().delta(before)
        episodes.append(episode)

        compile_start = time.perf_counter()
        promotion = compiler.ingest(episode, stream_episode=idx)
        compile_ms = (time.perf_counter() - compile_start) * 1e3
        compile_wallclock_ms += compile_ms
        if promotion is not None:
            record = asdict(promotion)
            record["families_in_buffer"] = sorted({ep.family for ep in compiler.buffer.episodes})
            record["compile_wallclock_ms"] = compile_ms
            promotion_events.append(record)
            if promotion.promoted and novel_represented_from is None and novel_family in record["families_in_buffer"]:
                novel_represented_from = idx

        per_episode.append(
            {
                "episode": idx,
                "phase": phase,
                "family": episode.family,
                "success": episode.success,
                "steps": episode.steps,
                "llm_calls": usage.calls,
                "reflex_calls": episode.reflex_calls,
                "tokens": usage.total_tokens,
                "llm_latency_ms": usage.latency_ms,
                "invalid_llm_actions": usage.invalid_actions,
                "invalid_reflex_actions": episode.invalid_reflex_actions,
                "fallback_reasons": dict(episode.fallback_reasons),
                "active_version_during_episode": version_before,
                "compile_wallclock_ms": compile_ms,
            }
        )
    online_usage = controller.snapshot().delta(online_before)

    baseline_before = controller.snapshot()
    baseline_agent = ParadigmCodingAgent(controller, encoder=encoder)
    baseline_episodes = []
    for idx, task in enumerate(stream, start=1):
        before = controller.snapshot()
        episode = baseline_agent.run(task)
        usage = controller.snapshot().delta(before)
        baseline_episodes.append(episode)
        per_episode[idx - 1]["baseline_tokens"] = usage.total_tokens
        per_episode[idx - 1]["baseline_llm_calls"] = usage.calls
        per_episode[idx - 1]["baseline_llm_latency_ms"] = usage.latency_ms
        per_episode[idx - 1]["baseline_success"] = episode.success
    baseline_usage = controller.snapshot().delta(baseline_before)

    cum_online = cum_baseline = cum_reflex = 0
    cum_online_latency = cum_baseline_latency = cum_compile = 0.0
    latency_break_even_episode: int | None = None
    for row in per_episode:
        cum_online += row["tokens"]
        cum_baseline += row["baseline_tokens"]
        cum_reflex += row["reflex_calls"]
        cum_online_latency += row["llm_latency_ms"]
        cum_baseline_latency += row["baseline_llm_latency_ms"]
        cum_compile += row["compile_wallclock_ms"]
        row["cumulative_tokens_online"] = cum_online
        row["cumulative_tokens_baseline"] = cum_baseline
        row["cumulative_tokens_saved"] = cum_baseline - cum_online
        row["cumulative_reflex_calls"] = cum_reflex
        row["cumulative_llm_latency_saved_ms"] = cum_baseline_latency - cum_online_latency
        row["cumulative_compile_wallclock_ms"] = cum_compile
        # Before the first reflex use, the latency difference is measurement noise only.
        if (
            latency_break_even_episode is None
            and cum_reflex > 0
            and row["cumulative_llm_latency_saved_ms"] >= cum_compile
        ):
            latency_break_even_episode = row["episode"]

    overall = summarize_episodes(episodes)
    baseline = summarize_episodes(baseline_episodes)
    known_eps = [e for e in episodes if e.family != novel_family]
    novel_eps = [e for e in episodes if e.family == novel_family]
    first_novel = next(i for i, e in enumerate(episodes, start=1) if e.family == novel_family)

    novel_rows = [r for r in per_episode if r["family"] == novel_family]
    first_novel_fast_path = next((r["episode"] for r in novel_rows if r["reflex_calls"] > 0), None)
    novel_episodes_before_fast_path = sum(
        1 for r in novel_rows if first_novel_fast_path is None or r["episode"] < first_novel_fast_path
    )
    novel_acquisition_tokens = sum(
        r["tokens"] for r in novel_rows if first_novel_fast_path is None or r["episode"] < first_novel_fast_path
    )

    # Unknown false fast path: reflex decisions on the novel family before any promoted
    # candidate had novel-family traces in its buffer.
    unrepresented_rows = [
        r for r in novel_rows if novel_represented_from is None or r["episode"] <= novel_represented_from
    ]
    unrepresented_decisions = sum(r["reflex_calls"] + r["llm_calls"] for r in unrepresented_rows)
    unrepresented_reflex = sum(r["reflex_calls"] for r in unrepresented_rows)

    def by_phase(label: str, family_filter=None) -> dict[str, Any]:
        items = [
            e for e, p in zip(episodes, phases) if p == label and (family_filter is None or family_filter(e))
        ]
        return summarize_episodes(items)

    known_phase_a = by_phase("A")
    known_phase_c = by_phase("C", lambda e: e.family != novel_family)
    novel_phase_b = by_phase("B")
    novel_phase_c = by_phase("C", lambda e: e.family == novel_family)
    known_before_novel = summarize_episodes(
        [e for i, e in enumerate(episodes, start=1) if e.family != novel_family and i < first_novel]
    )
    known_after_representation = summarize_episodes(
        [
            e
            for i, e in enumerate(episodes, start=1)
            if e.family != novel_family and novel_represented_from is not None and i > novel_represented_from
        ]
    )

    # Outcome-filter control: a failed episode must not enter the trusted buffer.
    before_traces = compiler.buffer.trusted_trace_count
    failed = ParadigmCodingAgent(_StallingDeliberator(), encoder=encoder).run(
        make_task("wrong_constant", 999), max_steps=4
    )
    compiler.buffer.ingest(failed)
    added_traces = compiler.buffer.trusted_trace_count - before_traces

    def reduction(a: float, b: float) -> float:
        return (a - b) / a if a else 0.0

    result = {
        "phase": "P2.3",
        "executed_live_llm": True,
        "scope": "P2.1 online acquisition with a real OpenAI-compatible LLM as the only teacher",
        "controller": {
            "base_url": controller.base_url,
            "model": controller.model,
            "temperature": controller.temperature,
            "max_tokens": controller.max_tokens,
            "pricing_configured": bool(controller.input_cost_per_million or controller.output_cost_per_million),
        },
        "learning_mode": {
            "active_runtime": "immutable between promotions",
            "teacher_labels": "LLM decisions from successful episodes only",
            "primary_compiler": "periodic supervised recompile with held-out shadow validation",
            "reinforcement_learning": False,
            "compiler_settings_identical_to_p21": True,
        },
        "stream": {
            "arrival": arrival,
            "random_state": random_state,
            "novel_family": novel_family,
            "episodes": len(episodes),
            "first_novel_family_episode": first_novel,
            "families": sorted({e.family for e in episodes}),
            "phase_sizes": {label: phases.count(label) for label in ("A", "B", "C")},
        },
        "baseline": baseline,
        "online": overall,
        "known": summarize_episodes(known_eps),
        "novel_family": {
            "overall": summarize_episodes(novel_eps),
            "phase_b": novel_phase_b,
            "phase_c": novel_phase_c,
            "first_fast_path_episode": first_novel_fast_path,
            "episodes_before_first_fast_path": novel_episodes_before_fast_path,
            "acquisition_tokens_before_first_fast_path": novel_acquisition_tokens,
            "represented_from_episode": novel_represented_from,
            "unrepresented_decisions": unrepresented_decisions,
            "unrepresented_reflex_decisions": unrepresented_reflex,
            "unknown_false_fast_path_rate": (
                unrepresented_reflex / unrepresented_decisions if unrepresented_decisions else 0.0
            ),
        },
        "old_family_retention": {
            "known_phase_a": known_phase_a,
            "known_phase_c": known_phase_c,
            "known_before_novel": known_before_novel,
            "known_after_representation": known_after_representation,
            "success_retained": bool(
                known_after_representation.get("success_rate", 1.0) >= known_before_novel.get("success_rate", 0.0)
            ),
        },
        "learning_curve": _window_metrics(episodes, 0, 8 if quick else 10),
        "per_episode": per_episode,
        "llm_usage": {
            "online": _usage_dict(online_usage),
            "baseline": _usage_dict(baseline_usage),
            "llm_call_reduction": reduction(baseline_usage.calls, online_usage.calls),
            "token_reduction": reduction(baseline_usage.total_tokens, online_usage.total_tokens),
            "llm_latency_reduction": reduction(baseline_usage.latency_ms, online_usage.latency_ms),
        },
        "amortization": {
            "compile_llm_tokens": 0,
            "compile_wallclock_ms": compile_wallclock_ms,
            "cumulative_tokens_saved": cum_baseline - cum_online,
            "cumulative_llm_latency_saved_ms": cum_baseline_latency - cum_online_latency,
            "latency_break_even_episode": latency_break_even_episode,
            "note": (
                "Online acquisition spends no extra LLM tokens on compilation: teacher labels come from "
                "deliberative calls the LLM-only baseline also pays for. Token savings are therefore net "
                "from the first reflex use. The only extra cost is local compile and validation wall-clock, "
                "compared here against cumulative LLM latency saved."
            ),
        },
        "experience_buffer": {
            "trusted_episodes": len(compiler.buffer.episodes),
            "trusted_traces": compiler.buffer.trusted_trace_count,
            "rejected_failed_episodes": compiler.buffer.rejected_failed_episodes,
            "ignored_self_labels": compiler.buffer.ignored_self_labels,
            "failed_episode_success": failed.success,
            "failed_episode_added_traces": added_traces,
        },
        "promotions": promotion_events,
        "active_version": compiler.state.version,
        "deliberative_calls_avoided": int(baseline["deliberative_calls"]) - int(overall["deliberative_calls"]),
        "success_preserved": bool(overall["success_rate"] >= baseline["success_rate"]),
        "limitations": [
            "Single model, single seed, one 69-episode stream in the full run. Not a robust estimate.",
            "Supervised imitation of LLM decisions from successful episodes only. No credit assignment, no RL.",
            "The compiled reflex covers tool-control decisions. apply_fix remains a validated repair primitive.",
            "Latency comparison mixes local compile wall-clock with remote model latency on one machine.",
        ],
    }
    result["signature_metrics"] = derive_signature_metrics(result)
    result["novel_family"]["time_to_reflex"] = result["signature_metrics"]["time_to_reflex"]
    result["promotion_audit"] = derive_promotion_audit(result)
    if return_compiler:
        result["_compiler"] = compiler
    return result


def write_p23_results(root: Path, result: dict[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "core_p23_online_llm.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    online = result["online"]
    baseline = result["baseline"]
    novel = result["novel_family"]
    usage = result["llm_usage"]
    amort = result["amortization"]
    retention = result["old_family_retention"]
    buffer = result["experience_buffer"]

    lines: list[str] = []
    lines.append("# P2.3 Real LLM Online Acquisition Report")
    lines.append("")
    lines.append(
        "P2.3 repeats the P2.1 online loop with the deterministic teacher replaced by a real language "
        "model. The stream, compiler thresholds, and outcome filter are unchanged. The model is the only "
        "source of teacher labels. The active reflex is never modified in place."
    )
    lines.append("")
    lines.append("## Controller")
    lines.append("")
    lines.append(f"- Model: `{result['controller']['model']}`")
    lines.append(f"- Endpoint: `{result['controller']['base_url']}`")
    lines.append("")
    lines.append("## End-to-end result")
    lines.append("")
    lines.append(f"- Episodes: {result['stream']['episodes']}")
    lines.append(f"- Baseline success: {baseline['success_rate']:.1%}")
    lines.append(f"- Online success: {online['success_rate']:.1%}")
    lines.append(f"- Online fast-path coverage: {online['fast_path_coverage']:.1%}")
    lines.append(f"- Baseline LLM calls: {usage['baseline']['calls']}")
    lines.append(f"- Online LLM calls: {usage['online']['calls']}")
    lines.append(f"- LLM call reduction: {usage['llm_call_reduction']:.1%}")
    lines.append(f"- Token reduction: {usage['token_reduction']:.1%}")
    lines.append(f"- LLM latency reduction: {usage['llm_latency_reduction']:.1%}")
    lines.append(f"- Invalid LLM actions (online / baseline): {usage['online']['invalid_actions']} / {usage['baseline']['invalid_actions']}")
    lines.append(f"- Invalid reflex actions reaching tools: {online['invalid_reflex_actions']:.0f}")
    lines.append(f"- Promotions: {sum(1 for p in result['promotions'] if p['promoted'])}")
    lines.append(f"- Active reflex version at end: {result['active_version']}")
    lines.append("")
    lines.append("## Novel family acquisition")
    lines.append("")
    lines.append(f"- First novel-family episode: {result['stream']['first_novel_family_episode']}")
    lines.append(f"- Phase B (novel only) fast-path coverage: {novel['phase_b'].get('fast_path_coverage', 0.0):.1%}")
    lines.append(f"- Phase C (mixed) novel-family fast-path coverage: {novel['phase_c'].get('fast_path_coverage', 0.0):.1%}")
    lines.append(f"- Novel-family overall success: {novel['overall']['success_rate']:.1%}")
    lines.append(f"- First novel-family fast-path episode: {novel['first_fast_path_episode']}")
    lines.append(f"- Novel-family episodes before first fast path: {novel['episodes_before_first_fast_path']}")
    lines.append(f"- Acquisition tokens before first fast path: {novel['acquisition_tokens_before_first_fast_path']}")
    lines.append(f"- Novel family represented from promotion at episode: {novel['represented_from_episode']}")
    lines.append(
        f"- Unknown false fast-path rate: {novel['unknown_false_fast_path_rate']:.1%} "
        f"({novel['unrepresented_reflex_decisions']} of {novel['unrepresented_decisions']} decisions while unrepresented)"
    )
    ttr = novel["time_to_reflex"]
    lines.append("")
    lines.append("## Time-to-reflex")
    lines.append("")
    lines.append(f"- Validated novel-family episodes before representation: {ttr['validated_episodes']}")
    lines.append(f"- Validated novel-family LLM decisions before representation: {ttr['validated_decisions']}")
    if ttr.get("learning_evidence"):
        le, ce = ttr["learning_evidence"], ttr["certification_evidence"]
        lines.append(
            f"- Learning evidence (novel share of the promoted candidate's train split): {le['episodes']} episodes, {le['decisions']} decisions"
        )
        lines.append(
            f"- Certification evidence (novel share of its validation split): {ce['episodes']} episodes, {ce['decisions']} decisions"
        )
    lines.append(f"- Outcome: {ttr.get('outcome')}")
    lines.append(f"- Candidates rejected by shadow validation before representation: {ttr['candidates_rejected_before_representation']}")
    lines.append(f"- Novel-family episodes before mature reflex (>= 95% fast path, success, no invalid action): {ttr['time_to_mature_episodes']}")
    sig = result.get("signature_metrics")
    if sig:
        debt = sig["acquisition_debt"]
        div = sig["reflex_dividend"]
        lines.append("")
        lines.append("## Acquisition debt and reflex dividend")
        lines.append("")
        lines.append(
            f"- Acquisition debt: {debt['episodes']} episodes, {debt['decisions']} LLM decisions, "
            f"{debt['tokens']} tokens, {debt['llm_latency_ms'] / 1000:.1f} s of LLM latency before the novel family's first fast path"
        )
        lines.append(f"- Reflex reached within stream: {debt['reflex_reached']}")
        lines.append(
            f"- Reflex dividend on the novel family after representation: {div['novel_llm_calls_saved']} LLM calls, "
            f"{div['novel_tokens_saved']} tokens, {div['novel_llm_latency_saved_ms'] / 1000:.1f} s saved over "
            f"{div['novel_episodes_after_representation']} episodes"
        )
        lines.append(f"- Total tokens saved across the stream: {div['total_tokens_saved']}")
        ratio = sig.get("debt_recovery_ratio_tokens")
        lines.append(f"- Debt recovery ratio (novel dividend tokens / acquisition debt tokens): {ratio:.1%}" if ratio is not None else "- Debt recovery ratio: n/a")
    lines.append("")
    lines.append("## Old family retention")
    lines.append("")
    lines.append(f"- Known-family success, phase A: {retention['known_phase_a'].get('success_rate', 0.0):.1%}")
    lines.append(f"- Known-family success, phase C: {retention['known_phase_c'].get('success_rate', 0.0):.1%}")
    lines.append(f"- Known-family fast-path coverage, phase A: {retention['known_phase_a'].get('fast_path_coverage', 0.0):.1%}")
    lines.append(f"- Known-family fast-path coverage, phase C: {retention['known_phase_c'].get('fast_path_coverage', 0.0):.1%}")
    lines.append("")
    lines.append("## Learning curve")
    lines.append("")
    lines.append("| Episodes | Success | Fast path | LLM calls | Reflex calls |")
    lines.append("|---|---|---|---|---|")
    for w in result["learning_curve"]:
        lines.append(
            f"| {w['start_episode']}-{w['end_episode']} | {w['success_rate']:.0%} | {w['fast_path_coverage']:.1%} "
            f"| {w['deliberative_calls']:.0f} | {w['reflex_calls']:.0f} |"
        )
    lines.append("")
    lines.append("## Cumulative cost")
    lines.append("")
    lines.append("| Episode | Baseline tokens | Online tokens | Saved |")
    lines.append("|---|---|---|---|")
    step = max(1, len(result["per_episode"]) // 10)
    rows = result["per_episode"]
    for row in rows[step - 1 :: step]:
        lines.append(
            f"| {row['episode']} | {row['cumulative_tokens_baseline']} | {row['cumulative_tokens_online']} "
            f"| {row['cumulative_tokens_saved']} |"
        )
    if rows and rows[-1] not in rows[step - 1 :: step]:
        row = rows[-1]
        lines.append(
            f"| {row['episode']} | {row['cumulative_tokens_baseline']} | {row['cumulative_tokens_online']} "
            f"| {row['cumulative_tokens_saved']} |"
        )
    lines.append("")
    lines.append("## Amortization")
    lines.append("")
    lines.append(f"- LLM tokens spent on compilation: {amort['compile_llm_tokens']}")
    lines.append(f"- Local compile and validation wall-clock: {amort['compile_wallclock_ms'] / 1000:.2f} s")
    lines.append(f"- Cumulative tokens saved: {amort['cumulative_tokens_saved']}")
    lines.append(f"- Cumulative LLM latency saved: {amort['cumulative_llm_latency_saved_ms'] / 1000:.1f} s")
    lines.append(f"- Episode at which saved LLM latency exceeds compile wall-clock: {amort['latency_break_even_episode']}")
    lines.append("")
    lines.append(amort["note"])
    lines.append("")
    audit = result.get("promotion_audit") or derive_promotion_audit(result)
    lines.append("## Promotion audit")
    lines.append("")
    lines.append(
        "Train and validation composition of every candidate, reconstructed from the per-episode log "
        "(traces = deliberative decisions of buffered successful episodes; validation = most recent 25% of episodes). "
        "Novel shadow acceptance is recorded only for runs made after per-family acceptance was added."
    )
    lines.append("")
    lines.append("| Episode | Decision | Train known / novel | Validation known / novel | Novel share of validation | Overall shadow acceptance | Novel shadow acceptance | Reason |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for a in audit:
        nov = "n/a" if a["novel_shadow_acceptance"] is None else f"{a['novel_shadow_acceptance']:.0%}"
        lines.append(
            f"| {a['stream_episode']} | {'promote' if a['promoted'] else 'reject'} | "
            f"{a['train_traces']['known']} / {a['train_traces']['novel']} | "
            f"{a['validation_traces']['known']} / {a['validation_traces']['novel']} | {a['validation_novel_share']:.0%} | "
            f"{a['overall_shadow_acceptance']:.0%} | {nov} | {a['reason']} |"
        )
    lines.append("")
    lines.append("## Outcome filtering")
    lines.append("")
    lines.append(f"- Failed control episode success: {buffer['failed_episode_success']}")
    lines.append(f"- Failed control episode admitted traces: {buffer['failed_episode_added_traces']}")
    lines.append(f"- Reflex self-labels ignored as teacher labels: {buffer['ignored_self_labels']}")
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    for item in result["limitations"]:
        lines.append(f"- {item}")
    lines.append("")
    (root / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_unexecuted_p23_report(root: Path, reason: str) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    result = {"phase": "P2.3", "executed_live_llm": False, "reason": reason}
    (root / "core_p23_online_llm.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    report = "# P2.3 Real LLM Online Acquisition Report\n\n"
    report += "No live LLM result is recorded in this repository snapshot.\n\n"
    report += f"Reason: {reason}.\n\n"
    report += "Set PARADIGM_LLM_BASE_URL and PARADIGM_LLM_MODEL, then run benchmarks/core_p23_online_llm.py.\n"
    (root / "REPORT.md").write_text(report, encoding="utf-8")
    return result
