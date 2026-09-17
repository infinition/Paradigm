"""C4: A+S against A+S+T on the frozen intent benchmark. See ``PREREG_C4.md``.

T is the deterministic temporality and actionability block (``intent_temporal_fr``),
in two pre-declared weightings (1 and 4). Same models, gate, thresholds and protocol as C3.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
from intent_bench_run import BENCH, MODELS, POSITIVE, TRANSFORMATIONS, evaluate, fmt, lexical, load, specialized  # noqa: E402
from intent_temporal_fr import features, vector  # noqa: E402

OUT_JSON = BENCH / "results_c4.json"
OUT_MD = BENCH / "RESULTS_C4.md"


def main() -> None:
    rows = load()
    texts = [r["text"] for r in rows]
    # Extractor outputs on the dataset, reported before any classifier.
    feats = [features(t) for t in texts]
    by_transformation: dict[str, Any] = {}
    for key in ("base_or_variant",) + TRANSFORMATIONS:
        sel = [f for r, f in zip(rows, feats) if (r["transformation"] or "base_or_variant") == key]
        by_transformation[key] = {
            "n": len(sel),
            "temporal": dict(collections.Counter(str(f["temporal"]) for f in sel)),
            "negated": sum(bool(f["negated"]) for f in sel),
            "actionable_now": sum(bool(f["actionable_now"]) for f in sel),
        }
    positives = [f for r, f in zip(rows, feats) if r["intent"] == POSITIVE]
    extractor_report = {"by_transformation": by_transformation, "positives_actionable_now": sum(bool(f["actionable_now"]) for f in positives), "positives": len(positives)}

    a = np.stack([lexical(t) for t in texts])
    s, lat_s = specialized(texts)
    t1 = np.stack([vector(t, 1.0) for t in texts])
    t4 = np.stack([vector(t, 4.0) for t in texts])
    reps = {"A+S": np.concatenate([a, s], axis=1), "A+S+T": np.concatenate([a, s, t1], axis=1), "A+S+T(x4)": np.concatenate([a, s, t4], axis=1)}
    results: dict[str, Any] = {"dataset_sha256": (BENCH / "DATASET_SHA256.txt").read_text().split()[0], "extractor": extractor_report, "evaluations": {}}
    for rn, x in reps.items():
        for mn, make in MODELS.items():
            results["evaluations"][f"{rn}|{mn}"] = evaluate(rows, x, make)
    # Pre-registered criterion, verbatim, per model: hard-negative false fast paths fall and
    # unseen positive recall does not fall, against A+S with the same model.
    for rn in ("A+S+T", "A+S+T(x4)"):
        for mn in MODELS:
            e, base = results["evaluations"][f"{rn}|{mn}"], results["evaluations"][f"A+S|{mn}"]
            e["criterion_c4"] = bool(e["false_fast_paths_on_hard_negatives"] < base["false_fast_paths_on_hard_negatives"] and e["unseen_positive_recall_under_gate"] >= base["unseen_positive_recall_under_gate"])
            e["temporal_ffp_fell"] = bool(e["per_transformation"]["temporal"]["false_fast_paths"] < base["per_transformation"]["temporal"]["false_fast_paths"])
    OUT_JSON.write_text(json.dumps(results, indent=1, default=float))

    L = ["# C4 results: explicit temporality and actionability features", "",
         f"Dataset sha256 `{results['dataset_sha256']}`. Extractor `intent_temporal_fr` frozen before this run.", "",
         "## Extractor outputs on the dataset (before any classifier)", "",
         "| sentences | n | temporal categories | negated | actionable_now |", "|---|---|---|---|---|"]
    for key, v in by_transformation.items():
        L.append(f"| {key} | {v['n']} | " + ", ".join(f"{k} {n}" for k, n in sorted(v["temporal"].items())) + f" | {v['negated']} | {v['actionable_now']} |")
    L += [f"| CAPTURE_PERSON sentences | {extractor_report['positives']} | | | {extractor_report['positives_actionable_now']} |", "",
          "## Under the gate: A+S against A+S+T", "",
          "| representation | model | unseen positive recall | FFP hard neg. | FFP per transformation: " + ", ".join(TRANSFORMATIONS) + " | coverage | sel. acc. | selector feasible | ECE | criterion C4 | temporal FFP fell |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, e in results["evaluations"].items():
        rn, mn = key.split("|")
        L.append(f"| {rn} | {mn} | {fmt(e['unseen_positive_recall_under_gate'])} | {e['false_fast_paths_on_hard_negatives']} | " + ", ".join(str(e["per_transformation"][t]["false_fast_paths"]) for t in TRANSFORMATIONS) + f" | {fmt(e['coverage'])} | {fmt(e['selective_accuracy'])} | {e['feasible']} | {fmt(e['ece'])} | {e.get('criterion_c4', '')} | {e.get('temporal_ffp_fell', '')} |")
    L += ["", "## Without the gate", "", "| representation | model | accuracy | recall CAPTURE_PERSON | predicted CAPTURE_PERSON on: " + ", ".join(TRANSFORMATIONS) + " |", "|---|---|---|---|---|"]
    for key, e in results["evaluations"].items():
        rn, mn = key.split("|")
        L.append(f"| {rn} | {mn} | {fmt(e['accuracy_no_gate'])} | {fmt(e['per_class_recall_no_gate'].get(POSITIVE))} | " + ", ".join(str(e["per_transformation"][t]["predicted_positive_no_gate"]) for t in TRANSFORMATIONS) + " |")
    L.append("")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
