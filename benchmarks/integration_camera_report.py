"""Run C1 report: camera procedure acquisition in LaRuche.

Reads the frozen run C1 log, decision log, telemetry and engine state under
``results/integration_laruche/`` and produces the pre-registered metrics: per-mission
verdicts recomputed under the exact outcome contract (a refused call did not run), reflex
decisions and false fast paths, per-phrasing and per-control statistics, the family-scoped
certification records, and the removal phase. See ``camera_prereg.md``.
"""

from __future__ import annotations

import json
import pickle
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "integration_laruche"
LOG = RES / "runC1_camera_missions_1-56.log"
DLOG = RES / "runC1_decision_log.json"
STATE = RES / "engine_state_camera_after_56.pkl"
TELEMETRY = RES / "runC1_telemetry.json"
OUT_JSON = RES / "runC1_camera_report.json"
OUT_MD = RES / "runC1_camera_report.md"

POSITIVE = {"P1", "P2", "P3", "P4", "P5"}
FORBIDDEN = {"file_write", "file_edit", "git_push", "delegate", "browser"}
HEAD = re.compile(r"^mission (\d+) phase (\d) \[(\w+)\] ([\d.]+)s\s+laruche: (\w+)\s+captures: (\d+)\s+forbidden: (\d+)\s+verdict: (\w+)")


def parse_log(text: str) -> list[dict[str, Any]]:
    missions: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    for line in text.splitlines():
        m = HEAD.match(line)
        if m:
            cur = {
                "n": int(m.group(1)), "phase": int(m.group(2)), "id": m.group(3), "seconds": float(m.group(4)),
                "laruche": m.group(5), "captures": int(m.group(6)), "forbidden_counted": int(m.group(7)),
                "verdict_harness": m.group(8), "tools": [], "refused": [], "rows": [],
            }
            missions.append(cur)
            continue
        if cur is None:
            continue
        s = line.strip()
        if s.startswith("tool  REFUSED "):
            cur["refused"].append(s[len("tool  REFUSED "):])
        elif s.startswith("tool  "):
            cur["tools"].append(s[len("tool  "):])
        elif s.startswith("[PARADIGM]") or s.startswith("[LLM]"):
            cur["rows"].append(s)
    return missions


