from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .evaluation import evaluate_reflex
from .promotion import PromotionCheck, PromotionManifest
from .reflex import CompiledReflex


@dataclass(slots=True)
class ShadowWindow:
    window_id: str
    x: np.ndarray
    y: np.ndarray
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ShadowPolicy:
    minimum_accuracy: float = 0.90
    maximum_ece: float = 0.12
    maximum_accuracy_regression: float = 0.02
    minimum_windows: int = 2

    def evaluate(
        self,
        *,
        candidate_name: str,
        candidate: CompiledReflex,
        active: CompiledReflex,
        windows: list[ShadowWindow],
        metadata: dict[str, Any] | None = None,
    ) -> PromotionManifest:
        if len(windows) < self.minimum_windows:
            raise ValueError(f"At least {self.minimum_windows} shadow windows are required.")

        checks: list[PromotionCheck] = []
        window_records: list[dict[str, Any]] = []
        for window in windows:
            candidate_report = evaluate_reflex(candidate, window.x, window.y, accept_threshold=0.0)
            active_report = evaluate_reflex(active, window.x, window.y, accept_threshold=0.0)
            regression = active_report.accuracy - candidate_report.accuracy
            prefix = f"shadow.{window.window_id}"
            checks.extend(
                [
                    PromotionCheck(
                        f"{prefix}.accuracy",
                        candidate_report.accuracy >= self.minimum_accuracy,
                        candidate_report.accuracy,
                        f">= {self.minimum_accuracy:.3f}",
                    ),
                    PromotionCheck(
                        f"{prefix}.ece",
                        candidate_report.ece <= self.maximum_ece,
                        candidate_report.ece,
                        f"<= {self.maximum_ece:.3f}",
                    ),
                    PromotionCheck(
                        f"{prefix}.regression_vs_active",
                        regression <= self.maximum_accuracy_regression,
                        regression,
                        f"<= {self.maximum_accuracy_regression:.3f}",
                    ),
                ]
            )
            window_records.append(
                {
                    "window_id": window.window_id,
                    "candidate_accuracy": candidate_report.accuracy,
                    "active_accuracy": active_report.accuracy,
                    "candidate_ece": candidate_report.ece,
                    "accuracy_regression": regression,
                    "metadata": dict(window.metadata),
                }
            )

        merged_metadata = dict(metadata or {})
        merged_metadata["shadow_windows"] = window_records
        return PromotionManifest(candidate_name=candidate_name, checks=checks, metadata=merged_metadata)

    def delayed_regression_manifest(
        self,
        *,
        active_name: str,
        active: CompiledReflex,
        reference: CompiledReflex,
        window: ShadowWindow,
        metadata: dict[str, Any] | None = None,
    ) -> PromotionManifest:
        active_report = evaluate_reflex(active, window.x, window.y, accept_threshold=0.0)
        reference_report = evaluate_reflex(reference, window.x, window.y, accept_threshold=0.0)
        regression = reference_report.accuracy - active_report.accuracy
        checks = [
            PromotionCheck(
                f"monitor.{window.window_id}.accuracy",
                active_report.accuracy >= self.minimum_accuracy,
                active_report.accuracy,
                f">= {self.minimum_accuracy:.3f}",
            ),
            PromotionCheck(
                f"monitor.{window.window_id}.regression_vs_previous",
                regression <= self.maximum_accuracy_regression,
                regression,
                f"<= {self.maximum_accuracy_regression:.3f}",
            ),
        ]
        merged_metadata = dict(metadata or {})
        merged_metadata.update(
            {
                "window_id": window.window_id,
                "active_accuracy": active_report.accuracy,
                "reference_accuracy": reference_report.accuracy,
                "accuracy_regression": regression,
                "window_metadata": dict(window.metadata),
            }
        )
        return PromotionManifest(candidate_name=active_name, checks=checks, metadata=merged_metadata)
