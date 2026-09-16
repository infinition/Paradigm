from __future__ import annotations

from dataclasses import dataclass, field

from .promotion import PromotionManifest
from .reflex import CompiledReflex


@dataclass
class ActiveCandidateRegistry:
    active: CompiledReflex | None = None
    candidate: CompiledReflex | None = None
    previous_active: CompiledReflex | None = None
    history: list[str] = field(default_factory=list)
    promotion_records: list[dict[str, object]] = field(default_factory=list)

    def stage(self, reflex: CompiledReflex) -> None:
        self.candidate = reflex
        self.history.append(f"staged:{reflex.name}")

    def promote(self, manifest: PromotionManifest | None = None) -> None:
        if self.candidate is None:
            raise RuntimeError("No candidate is staged.")
        if manifest is not None and not manifest.approved:
            self.promotion_records.append(manifest.to_dict())
            self.history.append(
                f"promotion_blocked:{self.candidate.name}:{'|'.join(manifest.failure_reasons)}"
            )
            raise RuntimeError("Candidate promotion was blocked by the promotion manifest.")

        self.previous_active = self.active
        self.active = self.candidate
        self.candidate = None
        self.history.append(f"promoted:{self.active.name}")
        if manifest is not None:
            self.promotion_records.append(manifest.to_dict())

    def reject(self, reason: str = "", manifest: PromotionManifest | None = None) -> None:
        if self.candidate is not None:
            self.history.append(f"rejected:{self.candidate.name}:{reason}")
        if manifest is not None:
            self.promotion_records.append(manifest.to_dict())
        self.candidate = None

    def rollback(self) -> None:
        if self.previous_active is None:
            raise RuntimeError("No previous active reflex is available for rollback.")
        current = self.active
        self.active = self.previous_active
        self.previous_active = current
        self.history.append(f"rollback:{self.active.name if self.active else 'none'}")
