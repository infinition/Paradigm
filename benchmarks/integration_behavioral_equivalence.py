"""Offline replay of behavioral-equivalence scoring on the frozen records.

For run 12 (compile points 16 to 33), run 11 (16 to 24) and the runs 9A/9B record
(counterfactual family-scoped, 20 to 32): sequential family-scoped certification without
and with the LaRuche equivalence contract (TEST_EXECUTION only), under the recorded
rule, the triadic veto for m in {1, 2, 3, 5, 8}, and the naive veto at m = 8. Reports the
pre-registered checks and the materialized, hashed contract. See
``behavioral_equivalence_prereg.md``.
"""

from __future__ import annotations

import copy
import json
import pickle
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
from integration_sparse_heldout_sensitivity import fresh_compiler  # noqa: E402

from paradigm.integration.laruche import LaRucheAdapter  # noqa: E402

RES = ROOT / "results" / "integration_laruche"
RECORDS = {
    "run12": RES / "engine_state_shadow_after_36.pkl",
    "run11": RES / "engine_state_family_scoped_after_24.pkl",
    "run9": RES / "engine_state_after_32.pkl",
}
OUT_JSON = RES / "behavioral_equivalence_audit.json"
OUT_MD = RES / "behavioral_equivalence_audit.md"
MS = (1, 2, 3, 5, 8)
FAMILY = "laruche:file_edit:success:other"


def load_payload(path: Path) -> dict[str, Any]:
    with path.open("rb") as fh:
        return pickle.load(fh)


def compile_points(compiler) -> tuple[list[int], list[int]]:
    """(buffer sizes, stream labels) of the compile points at or after the first promotion,
    or every point from 8 + 4 * 3 for a record without family-scoped promotions."""
    labels = [p.stream_episode for p in compiler.state.promotions]
    if compiler.certification == "family_scoped":
        sizes = [compiler.min_episodes + compiler.compile_every * i for i in range(len(labels))]
        keep = [i for i, lab in enumerate(labels) if lab >= 16]
        return [sizes[i] for i in keep], [labels[i] for i in keep]
    n = len(compiler.buffer.episodes)
    sizes = list(range(20, n + 1, 4))
    return sizes, sizes


def sequential(template, episodes, points, labels, *, recertify, m, triadic, contract):
    c = fresh_compiler(template, recertify=recertify, m=m)
    c.triadic_veto = triadic
    c.equivalence = contract
    out = []
    for point, label in zip(points, labels):
        c.buffer.episodes = [copy.deepcopy(ep) for ep in episodes[:point]]
        active_before = dict(c.state.family_thresholds)
        rec = c._compile_candidate(point)
        groups = rec.certification.get("groups", {})
        out.append({
            "label": label, "outcome": rec.outcome, "reason": rec.reason, "version_after": c.state.version,
            "active_after": sorted(c.state.family_thresholds),
            "active": {f: groups.get(f) for f in active_before},
            "contract": (rec.certification or {}).get("equivalence"),
        })
    return out


def decisions(rows: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
    return [(r["label"], r["outcome"], r["version_after"], tuple(r["active_after"])) for r in rows]


def fmt(v: Any) -> str:
    return "n/a" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))


