from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

import numpy as np

from .promotion import PromotionCheck, PromotionManifest


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _normalized(values: list[float] | np.ndarray) -> np.ndarray:
    x = np.asarray(values, dtype=np.float64)
    return x / (np.linalg.norm(x) + 1e-12)


@dataclass(frozen=True, slots=True)
class FamilyDefinition:
    name: str
    risk: str
    maximum_epsilon: float
    parameter_prototype: list[float]
    parameter_threshold: float
    behavior_prototype: list[float]
    behavior_threshold: float
    semantic_floors: dict[str, float]
    parent_lineage: str
    research_phase: str = "P1.3"

    def canonical_payload(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def family_id(self) -> str:
        digest = hashlib.sha256(_canonical_json(self.canonical_payload())).hexdigest()
        return f"fam-{digest[:24]}"


@dataclass(frozen=True, slots=True)
class FamilyRoute:
    status: str
    family_id: str | None
    family_name: str | None
    reason: str
    matches: list[dict[str, Any]]

    @property
    def represented(self) -> bool:
        return self.status == "represented" and self.family_id is not None


class PersistentFamilyRegistry:
    """Persistent registry for immutable trusted update-family definitions.

    Family definitions are content-addressed and never mutated. Operational
    state such as active, quarantined, or retired is stored separately. Adding
    a new family therefore cannot silently widen the thresholds of an existing
    family.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.family_dir = self.root / "families"
        self.state_path = self.root / "family_state.json"
        self.events_path = self.root / "family_events.jsonl"
        self.family_dir.mkdir(parents=True, exist_ok=True)
        if not self.state_path.exists():
            _atomic_json(self.state_path, {"status": {}})

    def _state(self) -> dict[str, Any]:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _write_state(self, state: dict[str, Any]) -> None:
        _atomic_json(self.state_path, state)

    def _append_event(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {"event_type": event_type, "timestamp": _utc_now(), "payload": payload}
        event_id = "fev-" + hashlib.sha256(_canonical_json(body)).hexdigest()[:24]
        event = {"event_id": event_id, **body}
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return event

    def events(self) -> list[dict[str, Any]]:
        if not self.events_path.exists():
            return []
        return [json.loads(line) for line in self.events_path.read_text(encoding="utf-8").splitlines() if line]

    def register(self, definition: FamilyDefinition, *, provenance: dict[str, Any] | None = None) -> str:
        family_id = definition.family_id
        path = self.family_dir / f"{family_id}.json"
        payload = {"family_id": family_id, "definition": definition.canonical_payload(), "created_at": _utc_now()}
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing["definition"] != payload["definition"]:
                raise RuntimeError(f"Immutable family definition mismatch for {family_id}.")
        else:
            _atomic_json(path, payload)

        state = self._state()
        state.setdefault("status", {}).setdefault(family_id, "active")
        self._write_state(state)
        self._append_event(
            "family_registered",
            {"family_id": family_id, "name": definition.name, "provenance": provenance or {}},
        )
        return family_id

    def load(self, family_id: str) -> FamilyDefinition:
        path = self.family_dir / f"{family_id}.json"
        if not path.exists():
            raise KeyError(f"Unknown family {family_id!r}.")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return FamilyDefinition(**payload["definition"])

    def list(self, *, include_inactive: bool = False) -> list[tuple[str, FamilyDefinition, str]]:
        state = self._state().get("status", {})
        items = []
        for path in sorted(self.family_dir.glob("fam-*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            family_id = payload["family_id"]
            status = state.get(family_id, "active")
            if include_inactive or status == "active":
                items.append((family_id, FamilyDefinition(**payload["definition"]), status))
        return items

    def set_status(self, family_id: str, status: str, *, reason: str) -> None:
        if status not in {"active", "quarantined", "retired"}:
            raise ValueError("status must be active, quarantined, or retired")
        self.load(family_id)
        state = self._state()
        state.setdefault("status", {})[family_id] = status
        self._write_state(state)
        self._append_event("family_status", {"family_id": family_id, "status": status, "reason": reason})

    def definition_hash(self, family_id: str) -> str:
        payload = (self.family_dir / f"{family_id}.json").read_bytes()
        return hashlib.sha256(payload).hexdigest()

    def route(self, parameter_signature: np.ndarray, behavior_signature: np.ndarray) -> FamilyRoute:
        p = _normalized(parameter_signature)
        b = _normalized(behavior_signature)
        matches: list[dict[str, Any]] = []
        for family_id, definition, _ in self.list(include_inactive=False):
            ps = float(p @ _normalized(definition.parameter_prototype))
            bs = float(b @ _normalized(definition.behavior_prototype))
            parameter_pass = ps >= definition.parameter_threshold
            behavior_pass = bs >= definition.behavior_threshold
            if parameter_pass and behavior_pass:
                matches.append(
                    {
                        "family_id": family_id,
                        "family_name": definition.name,
                        "parameter_similarity": ps,
                        "behavior_similarity": bs,
                        "margin": min(ps - definition.parameter_threshold, bs - definition.behavior_threshold),
                    }
                )

        if not matches:
            return FamilyRoute("unknown", None, None, "no active family accepts both signatures", [])
        matches.sort(key=lambda item: item["margin"], reverse=True)
        if len(matches) > 1:
            return FamilyRoute("ambiguous", None, None, "multiple active families accept the candidate", matches)
        match = matches[0]
        return FamilyRoute("represented", match["family_id"], match["family_name"], "single family match", matches)

    def build_manifest(
        self,
        *,
        candidate_name: str,
        route: FamilyRoute,
        epsilon_used: float,
        current_accuracy: float,
        protected_accuracy: float,
        minimum_class_accuracy: float,
        subgroup_accuracy: float,
        metadata: dict[str, Any] | None = None,
    ) -> PromotionManifest:
        if not route.represented:
            return PromotionManifest(
                candidate_name=candidate_name,
                checks=[
                    PromotionCheck(
                        "family.route",
                        False,
                        route.status,
                        "exactly one active represented family",
                        route.reason,
                    )
                ],
                metadata={"route": asdict(route), **(metadata or {})},
            )

        definition = self.load(route.family_id)
        floors = definition.semantic_floors
        checks = [
            PromotionCheck("family.route", True, route.family_id, "single represented active family"),
            PromotionCheck(
                "plasticity.epsilon",
                epsilon_used <= definition.maximum_epsilon + 1e-12,
                float(epsilon_used),
                f"<= {definition.maximum_epsilon:.6f}",
                "candidate exceeds the family plasticity budget" if epsilon_used > definition.maximum_epsilon else "",
            ),
            PromotionCheck(
                "quality.current_accuracy",
                current_accuracy >= floors["current_accuracy"],
                float(current_accuracy),
                f">= {floors['current_accuracy']:.6f}",
            ),
            PromotionCheck(
                "quality.protected_accuracy",
                protected_accuracy >= floors["protected_accuracy"],
                float(protected_accuracy),
                f">= {floors['protected_accuracy']:.6f}",
            ),
            PromotionCheck(
                "quality.minimum_class_accuracy",
                minimum_class_accuracy >= floors["minimum_class_accuracy"],
                float(minimum_class_accuracy),
                f">= {floors['minimum_class_accuracy']:.6f}",
            ),
            PromotionCheck(
                "quality.subgroup_accuracy",
                subgroup_accuracy >= floors["subgroup_accuracy"],
                float(subgroup_accuracy),
                f">= {floors['subgroup_accuracy']:.6f}",
            ),
        ]
        payload = {
            "family_id": route.family_id,
            "family_name": route.family_name,
            "family_risk": definition.risk,
            "route": asdict(route),
            **(metadata or {}),
        }
        return PromotionManifest(candidate_name=candidate_name, checks=checks, metadata=payload)

    def record_manifest(self, candidate_update_id: str, manifest: PromotionManifest) -> None:
        self._append_event(
            "candidate_manifest",
            {"candidate_update_id": candidate_update_id, "manifest": manifest.to_dict()},
        )

    def record_evolution(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Record a persistent family-evolution event without mutating definitions."""

        return self._append_event(event_type, payload)

    def split_family(
        self,
        parent_family_id: str,
        child_definitions: list[FamilyDefinition],
        *,
        reason: str,
        provenance: dict[str, Any] | None = None,
    ) -> list[str]:
        """Register immutable successor families and retire the parent definition."""

        self.load(parent_family_id)
        if len(child_definitions) < 2:
            raise ValueError("A split requires at least two child definitions.")
        child_ids = [
            self.register(
                definition,
                provenance={
                    "evolution": "split",
                    "parent_family_id": parent_family_id,
                    **(provenance or {}),
                },
            )
            for definition in child_definitions
        ]
        self.set_status(parent_family_id, "retired", reason=reason)
        self._append_event(
            "family_split",
            {
                "parent_family_id": parent_family_id,
                "child_family_ids": child_ids,
                "reason": reason,
            },
        )
        return child_ids
