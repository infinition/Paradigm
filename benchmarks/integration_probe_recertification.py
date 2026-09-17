"""Offline counterfactual audit: probe-based re-certification on the frozen run 11 state.

Reads ``results/integration_laruche/engine_state_family_scoped_after_24.pkl`` (tag
``laruche-family-scoped-run11``) and replays compile points 20 and 24 of the family-scoped
compiler, first with the rule off (must reproduce the recorded verdicts), then with the
rule on, then with a damaged active family as the negative control. Nothing in the
frozen state is modified; the replay works on deep copies. See
``results/integration_laruche/probe_recertification_prereg.md``.
"""

from __future__ import annotations

import copy
import json
import pickle
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "results" / "integration_laruche" / "engine_state_family_scoped_after_24.pkl"
OUT_JSON = ROOT / "results" / "integration_laruche" / "probe_recertification_audit.json"
OUT_MD = ROOT / "results" / "integration_laruche" / "probe_recertification_audit.md"

ACTIVE = ("laruche:start:none:none", "laruche:file_edit:success:other")
POISONED_FAMILY = "laruche:file_edit:success:other"


def load_compiler():
    with STATE.open("rb") as fh:
        payload = pickle.load(fh)
    return payload["compiler"] if isinstance(payload, dict) else payload.compiler


def replay(compiler, point: int, *, recertify: bool, poison: str | None = None) -> dict[str, Any]:
    c = copy.deepcopy(compiler)
    c.buffer.episodes = c.buffer.episodes[:point]
    c.probe_recertification = recertify
    c.state.promotions = [p for p in c.state.promotions if p.stream_episode < point]
    if poison is not None:
        # Damage one active family in the training episodes only: relabel every one of its
        # traces with the most frequent action of another family. The probes are untouched.
        n_val = max(1, int(round(len(c.buffer.episodes) * c.validation_fraction)))
        train_eps = c.buffer.episodes[: len(c.buffer.episodes) - n_val]
        other = {}
        for ep in train_eps:
            for t in ep.traces:
                if t.metadata.get("family") != poison:
                    other[t.action] = other.get(t.action, 0) + 1
        wrong = max(other, key=other.get)
        for ep in train_eps:
            ep.traces = [replace(t, action=wrong) if t.metadata.get("family") == poison else t for t in ep.traces]
    rec = c._compile_candidate(point)
    groups = rec.certification.get("groups", {})
    return {
        "point": point,
        "probe_recertification": recertify,
        "poisoned_family": poison,
        "outcome": rec.outcome,
        "reason": rec.reason,
        "version_after": c.state.version,
        "active_families_after": sorted(c.state.family_thresholds),
        "whole_candidate": {
            "coverage": rec.validation_coverage,
            "selective_accuracy": rec.validation_selective_accuracy,
            "ece": rec.validation_ece,
            "train_traces": rec.train_traces,
            "validation_traces": rec.validation_traces,
        },
        "families": groups,
    }


def recorded(compiler, point: int) -> dict[str, Any]:
    rec = next(p for p in compiler.state.promotions if p.stream_episode == point)
    return {"outcome": rec.outcome, "reason": rec.reason, "families": rec.certification.get("groups", {})}


def same_verdicts(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if a["outcome"] != b["outcome"] or a["reason"] != b["reason"]:
        return False
    fa, fb = a["families"], b["families"]
    if set(fa) != set(fb):
        return False
    return all(fa[f]["status"] == fb[f]["status"] and fa[f]["reason"] == fb[f]["reason"] for f in fa)


def fmt(v: Any) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.3f}"
    return str(v)


def family_table(families: dict[str, Any]) -> list[str]:
    rows = ["| family | evidence | train / held-out | probes | coverage | agreement or sel. acc. | ECE | gate acc. | verdict | reason |", "|---|---|---|---|---|---|---|---|---|---|"]
    for f in sorted(families):
        v = families[f]
        ret = v.get("retention") or {}
        evidence = ret.get("evidence", "held-out" if v["validation_traces"] else "none")
        probes = ret.get("probes", "")
        agreement = ret.get("agreement") if evidence == "probes_only" else v.get("selective_accuracy")
        rows.append(
            f"| `{f}` | {evidence} | {v['train_traces']} / {v['validation_traces']} | {probes} | {fmt(v.get('coverage'))} | {fmt(agreement)} | {fmt(v.get('ece'))} | {fmt(v.get('gate_acceptance'))} | {v['status']} | {v['reason']} |"
        )
    return rows


