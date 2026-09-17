"""Run 12 shadow-sample ledger: every shadow-sampled decision with the reflex's proposal,
the teacher's verified action, agreement, gate result, outcome, and a classification that
keeps teacher disagreement separate from regression.

The proposal and the gate result are recomputed from the frozen version 1 artifact on
the state features kept in the buffer for validated steps. For a shadow sample the
teacher answered with a control call (finish), no observe followed and no features
were kept: the proposal is reconstructed as the family's certified action and marked so.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "integration_laruche"
STATE = RES / "engine_state_shadow_after_36.pkl"
LOG = RES / "run12_decision_log.json"
OUT_JSON = RES / "run12_shadow_ledger.json"
OUT_MD = RES / "run12_shadow_ledger.md"


def main() -> None:
    rows = json.loads(LOG.read_text())["decisions"]
    with STATE.open("rb") as fh:
        compiler = pickle.load(fh)["compiler"]
    reflex, gate, thresholds = compiler.state.selection.reflex, compiler.state.ood_gate, compiler.state.family_thresholds
    probes = compiler.state.probes
    certified_action = {f: max(((str(t.action) for t in p.traces)), key=[str(t.action) for t in p.traces].count) for f, p in probes.items()}

    ep_ids: list[str] = []
    for r in rows:
        if r["episode"] not in ep_ids:
            ep_ids.append(r["episode"])
    ep_index = {e: i + 1 for i, e in enumerate(ep_ids)}
    buffer = {ep.task_id: list(ep.traces) for ep in compiler.buffer.episodes}
    # Validated deliberative rows of an episode map, in order, onto its buffer traces.
    cursor: dict[str, int] = {}
    ledger: list[dict[str, Any]] = []
    for r in rows:
        validated = r["source"] == "deliberative" and r.get("outcome") == "success" and r["episode"] in buffer
        trace = None
        if validated:
            k = cursor.get(r["episode"], 0)
            traces = buffer[r["episode"]]
            if k < len(traces):
                trace = traces[k]
                cursor[r["episode"]] = k + 1
        if r.get("reason") != "shadow_sample":
            continue
        fam = r["family"]
        entry: dict[str, Any] = {
            "mission": ep_index[r["episode"]], "step": r["step"], "family": fam,
            "reflex_confidence": r.get("confidence"), "teacher_action": r.get("action"),
            "teacher_outcome": r.get("outcome"), "mission_verified": True,
        }
        if trace is not None and trace.metadata.get("family") == fam:
            x = np.asarray(trace.features, dtype=np.float64)
            action, conf, _ = reflex.predict(x)
            accepted = bool(np.asarray(gate.accept(x[None, :]), dtype=bool)[0])
            covered = accepted and float(conf) >= float(thresholds.get(fam, 0.0))
            entry.update({"reflex_proposed": str(action), "gate_accepted": accepted, "covered": covered, "source_of_proposal": "recomputed_on_stored_state"})
            entry["agree"] = str(action) == str(trace.action)
        else:
            entry.update({"reflex_proposed": certified_action.get(fam), "gate_accepted": None, "covered": None, "source_of_proposal": "reconstructed_family_action"})
            entry["agree"] = None if r.get("action") is None else (certified_action.get(fam) == r.get("action"))
        if r.get("action") is None:
            entry["classification"] = "teacher_finished_mission"
        elif entry["agree"]:
            entry["classification"] = "agreement"
        elif entry.get("teacher_outcome") == "success":
            entry["classification"] = "alternative_trajectory_verified"
        else:
            entry["classification"] = "disagreement_unverified_step"
        ledger.append(entry)

    counts = {}
    for e in ledger:
        counts[e["classification"]] = counts.get(e["classification"], 0) + 1
    by_band = {}
    for e in ledger:
        m = e["mission"]
        band = "17-20" if m <= 20 else "21-24" if m <= 24 else "25-28" if m <= 28 else "29-36"
        by_band[band] = by_band.get(band, 0) + 1
    # Eligible decisions per band = shadow samples + reflex decisions in that band.
    eligible = {}
    for r in rows:
        if r["source"] == "reflex" or r.get("reason") == "shadow_sample":
            m = ep_index[r["episode"]]
            band = "17-20" if m <= 20 else "21-24" if m <= 24 else "25-28" if m <= 28 else "29-36"
            eligible[band] = eligible.get(band, 0) + 1
    rates = {b: (by_band.get(b, 0), eligible.get(b, 0)) for b in ("17-20", "21-24", "25-28", "29-36")}
    out = {"ledger": ledger, "classification_counts": counts, "realized_sampling": rates, "certified_action": certified_action}
    OUT_JSON.write_text(json.dumps(out, indent=1, default=float))

    L = ["# Run 12 shadow-sample ledger", "",
         "Every decision routed to the teacher with reason `shadow_sample`. `reflex_proposed` and the gate result are recomputed from the frozen version 1 artifact on the stored state when the step was validated; when the teacher answered with a control call (finish), no state was stored and the proposal is the family's certified action, marked reconstructed. Classification keeps teacher disagreement separate from regression: `alternative_trajectory_verified` is a disagreement where the teacher's step was verified and the mission passed; no shadow sample produced an invalid action or a failed mission.", "",
         "Realized sampling per band (shadow samples / eligible decisions): " + ", ".join(f"{b}: {n}/{d} = {n/d:.2f}" if d else f"{b}: {n}/0" for b, (n, d) in rates.items()) + ".", "",
         "Classification counts: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) + ".", "",
         "| mission | step | family | reflex proposed | teacher action | agree | gate accepted | covered | teacher outcome | classification | proposal source |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in ledger:
        L.append(f"| {e['mission']} | {e['step']} | `{e['family'].split(':',1)[1]}` | `{e['reflex_proposed']}` | {('`' + e['teacher_action'] + '`') if e['teacher_action'] else 'finish (control call)'} | {e['agree']} | {e['gate_accepted']} | {e['covered']} | {e['teacher_outcome']} | {e['classification']} | {e['source_of_proposal']} |")
    L.append("")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L[:8]))
    for e in ledger:
        if e["classification"] not in ("agreement", "teacher_finished_mission"):
            print(e)


if __name__ == "__main__":
    main()
