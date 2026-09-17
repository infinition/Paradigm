"""C7: language-aware trust gating, exploratory on versions 1 and 2. See ``PREREG_C7.md``.

The decision model is the frozen C6R model; only the acceptance gate changes. On version 1
the predictions are the C6 out-of-fold ones (leave-one-group-out); on version 2 they are the
frozen model's. G3-exp transports an out-of-fold uncertainty threshold; it is not conformal.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import sys
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
from intent_bench_run import BENCH, POSITIVE, fmt, lexical, specialized  # noqa: E402
from intent_temporal_fr import features, vector  # noqa: E402

from paradigm.ood import MahalanobisGate  # noqa: E402

OUT_JSON = BENCH / "results_c7.json"
OUT_MD = BENCH / "RESULTS_C7.md"
PERCENTILES = (90, 95, 99)
ALPHAS = (0.05, 0.10)
MIN_CLASS = 20


def dataset(path: Path, sha_file: Path, scores_file: Path):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == sha_file.read_text().split()[0]
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    texts = [r["text"] for r in rows]
    sc = json.loads(scores_file.read_text()); assert sc["texts"] == texts
    a = np.stack([lexical(t) for t in texts]); s, _ = specialized(texts); t = np.stack([vector(x, 1.0) for x in texts]); e = np.asarray(sc["E_RERANK"])
    return rows, a, s, t, e, np.concatenate([a, s, e, t], axis=1)


def gates_from_v1(x1, s1, y1, classes):
    g0 = MahalanobisGate(quantile=0.997).fit(x1)
    g1 = {}
    for c in classes:
        m = y1 == c
        g1[c] = MahalanobisGate(quantile=0.997).fit(x1[m]) if m.sum() >= MIN_CLASS else None
    nn = NearestNeighbors(n_neighbors=4).fit(s1)
    d, _ = nn.kneighbors(s1); train_density = d[:, 1:4].mean(axis=1)
    g2_thr = {p: float(np.percentile(train_density, p)) for p in PERCENTILES}
    return g0, g1, nn, g2_thr


def apply_gates(x, s, pred, rows, g0, g1, nn, g2_thr, g3_thr):
    out = {"G0": np.asarray(g0.accept(x), dtype=bool)}
    acc1 = np.zeros(len(x), dtype=bool)
    for i in range(len(x)):
        g = g1.get(str(pred[i]))
        acc1[i] = bool(np.asarray(g.accept(x[i:i + 1]), dtype=bool)[0]) if g is not None else False
    out["G1"] = acc1
    d, _ = nn.kneighbors(s, n_neighbors=3); dens = d.mean(axis=1)
    for p in PERCENTILES:
        out[f"G2_p{p}"] = dens <= g2_thr[p]
    actionable = np.asarray([bool(features(r["text"])["actionable_now"]) for r in rows])
    out["G4"] = acc1 & actionable
    return out, actionable


def report(rows, y, pred, conf, thr, accepted, extra_mask=None) -> dict[str, Any]:
    m = np.ones(len(rows), dtype=bool) if extra_mask is None else extra_mask
    is_pos = y == POSITIVE; hard = np.asarray([r["role"] == "hard_negative" for r in rows]) & ~is_pos
    fired = (conf >= thr) & accepted & m
    return {
        "acceptance_positives": float(np.mean(accepted[m & is_pos])), "acceptance_hard_negatives": float(np.mean(accepted[m & hard])),
        "coverage": float(fired.sum() / m.sum()), "selective_accuracy": float(np.mean((pred == y)[fired])) if fired.any() else None,
        "hard_false_fast_paths": int(np.sum(fired & (pred == POSITIVE) & hard)), "false_fast_paths_all": int(np.sum(fired & (pred == POSITIVE) & ~is_pos)),
        "positive_reflex_coverage": float(np.mean((fired & (pred == POSITIVE))[m & is_pos])), "n_fired": int(fired.sum()),
    }


def main() -> None:
    with (BENCH / "c6r_frozen_model.pkl").open("rb") as fh:
        frozen = pickle.load(fh)
    assert hashlib.sha256((BENCH / "c6r_frozen_model.pkl").read_bytes()).hexdigest() == (BENCH / "c6r_frozen_model.sha256").read_text().split()[0]
    clf, thr = frozen["classifier"], float(frozen["threshold"])
    classes = [str(c) for c in clf.classes_]

    rows1, a1, s1, t1, e1, x1 = dataset(BENCH / "phrases.jsonl", BENCH / "DATASET_SHA256.txt", BENCH / "results_c6_scores.json")
    rows2, a2, s2, t2, e2, x2 = dataset(BENCH / "phrases_v2.jsonl", BENCH / "DATASET_v2_SHA256.txt", BENCH / "results_c6r_scores_v2.json")
    y1 = np.asarray([r["intent"] for r in rows1]); y2 = np.asarray([r["intent"] for r in rows2]); grp1 = np.asarray([r["group"] for r in rows1])

    # Version 1 out of sample: the C6 configuration refitted leave-one-group-out (not the frozen model).
    probs_oof = np.zeros((len(rows1), len(classes)))
    for g in sorted(set(grp1)):
        tr, te = grp1 != g, grp1 == g
        m = LogisticRegression(max_iter=3000, C=1.0).fit(x1[tr], y1[tr]); p = m.predict_proba(x1[te])
        for j, c in enumerate(m.classes_):
            probs_oof[te, classes.index(str(c))] = p[:, j]
    pred1 = np.asarray(classes)[np.argmax(probs_oof, axis=1)]; conf1 = probs_oof.max(axis=1)
    nonconf_oof = 1.0 - conf1
    g3_thr = {alpha: float(np.quantile(nonconf_oof, 1 - alpha)) for alpha in ALPHAS}

    probs2 = clf.predict_proba(x2); pred2 = np.asarray(classes)[np.argmax(probs2, axis=1)]; conf2 = probs2.max(axis=1)

    g0, g1, nn, g2_thr = gates_from_v1(x1, s1, y1, classes)
    results: dict[str, Any] = {"threshold": thr, "g2_thresholds": g2_thr, "g3_exp_thresholds": g3_thr, "v1_oof": {}, "v2": {}}
    for name, (rows, x, s, pred, conf, y) in {"v1_oof": (rows1, x1, s1, pred1, conf1, y1), "v2": (rows2, x2, s2, pred2, conf2, y2)}.items():
        gates, actionable = apply_gates(x, s, pred, rows, g0, g1, nn, g2_thr, g3_thr)
        for alpha in ALPHAS:
            gates[f"G3exp_a{alpha}"] = (1.0 - conf) <= g3_thr[alpha]
        primary = np.asarray(["ambiguous" not in r.get("tags", []) for r in rows])
        for gname, acc in gates.items():
            results[name][gname] = report(rows, y, pred, conf, thr, acc, primary)
            results[name][gname]["by_source"] = {src: report(rows, y, pred, conf, thr, acc, primary & np.asarray([r["source"] == src for r in rows])) for src in sorted({r["source"] for r in rows})}
            is_pos = y == POSITIVE
            results[name][gname]["hard_fired_by_transformation"] = {tn: int(np.sum((conf >= thr) & acc & primary & (pred == POSITIVE) & ~is_pos & np.asarray([r["transformation"] == tn for r in rows]))) for tn in ("negation", "temporal", "past_question", "object_change", "inspection_only", "conditional")}
    OUT_JSON.write_text(json.dumps(results, indent=1, default=float))

    L = ["# C7 results: language-aware trust gating (exploratory)", "",
         f"Frozen decision model of C6R (threshold {thr:.4f}); version 1 scored out of fold (leave-one-group-out refit of the same configuration), version 2 scored by the frozen model. G2 thresholds (mean distance to 3 nearest v1 sentences in S): " + ", ".join(f"p{p} {v:.3f}" for p, v in g2_thr.items()) + ". G3-exp thresholds on out-of-fold nonconformity: " + ", ".join(f"alpha {a} -> {v:.3f}" for a, v in g3_thr.items()) + ". PRIMARY slices (ambiguous excluded).", ""]
    for name, title in (("v1_oof", "Version 1, out of fold"), ("v2", "Version 2, frozen model (the C6R record)")):
        L += [f"## {title}", "", "| gate | acc. positives | acc. hard negatives | coverage | sel. acc. | hard FFP | FFP all | positive reflex coverage | fired | hard fired as CAPTURE by transformation (neg, temp, past, obj, insp, cond) |", "|---|---|---|---|---|---|---|---|---|---|"]
        for gname, r in results[name].items():
            L.append(f"| {gname} | {fmt(r['acceptance_positives'])} | {fmt(r['acceptance_hard_negatives'])} | {fmt(r['coverage'])} | {fmt(r['selective_accuracy'])} | {r['hard_false_fast_paths']} | {r['false_fast_paths_all']} | {fmt(r['positive_reflex_coverage'])} | {r['n_fired']} | " + ", ".join(str(v) for v in r["hard_fired_by_transformation"].values()) + " |")
        L.append("")
    L += ["## Version 2 by source, positive reflex coverage / selective accuracy / hard FFP", "", "| gate | " + " | ".join(sorted({r['source'] for r in rows2})) + " |", "|---|---|---|---|"]
    for gname, r in results["v2"].items():
        L.append(f"| {gname} | " + " | ".join(f"{fmt(r['by_source'][s_]['positive_reflex_coverage'])} / {fmt(r['by_source'][s_]['selective_accuracy'])} / {r['by_source'][s_]['hard_false_fast_paths']}" for s_ in sorted(r["by_source"])) + " |")
    L.append("")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
