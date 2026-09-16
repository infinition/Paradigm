from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from .compiler import ReflexCompiler
from .evaluation import expected_calibration_error, multiclass_brier
from .reflex import CompiledReflex
from .schema import Trace
from .selection import select_confidence_threshold


@dataclass(slots=True)
class CandidateScore:
    backend: str
    feasible: bool
    threshold: float
    coverage: float
    selective_accuracy: float
    ece: float
    brier: float
    latency_us_per_item: float


@dataclass(slots=True)
class ReflexSelection:
    reflex: CompiledReflex
    threshold: float
    backend: str
    feasible: bool
    candidates: list[CandidateScore]


class MinimalReflexSelector:
    """Select the simplest reference backend that satisfies declared constraints.

    Candidate order encodes complexity preference. Paradigm only moves to a more
    expensive backend when the simpler candidate fails quality or calibration.
    """

    def __init__(
        self,
        *,
        backends: tuple[str, ...] = ("tree", "calibrated_tree", "calibrated_forest"),
        minimum_coverage: float = 0.50,
        maximum_ece: float = 0.05,
        accuracy_tolerance: float = 0.01,
        random_state: int = 0,
        stop_on_first_feasible: bool = True,
    ) -> None:
        self.backends = backends
        self.minimum_coverage = minimum_coverage
        self.maximum_ece = maximum_ece
        self.accuracy_tolerance = accuracy_tolerance
        self.random_state = random_state
        self.stop_on_first_feasible = stop_on_first_feasible

    @staticmethod
    def _matrix(traces: list[Trace]) -> tuple[np.ndarray, np.ndarray]:
        x = np.stack([np.asarray(t.features, dtype=np.float64) for t in traces])
        y = np.asarray([t.action for t in traces]).astype(str)
        return x, y

    @staticmethod
    def _latency_us(reflex: CompiledReflex, x: np.ndarray, repeats: int = 8) -> float:
        sample = x[: min(256, len(x))]
        reflex.predict_proba(sample)
        start = time.perf_counter()
        for _ in range(repeats):
            reflex.predict_proba(sample)
        return float((time.perf_counter() - start) / repeats / len(sample) * 1e6)

    def select(
        self,
        train: list[Trace],
        validation: list[Trace],
        *,
        reference_predictions: np.ndarray,
        name: str = "candidate",
    ) -> ReflexSelection:
        x_val, y_val = self._matrix(validation)
        reference_predictions = np.asarray(reference_predictions).astype(str)
        candidates: list[tuple[CompiledReflex, CandidateScore]] = []

        for i, backend in enumerate(self.backends):
            reflex = ReflexCompiler(backend=backend, random_state=self.random_state + i).fit(
                train, name=f"{name}:{backend}"
            )
            probs = reflex.predict_proba(x_val)
            classes = reflex.classes_.astype(str)
            threshold = select_confidence_threshold(
                y_val,
                probs,
                classes,
                reference_predictions=reference_predictions,
                tolerance=self.accuracy_tolerance,
                minimum_coverage=self.minimum_coverage,
            )
            ece = expected_calibration_error(y_val, probs, classes)
            score = CandidateScore(
                backend=backend,
                feasible=bool(threshold.feasible and ece <= self.maximum_ece),
                threshold=threshold.threshold,
                coverage=threshold.coverage,
                selective_accuracy=threshold.selective_accuracy,
                ece=ece,
                brier=multiclass_brier(y_val, probs, classes),
                latency_us_per_item=self._latency_us(reflex, x_val),
            )
            candidates.append((reflex, score))
            if score.feasible and self.stop_on_first_feasible:
                break

        feasible = [(reflex, score) for reflex, score in candidates if score.feasible]
        if feasible:
            # Backends are already ordered from simplest to most expensive.
            chosen_reflex, chosen_score = feasible[0]
        else:
            # Preserve a usable result for analysis. Prefer the best selective
            # accuracy, then lower ECE, then higher coverage.
            chosen_reflex, chosen_score = max(
                candidates,
                key=lambda item: (
                    item[1].selective_accuracy,
                    -item[1].ece,
                    item[1].coverage,
                ),
            )

        chosen_reflex.name = name
        chosen_reflex.metadata.update(
            {
                "selected_backend": chosen_score.backend,
                "selection_feasible": chosen_score.feasible,
                "selection_threshold": chosen_score.threshold,
            }
        )
        return ReflexSelection(
            reflex=chosen_reflex,
            threshold=chosen_score.threshold,
            backend=chosen_score.backend,
            feasible=chosen_score.feasible,
            candidates=[score for _, score in candidates],
        )
