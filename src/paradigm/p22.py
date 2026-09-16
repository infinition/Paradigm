from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .agent_scenarios import make_split, make_task
from .agent_vertical import AgentFeatureEncoder, ParadigmCodingAgent, compile_agent_reflex, summarize_episodes
from .llm_controller import LLMUsage, OpenAICompatibleCodingDeliberator


def _usage_dict(usage: LLMUsage) -> dict[str, Any]:
    data = asdict(usage)
    data["mean_latency_ms"] = usage.latency_ms / usage.calls if usage.calls else 0.0
    data["mean_tokens_per_call"] = usage.total_tokens / usage.calls if usage.calls else 0.0
    return data


def _amortization(compile_usage: dict[str, Any], baseline_usage: dict[str, Any], hybrid_usage: dict[str, Any], reflex_uses: float) -> dict[str, Any]:
    """Compare one-time compilation cost against per-use inference savings.

    The reflex is compiled once and reused on every represented decision. Whether that
    fixed cost is worthwhile depends on how many times the reflex is actually used
    before compilation cost, measured in tokens or LLM wall-clock latency, is repaid by
    avoided LLM calls. This does not model retraining or drift monitoring cost.
    """
    if reflex_uses <= 0:
        return {
            "reflex_uses": reflex_uses,
            "tokens_saved_per_reflex_use": None,
            "latency_saved_ms_per_reflex_use": None,
            "break_even_reflex_uses_tokens": None,
            "break_even_reflex_uses_latency": None,
            "amortized_fraction_tokens": None,
            "amortized_fraction_latency": None,
            "break_even_reached": False,
        }

    tokens_saved = baseline_usage["total_tokens"] - hybrid_usage["total_tokens"]
    latency_saved_ms = baseline_usage["latency_ms"] - hybrid_usage["latency_ms"]
    tokens_saved_per_use = tokens_saved / reflex_uses
    latency_saved_per_use = latency_saved_ms / reflex_uses

    break_even_tokens = (
        compile_usage["total_tokens"] / tokens_saved_per_use if tokens_saved_per_use > 0 else None
    )
    break_even_latency = (
        compile_usage["latency_ms"] / latency_saved_per_use if latency_saved_per_use > 0 else None
    )

    return {
        "reflex_uses": reflex_uses,
        "tokens_saved_per_reflex_use": tokens_saved_per_use,
        "latency_saved_ms_per_reflex_use": latency_saved_per_use,
        "break_even_reflex_uses_tokens": break_even_tokens,
        "break_even_reflex_uses_latency": break_even_latency,
        "amortized_fraction_tokens": (reflex_uses / break_even_tokens) if break_even_tokens else None,
        "amortized_fraction_latency": (reflex_uses / break_even_latency) if break_even_latency else None,
        "break_even_reached": bool(
            break_even_tokens is not None and reflex_uses >= break_even_tokens
        ),
    }


def _evaluation_tasks(*, quick: bool) -> list:
    known = ["missing_import", "wrong_constant", "renamed_symbol", "off_by_one"]
    tasks = []
    n = 1 if quick else 3
    for r in range(n):
        for i, family in enumerate(known):
            tasks.append(make_task(family, 500 + r * 10 + i))
    # syntax_error is withheld from reflex compilation to test fallback behavior.
    for i in range(1 if quick else 3):
        tasks.append(make_task("syntax_error", 800 + i))
    return tasks


