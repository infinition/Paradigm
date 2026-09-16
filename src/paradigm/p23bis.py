from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from .agent_vertical import PHASES
from .llm_controller import OpenAICompatibleCodingDeliberator
from .online_learning import OnlineReflexCompiler
from .p23 import NOVEL_FAMILY, run_p23_live_online_benchmark
from .p23r import ARRIVALS, make_arrival_stream
from .schema import Trace

POISON_FROM = "inspect_file"
POISON_TO = "search_symbol"


def _is_failed_phase(trace: Trace) -> bool:
    return bool(trace.features[PHASES.index("failed")] > 0.5)


def _poisonable(trace: Trace, family: str) -> bool:
    return str(trace.metadata.get("family")) == family and trace.action == POISON_FROM and _is_failed_phase(trace)


def _poison_family(traces: list[Trace], family: str) -> tuple[list[Trace], int]:
    """Relabel one mature family's failed-phase decisions with a valid but wasteful action.

    Only failed-phase traces are relabelled: there, search_symbol is inside the allowed
    action set, so the runtime validity check cannot block it. Its effect is one extra
    tool call per episode of that family, a regression that never fails a test.
    """
    out: list[Trace] = []
    changed = 0
    for t in traces:
        if _poisonable(t, family):
            out.append(Trace(features=t.features, action=POISON_TO, valid=t.valid, metadata=dict(t.metadata)))
            changed += 1
        else:
            out.append(t)
    return out, changed


def negative_control(compiler: OnlineReflexCompiler, *, damaged_family: str | None = None) -> dict[str, Any]:
    """Certify a candidate that keeps the novel family intact but damages one mature family.

    Evaluated on the buffer state at the end of the stream, under both certification rules.
    Also certifies the clean candidate from the same split so an unnecessary rejection of a
    good candidate would be visible.
    """
    train, validation = compiler.buffer.split(compiler.validation_fraction)
    if not train or not validation:
        return {"feasible": False, "reason": "insufficient_split"}
    families_with_probes = sorted(f for f in compiler.state.probes if f != NOVEL_FAMILY)
    if damaged_family is None:
        damaged_family = next((f for f in families_with_probes if any(_poisonable(t, f) for t in train)), None)
    if damaged_family is None:
        return {"feasible": False, "reason": "no_mature_family_with_poisonable_traces"}

    poisoned_train, changed = _poison_family(train, damaged_family)
    clean_sel, clean_gate, _ = compiler.fit_candidate(train, validation)
    poison_sel, poison_gate, _ = compiler.fit_candidate(poisoned_train, validation)

    def agreement_on_family(selection, family: str) -> dict[str, Any]:
        probe = compiler.state.probes.get(family)
        if probe is None:
            return {"probes": 0, "agreement": None}
        hits = 0
        for t in probe.traces:
            action, _, _ = selection.reflex.predict(t.features)
            hits += int(str(action) == t.action)
        return {"probes": len(probe.traces), "agreement": hits / len(probe.traces)}

    return {
        "feasible": True,
        "damaged_family": damaged_family,
        "poisoned_traces": changed,
        "train_traces": len(train),
        "validation_traces": len(validation),
        "validation_contains_damaged_family": any(t.metadata.get("family") == damaged_family for t in validation),
        "clean_candidate": {
            "recent": compiler.certify_candidate(clean_sel, clean_gate, train, validation, mode="recent"),
            "family_aware": compiler.certify_candidate(clean_sel, clean_gate, train, validation, mode="family_aware"),
            "damaged_family_probe_agreement": agreement_on_family(clean_sel, damaged_family),
            "novel_family_probe_agreement": agreement_on_family(clean_sel, NOVEL_FAMILY),
        },
        "poisoned_candidate": {
            "recent": compiler.certify_candidate(poison_sel, poison_gate, poisoned_train, validation, mode="recent"),
            "family_aware": compiler.certify_candidate(poison_sel, poison_gate, poisoned_train, validation, mode="family_aware"),
            "damaged_family_probe_agreement": agreement_on_family(poison_sel, damaged_family),
            "novel_family_probe_agreement": agreement_on_family(poison_sel, NOVEL_FAMILY),
        },
    }


