from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Outcome(str, Enum):
    """Verified result of an executed action. Only SUCCESS can become teacher evidence."""

    SUCCESS = "success"
    FAILURE = "failure"
    UNKNOWN = "unknown"


class TrustStatus(str, Enum):
    ACTIVE = "active"
    CANDIDATE = "candidate"
    DELIBERATIVE = "deliberative"
    NO_REFLEX = "no_reflex"


@dataclass(slots=True)
class ParadigmState:
    """Structured decision state. Small, categorical, teacher-independent.

    ``features`` holds domain-specific structured values (numbers, booleans, short
    strings). ``goal`` is hashed by the encoder; keep it short. ``family_hint`` is the
    behavior family the adapter assigns; the engine certifies and trusts per family.
    """

    domain: str
    phase: str
    available_actions: tuple[str, ...]
    goal: str = ""
    last_action: str | None = None
    last_outcome: str = "none"
    recent_actions: tuple[str, ...] = ()
    step: int = 0
    features: dict[str, Any] = field(default_factory=dict)
    risk: str = "low"
    family_hint: str | None = None
    context_refs: dict[str, str] = field(default_factory=dict)

    @property
    def family(self) -> str:
        return self.family_hint or f"{self.domain}:{self.phase}:{self.last_outcome}"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["available_actions"] = list(self.available_actions)
        data["recent_actions"] = list(self.recent_actions)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParadigmState":
        return cls(
            domain=str(data["domain"]),
            phase=str(data["phase"]),
            available_actions=tuple(str(a) for a in data.get("available_actions", ())),
            goal=str(data.get("goal", "")),
            last_action=data.get("last_action"),
            last_outcome=str(data.get("last_outcome", "none")),
            recent_actions=tuple(str(a) for a in data.get("recent_actions", ())),
            step=int(data.get("step", 0)),
            features=dict(data.get("features") or {}),
            risk=str(data.get("risk", "low")),
            family_hint=data.get("family_hint"),
            context_refs=dict(data.get("context_refs") or {}),
        )


@dataclass(slots=True)
class VerifiedOutcome:
    """What the application verified after executing an action.

    ``outcome`` must come from a check the application performed (tests, contract,
    environment feedback, human validation). The absence of an error is not SUCCESS.
    """

    outcome: Outcome
    evidence: dict[str, Any] = field(default_factory=dict)
    verifier: str = ""

    @classmethod
    def success(cls, verifier: str = "", **evidence: Any) -> "VerifiedOutcome":
        return cls(Outcome.SUCCESS, dict(evidence), verifier)

    @classmethod
    def failure(cls, verifier: str = "", **evidence: Any) -> "VerifiedOutcome":
        return cls(Outcome.FAILURE, dict(evidence), verifier)

    @classmethod
    def unknown(cls, verifier: str = "", **evidence: Any) -> "VerifiedOutcome":
        return cls(Outcome.UNKNOWN, dict(evidence), verifier)


@dataclass(slots=True)
class ReflexDecision:
    """A trusted reflex action. The application executes it without consulting the model."""

    action: str
    source: str = "reflex"
    confidence: float = 0.0
    family: str = ""
    reflex_id: str = ""
    arguments: dict[str, Any] | None = None
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DeliberateDecision:
    """A first-class result: the application must consult its deliberative system.

    ``proposed_action`` is what the reflex would have done, exposed for audit and shadow
    evaluation only. It is never executed by Paradigm. Capability is not authorization.
    """

    reason: str
    source: str = "deliberative"
    family: str = ""
    trust_status: str = TrustStatus.NO_REFLEX.value
    reflex_confidence: float | None = None
    proposed_action: str | None = None
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
