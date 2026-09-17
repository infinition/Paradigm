"""Intent generalization benchmark, offline. See ``results/intent_bench/PREREG.md``.

Representations: A lexical (GenericStateEncoder goal hashing), B nomic-embed-text-v1.5 as
LaRuche's memory calls it (llama-server at INTENT_NOMIC_URL, default 127.0.0.1:18089),
S paraphrase-multilingual-MiniLM-L12-v2 via sentence-transformers on CPU, A+B, A+S.
Models: prototype, k-NN (3), logistic regression, Paradigm's tree. Leave-one-group-out.
Encoders frozen; gate and thresholds are Paradigm's, unchanged.
"""

from __future__ import annotations

import hashlib
import json
import os
import resource
import time
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier

from paradigm.evaluation import expected_calibration_error
from paradigm.integration.contract import ParadigmState
from paradigm.integration.encoder import GenericStateEncoder
from paradigm.ood import MahalanobisGate
from paradigm.selection import select_confidence_threshold

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "results" / "intent_bench"
DATA = BENCH / "phrases.jsonl"
OUT_JSON = BENCH / "results_v1.json"
OUT_MD = BENCH / "RESULTS_v1.md"
NOMIC_URL = os.environ.get("INTENT_NOMIC_URL", "http://127.0.0.1:18089")
SPECIALIZED = "paraphrase-multilingual-MiniLM-L12-v2"
POSITIVE = "CAPTURE_PERSON"
TRANSFORMATIONS = ("negation", "temporal", "past_question", "object_change", "inspection_only")


def load() -> list[dict[str, Any]]:
    digest = hashlib.sha256(DATA.read_bytes()).hexdigest()
    expected = (BENCH / "DATASET_SHA256.txt").read_text().split()[0]
    assert digest == expected, "dataset hash mismatch: the frozen file changed"
    return [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines()]


def lexical(text: str) -> np.ndarray:
    enc = GenericStateEncoder()
    return enc.encode(ParadigmState(domain="laruche", phase="start", available_actions=("camera",), goal=text, family_hint="laruche:start:none:none"))


def nomic(texts: list[str]) -> tuple[np.ndarray, dict[str, float]]:
    vecs, lat = [], []
    for t in texts:
        body = json.dumps({"model": "nomic", "input": t}).encode()
        req = urllib.request.Request(f"{NOMIC_URL}/v1/embeddings", data=body, headers={"Content-Type": "application/json"})
        t0 = time.perf_counter()
        r = json.load(urllib.request.urlopen(req))
        lat.append((time.perf_counter() - t0) * 1000)
        vecs.append(np.asarray(r["data"][0]["embedding"], dtype=np.float64))
    return np.stack(vecs), {"median_ms": float(np.median(lat)), "max_ms": float(np.max(lat))}


def specialized(texts: list[str]) -> tuple[np.ndarray, dict[str, float]]:
    from sentence_transformers import SentenceTransformer

    rss0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
    model = SentenceTransformer(SPECIALIZED, device="cpu")
    lat = []
    vecs = []
    for t in texts:
        t0 = time.perf_counter()
        vecs.append(model.encode(t, normalize_embeddings=True))
        lat.append((time.perf_counter() - t0) * 1000)
    rss1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
    return np.stack(vecs).astype(np.float64), {"median_ms": float(np.median(lat)), "max_ms": float(np.max(lat)), "added_rss_mb": rss1 - rss0, "dims": int(np.stack(vecs).shape[1])}


class Prototype:
    def __init__(self, tau: float = 0.05) -> None:
        self.tau = tau

    def fit(self, x, y):
        self.classes_ = np.unique(y)
        xn = x / (np.linalg.norm(x, axis=1, keepdims=True) + 1e-12)
        self.centroids_ = np.stack([xn[y == c].mean(axis=0) for c in self.classes_])
        self.centroids_ /= np.linalg.norm(self.centroids_, axis=1, keepdims=True) + 1e-12
        return self

    def predict_proba(self, x):
        xn = x / (np.linalg.norm(x, axis=1, keepdims=True) + 1e-12)
        s = xn @ self.centroids_.T / self.tau
        s -= s.max(axis=1, keepdims=True)
        p = np.exp(s)
        return p / p.sum(axis=1, keepdims=True)


MODELS = {
    "prototype": lambda: Prototype(),
    "knn3": lambda: KNeighborsClassifier(n_neighbors=3),
    "logreg": lambda: LogisticRegression(max_iter=3000, C=1.0),
    "tree": lambda: DecisionTreeClassifier(max_depth=8, min_samples_leaf=4, random_state=21),
}


