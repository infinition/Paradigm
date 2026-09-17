"""Read-only sensitivity study: sparse fresh held-out evidence versus frozen probes.

Replays family-scoped certification sequentially over the frozen LaRuche records (run 11,
and runs 9A/9B under a counterfactual family-scoped rule) for minimum fresh support
m in {1, 2, 3, 5, 8}, plus the recorded rule as baseline and the damaged-family negative
control. Nothing in the frozen states is modified. See
``results/integration_laruche/sparse_heldout_prereg.md``. No m is selected here.
"""

from __future__ import annotations

import copy
import json
import pickle
from dataclasses import replace
from pathlib import Path
from typing import Any

from paradigm.online_learning import OnlineReflexCompiler

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "integration_laruche"
RUN11 = RES / "engine_state_family_scoped_after_24.pkl"
RUN9 = RES / "engine_state_after_32.pkl"
OUT_JSON = RES / "sparse_heldout_sensitivity.json"
OUT_MD = RES / "sparse_heldout_sensitivity.md"

MS = (1, 2, 3, 5, 8)
POISONED_FAMILY = "laruche:file_edit:success:other"


def load(path: Path):
    with path.open("rb") as fh:
        payload = pickle.load(fh)
    return payload["compiler"] if isinstance(payload, dict) else payload.compiler


def fresh_compiler(template, *, recertify: bool, m: int) -> OnlineReflexCompiler:
    c = OnlineReflexCompiler(
        min_episodes=template.min_episodes, compile_every=template.compile_every,
        validation_fraction=template.validation_fraction, minimum_ood_acceptance=template.minimum_ood_acceptance,
        random_state=template.random_state, certification="family_scoped", probe_size=template.probe_size,
        probe_coverage_floor=template.probe_coverage_floor, probe_accuracy_floor=template.probe_accuracy_floor,
        probe_coverage_regression_tolerance=template.probe_coverage_regression_tolerance,
        min_family_validation_episodes=template.min_family_validation_episodes,
        probe_recertification=recertify, min_fresh_support=m,
    )
    return c


def poison_train(c: OnlineReflexCompiler, family: str) -> None:
    n_val = max(1, int(round(len(c.buffer.episodes) * c.validation_fraction)))
    train_eps = c.buffer.episodes[: len(c.buffer.episodes) - n_val]
    other: dict[str, int] = {}
    for ep in train_eps:
        for t in ep.traces:
            if t.metadata.get("family") != family:
                other[t.action] = other.get(t.action, 0) + 1
    wrong = max(other, key=other.get)
    for ep in train_eps:
        ep.traces = [replace(t, action=wrong) if t.metadata.get("family") == family else t for t in ep.traces]


def sequential(template, episodes, points: list[int], *, recertify: bool, m: int, poison_at: int | None = None) -> list[dict[str, Any]]:
    c = fresh_compiler(template, recertify=recertify, m=m)
    out = []
    for point in points:
        c.buffer.episodes = [copy.deepcopy(ep) for ep in episodes[:point]]
        if poison_at == point:
            poison_train(c, POISONED_FAMILY)
        active_before = dict(c.state.family_thresholds)
        rec = c._compile_candidate(point)
        groups = rec.certification.get("groups", {})
        active_verdicts = {}
        for f in active_before:
            v = groups.get(f)
            if v is None:
                active_verdicts[f] = {"status": "missing"}
                continue
            ret = v.get("retention") or {}
            active_verdicts[f] = {
                "status": v["status"], "reason": v["reason"], "n_fresh": v["validation_traces"],
                "evidence": ret.get("evidence", "held-out"), "probes": ret.get("probes"),
                "probe_coverage": ret.get("coverage"), "probe_agreement": ret.get("agreement"),
                "gate_acceptance": v.get("gate_acceptance"), "ece": v.get("ece"), "fresh": ret.get("fresh"),
            }
        out.append({
            "point": point, "outcome": rec.outcome, "reason": rec.reason, "version_after": c.state.version,
            "active_before": sorted(active_before), "active_after": sorted(c.state.family_thresholds),
            "newly_active": sorted(set(c.state.family_thresholds) - set(active_before)),
            "active_verdicts": active_verdicts,
            "families": groups,
        })
    return out


def classify(row: dict[str, Any], poisoned: bool) -> dict[str, bool]:
    """False accept / false reject per the pre-registered definitions."""
    false_accept = False
    false_reject = False
    if poisoned:
        false_accept = row["outcome"] == "promoted"
    else:
        for v in row["active_verdicts"].values():
            fr = v.get("fresh") or {}
            if v.get("evidence") == "probes_only" and v.get("status") == "active" and fr.get("disagreements", 0) > 0:
                false_accept = True
        if row["outcome"] == "rejected" and row["active_verdicts"]:
            all_probes_pass = True
            any_disagreement = False
            for v in row["active_verdicts"].values():
                pc, pa = v.get("probe_coverage"), v.get("probe_agreement")
                if pc is None or pa is None or pc < 0.65 or pa < 0.95:
                    all_probes_pass = False
                fr = v.get("fresh") or {}
                if fr.get("disagreements", 0) > 0:
                    any_disagreement = True
            false_reject = all_probes_pass and not any_disagreement and row["reason"].startswith("active_family_regressed")
    return {"false_accept": false_accept, "false_reject": false_reject}


