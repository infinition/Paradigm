from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(slots=True)
class Trace:
    """A validated or rejected deliberative outcome used as compilation data."""

    features: np.ndarray
    action: str
    valid: bool = True
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Prediction:
    action: str
    confidence: float
    probabilities: dict[str, float]
    accepted: bool
    source: str
    reason: str = ""


@dataclass(slots=True)
class EvaluationReport:
    accuracy: float
    brier: float
    ece: float
    coverage: float
    selective_accuracy: float
    n: int