def run_p22_live_benchmark(
    controller: OpenAICompatibleCodingDeliberator,
    *,
    quick: bool = False,
) -> dict[str, Any]:
    encoder = AgentFeatureEncoder()
    train = make_split(300, 2 if quick else 5, include_ood=False)
    validation = make_split(400, 1 if quick else 2, include_ood=False)

    warmup_before = controller.snapshot()
    selection, gate, encoder, compile_stats = compile_agent_reflex(
        train,
        validation,
        controller,
        encoder=encoder,
        random_state=22,
    )
    warmup_usage = controller.snapshot().delta(warmup_before)

    eval_tasks = _evaluation_tasks(quick=quick)

    baseline_before = controller.snapshot()
    baseline_agent = ParadigmCodingAgent(controller, encoder=encoder)
    baseline_eps = [baseline_agent.run(task) for task in eval_tasks]
    baseline_usage = controller.snapshot().delta(baseline_before)

    hybrid_before = controller.snapshot()
    hybrid_agent = ParadigmCodingAgent(controller, encoder=encoder, selection=selection, ood_gate=gate)
    hybrid_eps = [hybrid_agent.run(task) for task in eval_tasks]
    hybrid_usage = controller.snapshot().delta(hybrid_before)

    baseline_summary = summarize_episodes(baseline_eps)
    hybrid_summary = summarize_episodes(hybrid_eps)
    known_hybrid = summarize_episodes([e for e in hybrid_eps if e.family != "syntax_error"])
    ood_hybrid = summarize_episodes([e for e in hybrid_eps if e.family == "syntax_error"])

    def reduction(a: float, b: float) -> float:
        return (a - b) / a if a else 0.0

    warmup_usage_dict = _usage_dict(warmup_usage)
    baseline_usage_dict = _usage_dict(baseline_usage)
    hybrid_usage_dict = _usage_dict(hybrid_usage)
    amortization = _amortization(
        warmup_usage_dict, baseline_usage_dict, hybrid_usage_dict, float(hybrid_summary.get("reflex_calls", 0.0))
    )

    result = {
        "phase": "P2.2",
        "executed_live_llm": True,
        "controller": {
            "base_url": controller.base_url,
            "model": controller.model,
            "temperature": controller.temperature,
            "max_tokens": controller.max_tokens,
            "pricing_configured": bool(
                controller.input_cost_per_million or controller.output_cost_per_million
            ),
        },
        "scope": "real OpenAI-compatible LLM slow path versus compiled Paradigm control reflex",
        "compile": {
            "stats": compile_stats,
            "selected_backend": selection.backend,
            "threshold": selection.threshold,
            "llm_usage": warmup_usage_dict,
        },
        "evaluation": {
            "episodes": len(eval_tasks),
            "families": sorted({task.family for task in eval_tasks}),
            "baseline": baseline_summary,
            "hybrid": hybrid_summary,
            "known_hybrid": known_hybrid,
            "withheld_ood_hybrid": ood_hybrid,
            "baseline_llm_usage": baseline_usage_dict,
            "hybrid_llm_usage": hybrid_usage_dict,
            "llm_call_reduction": reduction(baseline_usage.calls, hybrid_usage.calls),
            "token_reduction": reduction(baseline_usage.total_tokens, hybrid_usage.total_tokens),
            "llm_latency_reduction": reduction(baseline_usage.latency_ms, hybrid_usage.latency_ms),
            "estimated_cost_reduction": reduction(
                baseline_usage.estimated_cost_usd, hybrid_usage.estimated_cost_usd
            )
            if baseline_usage.estimated_cost_usd
            else None,
            "success_preserved": bool(
                float(hybrid_summary.get("success_rate", 0.0))
                >= float(baseline_summary.get("success_rate", 0.0))
            ),
            "amortization": amortization,
        },
        "limitations": [
            "P2.2 compiles control-policy decisions only. It does not compile free-form code generation.",
            "The apply_fix tool remains a validated task repair primitive in this controlled vertical.",
            "LLM-output repair is counted explicitly and uses a deterministic safe action.",
            "Compilation cost is reported separately from evaluation savings.",
            "This benchmark is a static compile-then-evaluate design, not the P2.1 online acquisition loop. "
            "Whether savings grow with continued sequential use against a real model is not yet measured.",
            "The reflex amortization point compares tokens and latency only. It does not price compute, "
            "engineering time, or monitoring cost.",
        ],
    }
    return result


def live_environment_available() -> tuple[bool, str]:
    if not os.environ.get("PARADIGM_LLM_BASE_URL"):
        return False, "PARADIGM_LLM_BASE_URL is not set"
    if not os.environ.get("PARADIGM_LLM_MODEL"):
        return False, "PARADIGM_LLM_MODEL is not set"
    return True, "configured"


