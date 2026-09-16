from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import pickle
import tempfile
from typing import Any

from .reflex import CompiledReflex


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return str(value)


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        _jsonable(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_write_bytes(path, json.dumps(_jsonable(payload), indent=2, sort_keys=True).encode("utf-8") + b"\n")


@dataclass(frozen=True, slots=True)
class ReflexArtifactRecord:
    version_id: str
    model_sha256: str
    name: str
    metadata: dict[str, Any]
    created_at: str


class ReflexArtifactStore:
    """Content-addressed storage for immutable reflex artifacts and append-only evidence.

    A version identifier is derived from the exact serialized reflex bytes. Once a
    version exists, its model payload is never overwritten. Provenance and lifecycle
    evidence are stored as append-only events that reference immutable version IDs.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.versions_dir = self.root / "versions"
        self.events_path = self.root / "events.jsonl"
        self.state_path = self.root / "registry_state.json"
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def serialize(reflex: CompiledReflex) -> bytes:
        return pickle.dumps(reflex, protocol=5)

    @staticmethod
    def version_id_from_bytes(payload: bytes) -> tuple[str, str]:
        digest = hashlib.sha256(payload).hexdigest()
        return f"rfx-{digest[:24]}", digest

    def archive(
        self,
        reflex: CompiledReflex,
        *,
        provenance: dict[str, Any] | None = None,
    ) -> ReflexArtifactRecord:
        payload = self.serialize(reflex)
        version_id, digest = self.version_id_from_bytes(payload)
        version_dir = self.versions_dir / version_id
        model_path = version_dir / "model.pkl"
        artifact_path = version_dir / "artifact.json"

        if model_path.exists():
            existing = model_path.read_bytes()
            existing_digest = hashlib.sha256(existing).hexdigest()
            if existing_digest != digest:
                raise RuntimeError(f"Artifact hash mismatch for existing version {version_id}.")
        else:
            version_dir.mkdir(parents=True, exist_ok=True)
            _atomic_write_bytes(model_path, payload)

        if artifact_path.exists():
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        else:
            artifact = {
                "version_id": version_id,
                "model_sha256": digest,
                "name": reflex.name,
                "metadata": _jsonable(reflex.metadata),
                "created_at": _utc_now(),
            }
            _atomic_write_json(artifact_path, artifact)

        if provenance is not None:
            self.append_event(
                "provenance",
                {
                    "version_id": version_id,
                    "provenance": _jsonable(provenance),
                },
            )

        return ReflexArtifactRecord(**artifact)

    def load(self, version_id: str) -> CompiledReflex:
        model_path = self.versions_dir / version_id / "model.pkl"
        artifact_path = self.versions_dir / version_id / "artifact.json"
        if not model_path.exists() or not artifact_path.exists():
            raise KeyError(f"Unknown reflex version {version_id!r}.")

        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        payload = model_path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if digest != artifact["model_sha256"]:
            raise RuntimeError(f"Stored artifact {version_id} failed SHA-256 verification.")
        reflex = pickle.loads(payload)
        if not isinstance(reflex, CompiledReflex):
            raise TypeError(f"Artifact {version_id} does not contain a CompiledReflex.")
        return reflex

    def record(self, version_id: str) -> ReflexArtifactRecord:
        artifact_path = self.versions_dir / version_id / "artifact.json"
        if not artifact_path.exists():
            raise KeyError(f"Unknown reflex version {version_id!r}.")
        return ReflexArtifactRecord(**json.loads(artifact_path.read_text(encoding="utf-8")))

    def append_event(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "event_type": str(event_type),
            "timestamp": _utc_now(),
            "payload": _jsonable(payload),
        }
        event_id = "evt-" + hashlib.sha256(_canonical_json(body)).hexdigest()[:24]
        event = {"event_id": event_id, **body}
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return event

    def events(self, *, event_type: str | None = None) -> list[dict[str, Any]]:
        if not self.events_path.exists():
            return []
        items = [json.loads(line) for line in self.events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if event_type is None:
            return items
        return [item for item in items if item.get("event_type") == event_type]

    def provenance(self, version_id: str) -> list[dict[str, Any]]:
        return [
            event["payload"]["provenance"]
            for event in self.events(event_type="provenance")
            if event.get("payload", {}).get("version_id") == version_id
        ]

    def write_state(self, state: dict[str, Any]) -> None:
        _atomic_write_json(self.state_path, state)

    def read_state(self) -> dict[str, Any] | None:
        if not self.state_path.exists():
            return None
        return json.loads(self.state_path.read_text(encoding="utf-8"))
