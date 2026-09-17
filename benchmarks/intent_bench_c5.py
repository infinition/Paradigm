"""C5: certifiability of pre-defined sub-regions of the start family. See ``PREREG_C5.md``.

Everything is out of sample: in the fold where a sentence's group is held out, the fused
k-NN (A+S+T), the lexical k-NN (A), the paraphrase k-NN (S), the gate and the density
threshold are all fitted on the training fold only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.neighbors import KNeighborsClassifier, NearestNeighbors

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
from intent_bench_run import BENCH, POSITIVE, fmt, lexical, load, specialized  # noqa: E402
from intent_temporal_fr import features, vector  # noqa: E402

from paradigm.evaluation import expected_calibration_error  # noqa: E402
from paradigm.ood import MahalanobisGate  # noqa: E402
from paradigm.selection import select_confidence_threshold  # noqa: E402

OUT_JSON = BENCH / "results_c5.json"
OUT_MD = BENCH / "RESULTS_C5.md"
PERCENTILES = (90, 95, 99)


def main() -> None:
    rows = load()
    texts = [r["text"] for r in rows]
    a = np.stack([lexical(t) for t in texts])
    s, _ = specialized(texts)
    t = np.stack([vector(x, 1.0) for x in texts])
    fused = np.concatenate([a, s, t], axis=1)
    y = np.asarray([r["intent"] for r in rows])
    grp = np.asarray([r["group"] for r in rows])
    classes = sorted(set(y))
    n = len(rows)

    probs = np.zeros((n, len(classes)))
    pred_a = np.empty(n, dtype=object)
    pred_s = np.empty(n, dtype=object)
    accepted = np.zeros(n, dtype=bool)
    density = np.zeros(n)
    density_thr = {p: np.zeros(n) for p in PERCENTILES}
    for g in sorted(set(grp)):
        tr, te = grp != g, grp == g
        model = KNeighborsClassifier(n_neighbors=3).fit(fused[tr], y[tr])
        pr = model.predict_proba(fused[te])
        for j, c in enumerate(model.classes_):
            probs[te, classes.index(str(c))] = pr[:, j]
        pred_a[te] = KNeighborsClassifier(n_neighbors=3).fit(a[tr], y[tr]).predict(a[te])
        pred_s[te] = KNeighborsClassifier(n_neighbors=3).fit(s[tr], y[tr]).predict(s[te])
        accepted[te] = np.asarray(MahalanobisGate(quantile=0.997).fit(fused[tr]).accept(fused[te]), dtype=bool)
        nn = NearestNeighbors(n_neighbors=4).fit(fused[tr])
        d_tr, _ = nn.kneighbors(fused[tr])  # first neighbor is the point itself
        train_density = d_tr[:, 1:4].mean(axis=1)
        d_te, _ = nn.kneighbors(fused[te], n_neighbors=3)
        density[te] = d_te.mean(axis=1)
        for p in PERCENTILES:
            density_thr[p][te] = np.percentile(train_density, p)

    pred = np.asarray(classes)[np.argmax(probs, axis=1)]
    conf = probs.max(axis=1)
    actionable = np.asarray([bool(features(x)["actionable_now"]) for x in texts])
    agree = pred_a == pred_s
    is_pos = y == POSITIVE
    hard = np.asarray([r["role"] == "hard_negative" for r in rows]) & ~is_pos

    regions: dict[str, np.ndarray] = {"R1": actionable, "R2": actionable & agree}
    for p in PERCENTILES:
        dens = density <= density_thr[p]
        regions[f"R3_p{p}"] = actionable & dens
        regions[f"R4_p{p}"] = actionable & agree & dens
    regions["all"] = np.ones(n, dtype=bool)

    results: dict[str, Any] = {"dataset_sha256": (BENCH / "DATASET_SHA256.txt").read_text().split()[0], "regions": {}}
    for name, member in regions.items():
        m = member
        if m.sum() == 0:
            results["regions"][name] = {"size": 0}
            continue
        thr = select_confidence_threshold(y[m], probs[m], np.asarray(classes), reference_predictions=y[m], tolerance=0.01, minimum_coverage=0.55)
        covered = m & (conf >= thr.threshold)
        fired = covered & accepted
        sel_acc_under_gate = float(np.mean((pred == y)[fired])) if fired.any() else None
        ffp_hard = int(np.sum(fired & (pred == POSITIVE) & hard))
        coverage_in_region = float(np.mean(fired[m]))
        certifiable = bool(thr.feasible and ffp_hard == 0 and coverage_in_region > 0 and (sel_acc_under_gate or 0.0) >= 0.99)
        results["regions"][name] = {
            "size": int(m.sum()), "share_all": float(m.mean()), "share_positives": float(np.mean(m[is_pos])), "share_hard_negatives": float(np.mean(m[hard])),
            "accuracy_inside_no_gate": float(np.mean((pred == y)[m])), "accuracy_outside_no_gate": float(np.mean((pred == y)[~m])) if (~m).any() else None,
            "selector_threshold": float(thr.threshold), "selector_coverage": float(thr.coverage), "selector_selective_accuracy": float(thr.selective_accuracy), "selector_feasible": bool(thr.feasible),
            "gate_acceptance_inside": float(np.mean(accepted[m])), "coverage_under_gate": coverage_in_region, "selective_accuracy_under_gate": sel_acc_under_gate,
            "false_fast_paths_hard_negatives": ffp_hard, "false_fast_paths_all": int(np.sum(fired & (pred == POSITIVE) & ~is_pos)),
            "positive_recall_under_gate": float(np.mean((fired & (pred == POSITIVE))[is_pos])),
            "ece_inside": float(expected_calibration_error(y[m], probs[m], np.asarray(classes))),
            "certifiable": certifiable,
        }
    OUT_JSON.write_text(json.dumps(results, indent=1, default=float))

    L = ["# C5 results: pre-defined sub-regions of `start`", "",
         f"Dataset sha256 `{results['dataset_sha256']}`. Fused model k-NN (3) on A+S+T; pred_A and pred_S from independent k-NN on A and on S; density and gate fitted on each training fold. Criterion, unchanged: selector feasible inside the region (selective accuracy within 0.01 of the teacher at coverage at least 0.55 of the region), 0 hard-negative false fast paths under the gate, coverage above 0.", "",
         "| region | size | share of positives / hard negatives | accuracy inside / outside (no gate) | selector: threshold, coverage, sel. acc., feasible | gate acc. inside | coverage under gate | sel. acc. under gate | FFP hard / all | positive recall under gate | ECE inside | certifiable |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in results["regions"].items():
        if r.get("size", 0) == 0:
            L.append(f"| {name} | 0 | | | | | | | | | | False |")
            continue
        L.append(f"| {name} | {r['size']} ({r['share_all']:.2f}) | {r['share_positives']:.2f} / {r['share_hard_negatives']:.2f} | {fmt(r['accuracy_inside_no_gate'])} / {fmt(r['accuracy_outside_no_gate'])} | {r['selector_threshold']:.2f}, {r['selector_coverage']:.2f}, {r['selector_selective_accuracy']:.2f}, {r['selector_feasible']} | {fmt(r['gate_acceptance_inside'])} | {fmt(r['coverage_under_gate'])} | {fmt(r['selective_accuracy_under_gate'])} | {r['false_fast_paths_hard_negatives']} / {r['false_fast_paths_all']} | {fmt(r['positive_recall_under_gate'])} | {fmt(r['ece_inside'])} | {r['certifiable']} |")
    L.append("")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