def write_p22_results(root: Path, result: dict[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "core_p22_llm.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    evaluation = result["evaluation"]
    compile_usage = result["compile"]["llm_usage"]
    baseline_usage = evaluation["baseline_llm_usage"]
    hybrid_usage = evaluation["hybrid_llm_usage"]
    known = evaluation["known_hybrid"]
    ood = evaluation["withheld_ood_hybrid"]
    amort = evaluation["amortization"]
    controller = result["controller"]

    lines: list[str] = []
    lines.append("# P2.2 Real LLM Controller Report")
    lines.append("")
    lines.append(
        "Paradigm's compiled control reflex is compared against the same OpenAI-compatible language model "
        "acting alone on the same evaluation stream. The model is queried only for the next tool-control "
        "action, never for patch synthesis. Compilation cost is measured separately from evaluation savings."
    )
    lines.append("")
    lines.append("## Controller")
    lines.append("")
    lines.append(f"- Model: `{controller['model']}`")
    lines.append(f"- Endpoint: `{controller['base_url']}`")
    lines.append(f"- Pricing configured: {controller['pricing_configured']}")
    lines.append("")
    lines.append("## Compilation cost")
    lines.append("")
    lines.append(f"- LLM calls used to gather training and validation traces: {compile_usage['calls']}")
    lines.append(f"- Tokens spent compiling: {compile_usage['total_tokens']}")
    lines.append(f"- Wall-clock LLM time spent compiling: {compile_usage['latency_ms'] / 1000:.1f} s")
    lines.append(f"- Selected backend: `{result['compile']['selected_backend']}`")
    lines.append("")
    lines.append("## End-to-end result")
    lines.append("")
    lines.append(f"- Evaluation episodes: {evaluation['episodes']}")
    lines.append(f"- Baseline success: {evaluation['baseline']['success_rate']:.1%}")
    lines.append(f"- Hybrid success: {evaluation['hybrid']['success_rate']:.1%}")
    lines.append(f"- Success preserved: {evaluation['success_preserved']}")
    lines.append(f"- Baseline LLM calls: {baseline_usage['calls']}")
    lines.append(f"- Hybrid LLM calls: {hybrid_usage['calls']}")
    lines.append(f"- Hybrid reflex calls: {evaluation['hybrid']['reflex_calls']:.0f}")
    lines.append(f"- LLM call reduction: {evaluation['llm_call_reduction']:.1%}")
    lines.append(f"- Token reduction: {evaluation['token_reduction']:.1%}")
    lines.append(f"- LLM latency reduction: {evaluation['llm_latency_reduction']:.1%}")
    lines.append(
        f"- Baseline invalid LLM actions / repairs: {baseline_usage['invalid_actions']} / {baseline_usage['repaired_actions']}"
    )
    lines.append(
        f"- Hybrid invalid LLM actions / repairs: {hybrid_usage['invalid_actions']} / {hybrid_usage['repaired_actions']}"
    )
    lines.append(f"- Invalid reflex actions reaching tools: {evaluation['hybrid']['invalid_reflex_actions']:.0f}")
    lines.append("")
    lines.append("## Known versus withheld families")
    lines.append("")
    lines.append(
        f"- Known-family fast-path coverage: {known.get('fast_path_coverage', 0.0):.1%} "
        f"({known.get('reflex_calls', 0.0):.0f} reflex calls, {known.get('deliberative_calls', 0.0):.0f} deliberative calls)"
    )
    lines.append(
        f"- Withheld syntax-error fast-path coverage: {ood.get('fast_path_coverage', 0.0):.1%} "
        f"({ood.get('reflex_calls', 0.0):.0f} reflex calls, {ood.get('deliberative_calls', 0.0):.0f} deliberative calls)"
    )
    lines.append("")
    lines.append(
        "The withheld family is expected to stay at 0% fast-path coverage. Paradigm does not force reflex "
        "coverage on a family it never compiled."
    )
    lines.append("")
    lines.append("## Reflex amortization")
    lines.append("")
    if amort.get("reflex_uses", 0):
        lines.append(f"- Reflex uses in this evaluation run: {amort['reflex_uses']:.0f}")
        lines.append(f"- Tokens saved per reflex use: {amort['tokens_saved_per_reflex_use']:.1f}")
        lines.append(f"- LLM latency saved per reflex use: {amort['latency_saved_ms_per_reflex_use']:.1f} ms")
        if amort.get("break_even_reflex_uses_tokens"):
            lines.append(
                f"- Break-even reflex uses (token cost basis): {amort['break_even_reflex_uses_tokens']:.1f}"
            )
            lines.append(
                f"- Break-even reflex uses (LLM latency basis): {amort['break_even_reflex_uses_latency']:.1f}"
            )
            lines.append(
                f"- Fraction of compilation cost recovered in this run (tokens): {amort['amortized_fraction_tokens']:.1%}"
            )
            lines.append(f"- Break-even reached in this run: {amort['break_even_reached']}")
    else:
        lines.append("- The reflex was never used in this evaluation run, so no amortization can be computed.")
    lines.append("")
    lines.append(
        "Compilation happens once; every additional represented episode adds reflex uses without adding "
        "compilation cost. A run that has not reached break-even is not a negative result by itself, but it "
        "means the measured evaluation stream was not long enough to recover the cost of training and "
        "validating this particular reflex."
    )
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    for item in result["limitations"]:
        lines.append(f"- {item}")
    lines.append("")
    (root / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_unexecuted_p22_report(root: Path, reason: str) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    result = {
        "phase": "P2.2",
        "executed_live_llm": False,
        "reason": reason,
        "required_environment": {
            "PARADIGM_LLM_BASE_URL": "OpenAI-compatible /v1 base URL, for example http://127.0.0.1:8080/v1",
            "PARADIGM_LLM_MODEL": "served model identifier",
            "PARADIGM_LLM_API_KEY": "optional",
            "PARADIGM_LLM_INPUT_COST_PER_M": "optional USD per million prompt tokens",
            "PARADIGM_LLM_OUTPUT_COST_PER_M": "optional USD per million completion tokens",
        },
    }
    (root / "core_p22_llm.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    report = "# P2.2 Real LLM Controller Report\n\n"
    report += "No live LLM result is recorded in this repository snapshot.\n\n"
    report += f"Reason: {reason}.\n\n"
    report += "The P2.2 adapter, telemetry, tests, and benchmark runner are implemented. Run the benchmark against "
    report += "an OpenAI-compatible endpoint to produce token, latency, call-reduction, cost, success, and OOD metrics.\n"
    (root / "REPORT.md").write_text(report, encoding="utf-8")
    return result
