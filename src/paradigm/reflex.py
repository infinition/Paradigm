from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class CompiledReflex:
    """Thin wrapper around a probabilistic model used as a reflex."""

    model: object
    name: str = "reflex"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def classes_(self) -> np.ndarray:
        return np.asarray(self.model.classes_)

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x[None, :]
        return np.asarray(self.model.predict_proba(x), dtype=np.float64)

    def predict(self, x: np.ndarray) -> tuple[str, float, dict[str, float]]:
        probs = self.predict_proba(x)[0]
        idx = int(np.argmax(probs))
        classes = [str(c) for c in self.classes_]
        mapping = {label: float(p) for label, p in zip(classes, probs)}
        return classes[idx], float(probs[idx]), mapping