def _candidate_comparison(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for p in result["promotions"]:
        primary = p.get("certification") or {}
        shadow = p.get("shadow_certification") or {}
        if not primary:
            continue
        rows.append(
            {
                "stream_episode": p["stream_episode"],
                "primary_mode": primary.get("mode"),
                "primary_outcome": primary.get("outcome"),
                "primary_reason": primary.get("reason"),
                "shadow_mode": shadow.get("mode"),
                "shadow_outcome": shadow.get("outcome"),
                "shadow_reason": shadow.get("reason"),
                "probe_evaluations": primary.get("probe_evaluations", 0) + shadow.get("probe_evaluations", 0),
                "groups": primary.get("groups") or shadow.get("groups") or {},
            }
        )
    return rows


def run_p23bis_pair(
    controller: OpenAICompatibleCodingDeliberator,
    *,
    arrival: str,
    seed: int,
    root: Path,
    log=print,
    compiler_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the same stream under both certification rules, each shadowing the other."""
    root.mkdir(parents=True, exist_ok=True)
    out = {}
    for primary, shadow in (("recent", "family_aware"), ("family_aware", "recent")):
        run_root = root / f"{arrival}__s{seed}__{primary}"
        path = run_root / "core_p23_online_llm.json"
        if path.exists():
            log(f"skip {run_root.name}")
            out[primary] = json.loads(path.read_text())
            continue
        stream, phases = make_arrival_stream(arrival, seed)
        result = run_p23_live_online_benchmark(
            controller,
            stream=stream,
            phases=phases,
            random_state=21 + seed,
            arrival=arrival,
            compiler_options={"certification": primary, "shadow_certification": shadow, **(compiler_options or {})},
            return_compiler=True,
        )
        compiler = result.pop("_compiler")
        result["replication"] = {"model": controller.model, "api_style": controller.api_style, "arrival": arrival, "seed": seed}
        result["certification_mode"] = primary
        result["certification_options"] = dict(compiler_options or {})
        result["candidate_comparison"] = _candidate_comparison(result)
        if primary == "family_aware":
            result["negative_control"] = negative_control(compiler)
            result["retention_probes"] = {
                fam: {"traces": len(pr.traces), "created_version": pr.created_version, "created_episode": pr.created_stream_episode}
                for fam, pr in compiler.state.probes.items()
            }
        run_root.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
        sig = result["signature_metrics"]
        log(
            f"done {run_root.name}: success {result['online']['success_rate']:.0%}, calls -{result['llm_usage']['llm_call_reduction']:.0%}, "
            f"TTR {sig['time_to_reflex']['validated_episodes']}, deploy {result['novel_family']['represented_from_episode']}, "
            f"outcome {sig['time_to_reflex'].get('outcome')}"
        )
        out[primary] = result
    return out


def _disagreement_matrix(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare the recent and family-aware verdicts on every candidate seen in any run.

    Each candidate is classified by the pair (recent verdict, family-aware verdict) whichever
    rule was authoritative. A family-aware rejection is a retention catch when a retention
    probe group failed, a conservative rejection when only a novel-family group failed while
    the recent rule accepted, and an evidence gap when the verdict was insufficient_evidence.
    """
    counts: dict[str, int] = {}
    for r in runs:
        primary_mode = r["certification_mode"]
        for p in r["promotions"]:
            c = p.get("certification") or {}
            sh = p.get("shadow_certification") or {}
            if not c or not sh:
                continue
            recent = c if primary_mode == "recent" else sh
            fam = sh if primary_mode == "recent" else c
            ro, fo = recent.get("outcome"), fam.get("outcome")
            groups = fam.get("groups") or {}
            if ro == fo:
                key = f"agree_{ro}"
            elif fo == "insufficient_evidence":
                key = f"recent_{ro}__family_insufficient_evidence"
            elif ro == "promoted" and fo == "rejected":
                retention_failed = any(g["kind"] == "retention" and g["status"] == "fail" for g in groups.values())
                key = "recent_promoted__family_rejected_retention_catch" if retention_failed else "recent_promoted__family_rejected_conservative"
            elif ro == "rejected" and fo == "promoted":
                key = "recent_rejected__family_promoted_rescue"
            else:
                key = f"recent_{ro}__family_{fo}"
            counts[key] = counts.get(key, 0) + 1
    return counts


def aggregate_p23bis(root: Path) -> dict[str, Any]:
    runs = [json.loads(p.read_text()) for p in sorted(root.glob("*/core_p23_online_llm.json"))]
    by_key: dict[tuple[str, int], dict[str, dict[str, Any]]] = {}
    for r in runs:
        key = (r["replication"]["arrival"], r["replication"]["seed"])
        by_key.setdefault(key, {})[r["certification_mode"]] = r
    pairs = []
    for (arrival, seed), modes in sorted(by_key.items()):
        rec, fam = modes.get("recent"), modes.get("family_aware")
        row: dict[str, Any] = {"arrival": arrival, "seed": seed}
        for label, r in (("recent", rec), ("family_aware", fam)):
            if r is None:
                continue
            sig = r["signature_metrics"]
            row[label] = {
                "online_success": r["online"]["success_rate"],
                "llm_call_reduction": r["llm_usage"]["llm_call_reduction"],
                "ttr_episodes": sig["time_to_reflex"]["validated_episodes"],
                "deployment_episode": r["novel_family"]["represented_from_episode"],
                "outcome": sig["time_to_reflex"].get("outcome"),
                "false_fast_path": r["novel_family"]["unknown_false_fast_path_rate"],
                "known_success_after": r["old_family_retention"]["known_after_representation"].get("success_rate"),
                "known_fast_path_after": r["old_family_retention"]["known_after_representation"].get("fast_path_coverage"),
                "promotions": sum(1 for p in r["promotions"] if p["promoted"]),
                "candidates": len(r["promotions"]),
                "probe_evaluations": sum((p.get("certification") or {}).get("probe_evaluations", 0) for p in r["promotions"]),
                "outcomes": {
                    o: sum(1 for p in r["promotions"] if (p.get("certification") or {}).get("outcome") == o)
                    for o in ("promoted", "rejected", "insufficient_evidence")
                },
                "shadow_disagreements": sum(
                    1 for c in r.get("candidate_comparison", []) if c["primary_outcome"] != c["shadow_outcome"]
                ),
            }
        if rec and fam:
            d_rec, d_fam = row["recent"]["deployment_episode"], row["family_aware"]["deployment_episode"]
            row["certification_delay_episodes"] = (d_fam - d_rec) if (d_rec is not None and d_fam is not None) else None
            row["additional_deliberative_decisions"] = int(
                fam["llm_usage"]["online"]["calls"] - rec["llm_usage"]["online"]["calls"]
            )
            row["negative_control"] = fam.get("negative_control")
            nc = fam.get("negative_control") or {}
            # A rule only discriminates when it promotes the clean candidate; a rule that rejects
            # both clean and poisoned candidates says nothing about the damage.
            row["negative_control_verdict"] = {}
            if nc.get("feasible"):
                for rule in ("recent", "family_aware"):
                    clean = nc["clean_candidate"][rule]["outcome"]
                    poisoned = nc["poisoned_candidate"][rule]["outcome"]
                    if clean != "promoted" and poisoned == "promoted":
                        verdict = "inversion"
                    elif clean != "promoted":
                        verdict = "non_discriminating"
                    elif poisoned == "promoted":
                        verdict = "missed"
                    else:
                        verdict = "caught"
                    row["negative_control_verdict"][rule] = verdict
        pairs.append(row)
    matrix = _disagreement_matrix(runs)
    verdicts = {rule: {"caught": 0, "missed": 0, "non_discriminating": 0, "inversion": 0} for rule in ("recent", "family_aware")}
    for row in pairs:
        for rule, v in (row.get("negative_control_verdict") or {}).items():
            verdicts[rule][v] += 1
    caught = verdicts["family_aware"]["caught"]
    extra = sum(row.get("additional_deliberative_decisions", 0) for row in pairs if "additional_deliberative_decisions" in row)
    summary = {
        "phase": "P2.3R-bis",
        "pairs": pairs,
        "disagreement_matrix": matrix,
        "retention_protection": {
            "negative_control_verdicts": verdicts,
            "pairs_with_negative_control": sum(1 for row in pairs if (row.get("negative_control") or {}).get("feasible")),
            "additional_deliberative_decisions_total": extra,
            "yield_regressions_caught_per_additional_decision": (caught / extra) if extra > 0 else None,
        },
    }
    (root / "core_p23r_bis_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_p23bis_report(root, summary)
    return summary


def _pct(value) -> str:
    return "n/a" if value is None else f"{value:.0%}"


def write_p23bis_report(root: Path, summary: dict[str, Any]) -> None:
    lines = ["# P2.3R-bis Family-Aware Certification Report", ""]
    lines.append(
        "Each stream is run twice with the same model, tasks, compiler cadence, and thresholds. In one run the "
        "P2.1 recent-split rule decides promotion and family-aware certification is evaluated in shadow; in the "
        "other the roles are reversed. Family-aware certification requires every family in the validation split "
        "to have enough episodes and pass shadow acceptance on its own, and every mature family to pass coverage "
        "and agreement on an immutable retention probe set frozen at its first promotion. A negative control "
        "candidate that preserves the novel family but relabels one mature family's decisions is certified "
        "under both rules on the final buffer."
    )
    lines.append("")
    lines.append("Narrative interpretation: `INTERPRETATION.md` in this directory.")
    lines.append("")
    lines.append("## Live stream comparison")
    lines.append("")
    lines.append("| Arrival | Seed | Rule | Success | LLM calls | TTR | Deployed at | Outcome | False FP | Known success after | Known fast path after | Candidates promoted / rejected / insufficient | Probe evaluations | Shadow disagreements |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for row in summary["pairs"]:
        for rule in ("recent", "family_aware"):
            r = row.get(rule)
            if not r:
                continue
            o = r["outcomes"]
            ks = "n/a" if r["known_success_after"] is None else f"{r['known_success_after']:.0%}"
            kf = "n/a" if r["known_fast_path_after"] is None else f"{r['known_fast_path_after']:.0%}"
            lines.append(
                f"| {row['arrival']} | {row['seed']} | {rule} | {r['online_success']:.0%} | -{r['llm_call_reduction']:.0%} | "
                f"{r['ttr_episodes']} | {r['deployment_episode']} | {r['outcome']} | {r['false_fast_path']:.0%} | {ks} | {kf} | "
                f"{o['promoted']} / {o['rejected']} / {o['insufficient_evidence']} | {r['probe_evaluations']} | {r['shadow_disagreements']} |"
            )
    lines.append("")
    lines.append("## Certifier disagreement on live candidates")
    lines.append("")
    lines.append(
        "Every candidate compiled in any run, classified by the verdict each rule gave (one of them authoritative, "
        "the other in shadow). Live streams contain no deliberately damaged candidates, so retention catches on live "
        "candidates are not expected; the negative control section reports the deliberate damage case."
    )
    lines.append("")
    lines.append("| Recent | Family-aware | Count | Interpretation |")
    lines.append("|---|---|---|---|")
    labels = {
        "agree_promoted": ("promote", "promote", "agreement"),
        "agree_rejected": ("reject", "reject", "agreement"),
        "agree_insufficient_evidence": ("insufficient", "insufficient", "agreement"),
        "recent_promoted__family_rejected_retention_catch": ("promote", "reject", "retention catch: a mature-family probe group failed"),
        "recent_promoted__family_rejected_conservative": ("promote", "reject", "conservative: novel family below floor on its own while the overall rule passed"),
        "recent_rejected__family_promoted_rescue": ("reject", "promote", "family-aware accepts what recent blocks"),
        "recent_promoted__family_insufficient_evidence": ("promote", "insufficient", "evidence availability: a family was absent from the validation split"),
        "recent_rejected__family_insufficient_evidence": ("reject", "insufficient", "evidence availability"),
    }
    for key, count in sorted(summary["disagreement_matrix"].items()):
        a, b, why = labels.get(key, (key, "", ""))
        lines.append(f"| {a} | {b} | {count} | {why} |")
    rp = summary["retention_protection"]
    v = rp["negative_control_verdicts"]
    lines.append("")
    lines.append(
        "Negative control verdicts (a rule discriminates only when it promotes the clean candidate): "
        f"family-aware caught {v['family_aware']['caught']}, missed {v['family_aware']['missed']}, "
        f"non-discriminating {v['family_aware']['non_discriminating']}, inversions {v['family_aware']['inversion']}; "
        f"recent caught {v['recent']['caught']}, missed {v['recent']['missed']}, non-discriminating "
        f"{v['recent']['non_discriminating']}, inversions {v['recent']['inversion']}, out of "
        f"{rp['pairs_with_negative_control']} pairs. Additional deliberative decisions across pairs: "
        f"{rp['additional_deliberative_decisions_total']}. Diagnostic yield (regressions caught by family-aware per "
        f"additional deliberative decision): {rp['yield_regressions_caught_per_additional_decision']:.4f}."
    )
    lines.append("")
    lines.append("## Certification delay and negative control")
    lines.append("")
    lines.append("| Arrival | Seed | Novel deployment delay (episodes) | Additional deliberative decisions | Damaged family | Poisoned traces | Damaged family in validation | Clean: recent / family-aware | Poisoned: recent / family-aware | Verdict recent / family-aware | Poisoned probe agreement on damaged family | Poisoned probe agreement on novel family |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for row in summary["pairs"]:
        nc = row.get("negative_control") or {}
        if not nc.get("feasible"):
            lines.append(f"| {row['arrival']} | {row['seed']} | {row.get('certification_delay_episodes')} | {row.get('additional_deliberative_decisions')} | n/a | | | | | | | |")
            continue
        c, pz = nc["clean_candidate"], nc["poisoned_candidate"]
        lines.append(
            f"| {row['arrival']} | {row['seed']} | {row.get('certification_delay_episodes')} | {row.get('additional_deliberative_decisions')} | {nc['damaged_family']} | {nc['poisoned_traces']} | "
            f"{nc['validation_contains_damaged_family']} | {c['recent']['outcome']} / {c['family_aware']['outcome']} | "
            f"{pz['recent']['outcome']} / {pz['family_aware']['outcome']} | "
            f"{row['negative_control_verdict'].get('recent')} / {row['negative_control_verdict'].get('family_aware')} | "
            f"{_pct(pz['damaged_family_probe_agreement']['agreement'])} | {_pct(pz['novel_family_probe_agreement']['agreement'])} |"
        )
    lines.append("")
    (root / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
