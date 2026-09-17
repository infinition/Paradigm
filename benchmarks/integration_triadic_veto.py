"""Offline replay of the triadic veto on the frozen run 12 record.

Replays family-scoped certification sequentially on the run 12 buffer for the recorded
rule, the naive veto (any covered fresh disagreement) and the triadic veto (candidate
regression only), for m in {1, 2, 3, 5, 8}. Reports, per compile point and active family,
the classes of covered fresh disagreements and the verdicts, and answers the two
pre-registered questions at points 25 and 33. See ``triadic_veto_prereg.md``.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
from integration_sparse_heldout_sensitivity import fresh_compiler, load  # noqa: E402

RES = ROOT / "results" / "integration_laruche"
STATE = RES / "engine_state_shadow_after_36.pkl"
OUT_JSON = RES / "triadic_veto_audit.json"
OUT_MD = RES / "triadic_veto_audit.md"
MS = (1, 2, 3, 5, 8)
FAMILY = "laruche:file_edit:success:other"


def sequential(template, episodes, points, labels, *, recertify, m, triadic):
    c = fresh_compiler(template, recertify=recertify, m=m)
    c.triadic_veto = triadic
    out = []
    for point, label in zip(points, labels):
        c.buffer.episodes = [copy.deepcopy(ep) for ep in episodes[:point]]
        active_before = dict(c.state.family_thresholds)
        rec = c._compile_candidate(point)
        groups = rec.certification.get("groups", {})
        out.append({
            "label": label, "outcome": rec.outcome, "reason": rec.reason, "version_after": c.state.version,
            "active": {f: groups.get(f) for f in active_before},
        })
    return out


def main() -> None:
    compiler = load(STATE)
    labels_all = [p.stream_episode for p in compiler.state.promotions]
    sizes_all = [compiler.min_episodes + compiler.compile_every * i for i in range(len(labels_all))]
    keep = [i for i, lab in enumerate(labels_all) if lab >= 16]
    points = [sizes_all[i] for i in keep]
    labels = [labels_all[i] for i in keep]
    episodes = compiler.buffer.episodes

    variants = [("recorded", False, 1, False)]
    variants += [(f"naive m={m}", True, m, False) for m in MS]
    variants += [(f"triadic m={m}", True, m, True) for m in MS]
    replays = {v[0]: sequential(compiler, episodes, points, labels, recertify=v[1], m=v[2], triadic=v[3]) for v in variants}
    rec = {p.stream_episode: (p.outcome, p.reason) for p in compiler.state.promotions}
    reproduced = all((r["outcome"], r["reason"]) == rec[r["label"]] for r in replays["recorded"])

    def fam(label: str, point_label: int, family: str) -> dict[str, Any]:
        r = next(x for x in replays[label] if x["label"] == point_label)
        return r["active"].get(family) or {}

    # Pre-registered checks.
    checks: dict[str, Any] = {"reproduced": reproduced}
    fe25 = {v[0]: fam(v[0], 25, FAMILY) for v in variants}
    fe33 = {v[0]: fam(v[0], 33, FAMILY) for v in variants}
    fr25 = (fe25["triadic m=8"].get("retention") or {}).get("fresh") or {}
    fr33 = (fe33["triadic m=8"].get("retention") or {}).get("fresh") or {}
    checks["25_classified_candidate_regression"] = fr25.get("candidate_regression") == 1 and fr25.get("alternative_trajectory", 0) == 0
    checks["25_rejected_under_every_variant"] = all(v.get("status") == "rejected" for v in fe25.values())
    checks["25_triadic_veto_fires_in_probe_branch"] = "candidate_regression" in (fe25["triadic m=8"].get("reason") or "")
    checks["33_classified_alternative_trajectory"] = fr33.get("alternative_trajectory") == 1 and fr33.get("candidate_regression", 0) == 0
    checks["33_naive_veto_fires_m8"] = "fresh_disagreement" in (fe33["naive m=8"].get("reason") or "")
    checks["33_triadic_no_veto_m8"] = fe33["triadic m=8"].get("status") == "active" and fe33["triadic m=8"].get("reason") == "probe_recertified"
    held_out_33 = {l: fe33[l] for l in ("triadic m=1", "triadic m=2", "triadic m=3", "triadic m=5")}
    checks["33_held_out_still_rejected"] = all(v.get("status") == "rejected" for v in held_out_33.values())
    checks["33_held_out_reasons"] = sorted({v.get("reason") for v in held_out_33.values()})
    checks["33_held_out_selective_accuracy"] = fe33["triadic m=5"].get("selective_accuracy")
    checks["33_held_out_ece"] = fe33["triadic m=5"].get("ece")

    out = {"checks": checks, "replays": replays, "points": labels}
    OUT_JSON.write_text(json.dumps(out, indent=1, default=float))

    def fmt(v):
        return "n/a" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))

    L = ["# Triadic veto audit on frozen run 12", "",
         f"Live rule reproduced by the `recorded` replay: {'yes' if reproduced else 'no'}. Compile points (stream episodes): {labels}.", "",
         "## Covered fresh disagreements by class, per compile point and active family (triadic m=8 replay, probe branch with the fresh report)", "",
         "| point | family | fresh | covered | disagreements | candidate regression | alternative trajectory | ambiguous |", "|---|---|---|---|---|---|---|---|"]
    for r in replays["triadic m=8"]:
        for f, v in r["active"].items():
            fr = ((v or {}).get("retention") or {}).get("fresh") or {}
            L.append(f"| {r['label']} | `{f.split(':',1)[1]}` | {fr.get('n', (v or {}).get('validation_traces'))} | {fmt(fr.get('covered'))} | {fmt(fr.get('disagreements'))} | {fmt(fr.get('candidate_regression'))} | {fmt(fr.get('alternative_trajectory'))} | {fmt(fr.get('ambiguous'))} |")
    L += ["", f"## `{FAMILY.split(':',1)[1]}` at points 25 and 33 under every variant", "",
          "| variant | 25: verdict (reason) | 25: evidence | 33: verdict (reason) | 33: evidence | 33: sel. acc. | 33: ECE |", "|---|---|---|---|---|---|---|"]
    for v in variants:
        a, b = fe25[v[0]], fe33[v[0]]
        L.append(f"| {v[0]} | {a.get('status')} ({a.get('reason')}) | {(a.get('retention') or {}).get('evidence', 'held-out')} | {b.get('status')} ({b.get('reason')}) | {(b.get('retention') or {}).get('evidence', 'held-out')} | {fmt(b.get('selective_accuracy'))} | {fmt(b.get('ece'))} |")
    L += ["", "## Candidate decisions per variant", "", "| variant | " + " | ".join(str(l) for l in labels) + " | final version |", "|---|" + "---|" * len(labels) + "---|"]
    for v in variants:
        rs = replays[v[0]]
        L.append(f"| {v[0]} | " + " | ".join(f"{r['outcome']} ({r['reason'].split(':')[0]})" for r in rs) + f" | v{rs[-1]['version_after']} |")
    L += ["", "## Pre-registered checks", ""] + [f"- {k}: {v if not isinstance(v, bool) else ('pass' if v else 'FAIL')}" for k, v in checks.items()] + [""]
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