def evaluate(rows: list[dict[str, Any]], x: np.ndarray, make) -> dict[str, Any]:
    classes = sorted({r["intent"] for r in rows})
    groups = sorted({r["group"] for r in rows})
    y = np.asarray([r["intent"] for r in rows])
    grp = np.asarray([r["group"] for r in rows])
    probs = np.zeros((len(rows), len(classes)))
    accepted = np.zeros(len(rows), dtype=bool)
    for g in groups:
        tr, te = grp != g, grp == g
        model = make().fit(x[tr], y[tr])
        p = model.predict_proba(x[te])
        for j, c in enumerate(model.classes_):
            probs[te, classes.index(str(c))] = p[:, j]
        gate = MahalanobisGate(quantile=0.997).fit(x[tr])
        accepted[te] = np.asarray(gate.accept(x[te]), dtype=bool)
    pred = np.asarray(classes)[np.argmax(probs, axis=1)]
    conf = probs.max(axis=1)
    thr = select_confidence_threshold(y, probs, np.asarray(classes), reference_predictions=y, tolerance=0.01, minimum_coverage=0.55)
    covered = conf >= thr.threshold
    fired = covered & accepted  # what Paradigm would let a reflex act on
    is_pos = y == POSITIVE
    # A hard negative is a hard-negative-role sentence whose class is not the positive one
    # (an object_change that turns the request back into a capture is a positive).
    hard = np.asarray([r["role"] == "hard_negative" for r in rows]) & ~is_pos
    out: dict[str, Any] = {
        "accuracy_no_gate": float(np.mean(pred == y)),
        "per_class_recall_no_gate": {c: float(np.mean(pred[y == c] == c)) for c in classes},
        "positive_confusions_no_gate": {c: int(np.sum((pred == POSITIVE) & (y == c))) for c in classes if c != POSITIVE},
        "threshold": float(thr.threshold), "coverage": float(thr.coverage), "selective_accuracy": float(thr.selective_accuracy), "feasible": bool(thr.feasible),
        "ece": float(expected_calibration_error(y, probs, np.asarray(classes))),
        "gate_acceptance": float(np.mean(accepted)), "gate_acceptance_positives": float(np.mean(accepted[is_pos])), "gate_acceptance_hard_negatives": float(np.mean(accepted[hard])),
        "fired_share": float(np.mean(fired)),
        "false_fast_paths": int(np.sum(fired & (pred == POSITIVE) & ~is_pos)),
        "false_fast_paths_on_hard_negatives": int(np.sum(fired & (pred == POSITIVE) & hard)),
        "false_fast_paths_on_out_of_domain": int(np.sum(fired & (pred == POSITIVE) & np.asarray([r["group"] in ("c12", "c13", "g12", "g13", "u12", "u13") for r in rows]))),
        "unseen_positive_recall_under_gate": float(np.mean((fired & (pred == POSITIVE))[is_pos])),
        "hard_negative_rejection_under_gate": float(np.mean(~(fired & (pred == POSITIVE))[hard])),
        "selective_accuracy_under_gate": float(np.mean((pred == y)[fired])) if fired.any() else None,
        "per_transformation": {},
        "per_source_positive_recall": {},
    }
    # Known property of the frozen dataset: a few texts occur in two groups, so a held-out
    # sentence can have an identical twin in training. Counted, and the criterion metrics
    # are also given with those sentences excluded from the test side (dataset unchanged).
    texts = [r["text"] for r in rows]
    leaked = np.asarray([any(texts[j] == texts[i] and grp[j] != grp[i] for j in range(len(rows))) for i in range(len(rows))])
    keep = ~leaked
    out["leaked_test_sentences"] = int(leaked.sum())
    out["unseen_positive_recall_under_gate_excluding_leaks"] = float(np.mean((fired & (pred == POSITIVE))[is_pos & keep]))
    out["false_fast_paths_on_hard_negatives_excluding_leaks"] = int(np.sum(fired & (pred == POSITIVE) & hard & keep))
    trans = np.asarray([r["transformation"] or "" for r in rows])
    for t in TRANSFORMATIONS:
        m = (trans == t) & ~is_pos
        out["per_transformation"][t] = {
            "n": int(m.sum()), "predicted_positive_no_gate": int(np.sum((pred == POSITIVE) & m)),
            "false_fast_paths": int(np.sum(fired & (pred == POSITIVE) & m)), "gate_acceptance": float(np.mean(accepted[m])),
        }
    src = np.asarray([r["source"] for r in rows])
    for s in sorted(set(src)):
        m = (src == s) & is_pos
        out["per_source_positive_recall"][s] = float(np.mean((fired & (pred == POSITIVE))[m])) if m.any() else None
    return out


def fmt(v: Any) -> str:
    return "n/a" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v))


