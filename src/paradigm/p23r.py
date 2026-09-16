from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from typing import Any

from .agent_scenarios import make_task
from .llm_controller import OpenAICompatibleCodingDeliberator
from .p23 import (
    NOVEL_FAMILY,
    derive_promotion_audit,
    derive_signature_metrics,
    run_p23_live_online_benchmark,
    write_p23_results,
)

KNOWN = ("missing_import", "wrong_constant", "renamed_symbol", "off_by_one")
ARRIVALS = ("burst", "interleaved", "periodic", "rare")
WARMUP_ROUNDS = 3
STREAM_LENGTH = 69


def make_arrival_stream(arrival: str, seed: int) -> tuple[list, list[str]]:
    """69-episode stream with the novel family arriving in one of four patterns.

    burst: P2.1 layout (32 known, 12 novel, 25 mixed). interleaved: 17 novel episodes
    spread evenly after warmup. periodic: blocks of 3 novel then 9 known. rare: one
    novel episode every eighth episode. The seed offsets task indices so every seed
    sees different task instances.
    """
    if arrival not in ARRIVALS:
        raise ValueError(f"unknown arrival: {arrival!r}")
    offset = seed * 1000
    tasks: list = []
    phases: list[str] = []
    known_counter = 0
    novel_counter = 0

    def known_task():
        nonlocal known_counter
        family = KNOWN[known_counter % len(KNOWN)]
        task = make_task(family, offset + known_counter)
        known_counter += 1
        return task

    def novel_task():
        nonlocal novel_counter
        task = make_task(NOVEL_FAMILY, offset + 100 + novel_counter)
        novel_counter += 1
        return task

    if arrival == "burst":
        for _ in range(8 * len(KNOWN)):
            tasks.append(known_task())
            phases.append("A")
        for _ in range(12):
            tasks.append(novel_task())
            phases.append("B")
        for _ in range(5):
            for _ in range(len(KNOWN)):
                tasks.append(known_task())
                phases.append("C")
            tasks.append(novel_task())
            phases.append("C")
        return tasks, phases

    for _ in range(WARMUP_ROUNDS * len(KNOWN)):
        tasks.append(known_task())
        phases.append("A")
    remaining = STREAM_LENGTH - len(tasks)

    if arrival == "interleaved":
        novel_positions = {int((j + 0.5) * remaining / 17) for j in range(17)}
    elif arrival == "rare":
        novel_positions = {j for j in range(remaining) if j % 8 == 7}
    else:  # periodic
        novel_positions = {j for j in range(remaining) if j % 12 < 3 and j < 48}

    for j in range(remaining):
        tasks.append(novel_task() if j in novel_positions else known_task())
        phases.append("M")
    return tasks, phases


def run_p23r_matrix(
    *,
    controllers: dict[str, OpenAICompatibleCodingDeliberator],
    seeds: list[int],
    arrivals: list[str],
    root: Path,
    log=print,
) -> dict[str, Any]:
    """Run every (model, arrival, seed) combination, resuming from existing run files."""
    runs_dir = root / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    for model_name, controller in controllers.items():
        safe_model = f"{model_name.replace(':', '_').replace('/', '_')}__{controller.api_style}"
        for arrival in arrivals:
            for seed in seeds:
                run_root = runs_dir / f"{safe_model}__{arrival}__s{seed}"
                out = run_root / "core_p23_online_llm.json"
                if out.exists():
                    log(f"skip {run_root.name} (exists)")
                    continue
                stream, phases = make_arrival_stream(arrival, seed)
                start = time.perf_counter()
                result = run_p23_live_online_benchmark(
                    controller, stream=stream, phases=phases, random_state=21 + seed, arrival=arrival
                )
                result["replication"] = {
                    "model": model_name,
                    "api_style": controller.api_style,
                    "think": controller.think,
                    "arrival": arrival,
                    "seed": seed,
                }
                write_p23_results(run_root, result)
                sig = result["signature_metrics"]
                log(
                    f"done {run_root.name} in {time.perf_counter() - start:.0f}s: "
                    f"success {result['online']['success_rate']:.0%}, calls -{result['llm_usage']['llm_call_reduction']:.0%}, "
                    f"TTR {sig['time_to_reflex']['validated_episodes']}, "
                    f"false-fast {result['novel_family']['unknown_false_fast_path_rate']:.0%}"
                )
    return aggregate_p23r(root)


