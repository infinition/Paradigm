"""Run 12b report: the live run with ``laruche-equivalence-1`` active, replayed without the
contract on the same frozen record, with literal and behavioral agreement side by side,
the family verdicts and adoption decisions, every decision changed by equivalence, and
the divergence from run 12 at the common compile points. See
``live_equivalence_prereg.md``.
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
from integration_behavioral_equivalence import compile_points, sequential  # noqa: E402

from paradigm.integration.laruche import LaRucheAdapter  # noqa: E402

RES = ROOT / "results" / "integration_laruche"
STATE = RES / "engine_state_equivalence_after_24.pkl"
RUN12 = RES / "engine_state_shadow_after_36.pkl"
TELEMETRY = RES / "run12b_telemetry.json"
LOG = RES / "run12b_decision_log.json"
OUT_JSON = RES / "run12b_equivalence_report.json"
OUT_MD = RES / "run12b_equivalence_report.md"
TEST = LaRucheAdapter.TEST_EXECUTION


def fmt(v: Any) -> str:
    return "n/a" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))


def main() -> None:
    with STATE.open("rb") as fh:
        payload = pickle.load(fh)
    compiler = payload["compiler"]
    adapter = LaRucheAdapter(templates=payload.get("action_templates") or {})
    contract = adapter.equivalence_contract()
    telemetry = json.loads(TELEMETRY.read_text())
    rows = json.loads(LOG.read_text())["decisions"]
    points, labels = compile_points(compiler)
    episodes = compiler.buffer.episodes

    live = {p.stream_episode: p for p in compiler.state.promotions}
    with_c = sequential(compiler, episodes, points, labels, recertify=False, m=1, triadic=False, contract=contract)
    without = sequential(compiler, episodes, points, labels, recertify=False, m=1, triadic=False, contract=None)
    reproduced = all((r["outcome"], r["reason"]) == (live[r["label"]].outcome, live[r["label"]].reason) for r in with_c)

    # Which families contain a TEST_EXECUTION action anywhere in the buffer.
    fam_actions: dict[str, set[str]] = {}
    for ep in episodes:
        for t in ep.traces:
            fam_actions.setdefault(str(t.metadata.get("family")), set()).add(str(t.action))
    test_families = {f for f, acts in fam_actions.items() if any(contract.class_of(a) == TEST for a in acts)}

    # Family-level comparison per compile point, from the live records (all families, not only active).
    table: list[dict[str, Any]] = []
    changed: list[dict[str, Any]] = []
    for lab, w1, w0 in zip(labels, with_c, without):
        g1 = live[lab].certification.get("groups", {})
        # The replay without the contract has the same groups keyed by family.
        rec0 = next(x for x in without if x["label"] == lab)
        # sequential() keeps only active families in "active"; recompute groups from a fresh replay record.
        for f, v1 in g1.items():
            v0 = _group_without(compiler, episodes, points, labels, lab, f) if f not in (rec0["active"] or {}) else rec0["active"][f]
            ret1 = v1.get("retention") or {}
            entry = {
                "point": lab, "family": f, "has_test_action": f in test_families,
                "literal_agreement": ret1.get("literal_agreement"), "behavioral_agreement": ret1.get("equivalent_agreement"),
                "verdict_with": v1.get("status"), "reason_with": v1.get("reason"),
                "verdict_without": (v0 or {}).get("status"), "reason_without": (v0 or {}).get("reason"),
            }
            table.append(entry)
            if entry["verdict_with"] != entry["verdict_without"]:
                changed.append(entry)
    decisions = [{"point": lab, "with": (a["outcome"], a["reason"], a["version_after"], tuple(a["active_after"])), "without": (b["outcome"], b["reason"], b["version_after"], tuple(b["active_after"]))} for lab, a, b in zip(labels, with_c, without)]
    # An adoption decision is its outcome, the version it yields and the set of active families it leaves.
    decisions_changed = [d for d in decisions if (d["with"][0], d["with"][2], d["with"][3]) != (d["without"][0], d["without"][2], d["without"][3])]
    unexpected = [e for e in changed if not e["has_test_action"]]

    # Divergence from run 12 at common compile points (family verdicts of the live records).
    with RUN12.open("rb") as fh:
        c12 = pickle.load(fh)["compiler"]
    live12 = {p.stream_episode: p for p in c12.state.promotions}
    divergence = []
    for lab in labels:
        if lab in live12:
            g12 = live12[lab].certification.get("groups", {})
            g = live[lab].certification.get("groups", {})
            for f in sorted(set(g) | set(g12)):
                divergence.append({"point": lab, "family": f, "run12": (g12.get(f) or {}).get("status"), "run12b": (g.get(f) or {}).get("status")})

    reflex = sum(1 for r in rows if r["source"] == "reflex")
    shadow = sum(1 for r in rows if r.get("reason") == "shadow_sample")
    natural = sum(1 for r in rows if r["source"] != "reflex" and r.get("reason") not in ("shadow_sample", "no_decision_requested"))
    reflex_outcomes: dict[str, int] = {}
    for r in rows:
        if r["source"] == "reflex":
            reflex_outcomes[str(r.get("outcome"))] = reflex_outcomes.get(str(r.get("outcome")), 0) + 1

    out = {
        "reproduced": reproduced, "points": labels, "contract": telemetry.get("equivalence_contract"),
        "probe_contracts": {f: (p.contract or {}).get("digest") for f, p in compiler.state.probes.items()},
        "test_families": sorted(test_families), "table": table, "changed_family_verdicts": changed, "unexpected_changes": unexpected,
        "decisions": decisions, "decisions_changed": decisions_changed, "divergence_from_run12": divergence,
        "economy": {"natural_model_calls": natural, "shadow_sample_model_calls": shadow, "reflex_decisions": reflex, "reflex_outcomes": reflex_outcomes},
    }
    OUT_JSON.write_text(json.dumps(out, indent=1, default=float))

    L = ["# Run 12b report: live run with `laruche-equivalence-1`", "",
         f"Live certification reproduced by the replay with the contract: {'yes' if reproduced else 'no'}. Compile points (stream episodes): {labels}. Contract in telemetry: `{(telemetry.get('equivalence_contract') or {}).get('version')}` digest `{(telemetry.get('equivalence_contract') or {}).get('digest')}`; probe sets frozen under: " + ", ".join(f"`{f.split(':',1)[1]}` {str(d)[:12]}" for f, d in out["probe_contracts"].items()) + ".", "",
         "Families containing a TEST_EXECUTION action: " + ", ".join(f"`{f.split(':',1)[1]}`" for f in sorted(test_families)) + ".", "",
         "## Economy", "", f"natural model calls {natural}, shadow-sample model calls {shadow}, reflex decisions {reflex}, reflex outcomes {reflex_outcomes}.", "",
         "## Per compile point and family: literal versus behavioral agreement, verdict with and without the contract", "",
         "| point | family | test action in family | literal | behavioral | verdict with (reason) | verdict without (reason) |", "|---|---|---|---|---|---|---|"]
    for e in table:
        L.append(f"| {e['point']} | `{e['family'].split(':',1)[1]}` | {'yes' if e['has_test_action'] else 'no'} | {fmt(e['literal_agreement'])} | {fmt(e['behavioral_agreement'])} | {e['verdict_with']} ({e['reason_with']}) | {e['verdict_without']} ({e['reason_without']}) |")
    L += ["", "## Adoption decisions with and without the contract (outcome, version, active families after)", "", "| point | with | without |", "|---|---|---|"]
    for d in decisions:
        L.append(f"| {d['point']} | {d['with'][0]} ({d['with'][1].split(':')[0]}), v{d['with'][2]}: " + ", ".join(f"`{f.split(':',1)[1]}`" for f in d["with"][3]) + f" | {d['without'][0]} ({d['without'][1].split(':')[0]}), v{d['without'][2]}: " + ", ".join(f"`{f.split(':',1)[1]}`" for f in d["without"][3]) + " |")
    L += ["", f"Family verdicts changed by equivalence: {len(changed)}; adoption decisions changed: {len(decisions_changed)}; changes in families without a TEST_EXECUTION action: {len(unexpected)}.", "",
          "## Divergence from run 12 at the common compile points (family verdicts of the live records)", "", "| point | family | run 12 | run 12b |", "|---|---|---|---|"]
    for d in divergence:
        L.append(f"| {d['point']} | `{d['family'].split(':',1)[1]}` | {d['run12'] or 'absent'} | {d['run12b'] or 'absent'} |")
    L.append("")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


def _group_without(compiler, episodes, points, labels, lab, family):
    """Family verdict of the replay without the contract for a family that was not active."""
    if not hasattr(_group_without, "cache"):
        import copy

        from integration_sparse_heldout_sensitivity import fresh_compiler

        c = fresh_compiler(compiler, recertify=False, m=1)
        c.equivalence = None
        cache = {}
        for point, label in zip(points, labels):
            c.buffer.episodes = [copy.deepcopy(ep) for ep in episodes[:point]]
            rec = c._compile_candidate(point)
            cache[label] = rec.certification.get("groups", {})
        _group_without.cache = cache
    return _group_without.cache.get(lab, {}).get(family)


if __name__ == "__main__":
    main()
