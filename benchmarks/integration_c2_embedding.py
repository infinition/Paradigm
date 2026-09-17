"""C2, offline: the LaRuche memory embedding as goal representation, on the frozen run C1
record and pre-declared unseen phrasings. See ``c2_embedding_prereg.md``.

Representations: A lexical (GenericStateEncoder, as today), B the LaRuche encoder raw,
B' the same encoder with nomic's ``classification:`` prefix, C = A + B. Models: nearest
prototype, k-NN (3), logistic regression, Paradigm's decision tree. Encoder frozen.
Requires the embedding engine LaRuche uses (``llama-server --embeddings`` on the profile's
nomic model) at ``C2_EMBED_URL`` (default http://127.0.0.1:18089).
"""

from __future__ import annotations

import json
import os
import pickle
import re
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
RES = ROOT / "results" / "integration_laruche"
LOG = RES / "runC1_camera_missions_1-56.log"
DLOG = RES / "runC1_decision_log.json"
STATE = RES / "engine_state_camera_after_56.pkl"
OUT_JSON = RES / "c2_embedding_audit.json"
OUT_MD = RES / "c2_embedding_audit.md"
EMBED_URL = os.environ.get("C2_EMBED_URL", "http://127.0.0.1:18089")

REQUESTS = {
    "P1": "Prends-moi en photo.", "P2": "Fais une photo de moi.", "P3": "Tu peux me prendre en photo ?",
    "P4": "Prends une photo avec la webcam.", "P5": "Photographie-moi.",
    "N1": "Fais une capture d'écran.", "N2": "Trouve mes dernières photos.", "N3": "Est-ce que j'ai une webcam ?",
    "N4": "Ouvre la caméra sans prendre de photo.",
}
UNSEEN = {
    "U+1": ("Fais-moi un portrait.", "capture"), "U+2": ("Capture une image de moi avec la caméra.", "capture"),
    "U+3": ("Je veux une photo de moi maintenant.", "capture"),
    "U-1": ("Allume la caméra sans capturer.", "no_capture"), "U-2": ("Liste les caméras disponibles.", "no_capture"),
    "U-3": ("Combien de photos ai-je prises hier ?", "no_capture"), "U-4": ("Vérifie que la webcam fonctionne, sans photo.", "no_capture"),
}
HEAD = re.compile(r"^mission (\d+) phase (\d) \[(\w+)\]")
CAPTURE_PREFIX = "camera#"


def embed(text: str) -> tuple[np.ndarray, float]:
    body = json.dumps({"model": "nomic", "input": text}).encode()
    req = urllib.request.Request(f"{EMBED_URL}/v1/embeddings", data=body, headers={"Content-Type": "application/json"})
    t = time.perf_counter()
    r = json.load(urllib.request.urlopen(req))
    return np.asarray(r["data"][0]["embedding"], dtype=np.float64), (time.perf_counter() - t) * 1000


def lexical(text: str) -> np.ndarray:
    enc = GenericStateEncoder()
    return enc.encode(ParadigmState(domain="laruche", phase="start", available_actions=("camera",), goal=text, family_hint="laruche:start:none:none"))


def load_missions() -> list[dict[str, Any]]:
    missions = []
    for line in LOG.read_text().splitlines():
        m = HEAD.match(line)
        if m and int(m.group(2)) == 1:
            missions.append({"n": int(m.group(1)), "id": m.group(3), "text": REQUESTS[m.group(3)]})
    rows = json.loads(DLOG.read_text())["decisions"]
    ep_ids: list[str] = []
    for r in rows:
        if r["episode"] not in ep_ids:
            ep_ids.append(r["episode"])
    with STATE.open("rb") as fh:
        payload = pickle.load(fh)
    templates = payload.get("action_templates") or {}
    buffer = {ep.task_id: ep.traces for ep in payload["compiler"].buffer.episodes}
    for mi, e in zip(missions, ep_ids[: len(missions)]):
        first = next((t for t in buffer.get(e, []) if str(t.metadata.get("family")) == "laruche:start:none:none"), None)
        if first is None:
            mi["t1"] = "other"
        else:
            args = (templates.get(str(first.action)) or {}).get("args") or {}
            mi["t1"] = "capture" if args.get("action") == "capture" and "index" not in args else "capture_index0" if args.get("action") == "capture" else "list" if args.get("action") == "list" else "other"
        mi["t2"] = "capture" if mi["id"].startswith("P") else "no_capture"
    return missions


