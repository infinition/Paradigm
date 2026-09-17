from __future__ import annotations

import pickle
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from ..agent_vertical import AgentDecisionRecord, AgentEpisode, PolicyDecision
from ..online_learning import OnlineReflexCompiler
from .shadow import ShadowSampler
from .contract import DeliberateDecision, Outcome, ParadigmState, ReflexDecision, TrustStatus, VerifiedOutcome
from .encoder import GenericStateEncoder


@dataclass(slots=True)
class ReflexPolicy:
    """What a reflex is allowed to execute on its own. Everything else deliberates.

    ``allowed_actions`` is a whitelist of action labels (regular expressions are accepted).
    ``max_risk`` is the highest state risk at which a reflex may act. Defaults keep
    generative, destructive, and high-risk decisions deliberative.
    """

    allowed_actions: tuple[str, ...] = ()
    max_risk: str = "low"
    risk_order: tuple[str, ...] = ("low", "medium", "high")

    def allows_action(self, action: str) -> bool:
        return any(re.fullmatch(pattern, action) for pattern in self.allowed_actions)

    def allows_risk(self, risk: str) -> bool:
        order = {level: i for i, level in enumerate(self.risk_order)}
        return order.get(risk, len(order)) <= order.get(self.max_risk, -1)


@dataclass(slots=True)
class _Step:
    state: ParadigmState
    features: np.ndarray
    action: str
    source: str
    confidence: float
    outcome: Outcome
    latency_ms: float
    llm_tokens: int
    llm_latency_ms: float


@dataclass(slots=True)
class DecisionLog:
    """Per-decision telemetry row, the unit a UI or audit trail displays."""

    episode: str
    step: int
    action: str | None
    source: str
    family: str
    trust_status: str
    confidence: float | None
    reason: str | None
    reflex_id: str | None
    decision_latency_ms: float
    outcome: str | None = None
    llm_tokens: int = 0
    llm_latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode": self.episode,
            "step": self.step,
            "action": self.action,
            "source": self.source,
            "family": self.family,
            "trust_status": self.trust_status,
            "confidence": self.confidence,
            "reason": self.reason,
            "reflex_id": self.reflex_id,
            "decision_latency_ms": self.decision_latency_ms,
            "outcome": self.outcome,
            "llm_tokens": self.llm_tokens,
            "llm_latency_ms": self.llm_latency_ms,
        }


