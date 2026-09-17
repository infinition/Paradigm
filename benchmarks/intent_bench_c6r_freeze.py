"""C6R step 1: train the pre-registered configuration on dataset version 1, freeze it, hash it.

Run once, before dataset version 2 is written. See ``PREREG_C6R.md``.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
from intent_bench_run import BENCH, POSITIVE, lexical, load, specialized  # noqa: E402
from intent_temporal_fr import vector  # noqa: E402

from paradigm.ood import MahalanobisGate  # noqa: E402
from paradigm.selection import select_confidence_threshold  # noqa: E402

MODEL = BENCH / "c6r_frozen_model.pkl"
HASH = BENCH / "c6r_frozen_model.sha256"


def main() -> None:
    if MODEL.exists():
        raise SystemExit("frozen model already exists; C6R allows one freeze")
    rows = load()
    texts = [r["text"] for r in rows]
    sc = json.loads((BENCH / "results_c6_scores.json").read_text())
    assert sc["texts"] == texts, "cached reranker scores do not match dataset version 1"
    a = np.stack([lexical(t) for t in texts]); s, _ = specialized(texts); t = np.stack([vector(x, 1.0) for x in texts])
    e = np.asarray(sc["E_RERANK"])
    x = np.concatenate([a, s, e, t], axis=1)
    y = np.asarray([r["intent"] for r in rows])
    clf = LogisticRegression(max_iter=3000, C=1.0).fit(x, y)
    probs = clf.predict_proba(x)
    classes = np.asarray([str(c) for c in clf.classes_])
    thr = select_confidence_threshold(y, probs, classes, reference_predictions=y, tolerance=0.01, minimum_coverage=0.55)
    gate = MahalanobisGate(quantile=0.997).fit(x)
    # Reference values on version 1 itself (in sample), recorded for the report.
    pred = classes[np.argmax(probs, axis=1)]; conf = probs.max(axis=1)
    accepted = np.asarray(gate.accept(x), dtype=bool)
    fired = (conf >= thr.threshold) & accepted
    is_pos = y == POSITIVE
    hard = np.asarray([r["role"] == "hard_negative" for r in rows]) & ~is_pos
    reference = {
        "threshold": float(thr.threshold), "selector_coverage": float(thr.coverage), "selector_selective_accuracy": float(thr.selective_accuracy), "selector_feasible": bool(thr.feasible),
        "in_sample_fired_share": float(fired.mean()), "in_sample_selective_accuracy_under_gate": float(np.mean((pred == y)[fired])) if fired.any() else None,
        "in_sample_hard_false_fast_paths": int(np.sum(fired & (pred == POSITIVE) & hard)), "in_sample_positive_reflex_coverage": float(np.mean((fired & (pred == POSITIVE))[is_pos])),
    }
    payload = {
        "config": "A+S+E_RERANK+T | logistic regression | selector rule tol 0.01 min cov 0.55 | Mahalanobis 0.997",
        "dataset_v1_sha256": (BENCH / "DATASET_SHA256.txt").read_text().split()[0],
        "classifier": clf, "classes": classes.tolist(), "threshold": float(thr.threshold), "gate": gate, "reference_v1": reference,
        "feature_layout": {"A": int(a.shape[1]), "S": int(s.shape[1]), "E_RERANK": int(e.shape[1]), "T": int(t.shape[1])},
    }
    with MODEL.open("wb") as fh:
        pickle.dump(payload, fh)
    digest = hashlib.sha256(MODEL.read_bytes()).hexdigest()
    HASH.write_text(f"{digest}  c6r_frozen_model.pkl\n")
    print(json.dumps(reference, indent=1))
    print("sha256", digest)


if __name__ == "__main__":
    main()