class Prototype:
    """Class centroids on L2-normalized features; probabilities by a softmax on cosine."""

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

    def predict(self, x):
        return self.classes_[np.argmax(self.predict_proba(x), axis=1)]


def models() -> dict[str, Any]:
    return {
        "prototype": lambda: Prototype(),
        "knn3": lambda: KNeighborsClassifier(n_neighbors=3),
        "logreg": lambda: LogisticRegression(max_iter=2000, C=1.0),
        "tree": lambda: DecisionTreeClassifier(max_depth=8, min_samples_leaf=4, random_state=21),
    }


def score(y_true, probs, classes, positives_mask, negatives_mask) -> dict[str, Any]:
    classes = np.asarray(classes).astype(str)
    y_true = np.asarray(y_true).astype(str)
    thr = select_confidence_threshold(y_true, probs, classes, reference_predictions=y_true, tolerance=0.01, minimum_coverage=0.55)
    ece = float(expected_calibration_error(y_true, probs, classes))
    pred = classes[np.argmax(probs, axis=1)]
    conf = probs.max(axis=1)
    covered = conf >= thr.threshold
    ffp = int(np.sum(covered & negatives_mask & (pred == "capture")))
    recall_pos = float(np.mean((covered & (pred == "capture"))[positives_mask])) if positives_mask.any() else None
    return {"threshold": float(thr.threshold), "coverage": float(thr.coverage), "selective_accuracy": float(thr.selective_accuracy), "feasible": bool(thr.feasible), "ece": ece, "false_fast_paths": ffp, "recall_positives_covered": recall_pos, "n": int(len(y_true))}


