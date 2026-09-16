from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .promotion import PromotionManifest
from .reflex import CompiledReflex
from .storage import ReflexArtifactStore


@dataclass
class PersistentReflexRegistry:
    """Persistent active/candidate lifecycle over immutable content-addressed artifacts."""

    store: ReflexArtifactStore
    active_version_id: str | None = None
    candidate_version_id: str | None = None
    active_history: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        state = self.store.read_state()
        if state is not None:
            self.active_version_id = state.get("active_version_id")
            self.candidate_version_id = state.get("candidate_version_id")
            self.active_history = list(state.get("active_history", []))

    def _persist(self) -> None:
        self.store.write_state(
            {
                "active_version_id": self.active_version_id,
                "candidate_version_id": self.candidate_version_id,
                "active_history": list(self.active_history),
            }
        )

    @property
    def active(self) -> CompiledReflex | None:
        return self.store.load(self.active_version_id) if self.active_version_id else None

    @property
    def candidate(self) -> CompiledReflex | None:
        return self.store.load(self.candidate_version_id) if self.candidate_version_id else None

    def bootstrap_active(
        self,
        reflex: CompiledReflex,
        *,
        provenance: dict[str, Any] | None = None,
    ) -> str:
        if self.active_version_id is not None:
            raise RuntimeError("An active reflex is already registered.")
        record = self.store.archive(reflex, provenance=provenance)
        self.active_version_id = record.version_id
        self._persist()
        self.store.append_event(
            "bootstrap_active",
            {"version_id": record.version_id, "provenance": provenance or {}},
        )
        return record.version_id

    def stage(
        self,
        reflex: CompiledReflex,
        *,
        provenance: dict[str, Any] | None = None,
    ) -> str:
        parent = self.active_version_id
        merged_provenance = {"parent_active_version_id": parent, **(provenance or {})}
        record = self.store.archive(reflex, provenance=merged_provenance)
        self.candidate_version_id = record.version_id
        self._persist()
        self.store.append_event(
            "stage",
            {
                "candidate_version_id": record.version_id,
                "parent_active_version_id": parent,
                "provenance": merged_provenance,
            },
        )
        return record.version_id

    def promote(self, manifest: PromotionManifest) -> str:
        if self.candidate_version_id is None:
            raise RuntimeError("No candidate is staged.")

        candidate_id = self.candidate_version_id
        event_payload = {
            "candidate_version_id": candidate_id,
            "previous_active_version_id": self.active_version_id,
            "manifest": manifest.to_dict(),
        }
        if not manifest.approved:
            self.store.append_event("promotion_blocked", event_payload)
            raise RuntimeError("Candidate promotion was blocked by the promotion manifest.")

        if self.active_version_id is not None:
            self.active_history.append(self.active_version_id)
        self.active_version_id = candidate_id
        self.candidate_version_id = None
        self._persist()
        self.store.append_event("promote", event_payload)
        return candidate_id

    def reject(self, reason: str, manifest: PromotionManifest | None = None) -> str | None:
        candidate_id = self.candidate_version_id
        self.store.append_event(
            "reject",
            {
                "candidate_version_id": candidate_id,
                "reason": reason,
                "manifest": manifest.to_dict() if manifest is not None else None,
            },
        )
        self.candidate_version_id = None
        self._persist()
        return candidate_id

    def rollback(self, *, reason: str = "") -> str:
        if not self.active_history:
            raise RuntimeError("No archived active version is available for rollback.")
        current = self.active_version_id
        restored = self.active_history.pop()
        self.active_version_id = restored
        self.candidate_version_id = None
        self._persist()
        self.store.append_event(
            "rollback",
            {
                "from_version_id": current,
                "to_version_id": restored,
                "reason": reason,
            },
        )
        return restored

    def record_shadow_observation(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.store.append_event("shadow_observation", payload)
