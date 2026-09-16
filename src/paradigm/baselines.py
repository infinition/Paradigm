from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

import numpy as np
from sklearn.neighbors import KNeighborsClassifier


@dataclass(slots=True)
class ExactCache:
    """Exact feature to action cache with majority resolution for repeated keys."""

    decimals: int = 8
    _counts: dict[tuple[float, ...], Counter[str]] = field(default_factory=lambda: defaultdict(Counter), init=False)
    classes_: np.ndarray = field(default_factory=lambda: np.asarray([], dtype=str), init=False)

    def _key(self, row: np.ndarray) -> tuple[float, ...]:
        return tuple(np.round(np.asarray(row, dtype=np.float64), self.decimals).tolist())

    def fit(self, x: np.ndarray, y: np.ndarray) -> "ExactCache":
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y).astype(str)
        self.classes_ = np.unique(y)
        self._counts.clear()
        for row, label in zip(x, y):
            self._counts[self._key(row)][str(label)] += 1
        return self

    def predict_with_acceptance(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x[None, :]

        predictions: list[str] = []
        confidence: list[float] = []
        accepted: list[bool] = []
        fallback_label = str(self.classes_[0]) if len(self.classes_) else ""

        for row in x:
            counts = self._counts.get(self._key(row))
            if not counts:
                predictions.append(fallback_label)
                confidence.append(0.0)
                accepted.append(False)
                continue
            label, count = counts.most_common(1)[0]
            total = sum(counts.values())
            predictions.append(label)
            confidence.append(count / total)
            accepted.append(True)

        return (
            np.asarray(predictions, dtype=str),
            np.asarray(confidence, dtype=np.float64),
            np.asarray(accepted, dtype=bool),
        )


class NearestNeighborCache:
    """Small nearest-neighbor decision cache with probabilistic confidence."""

    def __init__(self, n_neighbors: int = 5) -> None:
        self.n_neighbors = n_neighbors
        self.model = KNeighborsClassifier(n_neighbors=n_neighbors, weights="distance")

    @property
    def classes_(self) -> np.ndarray:
        return np.asarray(self.model.classes_)

    def fit(self, x: np.ndarray, y: np.ndarray) -> "NearestNeighborCache":
        self.model.fit(np.asarray(x, dtype=np.float64), np.asarray(y).astype(str))
        return self

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        return np.asarray(self.model.predict_proba(np.asarray(x, dtype=np.float64)), dtype=np.float64)
