from __future__ import annotations

from collections.abc import Callable

import numpy as np

from .gates import TrustedSubspaceGate
from .reflex import CompiledReflex
from .schema import Prediction


class ParadigmRuntime:
    """Fast reflex path with explicit fallback to a deliberative solver."""

    def __init__(
        self,
        reflex: CompiledReflex,
        deliberate: Callable[[np.ndarray], str],
        *,
        confidence_threshold: float = 0.90,
        ood_gate: TrustedSubspaceGate | None = None,
    ) -> None:
        self.reflex = reflex
        self.deliberate = deliberate
        self.confidence_threshold = confidence_threshold
        self.ood_gate = ood_gate

    def decide(self, features: np.ndarray) -> Prediction:
        x = np.asarray(features, dtype=np.float64)

        if self.ood_gate is not None and not bool(self.ood_gate.accept(x)[0]):
            action = self.deliberate(x)
            return Prediction(
                action=action,
                confidence=0.0,
                probabilities={},
                accepted=False,
                source="deliberative",
                reason="out_of_distribution",
            )

        action, confidence, probabilities = self.reflex.predict(x)
        if confidence >= self.confidence_threshold:
            return Prediction(
                action=action,
                confidence=confidence,
                probabilities=probabilities,
                accepted=True,
                source="reflex",
            )

        fallback = self.deliberate(x)
        return Prediction(
            action=fallback,
            confidence=confidence,
            probabilities=probabilities,
            accepted=False,
            source="deliberative",
            reason="low_confidence",
        )
