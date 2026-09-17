"""C4b: extractor version 2 on versions 1 and 2. See ``PREREG_C4B.md``. Last experiment of the line.

1. Extractor outputs on both datasets, and every sentence whose category changed from v1 to v2.
2. The C4 protocol on version 1: A+S+T_v1 against A+S+T_v2.
3. The C7 gate grid with A+S+E_RERANK+T_v2, classifier refit (not the frozen C6R model).
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
from intent_bench_c7 import ALPHAS, apply_gates, dataset, gates_from_v1, report  # noqa: E402
from intent_bench_run import BENCH, MODELS, POSITIVE, TRANSFORMATIONS, evaluate, fmt  # noqa: E402
from intent_temporal_fr import features  # noqa: E402
from intent_temporal_fr_v2 import features_v2, vector_v2  # noqa: E402

from paradigm.selection import select_confidence_threshold  # noqa: E402

OUT_JSON = BENCH / "results_c4b.json"
OUT_MD = BENCH / "RESULTS_C4B.md"
TR6 = TRANSFORMATIONS + ("conditional",)


def extractor_report(rows) -> dict[str, Any]:
    out: dict[str, Any] = {"by_transformation": {}, "changed": []}
    for key in ("base_or_variant",) + TR6:
        sel = [r for r in rows if (r["transformation"] or "base_or_variant") == key]
        f1 = [features(r["text"]) for r in sel]; f2 = [features_v2(r["text"]) for r in sel]
        out["by_transformation"][key] = {"n": len(sel), "v1": dict(collections.Counter(str(f["temporal"]) for f in f1)), "v2": dict(collections.Counter(str(f["temporal"]) for f in f2)),
                                         "actionable_v1": sum(bool(f["actionable_now"]) for f in f1), "actionable_v2": sum(bool(f["actionable_now"]) for f in f2)}
    for r in rows:
        a, b = features(r["text"]), features_v2(r["text"])
        if a["temporal"] != b["temporal"] or a["actionable_now"] != b["actionable_now"]:
            out["changed"].append({"text": r["text"], "intent": r["intent"], "transformation": r["transformation"], "v1": a["temporal"], "v2": b["temporal"], "actionable_v1": a["actionable_now"], "actionable_v2": b["actionable_now"]})
    return out


def main() -> None:
    rows1, a1, s1, t1, e1, _ = dataset(BENCH / "phrases.jsonl", BENCH / "DATASET_SHA256.txt", BENCH / "results_c6_scores.json")
    rows2, a2, s2, t2, e2, _ = dataset(BENCH / "phrases_v2.jsonl", BENCH / "DATASET_v2_SHA256.txt", BENCH / "results_c6r_scores_v2.json")
    t1v2 = np.stack([vector_v2(r["text"], 1.0) for r in rows1]); t2v2 = np.stack([vector_v2(r["text"], 1.0) for r in rows2])
    results: dict[str, Any] = {"extractor_v1_dataset": extractor_report(rows1), "extractor_v2_dataset": extractor_report(rows2), "c4_protocol_v1": {}, "gates": {}}

    # 2. C4 protocol on version 1.
    reps = {"A+S+T_v1": np.concatenate([a1, s1, t1], axis=1), "A+S+T_v2": np.concatenate([a1, s1, t1v2], axis=1)}
    for rn, x in reps.items():
        for mn, make in MODELS.items():
            results["c4_protocol_v1"][f"{rn}|{mn}"] = evaluate(rows1, x, make)
    for mn in MODELS:
        e, b = results["c4_protocol_v1"][f"A+S+T_v2|{mn}"], results["c4_protocol_v1"][f"A+S+T_v1|{mn}"]
        e["criterion"] = bool(e["false_fast_paths_on_hard_negatives"] < b["false_fast_paths_on_hard_negatives"] and e["unseen_positive_recall_under_gate"] >= b["unseen_positive_recall_under_gate"])

    # 3. Gate grid with T_v2, classifier refit.
    y1 = np.asarray([r["intent"] for r in rows1]); y2 = np.asarray([r["intent"] for r in rows2]); grp1 = np.asarray([r["group"] for r in rows1])
    x1 = np.concatenate([a1, s1, e1, t1v2], axis=1); x2 = np.concatenate([a2, s2, e2, t2v2], axis=1)
    classes = sorted(set(y1))
    probs_oof = np.zeros((len(rows1), len(classes)))
    for g in sorted(set(grp1)):
        tr, te = grp1 != g, grp1 == g
        m = LogisticRegression(max_iter=3000, C=1.0).fit(x1[tr], y1[tr]); p = m.predict_proba(x1[te])
        for j, c in enumerate(m.classes_):
            probs_oof[te, classes.index(str(c))] = p[:, j]
    pred1 = np.asarray(classes)[np.argmax(probs_oof, axis=1)]; conf1 = probs_oof.max(axis=1)
    full = LogisticRegression(max_iter=3000, C=1.0).fit(x1, y1)
    thr_rule = select_confidence_threshold(y1, full.predict_proba(x1), np.asarray([str(c) for c in full.classes_]), reference_predictions=y1, tolerance=0.01, minimum_coverage=0.55)
    thr = float(thr_rule.threshold)
    probs2 = full.predict_proba(x2); pred2 = np.asarray([str(c) for c in full.classes_])[np.argmax(probs2, axis=1)]; conf2 = probs2.max(axis=1)
    g3_thr = {alpha: float(np.quantile(1.0 - conf1, 1 - alpha)) for alpha in ALPHAS}
    g0, g1, nn, g2_thr = gates_from_v1(x1, s1, y1, classes)
    results["gates"] = {"threshold_rule_value": thr, "selector_feasible_in_sample": bool(thr_rule.feasible), "v1_oof": {}, "v2": {}}
    # apply_gates reads actionable_now from the v1 extractor for G4; here G4 must use v2.
    for name, (rows, x, s, pred, conf, y) in {"v1_oof": (rows1, x1, s1, pred1, conf1, y1), "v2": (rows2, x2, s2, pred2, conf2, y2)}.items():
        gates, _ = apply_gates(x, s, pred, rows, g0, g1, nn, g2_thr, g3_thr)
        actionable_v2 = np.asarray([bool(features_v2(r["text"])["actionable_now"]) for r in rows])
        gates["G4"] = gates["G1"] & actionable_v2
        gates["G2_p95+actionable_v2"] = gates["G2_p95"] & actionable_v2
        for alpha in ALPHAS:
            gates[f"G3exp_a{alpha}"] = (1.0 - conf) <= g3_thr[alpha]
        primary = np.asarray(["ambiguous" not in r.get("tags", []) for r in rows])
        for gname, acc in gates.items():
            r = report(rows, y, pred, conf, thr, acc, primary)
            is_pos = y == POSITIVE
            r["hard_fired_by_transformation"] = {tn: int(np.sum((conf >= thr) & acc & primary & (pred == POSITIVE) & ~is_pos & np.asarray([rr["transformation"] == tn for rr in rows]))) for tn in TR6}
            r["meets_grid"] = bool((r["selective_accuracy"] or 0.0) >= 0.99 and r["hard_false_fast_paths"] == 0 and r["coverage"] >= 0.15)
            results["gates"][name][gname] = r
    OUT_JSON.write_text(json.dumps(results, indent=1, default=float))

    L = ["# C4b results: extractor version 2 (last experiment of the line)", "", "## Extractor outputs, version 1 dataset then version 2 dataset (v1 extractor -> v2 extractor)", ""]
    for dname in ("extractor_v1_dataset", "extractor_v2_dataset"):
        L += [f"### {dname.replace('extractor_', 'dataset ').replace('_dataset', '')}", "", "| sentences | n | categories v1 | categories v2 | actionable v1 -> v2 |", "|---|---|---|---|---|"]
        for key, v in results[dname]["by_transformation"].items():
            L.append(f"| {key} | {v['n']} | " + ", ".join(f"{k} {n}" for k, n in sorted(v["v1"].items())) + " | " + ", ".join(f"{k} {n}" for k, n in sorted(v["v2"].items())) + f" | {v['actionable_v1']} -> {v['actionable_v2']} |")
        L += ["", f"Sentences whose category or actionability changed: {len(results[dname]['changed'])}", "", "| text | class | transformation | v1 | v2 | actionable v1 -> v2 |", "|---|---|---|---|---|---|"]
        for c in results[dname]["changed"]:
            L.append(f"| {c['text']} | {c['intent']} | {c['transformation']} | {c['v1']} | {c['v2']} | {c['actionable_v1']} -> {c['actionable_v2']} |")
        L.append("")
    L += ["## C4 protocol on version 1: A+S+T_v1 against A+S+T_v2, under the gate", "", "| representation | model | unseen positive recall | FFP hard | per transformation: " + ", ".join(TRANSFORMATIONS) + " | coverage | sel. acc. | feasible | criterion |", "|---|---|---|---|---|---|---|---|---|"]
    for key, e in results["c4_protocol_v1"].items():
        rn, mn = key.split("|")
        L.append(f"| {rn} | {mn} | {fmt(e['unseen_positive_recall_under_gate'])} | {e['false_fast_paths_on_hard_negatives']} | " + ", ".join(str(e["per_transformation"][x]["false_fast_paths"]) for x in TRANSFORMATIONS) + f" | {fmt(e['coverage'])} | {fmt(e['selective_accuracy'])} | {e['feasible']} | {e.get('criterion', '')} |")
    L += ["", f"## Gate grid with A+S+E_RERANK+T_v2 (classifier refit, threshold by the rule = {thr:.4f}, in-sample selector feasible {results['gates']['selector_feasible_in_sample']})", ""]
    for name, title in (("v1_oof", "Version 1, out of fold"), ("v2", "Version 2, refit on all of version 1")):
        L += [f"### {title}", "", "| gate | acc. positives | acc. hard neg. | coverage | sel. acc. | hard FFP | FFP all | positive reflex coverage | fired | hard fired as CAPTURE (" + ", ".join(TR6) + ") | meets grid |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for gname, r in results["gates"][name].items():
            L.append(f"| {gname} | {fmt(r['acceptance_positives'])} | {fmt(r['acceptance_hard_negatives'])} | {fmt(r['coverage'])} | {fmt(r['selective_accuracy'])} | {r['hard_false_fast_paths']} | {r['false_fast_paths_all']} | {fmt(r['positive_reflex_coverage'])} | {r['n_fired']} | " + ", ".join(str(v) for v in r["hard_fired_by_transformation"].values()) + f" | {r['meets_grid']} |")
        L.append("")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