def _stat(values: list[float | None]) -> dict[str, Any]:
    clean = [float(v) for v in values if v is not None]
    if not clean:
        return {"n": 0, "mean": None, "median": None, "min": None, "max": None, "iqr": None}
    q = statistics.quantiles(clean, n=4) if len(clean) >= 2 else [clean[0], clean[0], clean[0]]
    return {
        "n": len(clean),
        "mean": statistics.fmean(clean),
        "median": statistics.median(clean),
        "min": min(clean),
        "max": max(clean),
        "iqr": q[2] - q[0],
    }


def _recovery_ratios(sig: dict[str, Any]) -> dict[str, float | None]:
    """Reflex dividend divided by acquisition debt, kept separate per unit."""
    debt = sig["acquisition_debt"]
    div = sig["reflex_dividend"]
    if sig["time_to_reflex"].get("outcome") != "promoted":
        return {"tokens": None, "calls": None, "latency": None}
    return {
        "tokens": (div["novel_tokens_saved"] / debt["tokens"]) if debt["tokens"] else None,
        "calls": (div["novel_llm_calls_saved"] / debt["decisions"]) if debt["decisions"] else None,
        "latency": (div["novel_llm_latency_saved_ms"] / debt["llm_latency_ms"]) if debt["llm_latency_ms"] else None,
    }


def _load_runs(directory: Path) -> list[dict[str, Any]]:
    runs = []
    for path in sorted(directory.glob("*/core_p23_online_llm.json")):
        r = json.loads(path.read_text())
        if "replication" not in r:
            name = path.parent.name.split("__")
            r["replication"] = {"model": name[0].replace("_", ":", 1), "api_style": name[1], "arrival": name[2], "seed": int(name[3][1:])}
        # Derived metrics are recomputed from the per-episode log so every run, whichever code
        # version wrote it, is summarized with the same definitions.
        r["signature_metrics"] = derive_signature_metrics(r)
        r["novel_family"]["time_to_reflex"] = r["signature_metrics"]["time_to_reflex"]
        r["promotion_audit"] = derive_promotion_audit(r)
        runs.append(r)
    return runs