def sparse_switches(row: dict[str, Any], baseline_row: dict[str, Any]) -> int:
    """Active-family verdicts that changed status only because the evidence source switched."""
    n = 0
    for f, v in row["active_verdicts"].items():
        b = baseline_row["active_verdicts"].get(f)
        if b is None:
            continue
        if v.get("evidence") == "probes_only" and b.get("evidence") != "probes_only" and v.get("status") != b.get("status"):
            n += 1
    return n


def fmt(v: Any) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.3f}"
    return str(v)


def main() -> None:
    run11 = load(RUN11)
    run9 = load(RUN9)
    assert run11.certification == "family_scoped"

    # Probe sets for the active-family probe checks come from the sequential replay
    # itself (frozen at the first promotion of that replay), never from the live state.
    results: dict[str, Any] = {"m_values": list(MS), "run11": {}, "run9": {}, "poison": {}}
    variants: list[tuple[str, bool, int]] = [("recorded", False, 1)] + [(f"m={m}", True, m) for m in MS]

    for label, recertify, m in variants:
        results["run11"][label] = sequential(run11, run11.buffer.episodes, [16, 20, 24], recertify=recertify, m=m)
        results["run9"][label] = sequential(run9, run9.buffer.episodes, [20, 24, 28, 32], recertify=recertify, m=m)
        results["poison"][label] = sequential(run11, run11.buffer.episodes, [16, 20, 24], recertify=recertify, m=m, poison_at=24)[-1]

    # Reproducibility: the recorded variant on run 11 must match the live record.
    rec11 = {p.stream_episode: (p.outcome, p.reason) for p in run11.state.promotions}
    results["run11_reproduced"] = all((r["outcome"], r["reason"]) == rec11[r["point"]] for r in results["run11"]["recorded"])

    # Retrospective labeling for the false-reject metric: a variant that never evaluated
    # an active family's probes (the family was "insufficient") gets the probe numbers of
    # the m=1 variant for the same point and family. The candidate is the same object in
    # both (identical state before the point and identical training split), so this
    # labels the recorded decisions on the same basis without changing any verdict.
    for name in ("run11", "run9"):
        ref_rows = results[name]["m=1"]
        for label, _, _ in variants:
            for r, ref in zip(results[name][label], ref_rows):
                for f, v in r["active_verdicts"].items():
                    if v.get("probe_coverage") is None and f in ref["active_verdicts"]:
                        rv = ref["active_verdicts"][f]
                        v["probe_coverage"], v["probe_agreement"] = rv.get("probe_coverage"), rv.get("probe_agreement")
                        v["retrospective_probe_label"] = True

    summary = []
    for label, _, _ in variants:
        rows11 = results["run11"][label]
        rows9 = results["run9"][label]
        base11 = results["run11"]["recorded"]
        base9 = results["run9"]["recorded"]
        fa = fr = changed = switches = 0
        for rows, base in ((rows11, base11), (rows9, base9)):
            for r, b in zip(rows, base):
                cl = classify(r, False)
                fa += cl["false_accept"]; fr += cl["false_reject"]
                if (r["outcome"], r["version_after"], tuple(r["active_after"])) != (b["outcome"], b["version_after"], tuple(b["active_after"])):
                    changed += 1
                switches += sparse_switches(r, b)
        pz = results["poison"][label]
        summary.append({
            "variant": label,
            "run11_20": results["run11"][label][1]["outcome"], "run11_24": results["run11"][label][2]["outcome"],
            "run11_versions": results["run11"][label][-1]["version_after"], "run11_active_final": results["run11"][label][-1]["active_after"],
            "run9_versions": rows9[-1]["version_after"], "run9_active_final": rows9[-1]["active_after"],
            "run9_activations": [(r["point"], r["newly_active"]) for r in rows9 if r["newly_active"]],
            "run11_activations": [(r["point"], r["newly_active"]) for r in rows11 if r["newly_active"]],
            "poison": pz["outcome"], "poison_false_accept": classify(pz, True)["false_accept"],
            "false_accepts": fa, "false_rejects": fr, "decisions_changed_vs_recorded": changed, "changed_by_sparse_arbitration": switches,
        })
    results["summary"] = summary
    OUT_JSON.write_text(json.dumps(results, indent=1, default=float))

    L = ["# Sparse held-out sensitivity study (read-only)", "",
         "Sources: run 11 state (`engine_state_family_scoped_after_24.pkl`) replayed at 16, 20, 24; runs 9A/9B state (`engine_state_after_32.pkl`, 32 validated episodes recorded without any active reflex) replayed under family-scoped certification at 20, 24, 28, 32, counterfactually. `recorded` is the run 11 rule (no probe re-certification); `m=1` is the rule of the previous pre-registration (probes only when no fresh trace) and the control. Probe sets are frozen inside each replay at its first promotion.", "",
         f"Run 11 reproduced by the `recorded` variant: {'yes' if results['run11_reproduced'] else 'no'}.", "",
         "`m=1` is behaviorally identical to the recorded rule: every verdict, version and active set is the same. The false accept and false reject counts are retrospective labels defined by the pre-registration; where a variant never evaluated an active family's probes, the label uses the probe numbers of the same candidate from the `m=1` replay (marked `retrospective_probe_label` in the JSON), so all variants are labeled on the same basis. A label difference never means a changed certification decision; the \"decisions changed\" column is the only one that does.", "",
         "## Summary per variant", "",
         "| variant | run 11: 20 | run 11: 24 | run 11 final version, active families | run 9: activations (point: families) | run 9 final version | poison at 24 | false accepts | false rejects | candidate decisions changed vs recorded | active-family verdicts changed by sparse arbitration |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in summary:
        r9 = "; ".join(f"{p}: " + ", ".join(f"`{f.split(':',1)[1]}`" for f in fams) for p, fams in s["run9_activations"]) or "none"
        L.append(f"| {s['variant']} | {s['run11_20']} | {s['run11_24']} | v{s['run11_versions']}: " + ", ".join(f"`{f.split(':',1)[1]}`" for f in s["run11_active_final"]) + f" | {r9} | v{s['run9_versions']} | {s['poison']} | {s['false_accepts']} | {s['false_rejects']} | {s['decisions_changed_vs_recorded']} | {s['changed_by_sparse_arbitration']} |")
    L += ["", "## Active-family re-certification, run 11", "",
          "| variant | point | family | n fresh | evidence | probes cov. / agr. | fresh: gate-accepted / covered / disagreements | gate acc. | ECE | verdict |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for label, _, _ in variants:
        for r in results["run11"][label]:
            for f, v in r["active_verdicts"].items():
                fr = v.get("fresh") or {}
                fresh = f"{fr.get('gate_accepted')} / {fr.get('covered')} / {fr.get('disagreements')}" if fr else ""
                pr = f"{fmt(v.get('probe_coverage'))} / {fmt(v.get('probe_agreement'))}" if v.get("probes") else ""
                L.append(f"| {label} | {r['point']} | `{f.split(':',1)[1]}` | {v.get('n_fresh')} | {v.get('evidence')} | {pr} | {fresh} | {fmt(v.get('gate_acceptance'))} | {fmt(v.get('ece'))} | {v['status']} ({v.get('reason')}) |")
    L += ["", "## Active-family re-certification, runs 9A/9B (counterfactual)", "",
          "| variant | point | family | n fresh | evidence | probes cov. / agr. | fresh: gate-accepted / covered / disagreements | gate acc. | ECE | verdict |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for label, _, _ in variants:
        for r in results["run9"][label]:
            for f, v in r["active_verdicts"].items():
                fr = v.get("fresh") or {}
                fresh = f"{fr.get('gate_accepted')} / {fr.get('covered')} / {fr.get('disagreements')}" if fr else ""
                pr = f"{fmt(v.get('probe_coverage'))} / {fmt(v.get('probe_agreement'))}" if v.get("probes") else ""
                L.append(f"| {label} | {r['point']} | `{f.split(':',1)[1]}` | {v.get('n_fresh')} | {v.get('evidence')} | {pr} | {fresh} | {fmt(v.get('gate_acceptance'))} | {fmt(v.get('ece'))} | {v['status']} ({v.get('reason')}) |")
    L += ["", "## Verdict per compile point", "", "| variant | record | point | outcome | reason | version after | newly active |", "|---|---|---|---|---|---|---|"]
    for label, _, _ in variants:
        for name in ("run11", "run9"):
            for r in results[name][label]:
                L.append(f"| {label} | {name} | {r['point']} | {r['outcome']} | {r['reason']} | v{r['version_after']} | " + (", ".join(f"`{f.split(':',1)[1]}`" for f in r["newly_active"]) or "") + " |")
    L += ["", "## Poison control at 24, run 11, per variant", "", "| variant | outcome | reason | file_edit verdict |", "|---|---|---|---|"]
    for label, _, _ in variants:
        pz = results["poison"][label]
        v = pz["families"].get(POISONED_FAMILY, {})
        L.append(f"| {label} | {pz['outcome']} | {pz['reason']} | {v.get('status')} ({v.get('reason')}) |")
    L.append("")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L[:20]))


if __name__ == "__main__":
    main()