def main() -> None:
    rows = load()
    texts = [r["text"] for r in rows]
    a = np.stack([lexical(t) for t in texts])
    b, lat_b = nomic(texts)
    s, lat_s = specialized(texts)
    reps = {"A_lexical": a, "B_nomic_laruche": b, "S_paraphrase_minilm": s, "A+B": np.concatenate([a, b], axis=1), "A+S": np.concatenate([a, s], axis=1)}
    results: dict[str, Any] = {"dataset_sha256": (BENCH / "DATASET_SHA256.txt").read_text().split()[0], "n": len(rows), "groups": len({r['group'] for r in rows}),
                               "encoders": {"B": {**lat_b, "dims": int(b.shape[1]), "server_rss_mb_measured_separately": 219}, "S": lat_s}, "evaluations": {}}
    for rn, x in reps.items():
        for mn, make in MODELS.items():
            results["evaluations"][f"{rn}|{mn}"] = evaluate(rows, x, make)
    # Pre-registered criterion, verbatim: a representation is better than A only if the
    # recall of unseen positive intents under the gate rises without any rise in false fast
    # paths on hard negatives. Evaluated against the lexical baseline with the same model,
    # and against the best lexical configuration (highest recall).
    lex = {mn: results["evaluations"][f"A_lexical|{mn}"] for mn in MODELS}
    best_lex = max(lex.values(), key=lambda e: e["unseen_positive_recall_under_gate"])
    for key, e in results["evaluations"].items():
        rn, mn = key.split("|")
        base = lex[mn]
        e["criterion_vs_lexical_same_model"] = bool(e["unseen_positive_recall_under_gate"] > base["unseen_positive_recall_under_gate"] and e["false_fast_paths_on_hard_negatives"] <= base["false_fast_paths_on_hard_negatives"])
        e["criterion_vs_best_lexical"] = bool(e["unseen_positive_recall_under_gate"] > best_lex["unseen_positive_recall_under_gate"] and e["false_fast_paths_on_hard_negatives"] <= best_lex["false_fast_paths_on_hard_negatives"])
    OUT_JSON.write_text(json.dumps(results, indent=1, default=float))

    L = ["# Intent generalization benchmark, results v1", "",
         "Metric correction, recorded: the first run of this script counted hard-negative-role sentences whose class is CAPTURE_PERSON (an object_change that turns the request back into a capture) as false fast paths when predicted CAPTURE_PERSON. That was a counting bug, fixed before any interpretation; the protocol, the dataset and the models are unchanged. Hard negatives below are hard-negative-role sentences whose class is not CAPTURE_PERSON.", "",
         f"Dataset `phrases.jsonl` sha256 `{results['dataset_sha256']}`, {results['n']} sentences, {results['groups']} groups, leave-one-group-out. Encoders: B nomic (LaRuche memory) {results['encoders']['B']['dims']} dims, median {results['encoders']['B']['median_ms']:.1f} ms; S {SPECIALIZED} {lat_s['dims']} dims, median {lat_s['median_ms']:.1f} ms on CPU, about {lat_s['added_rss_mb']:.0f} MB added resident memory in this process.", "",
         "## Under Paradigm's gate (what a reflex would act on): the pre-registered criterion", "",
         "| representation | model | unseen positive recall under gate | same, excluding leaked twins | false fast paths (all / hard neg. / hard neg. excl. leaks / out of domain) | FFP per transformation: " + ", ".join(t for t in TRANSFORMATIONS) + " | hard-negative rejection | gate acc. pos / hard neg | coverage | sel. acc. (selector) | selector feasible | sel. acc. under gate | ECE | criterion vs lexical same model | criterion vs best lexical |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, e in results["evaluations"].items():
        rn, mn = key.split("|")
        L.append(f"| {rn} | {mn} | {fmt(e['unseen_positive_recall_under_gate'])} | {fmt(e['unseen_positive_recall_under_gate_excluding_leaks'])} | {e['false_fast_paths']} / {e['false_fast_paths_on_hard_negatives']} / {e['false_fast_paths_on_hard_negatives_excluding_leaks']} / {e['false_fast_paths_on_out_of_domain']} | " + ", ".join(str(e["per_transformation"][t]["false_fast_paths"]) for t in TRANSFORMATIONS) + f" | {fmt(e['hard_negative_rejection_under_gate'])} | {fmt(e['gate_acceptance_positives'])} / {fmt(e['gate_acceptance_hard_negatives'])} | {fmt(e['coverage'])} | {fmt(e['selective_accuracy'])} | {e['feasible']} | {fmt(e['selective_accuracy_under_gate'])} | {fmt(e['ece'])} | {e['criterion_vs_lexical_same_model']} | {e['criterion_vs_best_lexical']} |")
    L += ["", f"Leaked test sentences (identical text in another group): {results['evaluations']['A_lexical|knn3']['leaked_test_sentences']} of {results['n']}."]
    L += ["", "## Without the gate: classification", "", "| representation | model | accuracy | recall CAPTURE_PERSON | predicted CAPTURE_PERSON on: " + ", ".join(t for t in TRANSFORMATIONS) + " |", "|---|---|---|---|---|"]
    for key, e in results["evaluations"].items():
        rn, mn = key.split("|")
        L.append(f"| {rn} | {mn} | {fmt(e['accuracy_no_gate'])} | {fmt(e['per_class_recall_no_gate'].get(POSITIVE))} | " + ", ".join(str(e["per_transformation"][t]["predicted_positive_no_gate"]) for t in TRANSFORMATIONS) + " |")
    L += ["", "## Per source, unseen positive recall under the gate (logistic regression)", "", "| representation | " + " | ".join(sorted({r['source'] for r in rows})) + " |", "|---|" + "---|" * 3]
    for rn in reps:
        e = results["evaluations"][f"{rn}|logreg"]
        L.append(f"| {rn} | " + " | ".join(fmt(e["per_source_positive_recall"].get(s_)) for s_ in sorted({r['source'] for r in rows})) + " |")
    L.append("")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