def _cell(model: str, arrival: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    sigs = [r["signature_metrics"] for r in items]
    ret = [r["old_family_retention"] for r in items]
    ratios = [_recovery_ratios(s) for s in sigs]
    # promoted: certified within the stream. exercised: used at least once after promotion.
    reached = [s for s in sigs if s["time_to_reflex"].get("outcome") == "promoted"]
    exercised = [s for s in sigs if s["acquisition_debt"]["reflex_reached"]]
    return {
        "model": model,
        "arrival": arrival,
        "api_styles": sorted({r["replication"].get("api_style", "openai") for r in items}),
        "seeds": sorted(r["replication"]["seed"] for r in items),
        "online_success": _stat([r["online"]["success_rate"] for r in items]),
        "baseline_success": _stat([r["baseline"]["success_rate"] for r in items]),
        "llm_call_reduction": _stat([r["llm_usage"]["llm_call_reduction"] for r in items]),
        "token_reduction": _stat([r["llm_usage"]["token_reduction"] for r in items]),
        "llm_latency_reduction": _stat([r["llm_usage"]["llm_latency_reduction"] for r in items]),
        "invalid_llm_actions": _stat(
            [r["llm_usage"]["online"]["invalid_actions"] + r["llm_usage"]["baseline"]["invalid_actions"] for r in items]
        ),
        "invalid_reflex_actions": _stat([r["online"]["invalid_reflex_actions"] for r in items]),
        "reflex_reached": len(reached),
        "reflex_exercised": len(exercised),
        "mature_reflex_rate": len(reached) / len(items),
        "outcomes": {
            o: sum(1 for s in sigs if s["time_to_reflex"].get("outcome") == o)
            for o in ("promoted", "rejected", "insufficient_evidence")
        },
        "learning_episodes": _stat(
            [(s["time_to_reflex"].get("learning_evidence") or {}).get("episodes") for s in sigs]
        ),
        "certification_episodes": _stat(
            [(s["time_to_reflex"].get("certification_evidence") or {}).get("episodes") for s in sigs]
        ),
        "ttr_episodes": _stat([s["time_to_reflex"]["validated_episodes"] for s in sigs]),
        "ttr_decisions": _stat([s["time_to_reflex"]["validated_decisions"] for s in sigs]),
        "candidates_rejected_before_representation": _stat(
            [s["time_to_reflex"]["candidates_rejected_before_representation"] for s in sigs]
        ),
        "time_to_deployment_episode": _stat([r["novel_family"]["represented_from_episode"] for r in items]),
        "post_promotion_novel_exposure": _stat(
            [s["reflex_dividend"]["novel_episodes_after_representation"] for s in reached]
        ),
        "acquisition_debt": {
            "episodes": _stat([s["acquisition_debt"]["episodes"] for s in reached]),
            "decisions": _stat([s["acquisition_debt"]["decisions"] for s in reached]),
            "tokens": _stat([s["acquisition_debt"]["tokens"] for s in reached]),
            "llm_latency_ms": _stat([s["acquisition_debt"]["llm_latency_ms"] for s in reached]),
        },
        "reflex_dividend": {
            "novel_llm_calls_saved": _stat([s["reflex_dividend"]["novel_llm_calls_saved"] for s in reached]),
            "novel_tokens_saved": _stat([s["reflex_dividend"]["novel_tokens_saved"] for s in reached]),
            "novel_llm_latency_saved_ms": _stat([s["reflex_dividend"]["novel_llm_latency_saved_ms"] for s in reached]),
            "novel_episodes_after_representation": _stat(
                [s["reflex_dividend"]["novel_episodes_after_representation"] for s in reached]
            ),
        },
        "debt_recovery_ratio": {
            "tokens": _stat([x["tokens"] for x in ratios]),
            "calls": _stat([x["calls"] for x in ratios]),
            "latency": _stat([x["latency"] for x in ratios]),
        },
        "novel_fast_path_after_representation": _stat(
            [s["reflex_dividend"]["novel_fast_path_after_representation"] for s in sigs]
        ),
        "novel_success": _stat([r["novel_family"]["overall"]["success_rate"] for r in items]),
        "unknown_false_fast_path_rate": _stat([r["novel_family"]["unknown_false_fast_path_rate"] for r in items]),
        "known_success_before_novel": _stat([x.get("known_before_novel", {}).get("success_rate") for x in ret]),
        "known_success_after_representation": _stat(
            [x.get("known_after_representation", {}).get("success_rate") for x in ret]
        ),
        "known_fast_path_after_representation": _stat(
            [x.get("known_after_representation", {}).get("fast_path_coverage") for x in ret]
        ),
        "total_tokens_saved": _stat([s["reflex_dividend"]["total_tokens_saved"] for s in sigs]),
    }


def _per_run(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for r in runs:
        sig = r["signature_metrics"]
        ratios = _recovery_ratios(sig)
        out.append(
            {
                "model": r["replication"]["model"],
                "api_style": r["replication"].get("api_style", "openai"),
                "arrival": r["replication"]["arrival"],
                "seed": r["replication"]["seed"],
                "online_success": r["online"]["success_rate"],
                "llm_call_reduction": r["llm_usage"]["llm_call_reduction"],
                "token_reduction": r["llm_usage"]["token_reduction"],
                "llm_latency_reduction": r["llm_usage"]["llm_latency_reduction"],
                "ttr_episodes": sig["time_to_reflex"]["validated_episodes"],
                "outcome": sig["time_to_reflex"].get("outcome"),
                "deployment_episode": r["novel_family"]["represented_from_episode"],
                "post_promotion_exposure": sig["reflex_dividend"]["novel_episodes_after_representation"],
                "learning_episodes": (sig["time_to_reflex"].get("learning_evidence") or {}).get("episodes"),
                "certification_episodes": (sig["time_to_reflex"].get("certification_evidence") or {}).get("episodes"),
                "debt_tokens": sig["acquisition_debt"]["tokens"],
                "debt_latency_ms": sig["acquisition_debt"]["llm_latency_ms"],
                "dividend_tokens": sig["reflex_dividend"]["novel_tokens_saved"],
                "dividend_calls": sig["reflex_dividend"]["novel_llm_calls_saved"],
                "recovery_tokens": ratios["tokens"],
                "recovery_calls": ratios["calls"],
                "recovery_latency": ratios["latency"],
                "false_fast_path": r["novel_family"]["unknown_false_fast_path_rate"],
                "promotions": sum(1 for p in r["promotions"] if p["promoted"]),
                "rejections": sum(1 for p in r["promotions"] if not p["promoted"]),
            }
        )
    return out


def aggregate_p23r(root: Path) -> dict[str, Any]:
    runs = _load_runs(root / "runs")
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in runs:
        groups.setdefault((r["replication"]["model"], r["replication"]["arrival"]), []).append(r)
    cells = [_cell(model, arrival, items) for (model, arrival), items in sorted(groups.items())]

    # Teacher efficiency: per model across all arrival orders, counting only runs that reached a reflex.
    by_model: dict[str, list[dict[str, Any]]] = {}
    for r in runs:
        by_model.setdefault(r["replication"]["model"], []).append(r)
    teacher = []
    for model, items in sorted(by_model.items()):
        reached = [r["signature_metrics"] for r in items if r["signature_metrics"]["time_to_reflex"].get("outcome") == "promoted"]
        teacher.append(
            {
                "model": model,
                "runs": len(items),
                "successful_reflexes_acquired": len(reached),
                "validated_episodes_before_maturity": _stat([s["time_to_reflex"]["validated_episodes"] for s in reached]),
                "acquisition_tokens_before_maturity": _stat([s["acquisition_debt"]["tokens"] for s in reached]),
                "acquisition_latency_ms_before_maturity": _stat([s["acquisition_debt"]["llm_latency_ms"] for s in reached]),
                "mean_tokens_per_llm_call": _stat([r["llm_usage"]["baseline"]["mean_tokens_per_call"] for r in items]),
                "mean_latency_ms_per_llm_call": _stat([r["llm_usage"]["baseline"]["mean_latency_ms"] for r in items]),
                "online_success": _stat([r["online"]["success_rate"] for r in items]),
                "invalid_llm_actions": sum(
                    r["llm_usage"]["online"]["invalid_actions"] + r["llm_usage"]["baseline"]["invalid_actions"] for r in items
                ),
            }
        )

    # Certification boundary: shadow acceptance of every candidate as a function of how many
    # novel-family episodes its train split contained, per model, across all orders and seeds.
    boundary = []
    for model, items in sorted(by_model.items()):
        buckets: dict[int, list[float]] = {}
        passes: dict[int, int] = {}
        for r in items:
            for a in r["promotion_audit"]:
                if a["validation_traces"]["novel"] == 0:
                    continue  # candidates never asked to cover the novel family are not boundary evidence
                k = a["train_episodes"]["novel"]
                buckets.setdefault(k, []).append(a["overall_shadow_acceptance"])
                passes[k] = passes.get(k, 0) + (1 if a["promoted"] else 0)
        boundary.append(
            {
                "model": model,
                "by_novel_train_episodes": [
                    {
                        "novel_train_episodes": k,
                        "candidates": len(v),
                        "promoted": passes.get(k, 0),
                        "acceptance_min": min(v),
                        "acceptance_max": max(v),
                        "acceptances": sorted(v),
                    }
                    for k, v in sorted(buckets.items())
                ],
            }
        )

    control_dir = root / "transport_control"
    control_runs = _load_runs(control_dir) if control_dir.exists() else []
    summary = {
        "phase": "P2.3R",
        "runs": len(runs),
        "cells": cells,
        "teacher_efficiency": teacher,
        "certification_boundary": boundary,
        "per_run": _per_run(runs),
        "transport_control": _per_run(control_runs),
    }
    (root / "core_p23r_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_p23r_report(root, summary)
    return summary


def _fmt(stat: dict[str, Any], pct: bool = False, digits: int = 1) -> str:
    if stat["n"] == 0:
        return "n/a"
    if pct:
        return f"{stat['mean']:.{digits}%} [{stat['min']:.{digits}%}, {stat['max']:.{digits}%}]"
    return f"{stat['mean']:.{digits}f} [{stat['min']:.{digits}f}, {stat['max']:.{digits}f}]"


def _fmt_med(stat: dict[str, Any], pct: bool = False, digits: int = 1) -> str:
    if stat["n"] == 0:
        return "n/a"
    if pct:
        return f"{stat['median']:.{digits}%} (IQR {stat['iqr']:.{digits}%})"
    return f"{stat['median']:.{digits}f} (IQR {stat['iqr']:.{digits}f})"


def _run_rows(rows: list[dict[str, Any]]) -> list[str]:
    out = [
        "| Model | API | Arrival | Seed | Success | LLM calls | Tokens | TTR (learn + certify) | Outcome | Deployed at | Exposure after | Debt tokens | Dividend tokens | Recovery tokens / calls / latency | False FP | Promoted / rejected |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        ttr = "never" if r["ttr_episodes"] is None else f"{r['ttr_episodes']} ({r['learning_episodes']} + {r['certification_episodes']})"
        rec = (
            "n/a"
            if r["recovery_tokens"] is None
            else f"{r['recovery_tokens']:.0%} / {r['recovery_calls']:.0%} / {r['recovery_latency']:.0%}"
        )
        out.append(
            f"| {r['model']} | {r['api_style']} | {r['arrival']} | {r['seed']} | {r['online_success']:.0%} | "
            f"-{r['llm_call_reduction']:.0%} | -{r['token_reduction']:.0%} | {ttr} | {r.get('outcome')} | "
            f"{r.get('deployment_episode') if r.get('deployment_episode') is not None else 'never'} | {r.get('post_promotion_exposure')} | {r['debt_tokens']} | "
            f"{r['dividend_tokens']} | {rec} | {r['false_fast_path']:.0%} | {r['promotions']} / {r['rejections']} |"
        )
    return out


def write_p23r_report(root: Path, summary: dict[str, Any]) -> None:
    lines = ["# P2.3R Replication Report", ""]
    lines.append(
        "P2.3 repeated across seeds, models, and novel-family arrival orders with one transport, prompt, "
        "schema, temperature, output budget, compiler configuration, and promotion rule. Time-to-reflex (TTR) "
        "counts validated novel-family episodes before the first promotion that represents the family. A run "
        "where the reflex is never reached within the stream is a valid outcome. Debt recovery ratio is reflex "
        "dividend divided by acquisition debt, reported separately for tokens, LLM calls, and LLM latency."
    )
    lines.append("")
    lines.append(f"Runs in the primary matrix: {summary['runs']}")
    lines.append("")
    lines.append("Narrative interpretation: `INTERPRETATION.md` in this directory.")
    lines.append("")
    lines.append("## Per run")
    lines.append("")
    lines.extend(_run_rows(summary["per_run"]))
    lines.append("")
    lines.append("## Success and savings by model and arrival order")
    lines.append("")
    lines.append("| Model | Arrival | Seeds | Online success | Baseline success | LLM call reduction mean [min, max] | LLM call reduction median | Token reduction mean [min, max] | Token reduction median | Latency reduction mean | Invalid actions |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for c in summary["cells"]:
        lines.append(
            f"| {c['model']} | {c['arrival']} | {len(c['seeds'])} | {_fmt(c['online_success'], True)} | "
            f"{_fmt(c['baseline_success'], True)} | {_fmt(c['llm_call_reduction'], True)} | {_fmt_med(c['llm_call_reduction'], True)} | "
            f"{_fmt(c['token_reduction'], True)} | {_fmt_med(c['token_reduction'], True)} | "
            f"{c['llm_latency_reduction']['mean']:.1%} | {_fmt(c['invalid_llm_actions'], digits=0)} |"
        )
    lines.append("")
    lines.append("## Novel family acquisition")
    lines.append("")
    lines.append("| Model | Arrival | Promoted (certified) | Exercised after promotion | Outcomes promoted / rejected / insufficient | TTR median (IQR) | TTR mean [min, max] | Learning episodes | Certification episodes | Rejected before | Novel fast path after | Novel success | False fast path |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in summary["cells"]:
        o = c["outcomes"]
        lines.append(
            f"| {c['model']} | {c['arrival']} | {c['reflex_reached']}/{len(c['seeds'])} | {c['reflex_exercised']}/{len(c['seeds'])} | {o['promoted']} / {o['rejected']} / {o['insufficient_evidence']} | "
            f"{_fmt_med(c['ttr_episodes'], digits=0)} | {_fmt(c['ttr_episodes'])} | {_fmt(c['learning_episodes'])} | "
            f"{_fmt(c['certification_episodes'])} | {_fmt(c['candidates_rejected_before_representation'])} | "
            f"{_fmt(c['novel_fast_path_after_representation'], True)} | {_fmt(c['novel_success'], True)} | "
            f"{_fmt(c['unknown_false_fast_path_rate'], True)} |"
        )
    lines.append("")
    lines.append("## Acquisition debt, reflex dividend, and recovery")
    lines.append("")
    lines.append("Only runs whose novel family was promoted contribute to debt and dividend cells. A promoted reflex with no later novel exposure has a dividend of zero.")
    lines.append("")
    lines.append("| Model | Arrival | Deployed at episode | Novel exposure after | Debt episodes | Debt decisions | Debt tokens | Debt latency s | Dividend calls | Dividend tokens | Dividend latency s | Recovery tokens | Recovery calls | Recovery latency |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in summary["cells"]:
        d = c["acquisition_debt"]
        v = c["reflex_dividend"]
        rr = c["debt_recovery_ratio"]
        lat = lambda st: "n/a" if st["n"] == 0 else f"{st['mean'] / 1000:.1f}"
        lines.append(
            f"| {c['model']} | {c['arrival']} | {_fmt(c['time_to_deployment_episode'], digits=0)} | {_fmt(c['post_promotion_novel_exposure'], digits=0)} | "
            f"{_fmt(d['episodes'], digits=0)} | {_fmt(d['decisions'], digits=0)} | "
            f"{_fmt(d['tokens'], digits=0)} | {lat(d['llm_latency_ms'])} | {_fmt(v['novel_llm_calls_saved'], digits=0)} | "
            f"{_fmt(v['novel_tokens_saved'], digits=0)} | {lat(v['novel_llm_latency_saved_ms'])} | "
            f"{_fmt(rr['tokens'], True, 0)} | {_fmt(rr['calls'], True, 0)} | {_fmt(rr['latency'], True, 0)} |"
        )
    lines.append("")
    lines.append("## Old family retention")
    lines.append("")
    lines.append("| Model | Arrival | Known success before novel | Known success after representation | Known fast path after representation |")
    lines.append("|---|---|---|---|---|")
    for c in summary["cells"]:
        lines.append(
            f"| {c['model']} | {c['arrival']} | {_fmt(c['known_success_before_novel'], True)} | "
            f"{_fmt(c['known_success_after_representation'], True)} | {_fmt(c['known_fast_path_after_representation'], True)} |"
        )
    lines.append("")
    lines.append("## Teacher efficiency")
    lines.append("")
    lines.append("Per model across all arrival orders. Acquisition columns count only runs that reached a reflex.")
    lines.append("")
    lines.append("| Model | Runs | Reflexes acquired | Validated episodes before maturity | Acquisition tokens before maturity | Acquisition latency s before maturity | Tokens per LLM call | Latency ms per LLM call | Online success | Invalid actions |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for t in summary["teacher_efficiency"]:
        lat = t["acquisition_latency_ms_before_maturity"]
        lines.append(
            f"| {t['model']} | {t['runs']} | {t['successful_reflexes_acquired']} | {_fmt_med(t['validated_episodes_before_maturity'], digits=0)} | "
            f"{_fmt(t['acquisition_tokens_before_maturity'], digits=0)} | "
            f"{'n/a' if lat['n'] == 0 else f'{lat['mean'] / 1000:.1f}'} | "
            f"{t['mean_tokens_per_llm_call']['mean']:.0f} | {t['mean_latency_ms_per_llm_call']['mean']:.0f} | "
            f"{_fmt(t['online_success'], True)} | {t['invalid_llm_actions']} |"
        )
    lines.append("")
    lines.append("## Certification boundary")
    lines.append("")
    lines.append(
        "Shadow OOD acceptance of every candidate whose validation split contained the novel family, grouped by "
        "the number of novel-family episodes in its train split. This is observational: the compile cadence "
        "decides which configurations are tested, so it does not establish a minimum requirement."
    )
    lines.append("")
    lines.append("| Model | Novel episodes in train | Candidates | Promoted | Acceptance min | Acceptance max | Acceptances |")
    lines.append("|---|---|---|---|---|---|---|")
    for b in summary.get("certification_boundary", []):
        for row in b["by_novel_train_episodes"]:
            accs = ", ".join(f"{a:.2f}" for a in row["acceptances"])
            lines.append(
                f"| {b['model']} | {row['novel_train_episodes']} | {row['candidates']} | {row['promoted']} | "
                f"{row['acceptance_min']:.2f} | {row['acceptance_max']:.2f} | {accs} |"
            )
    lines.append("")
    if summary.get("transport_control"):
        lines.append("## Transport control")
        lines.append("")
        lines.append(
            "Runs completed before the matrix was restarted so both models share the native Ollama transport. "
            "They use the OpenAI-compatible endpoint and are kept for comparison only; they are not part of the primary matrix."
        )
        lines.append("")
        lines.extend(_run_rows(summary["transport_control"]))
        lines.append("")
    (root / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