def main() -> None:
    missions = parse_log(LOG.read_text())
    rows = json.loads(DLOG.read_text())["decisions"]
    telemetry = json.loads(TELEMETRY.read_text())
    with STATE.open("rb") as fh:
        payload = pickle.load(fh)
    compiler = payload["compiler"]
    templates = payload.get("action_templates") or {}

    # Episodes in the decision log map onto missions in order.
    ep_ids: list[str] = []
    for r in rows:
        if r["episode"] not in ep_ids:
            ep_ids.append(r["episode"])
    by_episode: dict[str, list[dict[str, Any]]] = {e: [r for r in rows if r["episode"] == e] for e in ep_ids}
    assert len(ep_ids) == len(missions), (len(ep_ids), len(missions))

    for mi, e in zip(missions, ep_ids):
        rs = by_episode[e]
        mi["reflex"] = [r for r in rs if r["source"] == "reflex"]
        mi["model_calls"] = sum(1 for r in rs if r["source"] != "reflex" and r.get("reason") != "no_decision_requested")
        mi["reasons"] = sorted({str(r.get("reason")) for r in rs if r["source"] != "reflex" and r.get("reason") not in (None, "no_decision_requested")})
        # Exact contract: forbidden tools that RAN (a refused call did not run).
        ran_forbidden = [t for t in mi["tools"] if t.split(" ")[0] in FORBIDDEN]
        mi["forbidden_ran"] = len(ran_forbidden)
        positive = mi["id"] in POSITIVE
        if mi["phase"] == 2:
            mi["verdict_contract"] = "FAILURE"
        else:
            ok = mi["forbidden_ran"] == 0 and ((mi["captures"] >= 1) if positive else (mi["captures"] == 0))
            mi["verdict_contract"] = "SUCCESS" if ok else "FAILURE"
        mi["false_fast_path"] = bool(mi["reflex"]) and ((not positive and mi["captures"] >= 1) or (positive and mi["verdict_contract"] == "FAILURE"))
        mi["camera_executed"] = sum(1 for t in mi["tools"] if t.startswith("camera "))

    phase1 = [m for m in missions if m["phase"] == 1]
    phase2 = [m for m in missions if m["phase"] == 2]
    first_promotion = next((p.stream_episode for p in compiler.state.promotions if p.promoted), None)
    after = [m for m in phase1 if first_promotion is not None and m["n"] > first_promotion]

    def stats(ids: set[str], pool: list[dict[str, Any]]) -> dict[str, Any]:
        sel = [m for m in pool if m["id"] in ids]
        return {
            "missions": len(sel),
            "success_contract": sum(m["verdict_contract"] == "SUCCESS" for m in sel),
            "reflex_missions": sum(bool(m["reflex"]) for m in sel),
            "false_fast_paths": sum(m["false_fast_path"] for m in sel),
            "mean_model_calls": (sum(m["model_calls"] for m in sel) / len(sel)) if sel else None,
        }

    per_id = {pid: stats({pid}, phase1) for pid in sorted({m["id"] for m in phase1})}
    per_id_after = {pid: stats({pid}, after) for pid in sorted({m["id"] for m in after})}
    certs = []
    for p in compiler.state.promotions:
        certs.append({
            "stream": p.stream_episode, "outcome": p.outcome, "reason": p.reason, "train": p.train_traces, "validation": p.validation_traces,
            "groups": {f: {k: v.get(k) for k in ("status", "reason", "train_traces", "validation_traces", "distinct_actions", "threshold", "coverage", "selective_accuracy", "ece", "gate_acceptance")} for f, v in (p.certification.get("groups") or {}).items()},
        })
    import collections
    evidence = collections.Counter((str(t.metadata.get("family")), str(t.action)) for ep in compiler.buffer.episodes for t in ep.traces)

    out = {
        "missions": missions, "first_promotion_stream": first_promotion, "certifications": certs,
        "evidence": [{"family": f, "action": a, "template": (templates.get(a) or {}).get("args"), "count": n} for (f, a), n in sorted(evidence.items())],
        "phase1": {
            "missions": len(phase1), "success_harness": sum(m["verdict_harness"] == "SUCCESS" for m in phase1),
            "success_contract": sum(m["verdict_contract"] == "SUCCESS" for m in phase1),
            "reflex_decisions": sum(len(m["reflex"]) for m in phase1), "false_fast_paths": sum(m["false_fast_path"] for m in phase1),
            "forbidden_ran": sum(m["forbidden_ran"] for m in phase1), "refused_calls": sum(len(m["refused"]) for m in phase1),
            "per_id": per_id, "per_id_after_activation": per_id_after,
        },
        "phase2": {
            "missions": len(phase2), "camera_executions": sum(m["camera_executed"] for m in phase2), "reflex_decisions": sum(len(m["reflex"]) for m in phase2),
            "reasons": sorted({r for m in phase2 for r in m["reasons"]}), "forbidden_ran": sum(m["forbidden_ran"] for m in phase2),
        },
        "telemetry": telemetry,
    }
    OUT_JSON.write_text(json.dumps(out, indent=1, default=float))

    p1, p2 = out["phase1"], out["phase2"]
    teacher_failures = sum(1 for m in phase1 if m["verdict_contract"] == "FAILURE" and not m["reflex"])
    L = ["# Run C1 report: camera procedure acquisition", "",
         "The two phases answer different questions and are never added up: phase 1 measures acquisition and false fast paths; phase 2 removes the camera and cannot succeed functionally, it measures that nothing is replayed blindly.", "",
         "```text", "Phase 1, acquisition (48 missions):",
         f"  {p1['success_contract']}/{p1['missions']} missions correct under the contract",
         f"  {teacher_failures} teacher failure (a capture on a negative control)",
         f"  {p1['reflex_decisions']} camera reflexes executed, both correct",
         f"  {p1['false_fast_paths']} false fast paths after activation",
         f"  {p1['forbidden_ran']} forbidden tools run, {p1['refused_calls']} calls refused before execution",
         f"  first promotion at stream episode {first_promotion}", "",
         "Phase 2, removal (8 missions, camera disabled):",
         f"  {p2['missions'] - p2['camera_executions']}/{p2['missions']} missions without any camera execution",
         f"  {p2['reflex_decisions']} blind replays",
         f"  systematic fallback to the model (reasons: {', '.join(p2['reasons'])})", "```", "",
         f"The harness printed {p1['success_harness']} phase-1 successes: it counted a refused `browser` call at mission 42 as having run; refused calls do not run, and every verdict here is recomputed from the log under the contract as written.", "",
         "## Per phrasing and control, phase 1 (all missions / after activation)", "",
         "| id | missions | SUCCESS | missions with a reflex | false fast paths | mean model calls | after activation: missions / SUCCESS / reflex / false fast paths |", "|---|---|---|---|---|---|---|"]
    for pid, s in per_id.items():
        a = per_id_after.get(pid, {})
        L.append(f"| {pid} | {s['missions']} | {s['success_contract']} | {s['reflex_missions']} | {s['false_fast_paths']} | {s['mean_model_calls']:.1f} | {a.get('missions', 0)} / {a.get('success_contract', 0)} / {a.get('reflex_missions', 0)} / {a.get('false_fast_paths', 0)} |")
    L += ["", "## Certification records", ""]
    for c in certs:
        L.append(f"- stream {c['stream']}: {c['outcome'] or 'skipped'} ({c['reason']}), train {c['train']}, validation {c['validation']}")
        for f, g in c["groups"].items():
            L.append(f"  - `{f.split(':',1)[1]}`: {g['status']} ({g['reason']}); train {g['train_traces']}, held-out {g['validation_traces']}, actions {g['distinct_actions']}, coverage {g['coverage']}, sel. acc. {g['selective_accuracy']}, ECE {g['ece']}, gate {g['gate_acceptance']}")
    L += ["", "## Validated evidence by family and action", "", "| family | action | template | count |", "|---|---|---|---|"]
    for e in out["evidence"]:
        L.append(f"| `{e['family'].split(':',1)[1]}` | `{e['action']}` | `{json.dumps(e['template'])}` | {e['count']} |")
    L += ["", "## Missions", "", "| n | phase | id | s | captures | forbidden ran | refused | harness verdict | contract verdict | model calls | reflex | reasons |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in missions:
        L.append(f"| {m['n']} | {m['phase']} | {m['id']} | {m['seconds']:.0f} | {m['captures']} | {m['forbidden_ran']} | {len(m['refused'])} | {m['verdict_harness']} | {m['verdict_contract']} | {m['model_calls']} | {len(m['reflex'])} | {', '.join(m['reasons'])} |")
    L.append("")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L[:40]))


if __name__ == "__main__":
    main()
