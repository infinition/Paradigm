"""Run 12 report: per compile point and active family, fresh and probe evidence and the
counterfactual verdict under every m, plus the economy of shadow sampling.

Reads the run 12 engine state, telemetry and decision log under
``results/integration_laruche/`` and replays family-scoped certification sequentially
per m in {1, 2, 3, 5, 8} on the same record (the live rule is the run 11 rule). No m is
selected. See ``shadow_sampling_prereg.md``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
from integration_sparse_heldout_sensitivity import load, sequential  # noqa: E402

RES = ROOT / "results" / "integration_laruche"
STATE = RES / "engine_state_shadow_after_36.pkl"
TELEMETRY = RES / "run12_telemetry.json"
LOG = RES / "run12_decision_log.json"
OUT_JSON = RES / "run12_shadow_report.json"
OUT_MD = RES / "run12_shadow_report.md"
MS = (1, 2, 3, 5, 8)


def fmt(v: Any) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.3f}"
    return str(v)


def main() -> None:
    compiler = load(STATE)
    telemetry = json.loads(TELEMETRY.read_text())
    rows = json.loads(LOG.read_text())["decisions"]
    episodes = compiler.buffer.episodes
    # The live cadence counts validated episodes: the k-th compile point uses the first
    # 8 + 4(k-1) buffer episodes, and is labeled by the stream episode at which it ran.
    labels = [p.stream_episode for p in compiler.state.promotions]
    sizes = [compiler.min_episodes + compiler.compile_every * i for i in range(len(labels))]
    keep = [i for i, lab in enumerate(labels) if lab >= 16]
    points = [sizes[i] for i in keep]
    point_label = {sizes[i]: labels[i] for i in keep}
    variants = [("recorded", False, 1)] + [(f"m={m}", True, m) for m in MS]
    replays = {label: sequential(compiler, episodes, points, recertify=r, m=m) for label, r, m in variants}
    for rows_ in replays.values():
        for r in rows_:
            r["label"] = point_label[r["point"]]
    rec = {p.stream_episode: (p.outcome, p.reason) for p in compiler.state.promotions}
    reproduced = all((r["outcome"], r["reason"]) == rec[r["label"]] for r in replays["recorded"])

    # Economy from the decision log.
    reflex = sum(1 for r in rows if r["source"] == "reflex")
    shadow = sum(1 for r in rows if r.get("reason") == "shadow_sample")
    natural = sum(1 for r in rows if r["source"] != "reflex" and r.get("reason") not in ("shadow_sample", "no_decision_requested"))
    shadow_outcomes: dict[str, int] = {}
    for r in rows:
        if r.get("reason") == "shadow_sample":
            shadow_outcomes[str(r.get("outcome"))] = shadow_outcomes.get(str(r.get("outcome")), 0) + 1
    reflex_outcomes: dict[str, int] = {}
    for r in rows:
        if r["source"] == "reflex":
            reflex_outcomes[str(r.get("outcome"))] = reflex_outcomes.get(str(r.get("outcome")), 0) + 1

    # Mandatory log: one row per compile point and active family, all m side by side.
    table: list[dict[str, Any]] = []
    for i, point in enumerate(points):
        base = replays["m=1"][i]
        for fam in sorted(base["active_verdicts"]):
            v1 = base["active_verdicts"][fam]
            # Fresh and probe statistics are reported in every branch; take them from any
            # variant that has them (the candidate is the same object at this point as long
            # as the trajectories agree, which the candidate column makes visible).
            fr: dict[str, Any] = {}
            v8: dict[str, Any] = {}
            for label, _, _ in reversed(variants):
                cand = replays[label][i]["active_verdicts"].get(fam, {})
                if cand.get("fresh") and not fr:
                    fr = cand["fresh"]
                if cand.get("evidence") == "probes_only" and not v8:
                    v8 = cand
            entry = {
                "point": point_label[point], "family": fam,
                "fresh_count": v1.get("n_fresh"),
                "fresh_gate_accepted": fr.get("gate_accepted"),
                "fresh_covered": fr.get("covered"),
                "fresh_disagreements": fr.get("disagreements"),
                # Probe numbers at the incumbent threshold (the probes_only branch), which is
                # the same basis at every point; the held-out branch scores probes at the
                # threshold it selected on the fresh traces, which varies.
                "probe_count": v8.get("probes", v1.get("probes")),
                "probe_agreement": v8.get("probe_agreement", v1.get("probe_agreement")),
                "probe_coverage": v8.get("probe_coverage", v1.get("probe_coverage")),
                "probe_gate_acceptance": v8.get("gate_acceptance"),
                "hard_veto": bool(fr.get("disagreements", 0)),
                "verdicts": {label: replays[label][i]["active_verdicts"].get(fam, {}).get("status") for label, _, _ in variants},
                "reasons": {label: replays[label][i]["active_verdicts"].get(fam, {}).get("reason") for label, _, _ in variants},
                "evidence": {label: replays[label][i]["active_verdicts"].get(fam, {}).get("evidence") for label, _, _ in variants},
                "candidate": {label: replays[label][i]["outcome"] for label, _, _ in variants},
                "candidate_reason": {label: replays[label][i]["reason"] for label, _, _ in variants},
            }
            table.append(entry)

    # Three levels of change relative to the recorded rule, per variant.
    levels = {}
    base = replays["recorded"]
    for label, _, _ in variants:
        path = fam = cand = 0
        for r, b in zip(replays[label], base):
            for f, v in r["active_verdicts"].items():
                bv = b["active_verdicts"].get(f, {})
                path += v.get("evidence") != bv.get("evidence")
                fam += v.get("status") != bv.get("status")
            cand += (r["outcome"], r["version_after"], tuple(r["active_after"])) != (b["outcome"], b["version_after"], tuple(b["active_after"]))
        levels[label] = {"evidence_path_changed": path, "family_verdict_changed": fam, "candidate_decision_changed": cand}

    out = {
        "reproduced": reproduced, "points": points, "levels": levels, "economy": {
            "natural_model_calls": natural, "shadow_sample_model_calls": shadow, "reflex_decisions": reflex,
            "model_calls_avoided": reflex, "net_calls_avoided_after_sampling": reflex - shadow,
            "shadow_outcomes": shadow_outcomes, "reflex_outcomes": reflex_outcomes, "telemetry": telemetry,
        },
        "table": table, "replays": replays,
    }
    OUT_JSON.write_text(json.dumps(out, indent=1, default=float))

    L = ["# Run 12 report: shadow sampling", "",
         f"Live rule reproduced by the `recorded` replay: {'yes' if reproduced else 'no'}. Compile points from the first promotion, labeled by stream episode: {[point_label[p] for p in points]} (buffer sizes {points}).", "",
         "## Economy", "",
         "| natural model calls | shadow-sample model calls | reflex decisions | model calls avoided | net after sampling overhead |", "|---|---|---|---|---|",
         f"| {natural} | {shadow} | {reflex} | {reflex} | {reflex - shadow} |", "",
         f"Shadow-sample outcomes: {shadow_outcomes}. Reflex outcomes: {reflex_outcomes}.", "",
         "## Per compile point and active family", "",
         "| point | family | fresh | fresh gate-accepted | fresh covered | fresh disagreements | probes | probe agreement | probe coverage | probe gate acc. | hard veto | " + " | ".join(f"{l} (family / candidate)" for l, _, _ in variants) + " |",
         "|---|---|---|---|---|---|---|---|---|---|---|" + "---|" * len(variants)]
    for e in table:
        cells = " | ".join(f"{e['verdicts'][l] or 'n/a'} ({e['reasons'][l]}) / {e['candidate'][l]}" for l, _, _ in variants)
        L.append(f"| {e['point']} | `{e['family'].split(':',1)[1]}` | {e['fresh_count']} | {fmt(e['fresh_gate_accepted'])} | {fmt(e['fresh_covered'])} | {fmt(e['fresh_disagreements'])} | {e['probe_count']} | {fmt(e['probe_agreement'])} | {fmt(e['probe_coverage'])} | {fmt(e['probe_gate_acceptance'])} | {'yes' if e['hard_veto'] else 'no'} | {cells} |")
    L += ["", "## Three levels of change relative to the recorded rule", "",
          "| variant | evidence path changed (family-points) | family verdict changed | candidate adoption decision changed |", "|---|---|---|---|"]
    for label, _, _ in variants:
        lv = levels[label]
        L.append(f"| {label} | {lv['evidence_path_changed']} | {lv['family_verdict_changed']} | {lv['candidate_decision_changed']} |")
    L += ["", "## Candidate verdicts per variant", "", "| variant | " + " | ".join(str(point_label[p]) for p in points) + " | final version | final active families |", "|---|" + "---|" * len(points) + "---|---|"]
    for label, _, _ in variants:
        rs = replays[label]
        L.append(f"| {label} | " + " | ".join(f"{r['outcome']} ({r['reason'].split(':',1)[0]})" for r in rs) + f" | v{rs[-1]['version_after']} | " + ", ".join(f"`{f.split(':',1)[1]}`" for f in rs[-1]["active_after"]) + " |")
    L.append("")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
