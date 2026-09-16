from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .synthetic import teacher


@dataclass(slots=True)
class DeliberationResult:
    action: str
    stability: float


class PerturbationDeliberator:
    """Measured local deliberative surrogate for Core P0.1.

    The solver probes a small neighborhood around each state, applies the
    reference policy to every probe, and returns the majority action. This is
    deliberately more expensive than a compiled reflex and gives Paradigm a
    real measured fallback cost without depending on a remote model or API.

    It is a benchmark surrogate, not a claim that this is equivalent to an LLM,
    planner, or production deliberative system.
    """

    def __init__(
        self,
        *,
        probes: int = 1024,
        sigma: float = 0.018,
        seed: int = 0,
    ) -> None:
        if probes < 1:
            raise ValueError("probes must be positive")
        self.probes = int(probes)
        self.sigma = float(sigma)
        self.seed = int(seed)
        self._offsets: dict[int, np.ndarray] = {}

    def _probe_offsets(self, dimensions: int) -> np.ndarray:
        cached = self._offsets.get(dimensions)
        if cached is not None:
            return cached
        rng = np.random.default_rng(self.seed + dimensions * 1009)
        offsets = rng.normal(0.0, self.sigma, size=(self.probes, dimensions))
        offsets[0] = 0.0
        self._offsets[dimensions] = offsets
        return offsets

    def decide(self, features: np.ndarray) -> DeliberationResult:
        x = np.asarray(features, dtype=np.float64)
        if x.ndim != 1:
            raise ValueError("decide expects one feature vector")
        probes = np.clip(x[None, :] + self._probe_offsets(x.size), 0.0, 1.0)
        actions = np.asarray([teacher(row) for row in probes], dtype=str)
        labels, counts = np.unique(actions, return_counts=True)
        best = int(np.argmax(counts))
        return DeliberationResult(action=str(labels[best]), stability=float(counts[best] / len(actions)))

    def __call__(self, features: np.ndarray) -> str:
        return self.decide(features).action

    def predict(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x[None, :]
        return np.asarray([self(row) for row in x], dtype=str)