def main() -> None:
    missions = load_missions()
    texts = sorted({m["text"] for m in missions})
    lat: list[float] = []
    emb: dict[str, np.ndarray] = {}
    emb_cls: dict[str, np.ndarray] = {}
    for t in texts + [u[0] for u in UNSEEN.values()]:
        v, ms = embed(t); emb[t] = v; lat.append(ms)
        emb_cls[t], _ = embed("classification: " + t)
    lex = {t: lexical(t) for t in list(emb)}
    reps = {
        "A_lexical": lambda t: lex[t],
        "B_embedding": lambda t: emb[t],
        "B'_embedding_classification_prefix": lambda t: emb_cls[t],
        "C_lexical+embedding": lambda t: np.concatenate([lex[t], emb[t]]),
    }
    results: dict[str, Any] = {"latency_ms": {"median": float(np.median(lat)), "max": float(np.max(lat))}, "missions": missions, "unseen": UNSEEN, "evaluations": {}}
    phrasings = sorted({m["id"] for m in missions})
    for rep_name, feat in reps.items():
        for model_name, make in models().items():
            for target in ("t2", "t1"):
                # Leave-one-phrasing-out over the 9 C1 phrasings.
                y_all, p_all = [], []
                pos_mask, neg_mask, gate_acc = [], [], []
                classes_all = sorted({m[target] for m in missions})
                for held in phrasings:
                    train = [m for m in missions if m["id"] != held]
                    test = [m for m in missions if m["id"] == held]
                    xtr = np.stack([feat(m["text"]) for m in train]); ytr = np.asarray([m[target] for m in train])
                    xte = np.stack([feat(m["text"]) for m in test])
                    if len(np.unique(ytr)) < 2:
                        continue
                    model = make().fit(xtr, ytr)
                    proba = model.predict_proba(xte)
                    # Align to the full class list.
                    full = np.zeros((len(test), len(classes_all)))
                    for j, c in enumerate(model.classes_):
                        full[:, classes_all.index(str(c))] = proba[:, j]
                    gate = MahalanobisGate(quantile=0.997).fit(xtr)
                    acc = np.asarray(gate.accept(xte), dtype=bool)
                    for k, m in enumerate(test):
                        y_all.append(m[target]); p_all.append(full[k]); pos_mask.append(m["t2"] == "capture"); neg_mask.append(m["t2"] != "capture"); gate_acc.append(bool(acc[k]))
                y_all = np.asarray(y_all); p_all = np.stack(p_all); pos_mask = np.asarray(pos_mask); neg_mask = np.asarray(neg_mask); gate_acc = np.asarray(gate_acc)
                s = score(y_all, p_all, classes_all, pos_mask, neg_mask)
                s["gate_acceptance_unseen_positives"] = float(np.mean(gate_acc[pos_mask]))
                s["gate_acceptance_unseen_negatives"] = float(np.mean(gate_acc[neg_mask]))
                # Unseen phrasings, models trained on all 48 missions (T2 labels only).
                unseen = {}
                if target == "t2":
                    xtr = np.stack([feat(m["text"]) for m in missions]); ytr = np.asarray([m["t2"] for m in missions])
                    model = make().fit(xtr, ytr); gate = MahalanobisGate(quantile=0.997).fit(xtr)
                    for uid, (text, label) in UNSEEN.items():
                        x = feat(text)[None, :]
                        pr = model.predict_proba(x)[0]; cl = [str(c) for c in model.classes_]
                        conf = float(pr.max()); pred = cl[int(np.argmax(pr))]
                        unseen[uid] = {"text": text, "label": label, "pred": pred, "confidence": conf, "covered": conf >= s["threshold"], "gate_accepted": bool(np.asarray(gate.accept(x), dtype=bool)[0])}
                    s["unseen"] = unseen
                    s["unseen_false_fast_paths"] = sum(1 for u in unseen.values() if u["label"] == "no_capture" and u["pred"] == "capture" and u["covered"] and u["gate_accepted"])
                    s["unseen_positive_recall"] = float(np.mean([u["pred"] == "capture" and u["covered"] and u["gate_accepted"] for u in unseen.values() if u["label"] == "capture"]))
                    s["unseen_negative_fallback"] = float(np.mean([not (u["covered"] and u["gate_accepted"]) for u in unseen.values() if u["label"] == "no_capture"]))
                results["evaluations"][f"{rep_name}|{model_name}|{target}"] = s
    OUT_JSON.write_text(json.dumps(results, indent=1, default=float))

    def fmt(v):
        return "n/a" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v))

    L = ["# C2 audit: the LaRuche memory embedding as goal representation (offline)", "",
         f"Encoder latency: median {results['latency_ms']['median']:.1f} ms, max {results['latency_ms']['max']:.1f} ms per sentence. Leave-one-phrasing-out over the 9 C1 phrasings (48 missions); unseen phrasings scored by models trained on all 48.", "",
         "## Target T2 (intent under the outcome contract: capture / no capture), leave-one-phrasing-out", "",
         "| representation | model | coverage | sel. acc. | ECE | false fast paths (C1 negatives) | recall unseen-wording positives | gate acc. pos / neg | unseen 7: pos recall | unseen 7: neg fallback | unseen 7: false fast paths |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, s in results["evaluations"].items():
        rep, model, target = key.split("|")
        if target != "t2":
            continue
        L.append(f"| {rep} | {model} | {fmt(s['coverage'])} | {fmt(s['selective_accuracy'])} | {fmt(s['ece'])} | {s['false_fast_paths']} | {fmt(s['recall_positives_covered'])} | {fmt(s['gate_acceptance_unseen_positives'])} / {fmt(s['gate_acceptance_unseen_negatives'])} | {fmt(s.get('unseen_positive_recall'))} | {fmt(s.get('unseen_negative_fallback'))} | {s.get('unseen_false_fast_paths')} |")
    L += ["", "## Target T1 (teacher's literal first action), leave-one-phrasing-out", "", "| representation | model | coverage | sel. acc. | ECE | feasible |", "|---|---|---|---|---|---|"]
    for key, s in results["evaluations"].items():
        rep, model, target = key.split("|")
        if target != "t1":
            continue
        L.append(f"| {rep} | {model} | {fmt(s['coverage'])} | {fmt(s['selective_accuracy'])} | {fmt(s['ece'])} | {s['feasible']} |")
    L += ["", "## Unseen phrasings, T2, logistic regression on each representation", "", "| id | text | label | " + " | ".join(r for r in reps) + " |", "|---|---|---|" + "---|" * len(reps)]
    for uid, (text, label) in UNSEEN.items():
        cells = []
        for rep in reps:
            u = results["evaluations"][f"{rep}|logreg|t2"]["unseen"][uid]
            cells.append(f"{u['pred']} {u['confidence']:.2f}{' covered' if u['covered'] else ''}{' gate-ok' if u['gate_accepted'] else ' OOD'}")
        L.append(f"| {uid} | {text} | {label} | " + " | ".join(cells) + " |")
    L += ["", "## Teacher's first action at start per phrasing (T1 evidence)", "", "| id | text | first actions over its missions |", "|---|---|---|"]
    import collections
    for pid in phrasings:
        c = collections.Counter(m["t1"] for m in missions if m["id"] == pid)
        L.append(f"| {pid} | {REQUESTS[pid]} | " + ", ".join(f"{k} {v}" for k, v in c.most_common()) + " |")
    L.append("")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
