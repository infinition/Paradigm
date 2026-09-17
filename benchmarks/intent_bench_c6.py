"""C6: goal x candidate-action relation scores as representations. See ``PREREG_C6.md``.

H1 at the representation level (same protocol as C3 and C4), H2 at the certification level
(the C5 regions with the fused k-NN on A+S+E+T). Scores are cached in results_c6_scores.json
after the first computation; both scorers are frozen.
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
from intent_action_scorers import NLIScorer, RerankScorer  # noqa: E402
from intent_bench_run import BENCH, MODELS, POSITIVE, TRANSFORMATIONS, evaluate, fmt, lexical, load, specialized  # noqa: E402
from intent_temporal_fr import features, vector  # noqa: E402

from paradigm.ood import MahalanobisGate  # noqa: E402
from paradigm.selection import select_confidence_threshold  # noqa: E402

SCORES = BENCH / "results_c6_scores.json"
OUT_JSON = BENCH / "results_c6.json"
OUT_MD = BENCH / "RESULTS_C6.md"
PERCENTILES = (90, 95, 99)


def scores(texts: list[str]) -> dict[str, Any]:
    if SCORES.exists():
        cached = json.loads(SCORES.read_text())
        if cached.get("texts") == texts:
            return cached
    nli, rr = NLIScorer(), RerankScorer()
    e_nli, e_rr, lat_nli, lat_rr, detail = [], [], [], [], []
    for t in texts:
        v, d, ms = nli.score(t); e_nli.append(v.tolist()); lat_nli.append(ms)
        w, d2, ms2 = rr.score(t); e_rr.append(w.tolist()); lat_rr.append(ms2)
        detail.append({"text": t, "nli": d, "rerank": d2})
    out = {"texts": texts, "E_NLI": e_nli, "E_RERANK": e_rr, "latency_ms": {"nli_median": float(np.median(lat_nli)), "rerank_median": float(np.median(lat_rr))}, "detail": detail}
    SCORES.write_text(json.dumps(out, indent=1))
    return out


def regions_h2(rows, x, y, grp, a, s) -> dict[str, Any]:
    """C5 regions, unchanged, with the fused k-NN on the given representation."""
    n = len(rows); classes = sorted(set(y))
    probs = np.zeros((n, len(classes))); pred_a = np.empty(n, dtype=object); pred_s = np.empty(n, dtype=object)
    accepted = np.zeros(n, dtype=bool); density = np.zeros(n); thr = {p: np.zeros(n) for p in PERCENTILES}
    for g in sorted(set(grp)):
        tr, te = grp != g, grp == g
        m = KNeighborsClassifier(n_neighbors=3).fit(x[tr], y[tr]); pr = m.predict_proba(x[te])
        for j, c in enumerate(m.classes_):
            probs[te, classes.index(str(c))] = pr[:, j]
        pred_a[te] = KNeighborsClassifier(n_neighbors=3).fit(a[tr], y[tr]).predict(a[te])
        pred_s[te] = KNeighborsClassifier(n_neighbors=3).fit(s[tr], y[tr]).predict(s[te])
        accepted[te] = np.asarray(MahalanobisGate(quantile=0.997).fit(x[tr]).accept(x[te]), dtype=bool)
        nn = NearestNeighbors(n_neighbors=4).fit(x[tr]); d_tr, _ = nn.kneighbors(x[tr]); train_density = d_tr[:, 1:4].mean(axis=1)
        d_te, _ = nn.kneighbors(x[te], n_neighbors=3); density[te] = d_te.mean(axis=1)
        for p in PERCENTILES:
            thr[p][te] = np.percentile(train_density, p)
    pred = np.asarray(classes)[np.argmax(probs, axis=1)]; conf = probs.max(axis=1)
    actionable = np.asarray([bool(features(r["text"])["actionable_now"]) for r in rows]); agree = pred_a == pred_s
    is_pos = y == POSITIVE; hard = np.asarray([r["role"] == "hard_negative" for r in rows]) & ~is_pos
    regions = {"R1": actionable, "R2": actionable & agree}
    for p in PERCENTILES:
        regions[f"R3_p{p}"] = actionable & (density <= thr[p]); regions[f"R4_p{p}"] = actionable & agree & (density <= thr[p])
    out = {}
    for name, m in regions.items():
        if not m.any():
            out[name] = {"size": 0, "certifiable": False}; continue
        t = select_confidence_threshold(y[m], probs[m], np.asarray(classes), reference_predictions=y[m], tolerance=0.01, minimum_coverage=0.55)
        fired = m & (conf >= t.threshold) & accepted
        sel = float(np.mean((pred == y)[fired])) if fired.any() else None
        ffp = int(np.sum(fired & (pred == POSITIVE) & hard)); cov = float(np.mean(fired[m]))
        out[name] = {"size": int(m.sum()), "coverage_under_gate": cov, "selective_accuracy_under_gate": sel, "false_fast_paths_hard": ffp,
                     "positive_recall_under_gate": float(np.mean((fired & (pred == POSITIVE))[is_pos])), "selector_feasible": bool(t.feasible),
                     "certifiable": bool(t.feasible and ffp == 0 and cov > 0 and (sel or 0.0) >= 0.99)}
    return out


def main() -> None:
    rows = load(); texts = [r["text"] for r in rows]
    sc = scores(texts)
    e_nli = np.asarray(sc["E_NLI"]); e_rr = np.asarray(sc["E_RERANK"])
    a = np.stack([lexical(t) for t in texts]); s, _ = specialized(texts); t = np.stack([vector(x, 1.0) for x in texts])
    y = np.asarray([r["intent"] for r in rows]); grp = np.asarray([r["group"] for r in rows])
    reps = {
        "A+S": np.concatenate([a, s], axis=1), "A+S+T": np.concatenate([a, s, t], axis=1),
        "E_NLI": e_nli, "A+E_NLI": np.concatenate([a, e_nli], axis=1), "S+E_NLI": np.concatenate([s, e_nli], axis=1), "A+S+E_NLI+T": np.concatenate([a, s, e_nli, t], axis=1),
        "E_RERANK": e_rr, "A+E_RERANK": np.concatenate([a, e_rr], axis=1), "S+E_RERANK": np.concatenate([s, e_rr], axis=1), "A+S+E_RERANK+T": np.concatenate([a, s, e_rr, t], axis=1),
    }
    results: dict[str, Any] = {"dataset_sha256": (BENCH / "DATASET_SHA256.txt").read_text().split()[0], "latency_ms": sc["latency_ms"], "evaluations": {}, "h2": {}}
    for rn, x in reps.items():
        for mn, make in MODELS.items():
            results["evaluations"][f"{rn}|{mn}"] = evaluate(rows, x, make)
    for rn in reps:
        if rn in ("A+S", "A+S+T"):
            continue
        for mn in MODELS:
            e = results["evaluations"][f"{rn}|{mn}"]
            for base_name in ("A+S+T", "A+S"):
                b = results["evaluations"][f"{base_name}|{mn}"]
                e[f"h1_vs_{base_name}"] = bool(e["unseen_positive_recall_under_gate"] > b["unseen_positive_recall_under_gate"] and e["false_fast_paths_on_hard_negatives"] <= b["false_fast_paths_on_hard_negatives"])
    for rn in ("A+S+E_NLI+T", "A+S+E_RERANK+T", "A+S+T"):
        results["h2"][rn] = regions_h2(rows, reps[rn], y, grp, a, s)
    # Raw scores on the decisive sentences and per-transformation means, before any classifier.
    decisive = ["Prends-moi en photo.", "Ne me prends pas en photo.", "Tu m'as pris en photo tout à l'heure ?", "Fais une photo de moi avec la webcam quand je te le dirai."]
    results["decisive"] = [d for d in sc["detail"] if d["text"] in decisive]
    cap_e = e_nli[:, 0]; cap_r = e_rr[:, 0]
    per = {}
    for key in ("positives",) + TRANSFORMATIONS:
        m = (y == POSITIVE) if key == "positives" else np.asarray([r["transformation"] == key and r["intent"] != POSITIVE for r in rows])
        per[key] = {"n": int(m.sum()), "nli_capture_entailment_mean": float(cap_e[m].mean()), "nli_capture_entailment_gt_0.5": float(np.mean(cap_e[m] > 0.5)), "rerank_capture_yes_mean": float(cap_r[m].mean()), "rerank_capture_yes_gt_0.5": float(np.mean(cap_r[m] > 0.5))}
    results["capture_scores_by_group"] = per
    OUT_JSON.write_text(json.dumps(results, indent=1, default=float))

    L = ["# C6 results: goal x candidate action", "",
         f"Dataset sha256 `{results['dataset_sha256']}`. Scorers frozen: NLI median {sc['latency_ms']['nli_median']:.0f} ms per sentence (5 contracts), reranker median {sc['latency_ms']['rerank_median']:.0f} ms, CPU.", "",
         "## Raw `camera.capture` scores by sentence type, before any classifier", "",
         "| sentences | n | NLI entailment mean / share > 0.5 | reranker yes mean / share > 0.5 |", "|---|---|---|---|"]
    for key, v in per.items():
        L.append(f"| {key} | {v['n']} | {v['nli_capture_entailment_mean']:.2f} / {v['nli_capture_entailment_gt_0.5']:.2f} | {v['rerank_capture_yes_mean']:.2f} / {v['rerank_capture_yes_gt_0.5']:.2f} |")
    L += ["", "## H1, under the gate", "", "| representation | model | unseen positive recall | FFP hard | per transformation: " + ", ".join(TRANSFORMATIONS) + " | coverage | sel. acc. | feasible | H1 vs A+S+T | H1 vs A+S |", "|---|---|---|---|---|---|---|---|---|---|"]
    for key, e in results["evaluations"].items():
        rn, mn = key.split("|")
        L.append(f"| {rn} | {mn} | {fmt(e['unseen_positive_recall_under_gate'])} | {e['false_fast_paths_on_hard_negatives']} | " + ", ".join(str(e["per_transformation"][x]["false_fast_paths"]) for x in TRANSFORMATIONS) + f" | {fmt(e['coverage'])} | {fmt(e['selective_accuracy'])} | {e['feasible']} | {e.get('h1_vs_A+S+T', '')} | {e.get('h1_vs_A+S', '')} |")
    L += ["", "## Without the gate", "", "| representation | model | accuracy | recall CAPTURE_PERSON | predicted CAPTURE_PERSON on: " + ", ".join(TRANSFORMATIONS) + " |", "|---|---|---|---|---|"]
    for key, e in results["evaluations"].items():
        rn, mn = key.split("|")
        L.append(f"| {rn} | {mn} | {fmt(e['accuracy_no_gate'])} | {fmt(e['per_class_recall_no_gate'].get(POSITIVE))} | " + ", ".join(str(e["per_transformation"][x]["predicted_positive_no_gate"]) for x in TRANSFORMATIONS) + " |")
    L += ["", "## H2, the C5 regions with the fused k-NN", "", "| representation | region | size | coverage under gate | sel. acc. under gate | FFP hard | positive recall | feasible | certifiable |", "|---|---|---|---|---|---|---|---|---|"]
    for rn, regs in results["h2"].items():
        for name, r in regs.items():
            L.append(f"| {rn} | {name} | {r.get('size')} | {fmt(r.get('coverage_under_gate'))} | {fmt(r.get('selective_accuracy_under_gate'))} | {r.get('false_fast_paths_hard')} | {fmt(r.get('positive_recall_under_gate'))} | {r.get('selector_feasible')} | {r['certifiable']} |")
    L.append("")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
