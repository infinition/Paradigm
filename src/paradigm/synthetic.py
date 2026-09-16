from __future__ import annotations

import numpy as np

from .schema import Trace


FEATURE_NAMES = [
    "risk",
    "reversibility",
    "novelty",
    "expected_cost",
    "historical_success",
    "resource_pressure",
]


def teacher(features: np.ndarray) -> str:
    """Reference deliberative policy for the synthetic experiments."""
    risk, reversibility, novelty, cost, success, pressure = np.asarray(features, dtype=float)
    if risk > 0.78 or (risk > 0.58 and reversibility < 0.30):
        return "human_review"
    if novelty > 0.70 or success < 0.42 or (pressure > 0.80 and cost > 0.55):
        return "deliberate"
    return "execute"


def make_traces(n: int = 3000, seed: int = 0) -> list[Trace]:
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.0, 1.0, size=(n, len(FEATURE_NAMES)))
    return [Trace(features=row, action=teacher(row), valid=True) for row in x]


def make_xy(n: int = 1000, seed: int = 1) -> tuple[np.ndarray, np.ndarray]:
    traces = make_traces(n=n, seed=seed)
    return np.stack([t.features for t in traces]), np.asarray([t.action for t in traces])
