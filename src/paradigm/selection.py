from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import accuracy_score


@dataclass(slots=True)
class ThresholdSelection:
    threshold: float
    coverage: float
    selective_accuracy: float
    target_accuracy: float
    feasible: bool


def select_confidence_threshold(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    classes: np.ndarray,
    *,
    reference_predictions: np.ndarray | None = None,
    tolerance: float = 0.01,
    minimum_coverage: float = 0.0,
) -> ThresholdSelection:
    """Choose the lowest threshold that meets a selective accuracy target.

    The target is the validation accuracy of the deliberative reference minus
    ``tolerance``. Lower thresholds are preferred because they maximize coverage.
    """

    y_true = np.asarray(y_true).astype(str)
    probabilities = np.asarray(probabilities, dtype=np.float64)
    classes = np.asarray(classes).astype(str)
    pred = classes[np.argmax(probabilities, axis=1)]
    confidence = np.max(probabilities, axis=1)

    if reference_predictions is None:
        target_accuracy = 1.0 - tolerance
    else:
        reference_predictions = np.asarray(reference_predictions).astype(str)
        target_accuracy = max(0.0, float(accuracy_score(y_true, reference_predictions)) - tolerance)

    candidates = np.unique(np.concatenate(([0.0], confidence, [1.0])))
    candidates.sort()

    best: ThresholdSelection | None = None
    for threshold in candidates:
        accepted = confidence >= threshold
        if not np.any(accepted):
            continue
        coverage = float(np.mean(accepted))
        if coverage < minimum_coverage:
            continue
        selective_accuracy = float(accuracy_score(y_true[accepted], pred[accepted]))
        if selective_accuracy >= target_accuracy:
            best = ThresholdSelection(
                threshold=float(threshold),
                coverage=coverage,
                selective_accuracy=selective_accuracy,
                target_accuracy=target_accuracy,
                feasible=True,
            )
            break

    if best is not None:
        return best

    # No threshold satisfies the target. Return the highest-confidence operating point.
    threshold = float(np.max(confidence))
    accepted = confidence >= threshold
    return ThresholdSelection(
        threshold=threshold,
        coverage=float(np.mean(accepted)),
        selective_accuracy=float(accuracy_score(y_true[accepted], pred[accepted])),
        target_accuracy=target_accuracy,
        feasible=False,
    )