def main() -> None:
    variants = [("recorded", False, 1, False)] + [(f"triadic m={m}", True, m, True) for m in MS] + [("naive m=8", True, 8, False)]
    results: dict[str, Any] = {"records": {}, "checks": {}}
    for name, path in RECORDS.items():
        payload = load_payload(path)
        compiler = payload["compiler"]
        adapter = LaRucheAdapter(templates=payload.get("action_templates") or {})
        contract = adapter.equivalence_contract()
        points, labels = compile_points(compiler)
        episodes = compiler.buffer.episodes
        rec: dict[str, Any] = {"points": labels, "without": {}, "with": {}}
        for v in variants:
            rec["without"][v[0]] = sequential(compiler, episodes, points, labels, recertify=v[1], m=v[2], triadic=v[3], contract=None)
            rec["with"][v[0]] = sequential(compiler, episodes, points, labels, recertify=v[1], m=v[2], triadic=v[3], contract=contract)
        rec["contract"] = contract.materialize(set(payload.get("action_templates") or {}))
        rec["identical_decisions"] = {v[0]: decisions(rec["without"][v[0]]) == decisions(rec["with"][v[0]]) for v in variants}
        results["records"][name] = rec

    r12 = results["records"]["run12"]

    def fam(side: str, label: str, point: int, family: str = FAMILY) -> dict[str, Any]:
        row = next(x for x in r12[side][label] if x["label"] == point)
        return row["active"].get(family) or {}

    checks = results["checks"]
    live = {p.stream_episode: (p.outcome, p.reason) for p in load_payload(RECORDS["run12"])["compiler"].state.promotions}
    checks["run12_recorded_without_contract_reproduces_live"] = all((x["outcome"], x["reason"]) == live[x["label"]] for x in r12["without"]["recorded"])
    checks["25_rejected_every_variant_with_contract"] = all(fam("with", v[0], 25).get("status") == "rejected" for v in variants)
    fe33 = {v[0]: fam("with", v[0], 33) for v in variants}
    held = {l: fe33[l] for l in ("recorded", "triadic m=1", "triadic m=2", "triadic m=3", "triadic m=5")}
    checks["33_held_out_passes_with_contract"] = all(v.get("status") == "active" for v in held.values())
    checks["33_held_out_selective_accuracy"] = fe33["triadic m=5"].get("selective_accuracy")
    checks["33_held_out_ece"] = fe33["triadic m=5"].get("ece")
    checks["33_literal_agreement"] = (fe33["triadic m=5"].get("retention") or {}).get("literal_agreement")
    checks["33_equivalent_agreement"] = (fe33["triadic m=5"].get("retention") or {}).get("equivalent_agreement")
    checks["33_candidate_no_new_family_every_variant"] = all(next(x for x in r12["with"][v[0]] if x["label"] == 33)["reason"] == "no_new_family" for v in variants)
    checks["run11_identical"] = all(results["records"]["run11"]["identical_decisions"].values())
    checks["run9_identical"] = all(results["records"]["run9"]["identical_decisions"].values())
    earlier = [16, 20, 25, 29]
    checks["run12_earlier_points_identical"] = all(
        [(x["label"], x["outcome"], x["version_after"]) for x in r12["without"][v[0]] if x["label"] in earlier]
        == [(x["label"], x["outcome"], x["version_after"]) for x in r12["with"][v[0]] if x["label"] in earlier]
        for v in variants
    )
    checks["contract_digest_run12"] = r12["contract"]["digest"]
    checks["contract_version"] = r12["contract"]["version"]
    OUT_JSON.write_text(json.dumps(results, indent=1, default=float))

    L = ["# Behavioral equivalence audit (offline, frozen records)", "",
         f"Contract `{r12['contract']['version']}`, digest `{r12['contract']['digest']}` on the run 12 keys; classes other than identity: " + ", ".join(f"`{k}` -> {v}" for k, v in r12["contract"]["mapping"].items() if k != v) + ".", "",
         "## Pre-registered checks", ""] + [f"- {k}: {(('pass' if v else 'FAIL') if isinstance(v, bool) else v)}" for k, v in checks.items()]
    L += ["", f"## Run 12, `{FAMILY.split(':',1)[1]}` at 25 and 33, without and with the contract", "",
          "| variant | 25 without | 25 with | 33 without | 33 with | 33 sel. acc. with | 33 ECE with | 33 literal / equivalent agreement |", "|---|---|---|---|---|---|---|---|"]
    for v in variants:
        a0, a1 = fam("without", v[0], 25), fam("with", v[0], 25)
        b0, b1 = fam("without", v[0], 33), fam("with", v[0], 33)
        ret = b1.get("retention") or {}
        L.append(f"| {v[0]} | {a0.get('status')} ({a0.get('reason')}) | {a1.get('status')} ({a1.get('reason')}) | {b0.get('status')} ({b0.get('reason')}) | {b1.get('status')} ({b1.get('reason')}) | {fmt(b1.get('selective_accuracy'))} | {fmt(b1.get('ece'))} | {fmt(ret.get('literal_agreement'))} / {fmt(ret.get('equivalent_agreement'))} |")
    for name in RECORDS:
        rec = results["records"][name]
        L += ["", f"## {name}: candidate decisions without and with the contract", "", "| variant | " + " | ".join(str(p) for p in rec["points"]) + " | identical |", "|---|" + "---|" * len(rec["points"]) + "---|"]
        for v in variants:
            w0, w1 = rec["without"][v[0]], rec["with"][v[0]]
            cells = " | ".join(f"{a['outcome']} ({a['reason'].split(':')[0]}) / {b['outcome']} ({b['reason'].split(':')[0]})" if (a["outcome"], a["reason"]) != (b["outcome"], b["reason"]) else f"{a['outcome']} ({a['reason'].split(':')[0]})" for a, b in zip(w0, w1))
            L.append(f"| {v[0]} | {cells} | {'yes' if rec['identical_decisions'][v[0]] else 'no'} |")
    L.append("")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
