from __future__ import annotations

import json
from pathlib import Path

from .agent_scenarios import make_split
from .agent_vertical import (
    ParadigmCodingAgent,
    ReferenceCodingDeliberator,
    compile_agent_reflex,
    summarize_episodes,
)


def run_p20_benchmark(*, quick: bool = False) -> dict:
    train_n = 2 if quick else 12
    val_n = 1 if quick else 6
    test_n = 1 if quick else 8
    deliberator = ReferenceCodingDeliberator(analysis_rounds=25 if quick else 3500)
    train_tasks = make_split(0, train_n)
    validation_tasks = make_split(100, val_n)
    test_tasks = make_split(200, test_n, include_ood=True)

    selection, gate, encoder, compile_stats = compile_agent_reflex(
        train_tasks,
        validation_tasks,
        deliberator,
        random_state=20,
    )

    baseline_agent = ParadigmCodingAgent(deliberator, encoder=encoder)
    hybrid_agent = ParadigmCodingAgent(
        deliberator,
        encoder=encoder,
        selection=selection,
        ood_gate=gate,
    )
    baseline = [baseline_agent.run(task) for task in test_tasks]
    hybrid = [hybrid_agent.run(task) for task in test_tasks]
    baseline_summary = summarize_episodes(baseline)
    hybrid_summary = summarize_episodes(hybrid)

    baseline_calls = int(baseline_summary["deliberative_calls"])
    hybrid_calls = int(hybrid_summary["deliberative_calls"])
    known = [e for e in hybrid if e.family != "syntax_error"]
    ood = [e for e in hybrid if e.family == "syntax_error"]

    result = {
        "phase": "P2.0",
        "scope": "coding-agent control policy, not code-generation distillation",
        "compiler": {
            "backend": selection.backend,
            "threshold": selection.threshold,
            "feasible": selection.feasible,
            "candidates": [
                {
                    "backend": c.backend,
                    "feasible": c.feasible,
                    "coverage": c.coverage,
                    "selective_accuracy": c.selective_accuracy,
                    "ece": c.ece,
                    "latency_us_per_item": c.latency_us_per_item,
                }
                for c in selection.candidates
            ],
            **compile_stats,
        },
        "baseline": baseline_summary,
        "hybrid": hybrid_summary,
        "known_only": summarize_episodes(known),
        "ood_only": summarize_episodes(ood),
        "deliberative_calls_avoided": baseline_calls - hybrid_calls,
        "deliberative_call_reduction": (baseline_calls - hybrid_calls) / baseline_calls if baseline_calls else 0.0,
        "success_preserved": bool(hybrid_summary["success_rate"] >= baseline_summary["success_rate"]),
        "ood_success_preserved": bool(
            not ood or summarize_episodes(ood)["success_rate"] >= 0.999
        ),
    }
    return result


def write_p20_results(root: Path, result: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "core_p20_agent.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    baseline = result["baseline"]
    hybrid = result["hybrid"]
    known = result["known_only"]
    ood = result["ood_only"]
    report = "# P2.0 Paradigm Agent Report\n\n"
    report += (
        "Paradigm is connected to a real local coding-agent loop with filesystem reads, symbol search, "
        "a fixed test runner, controlled repair application, and explicit finish semantics. The compiled "
        "reflex controls tool selection only. Patch synthesis remains outside the reflex in this phase.\n\n"
    )
    report += "## Result\n\n"
    report += f"- Baseline success: {baseline['success_rate']:.1%}\n"
    report += f"- Hybrid success: {hybrid['success_rate']:.1%}\n"
    report += f"- Overall fast-path coverage: {hybrid['fast_path_coverage']:.1%}\n"
    report += f"- Known-task fast-path coverage: {known['fast_path_coverage']:.1%}\n"
    report += f"- OOD fast-path coverage: {ood.get('fast_path_coverage', 0.0):.1%}\n"
    report += f"- OOD success: {ood.get('success_rate', 0.0):.1%}\n"
    report += f"- Deliberative calls avoided: {result['deliberative_calls_avoided']}\n"
    report += f"- Deliberative call reduction: {result['deliberative_call_reduction']:.1%}\n"
    report += f"- Invalid reflex actions reaching tools: {int(hybrid['invalid_reflex_actions'])}\n\n"
    report += "## Interpretation\n\n"
    report += (
        "P2.0 tests the first concrete use of Paradigm as a procedural fast path for an agent. It does not "
        "claim that a local decision tree replaces language-model reasoning or code generation. The reflex only "
        "replaces repeated controller decisions when the state is represented and confidence is sufficient. "
        "Unknown states fall back to the deliberative policy.\n"
    )
    (root / "REPORT.md").write_text(report, encoding="utf-8")
