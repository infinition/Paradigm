"""Raw experience trace sink (D1 collection).

The engine's experience buffer keeps encoded features and only ingests episodes that
close SUCCESS, which is correct for compiling reflexes and insufficient for learning a
representation from experience: the goal phrasing is gone, and the steps of a FAILURE or
UNKNOWN episode are discarded at close. This sink writes the raw record next to that
pipeline, before either loss happens.

It observes and never decides. Nothing here is read back by the engine, no threshold,
gate, certification or promotion path consults it, and with no sink configured the engine
behaves exactly as before. What it writes is a JSONL stream of two row kinds, ``step``
and ``episode``, tagged with an attempt id so an invalidated attempt can never be mixed
with its restart.

Retention rule, unchanged by this file and restated because the sink is what makes the
distinction visible: a SUCCESS episode's verified step may become positive evidence;
FAILURE and UNKNOWN are kept for audit, hard negatives and analysis, never as positives.

No payload bytes are written: an image is recorded as the count and the verdict the
adapter derived from it, never as its content.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .contract import ParadigmState, VerifiedOutcome

TRACE_SCHEMA_VERSION = "d1-trace-1"


@dataclass
class TraceSink:
    """Append-only JSONL writer for raw decision steps and episode verdicts."""

    path: Path
    attempt_id: str
    schema_version: str = TRACE_SCHEMA_VERSION
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Opened once, in append mode: a restart under the same attempt id continues the
        # same stream instead of truncating what was already collected.
        self._fh = self.path.open("a", encoding="utf-8")

    def _write(self, row: dict[str, Any]) -> None:
        with self._lock:
            self._fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            # Flushed per row: a killed run keeps every step it paid the provider for.
            self._fh.flush()

    def write_step(
        self,
        *,
        episode_id: str,
        stream_episode: int,
        step_id: int,
        state: "ParadigmState",
        executed_action: str,
        source: str,
        outcome: "VerifiedOutcome",
        proposed_action: str | None,
        confidence: float,
        metadata: dict[str, Any],
    ) -> None:
        tokens_in = int(metadata.get("llm_input_tokens", 0) or 0)
        tokens_out = int(metadata.get("llm_output_tokens", 0) or 0)
        total = int(metadata.get("llm_tokens", 0) or 0)
        # Usage reaches the engine on the first call of a model response only, so a step
        # carrying usage is a model call and a step without one is a later call of the
        # same response. The split is absent on adapters that report a single total.
        self._write(
            {
                "record": "step",
                "trace_schema_version": self.schema_version,
                "attempt_id": self.attempt_id,
                "episode_id": episode_id,
                # The engine's episode id is a millisecond clock plus the instance address,
                # so two episodes closing inside the same millisecond share it. The dataset
                # key is (attempt_id, stream_episode, step_id), which cannot collide.
                "stream_episode": stream_episode,
                "step_id": step_id,
                "timestamp": time.time(),
                "goal_raw": state.goal,
                "state_raw": state.to_dict(),
                "available_actions": list(state.available_actions),
                "family": state.family,
                "phase": state.phase,
                "teacher_action": executed_action if source == "deliberative" else None,
                "executed_action": executed_action,
                "reflex_candidate_action": proposed_action,
                "decision_source": source,
                "confidence": confidence,
                "verified_outcome": outcome.outcome.value,
                "outcome_evidence": dict(outcome.evidence),
                "outcome_verifier": outcome.verifier,
                "failure_kind": state.last_outcome,
                "output_kind": state.features.get("last_output_kind"),
                "model_calls": 1 if total or tokens_in or tokens_out else 0,
                "input_tokens": tokens_in,
                "output_tokens": tokens_out,
                "total_tokens": total,
                "decision_latency_ms": float(metadata.get("decision_latency_ms", 0.0) or 0.0),
                "llm_latency_ms": float(metadata.get("llm_latency_ms", 0.0) or 0.0),
            }
        )

    def write_episode(
        self,
        *,
        episode_id: str,
        outcome: "VerifiedOutcome",
        step_count: int,
        family: str | None,
        stream_episode: int,
    ) -> None:
        self._write(
            {
                "record": "episode",
                "trace_schema_version": self.schema_version,
                "attempt_id": self.attempt_id,
                "episode_id": episode_id,
                "timestamp": time.time(),
                "episode_status": outcome.outcome.value,
                "episode_verified": bool(outcome.verifier),
                "episode_verifier": outcome.verifier,
                "episode_evidence": dict(outcome.evidence),
                "step_count": step_count,
                "family": family,
                "stream_episode": stream_episode,
            }
        )

    def close(self) -> None:
        with self._lock:
            self._fh.close()
