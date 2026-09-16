from __future__ import annotations

import numpy as np
from sklearn.metrics import accuracy_score

from .reflex import CompiledReflex
from .schema import EvaluationReport


def multiclass_brier(y_true: np.ndarray, probs: np.ndarray, classes: np.ndarray) -> float:
    class_to_idx = {str(c): i for i, c in enumerate(classes)}
    target = np.zeros_like(probs, dtype=np.float64)
    for row, label in enumerate(y_true):
        # A true label the reflex has never seen keeps an all-zero target row: the reflex
        # assigns it no probability mass, which is the correct penalty for that case.
        idx = class_to_idx.get(str(label))
        if idx is not None:
            target[row, idx] = 1.0
    return float(np.mean(np.sum((probs - target) ** 2, axis=1)))


def expected_calibration_error(
    y_true: np.ndarray,
    probs: np.ndarray,
    classes: np.ndarray,
    bins: int = 10,
) -> float:
    pred_idx = np.argmax(probs, axis=1)
    confidence = np.max(probs, axis=1)
    pred = classes[pred_idx].astype(str)
    correct = (pred == y_true.astype(str)).astype(np.float64)

    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (confidence >= lo) & (confidence < hi if i < bins - 1 else confidence <= hi)
        if not np.any(mask):
            continue
        ece += float(mask.mean()) * abs(float(correct[mask].mean()) - float(confidence[mask].mean()))
    return float(ece)


def evaluate_reflex(
    reflex: CompiledReflex,
    x: np.ndarray,
    y: np.ndarray,
    *,
    accept_threshold: float = 0.90,
) -> EvaluationReport:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y).astype(str)
    probs = reflex.predict_proba(x)
    classes = reflex.classes_.astype(str)
    pred = classes[np.argmax(probs, axis=1)]
    confidence = np.max(probs, axis=1)
    accepted = confidence >= accept_threshold

    coverage = float(np.mean(accepted))
    selective_accuracy = float(accuracy_score(y[accepted], pred[accepted])) if np.any(accepted) else float("nan")

    return EvaluationReport(
        accuracy=float(accuracy_score(y, pred)),
        brier=multiclass_brier(y, probs, classes),
        ece=expected_calibration_error(y, probs, classes),
        coverage=coverage,
        selective_accuracy=selective_accuracy,
        n=int(len(y)),
    )