def main() -> None:
    compiler = load_compiler()
    assert compiler.certification == "family_scoped"
    assert sorted(compiler.state.family_thresholds) == sorted(ACTIVE)
    probes = {f: len(p.traces) for f, p in compiler.state.probes.items()}

    results: dict[str, Any] = {"probes": probes, "replays": {}}
    checks: dict[str, bool] = {}

    for point in (20, 24):
        rec = recorded(compiler, point)
        off = replay(compiler, point, recertify=False)
        on = replay(compiler, point, recertify=True)
        results["replays"][f"{point}_recorded"] = rec
        results["replays"][f"{point}_rule_off"] = off
        results["replays"][f"{point}_rule_on"] = on
        checks[f"{point}_reproduced"] = same_verdicts(rec, off)

    poison = replay(compiler, 24, recertify=True, poison=POISONED_FAMILY)
    results["replays"]["24_rule_on_poisoned"] = poison

    on20 = results["replays"]["20_rule_on"]
    on24 = results["replays"]["24_rule_on"]
    checks["20_still_rejected"] = on20["outcome"] == "rejected" and "retention" in on20["families"][POISONED_FAMILY]["reason"]
    checks["24_promoted"] = on24["outcome"] == "promoted" and on24["version_after"] == 2
    checks["24_start_on_probes"] = on24["families"]["laruche:start:none:none"].get("retention", {}).get("evidence") == "probes_only" and on24["families"]["laruche:start:none:none"]["status"] == "active"
    checks["24_file_edit_active"] = on24["families"][POISONED_FAMILY]["status"] == "active"
    checks["24_tests_passed_activated"] = "laruche:shell_exec:success:tests_passed" in on24["active_families_after"]
    checks["24_active_families_kept"] = all(f in on24["active_families_after"] for f in ACTIVE)
    checks["poison_rejected"] = poison["outcome"] == "rejected" and poison["families"][POISONED_FAMILY]["status"] == "rejected"
    checks["discriminative"] = checks["24_promoted"] and checks["poison_rejected"]
    results["checks"] = checks
    supported = all(checks.values())
    results["conclusion"] = "supported" if supported else ("partially supported" if checks["discriminative"] else "unsupported")

    OUT_JSON.write_text(json.dumps(results, indent=1, default=float))

    lines = ["# Offline counterfactual audit: probe-based re-certification", "",
             "Source of truth: `engine_state_family_scoped_after_24.pkl` (tag `laruche-family-scoped-run11`). Frozen probes: " + ", ".join(f"`{f}` {n}" for f, n in sorted(probes.items())) + ". No threshold, split, family definition, probe set or historical artifact was modified; the replay works on deep copies.", ""]
    for point in (20, 24):
        off = results["replays"][f"{point}_rule_off"]
        on = results["replays"][f"{point}_rule_on"]
        lines += [f"## Compile point {point}", "",
                  f"Recorded verdict: {results['replays'][f'{point}_recorded']['outcome']} ({results['replays'][f'{point}_recorded']['reason']}). Replay with the rule off: {off['outcome']} ({off['reason']}). Reproduced exactly: {'yes' if checks[f'{point}_reproduced'] else 'no'}.", "",
                  f"Replay with the rule on: **{on['outcome']}** ({on['reason']}); version after: {on['version_after']}; active families after: {', '.join(f'`{f}`' for f in on['active_families_after'])}.", ""]
        lines += family_table(on["families"]) + [""]
    lines += ["## Negative control at 24, rule on", "",
              f"Every training trace of `{POISONED_FAMILY}` relabeled with another family's most frequent action; probes untouched. Verdict: **{poison['outcome']}** ({poison['reason']}).", ""]
    lines += family_table({f: v for f, v in poison["families"].items() if f in ACTIVE}) + [""]
    lines += ["## Checks", ""] + [f"- {k}: {'pass' if v else 'FAIL'}" for k, v in checks.items()] + ["", f"## Conclusion: {results['conclusion']}", ""]
    OUT_MD.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
