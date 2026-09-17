"""C6R step 2: the single scoring pass of the frozen model on dataset version 2.

No training, no calibration, no second attempt. See ``PREREG_C6R.md``.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
from intent_action_scorers import RerankScorer  # noqa: E402
from intent_bench_run import BENCH, POSITIVE, fmt, lexical, specialized  # noqa: E402
from intent_temporal_fr import vector  # noqa: E402

V2 = BENCH / "phrases_v2.jsonl"
MODEL = BENCH / "c6r_frozen_model.pkl"
SCORES = BENCH / "results_c6r_scores_v2.json"
OUT_JSON = BENCH / "results_c6r.json"
OUT_MD = BENCH / "RESULTS_C6R.md"
TRANSFORMATIONS = ("negation", "temporal", "past_question", "object_change", "inspection_only", "conditional")


def main() -> None:
    if OUT_JSON.exists():
        raise SystemExit("C6R results already exist; the protocol allows one pass")
    assert hashlib.sha256(V2.read_bytes()).hexdigest() == (BENCH / "DATASET_v2_SHA256.txt").read_text().split()[0], "v2 changed"
    assert hashlib.sha256(MODEL.read_bytes()).hexdigest() == (BENCH / "c6r_frozen_model.sha256").read_text().split()[0], "frozen model changed"
    with MODEL.open("rb") as fh:
        frozen = pickle.load(fh)
    rows = [json.loads(line) for line in V2.read_text(encoding="utf-8").splitlines()]
    texts = [r["text"] for r in rows]
    if SCORES.exists() and json.loads(SCORES.read_text()).get("texts") == texts:
        e = np.asarray(json.loads(SCORES.read_text())["E_RERANK"])
    else:
        rr = RerankScorer()
        vecs, details = [], []
        for t in texts:
            v, d, _ = rr.score(t); vecs.append(v.tolist()); details.append(d)
        SCORES.write_text(json.dumps({"texts": texts, "E_RERANK": vecs, "detail": details}, indent=1))
        e = np.asarray(vecs)
    a = np.stack([lexical(t) for t in texts]); s, _ = specialized(texts); t = np.stack([vector(x, 1.0) for x in texts])
    x = np.concatenate([a, s, e, t], axis=1)
    assert x.shape[1] == sum(frozen["feature_layout"].values())
    clf, gate, thr = frozen["classifier"], frozen["gate"], float(frozen["threshold"])
    classes = np.asarray([str(c) for c in clf.classes_])
    probs = clf.predict_proba(x); pred = classes[np.argmax(probs, axis=1)]; conf = probs.max(axis=1)
    accepted = np.asarray(gate.accept(x), dtype=bool)
    fired = (conf >= thr) & accepted
    y = np.asarray([r["intent"] for r in rows])
    is_pos = y == POSITIVE
    hard = np.asarray([r["role"] == "hard_negative" for r in rows]) & ~is_pos
    ambiguous = np.asarray(["ambiguous" in r["tags"] for r in rows])
    primary = ~ambiguous

    def slice_report(m: np.ndarray) -> dict[str, Any]:
        f = fired & m
        return {
            "n": int(m.sum()), "coverage": float(f.sum() / m.sum()) if m.any() else None,
            "selective_accuracy": float(np.mean((pred == y)[f])) if f.any() else None,
            "hard_false_fast_paths": int(np.sum(f & (pred == POSITIVE) & hard)), "false_fast_paths_all": int(np.sum(f & (pred == POSITIVE) & ~is_pos)),
            "positives": int((m & is_pos).sum()), "positives_fired_correct": int(np.sum(f & is_pos & (pred == POSITIVE))), "positives_fired_wrong": int(np.sum(f & is_pos & (pred != POSITIVE))),
            "positive_reflex_coverage": float(np.mean((f & (pred == POSITIVE))[m & is_pos])) if (m & is_pos).any() else None,
            "gate_acceptance": float(np.mean(accepted[m])), "covered_share": float(np.mean((conf >= thr)[m])),
            "accuracy_no_gate": float(np.mean((pred == y)[m])),
        }

    prim = slice_report(primary); diag = slice_report(ambiguous)
    criterion = bool((prim["selective_accuracy"] or 0.0) >= 0.99 and prim["hard_false_fast_paths"] == 0 and (prim["coverage"] or 0.0) >= 0.15)
    per_transformation = {}
    for tname in TRANSFORMATIONS:
        m = primary & np.asarray([r["transformation"] == tname for r in rows]) & ~is_pos
        per_transformation[tname] = {"n": int(m.sum()), "fired": int((fired & m).sum()), "fired_as_capture": int(np.sum(fired & m & (pred == POSITIVE))), "predicted_capture_no_gate": int(np.sum(m & (pred == POSITIVE)))}
    per_source = {src: slice_report(primary & np.asarray([r["source"] == src for r in rows])) for src in sorted({r["source"] for r in rows})}
    per_tag = {tag: slice_report(np.asarray([tag in r["tags"] for r in rows])) for tag in ("oral", "long")}
    fired_list = [{"text": rows[i]["text"], "true": y[i], "pred": pred[i], "confidence": float(conf[i]), "source": rows[i]["source"], "tags": rows[i]["tags"]} for i in np.flatnonzero(fired) if pred[i] != y[i] or (pred[i] == POSITIVE)]
    raw = {}
    cap = e[:, 0]
    for key in ("positives",) + TRANSFORMATIONS:
        m = is_pos if key == "positives" else np.asarray([r["transformation"] == key for r in rows]) & ~is_pos
        raw[key] = {"n": int(m.sum()), "rerank_capture_yes_mean": float(cap[m].mean()) if m.any() else None}
    out = {"dataset_v2_sha256": (BENCH / "DATASET_v2_SHA256.txt").read_text().split()[0], "frozen_model_sha256": (BENCH / "c6r_frozen_model.sha256").read_text().split()[0],
           "threshold": thr, "reference_v1": frozen["reference_v1"], "primary": prim, "diagnostic": diag, "criterion_replicated": criterion,
           "per_transformation_primary": per_transformation, "per_source_primary": per_source, "per_tag": per_tag, "fired_positive_or_wrong": fired_list, "raw_rerank_capture": raw}
    OUT_JSON.write_text(json.dumps(out, indent=1, default=float))

    L = ["# C6R results: prospective replication on dataset version 2", "",
         f"Frozen model `{out['frozen_model_sha256'][:16]}` (trained on v1, threshold {thr:.4f} by the pre-registered rule), dataset v2 `{out['dataset_v2_sha256'][:16]}`, one pass.", "",
         "## Verdict", "", f"**{'REPLICATED' if criterion else 'NOT REPLICATED'}** on the PRIMARY slice: selective accuracy {fmt(prim['selective_accuracy'])} (>= 0.99 required), hard-negative false fast paths {prim['hard_false_fast_paths']} (0 required), coverage {fmt(prim['coverage'])} (>= 0.15 required).", "",
         "## Slices", "", "| slice | n | coverage under gate | sel. acc. | hard FFP | FFP all | positives | fired correct / wrong | positive reflex coverage | gate acc. | covered share | accuracy no gate |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in (("PRIMARY", prim), ("DIAGNOSTIC (ambiguous)", diag)):
        L.append(f"| {name} | {r['n']} | {fmt(r['coverage'])} | {fmt(r['selective_accuracy'])} | {r['hard_false_fast_paths']} | {r['false_fast_paths_all']} | {r['positives']} | {r['positives_fired_correct']} / {r['positives_fired_wrong']} | {fmt(r['positive_reflex_coverage'])} | {fmt(r['gate_acceptance'])} | {fmt(r['covered_share'])} | {fmt(r['accuracy_no_gate'])} |")
    for name, r in per_source.items():
        L.append(f"| PRIMARY, source {name} | {r['n']} | {fmt(r['coverage'])} | {fmt(r['selective_accuracy'])} | {r['hard_false_fast_paths']} | {r['false_fast_paths_all']} | {r['positives']} | {r['positives_fired_correct']} / {r['positives_fired_wrong']} | {fmt(r['positive_reflex_coverage'])} | {fmt(r['gate_acceptance'])} | {fmt(r['covered_share'])} | {fmt(r['accuracy_no_gate'])} |")
    for name, r in per_tag.items():
        L.append(f"| tag {name} | {r['n']} | {fmt(r['coverage'])} | {fmt(r['selective_accuracy'])} | {r['hard_false_fast_paths']} | {r['false_fast_paths_all']} | {r['positives']} | {r['positives_fired_correct']} / {r['positives_fired_wrong']} | {fmt(r['positive_reflex_coverage'])} | {fmt(r['gate_acceptance'])} | {fmt(r['covered_share'])} | {fmt(r['accuracy_no_gate'])} |")
    L += ["", "## Hard negatives of the PRIMARY slice, per transformation", "", "| transformation | n | fired | fired as CAPTURE_PERSON | predicted CAPTURE_PERSON without gate | reranker capture yes mean |", "|---|---|---|---|---|---|"]
    for tname, r in per_transformation.items():
        L.append(f"| {tname} | {r['n']} | {r['fired']} | {r['fired_as_capture']} | {r['predicted_capture_no_gate']} | {fmt(raw[tname]['rerank_capture_yes_mean'])} |")
    L += ["", f"Reranker capture yes mean on positives: {fmt(raw['positives']['rerank_capture_yes_mean'])}.", "",
          "## Fired sentences that are wrong or predicted CAPTURE_PERSON", "", "| text | true | pred | confidence | source | tags |", "|---|---|---|---|---|---|"]
    for f in fired_list:
        L.append(f"| {f['text']} | {f['true']} | {f['pred']} | {f['confidence']:.2f} | {f['source']} | {', '.join(f['tags'])} |")
    L += ["", f"Reference on v1 (in sample, recorded at the freeze): {json.dumps(frozen['reference_v1'])}", ""]
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
