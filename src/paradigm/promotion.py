from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PromotionCheck:
    name: str
    passed: bool
    value: Any
    requirement: str
    detail: str = ""


@dataclass(slots=True)
class PromotionManifest:
    candidate_name: str
    checks: list[PromotionCheck]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def approved(self) -> bool:
        return bool(self.checks) and all(check.passed for check in self.checks)

    @property
    def failure_reasons(self) -> list[str]:
        return [f"{check.name}: {check.detail or check.requirement}" for check in self.checks if not check.passed]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_name": self.candidate_name,
            "approved": self.approved,
            "failure_reasons": self.failure_reasons,
            "checks": [
                {
                    "name": check.name,
                    "passed": check.passed,
                    "value": check.value,
                    "requirement": check.requirement,
                    "detail": check.detail,
                }
                for check in self.checks
            ],
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class PromotionPolicy:
    minimum_accuracy: float = 0.95
    maximum_ece: float = 0.06
    maximum_label_disagreement: float = 0.06
    maximum_total_variation: float = 0.08
    minimum_class_accuracy: float = 0.80
    minimum_protected_slice_accuracy: float = 0.70

    def build_manifest(
        self,
        *,
        candidate_name: str,
        accuracy: float,
        ece: float,
        parameter_space_accepted: bool,
        behavior_space_accepted: bool,
        label_disagreement: float,
        total_variation: float,
        minimum_class_accuracy: float,
        protected_slice_accuracy: float,
        metadata: dict[str, Any] | None = None,
    ) -> PromotionManifest:
        checks = [
            PromotionCheck(
                "quality.accuracy",
                accuracy >= self.minimum_accuracy,
                float(accuracy),
                f">= {self.minimum_accuracy:.3f}",
            ),
            PromotionCheck(
                "calibration.ece",
                ece <= self.maximum_ece,
                float(ece),
                f"<= {self.maximum_ece:.3f}",
            ),
            PromotionCheck(
                "trust.parameter_space",
                bool(parameter_space_accepted),
                bool(parameter_space_accepted),
                "accepted",
                "candidate is outside the current trusted parameter pool" if not parameter_space_accepted else "",
            ),
            PromotionCheck(
                "trust.behavior_space",
                bool(behavior_space_accepted),
                bool(behavior_space_accepted),
                "accepted",
                "candidate is outside the current trusted behavior pool" if not behavior_space_accepted else "",
            ),
            PromotionCheck(
                "drift.label_disagreement",
                label_disagreement <= self.maximum_label_disagreement,
                float(label_disagreement),
                f"<= {self.maximum_label_disagreement:.3f}",
            ),
            PromotionCheck(
                "drift.total_variation",
                total_variation <= self.maximum_total_variation,
                float(total_variation),
                f"<= {self.maximum_total_variation:.3f}",
            ),
            PromotionCheck(
                "quality.minimum_class_accuracy",
                minimum_class_accuracy >= self.minimum_class_accuracy,
                float(minimum_class_accuracy),
                f">= {self.minimum_class_accuracy:.3f}",
            ),
            PromotionCheck(
                "quality.protected_slice_accuracy",
                protected_slice_accuracy >= self.minimum_protected_slice_accuracy,
                float(protected_slice_accuracy),
                f">= {self.minimum_protected_slice_accuracy:.3f}",
            ),
        ]
        return PromotionManifest(candidate_name=candidate_name, checks=checks, metadata=metadata or {})