class Paradigm:
    """Public engine facade: ``decide`` before a control decision, ``observe`` after execution.

    Invariants carried over from P2.1 to P2.4:
    - the active reflex is never trained in place; candidates are compiled from the
      experience buffer and promoted atomically by the compiler;
    - only deliberative decisions from verified successful episodes enter acquisition;
      reflex-generated actions and unverified steps are never teacher labels;
    - ``decide`` may return DELIBERATE for a state the reflex could handle: the gate,
      the confidence threshold, the family trust status, and the reflex policy all have
      to agree before a reflex acts.
    """

    def __init__(
        self,
        *,
        policy: ReflexPolicy,
        encoder: GenericStateEncoder | None = None,
        compiler: OnlineReflexCompiler | None = None,
        action_templates: dict[str, dict[str, Any]] | None = None,
        shadow_sampler: "ShadowSampler | None" = None,
    ) -> None:
        self.policy = policy
        # Optional: deterministic routing of some reflex-eligible decisions to the teacher.
        self.shadow_sampler = shadow_sampler
        self.encoder = encoder or GenericStateEncoder()
        self.compiler = compiler or OnlineReflexCompiler(
            min_episodes=8, compile_every=4, validation_fraction=0.25, minimum_ood_acceptance=0.65,
            certification="family_aware", shadow_certification="recent",
        )
        self.action_templates = dict(action_templates or {})
        self._lock = threading.RLock()
        self._episode_steps: list[_Step] = []
        self._episode_id = self._new_episode_id()
        self._episode_counter = 0
        self._closed_episodes = 0
        self._log: list[DecisionLog] = []
        self._pending: dict[str, DecisionLog] = {}
        self.counters: dict[str, int] = {
            "reflex_decisions": 0,
            "deliberative_decisions": 0,
            "observed_steps": 0,
            "episodes_closed": 0,
            "episodes_ingested": 0,
            "episodes_rejected_failure": 0,
            "episodes_rejected_unknown": 0,
            "steps_rejected_unverified": 0,
            "promotions": 0,
            "candidates_rejected": 0,
            "candidates_insufficient": 0,
            "shadow_sample_decisions": 0,
        }
        self.llm_tokens_spent = 0
        self.llm_latency_ms_spent = 0.0

    # ------------------------------------------------------------------ decide

    def _new_episode_id(self) -> str:
        return f"ep-{int(time.time() * 1000)}-{id(self) & 0xFFFF:x}"

    @property
    def family_scoped(self) -> bool:
        return getattr(self.compiler, "certification", "") == "family_scoped"

    def trust_status(self, family: str) -> TrustStatus:
        if self.compiler.state.selection is None:
            return TrustStatus.NO_REFLEX
        if self.family_scoped:
            if family in self.compiler.family_thresholds():
                return TrustStatus.ACTIVE
        elif family in self.compiler.state.probes:
            return TrustStatus.ACTIVE
        if any(str(t.metadata.get("family")) == family for ep in self.compiler.buffer.episodes for t in ep.traces):
            return TrustStatus.CANDIDATE
        return TrustStatus.DELIBERATIVE

    def trust_manifest(self) -> dict[str, str]:
        """Per-family authorization derived from the compiler lifecycle state."""
        families: set[str] = set(self.compiler.state.probes) | set(self.compiler.family_thresholds()) | {
            str(t.metadata.get("family")) for ep in self.compiler.buffer.episodes for t in ep.traces
        }
        return {fam: self.trust_status(fam).value for fam in sorted(families)}

    def explain(self, state: ParadigmState, actions: tuple[str, ...] | None = None) -> dict[str, Any]:
        """Proposal and authorization for a state, without executing or logging anything."""
        avail = tuple(actions) if actions is not None else state.available_actions
        family = state.family
        result: dict[str, Any] = {
            "family": family,
            "trust_status": self.trust_status(family).value,
            "proposed_action": None,
            "confidence": None,
            "gate_accepted": None,
            "authorized": False,
            "reason": None,
        }
        selection = self.compiler.state.selection
        if selection is None:
            result["reason"] = "no_active_reflex"
            return result
        x = self.encoder.encode(state)
        action, confidence, _ = selection.reflex.predict(x)
        action = str(action)
        result["proposed_action"] = action
        result["confidence"] = float(confidence)
        gate = self.compiler.state.ood_gate
        accepted = bool(gate.accept(x)[0]) if gate is not None else True
        result["gate_accepted"] = accepted
        if not accepted:
            result["reason"] = "out_of_distribution"
        elif float(confidence) < float(self.compiler.family_thresholds().get(family, selection.threshold) if self.family_scoped else selection.threshold):
            result["reason"] = "low_confidence"
        elif action not in avail and action.split("#", 1)[0] not in avail:
            # Templated labels ("tool#args") are available when their tool is.
            result["reason"] = "action_not_available"
        elif self.trust_status(family) != TrustStatus.ACTIVE:
            result["reason"] = "family_not_trusted"
        elif not self.policy.allows_action(action):
            result["reason"] = "action_not_in_reflex_policy"
        elif not self.policy.allows_risk(state.risk):
            result["reason"] = "risk_above_policy"
        else:
            result["authorized"] = True
            result["reason"] = "trusted"
        return result

    def decide(self, state: ParadigmState, actions: tuple[str, ...] | None = None) -> ReflexDecision | DeliberateDecision:
        start = time.perf_counter()
        with self._lock:
            if actions is not None:
                state = ParadigmState.from_dict({**state.to_dict(), "available_actions": list(actions)})
            info = self.explain(state)
            latency = (time.perf_counter() - start) * 1e3
            step_index = len(self._episode_steps)
            sampled = bool(
                info["authorized"] and self.shadow_sampler is not None
                and self.shadow_sampler.sample(self._episode_counter + 1, str(info["family"]), step_index)
            )
            if sampled:
                # Eligible for the reflex, deliberately handed to the teacher for evidence.
                info = {**info, "authorized": False, "reason": "shadow_sample"}
            if info["authorized"]:
                reflex_id = f"v{self.compiler.state.version}"
                decision: ReflexDecision | DeliberateDecision = ReflexDecision(
                    action=info["proposed_action"],
                    confidence=float(info["confidence"]),
                    family=info["family"],
                    reflex_id=reflex_id,
                    arguments=self.action_templates.get(info["proposed_action"]),
                    latency_ms=latency,
                )
                self.counters["reflex_decisions"] += 1
                row = DecisionLog(self._episode_id, step_index, decision.action, "reflex", info["family"], info["trust_status"], decision.confidence, None, reflex_id, latency)
            else:
                decision = DeliberateDecision(
                    reason=str(info["reason"]),
                    family=info["family"],
                    trust_status=info["trust_status"],
                    reflex_confidence=info["confidence"],
                    proposed_action=info["proposed_action"],
                    latency_ms=latency,
                )
                self.counters["deliberative_decisions"] += 1
                if sampled:
                    self.counters["shadow_sample_decisions"] += 1
                row = DecisionLog(self._episode_id, step_index, None, "deliberative", info["family"], info["trust_status"], info["confidence"], decision.reason, None, latency)
            self._log.append(row)
            self._pending[f"{self._episode_id}:{step_index}"] = row
            return decision

    # ----------------------------------------------------------------- observe

    def observe(
        self,
        state: ParadigmState,
        action: str,
        outcome: VerifiedOutcome,
        *,
        source: str = "deliberative",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record one executed step with its verified outcome.

        ``source`` is "reflex" when the executed action came from a ReflexDecision and
        "deliberative" otherwise. Reflex steps are never teacher labels. A deliberative
        step is teacher evidence only if its own outcome is SUCCESS and the episode
        closes as SUCCESS.
        """
        metadata = dict(metadata or {})
        with self._lock:
            features = self.encoder.encode(state)
            tokens = int(metadata.get("llm_tokens", 0) or 0)
            llm_latency = float(metadata.get("llm_latency_ms", 0.0) or 0.0)
            step = _Step(state, features, action, source, float(metadata.get("confidence", 0.0) or 0.0), outcome.outcome, float(metadata.get("decision_latency_ms", 0.0) or 0.0), tokens, llm_latency)
            self._episode_steps.append(step)
            self.counters["observed_steps"] += 1
            if source == "deliberative":
                self.llm_tokens_spent += tokens
                self.llm_latency_ms_spent += llm_latency
            key = f"{self._episode_id}:{len(self._episode_steps) - 1}"
            row = self._pending.pop(key, None)
            if row is None:
                # Executed without a matching decide (for example the second call of a batched
                # model response): logged for the audit trail, never as a decision.
                row = DecisionLog(self._episode_id, len(self._episode_steps) - 1, action, source, state.family, self.trust_status(state.family).value, None, "no_decision_requested", None, 0.0)
                self._log.append(row)
            row.outcome = outcome.outcome.value
            row.llm_tokens = tokens
            row.llm_latency_ms = llm_latency
            if row.action is None:
                row.action = action
            return {"episode": self._episode_id, "step": len(self._episode_steps) - 1, "outcome": outcome.outcome.value}

    def close_episode(self, outcome: VerifiedOutcome, *, family: str | None = None) -> dict[str, Any]:
        """End the current episode. Only a SUCCESS episode can enter acquisition."""
        with self._lock:
            steps = self._episode_steps
            episode_id = self._episode_id
            self._episode_steps = []
            self._episode_counter += 1
            self._episode_id = self._new_episode_id()
            self._pending = {}
            self.counters["episodes_closed"] += 1
            result: dict[str, Any] = {"episode": episode_id, "steps": len(steps), "outcome": outcome.outcome.value, "ingested": False, "promotion": None}
            if outcome.outcome is Outcome.FAILURE:
                self.counters["episodes_rejected_failure"] += 1
                return result
            if outcome.outcome is Outcome.UNKNOWN:
                self.counters["episodes_rejected_unknown"] += 1
                return result
            if not steps:
                return result
            episode = AgentEpisode(task_id=episode_id, family=family or steps[-1].state.family, success=True, steps=len(steps))
            for s in steps:
                validated = s.outcome is Outcome.SUCCESS
                if s.source == "deliberative" and not validated:
                    self.counters["steps_rejected_unverified"] += 1
                episode.decisions.append(PolicyDecision(s.action, s.source, s.confidence, latency_ms=s.latency_ms))
                episode.records.append(
                    AgentDecisionRecord(
                        features=s.features, action=s.action, source=s.source, phase=s.state.phase,
                        failure_kind=s.state.last_outcome, confidence=s.confidence, family=s.state.family, validated=validated,
                    )
                )
                if s.source == "reflex":
                    episode.reflex_calls += 1
                else:
                    episode.deliberative_calls += 1
            before_version = self.compiler.state.version
            promotion = self.compiler.ingest(episode, stream_episode=self._episode_counter)
            result["ingested"] = True
            self.counters["episodes_ingested"] += 1
            if promotion is not None:
                result["promotion"] = {"outcome": promotion.outcome or ("promoted" if promotion.promoted else "rejected"), "reason": promotion.reason, "version": promotion.version}
                if promotion.promoted:
                    self.counters["promotions"] += 1
                elif (promotion.outcome or "") == "insufficient_evidence":
                    self.counters["candidates_insufficient"] += 1
                else:
                    self.counters["candidates_rejected"] += 1
            result["active_version"] = self.compiler.state.version
            result["version_changed"] = self.compiler.state.version != before_version
            return result

    # --------------------------------------------------------------- telemetry

    def telemetry(self) -> dict[str, Any]:
        with self._lock:
            deliberative = self.counters["deliberative_decisions"]
            reflex = self.counters["reflex_decisions"]
            mean_tokens = (self.llm_tokens_spent / deliberative) if deliberative else 0.0
            mean_latency = (self.llm_latency_ms_spent / deliberative) if deliberative else 0.0
            manifest = self.trust_manifest()
            shadow = self.counters.get("shadow_sample_decisions", 0)
            return {
                "reflex_decisions": reflex,
                "deliberative_decisions": deliberative,
                "natural_model_calls": deliberative - shadow,
                "shadow_sample_model_calls": shadow,
                "llm_calls_avoided": reflex,
                "net_calls_avoided_after_sampling": reflex - shadow,
                "shadow_sampler": self.shadow_sampler.to_dict() if self.shadow_sampler is not None else None,
                "llm_tokens_spent": self.llm_tokens_spent,
                "llm_tokens_avoided_estimate": int(round(reflex * mean_tokens)),
                "llm_latency_ms_avoided_estimate": reflex * mean_latency,
                "active_reflex_version": self.compiler.state.version,
                "active_families": sorted(f for f, s in manifest.items() if s == TrustStatus.ACTIVE.value),
                "candidate_families": sorted(f for f, s in manifest.items() if s == TrustStatus.CANDIDATE.value),
                "deliberative_only_families": sorted(f for f, s in manifest.items() if s == TrustStatus.DELIBERATIVE.value),
                "trust_manifest": manifest,
                "counters": dict(self.counters),
                "buffer": {
                    "trusted_episodes": len(self.compiler.buffer.episodes),
                    "trusted_traces": self.compiler.buffer.trusted_trace_count,
                    "rejected_failed_episodes": self.compiler.buffer.rejected_failed_episodes,
                    "ignored_self_labels": self.compiler.buffer.ignored_self_labels,
                    "rejected_unvalidated_steps": self.compiler.buffer.rejected_unvalidated_steps,
                },
            }

    def decision_log(self, last: int | None = None) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._log if last is None else self._log[-last:]
            return [r.to_dict() for r in rows]

    # ------------------------------------------------------------- persistence

    def save(self, path: Path) -> None:
        """Persist the compiler state and templates. The decision log is not persisted."""
        with self._lock:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("wb") as fh:
                pickle.dump({"compiler": self.compiler, "action_templates": self.action_templates, "counters": self.counters}, fh)

    @classmethod
    def load(cls, path: Path, *, policy: ReflexPolicy, encoder: GenericStateEncoder | None = None, shadow_sampler: ShadowSampler | None = None) -> "Paradigm":
        with Path(path).open("rb") as fh:
            payload = pickle.load(fh)
        engine = cls(policy=policy, encoder=encoder, compiler=payload["compiler"], action_templates=payload.get("action_templates"), shadow_sampler=shadow_sampler)
        engine.counters.update(payload.get("counters") or {})
        return engine
