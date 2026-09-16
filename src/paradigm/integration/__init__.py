"""Generic integration surface: structured state in, typed decision out, verified outcome back.

An application supplies three things: a structured state, the actions available in that
state, and a verified outcome after execution. The engine owns acquisition, compilation,
certification, retention, promotion, and routing. Adapters translate native application
objects into this contract; the core never imports application code.
"""

from .contract import (
    DeliberateDecision,
    Outcome,
    ParadigmState,
    ReflexDecision,
    TrustStatus,
    VerifiedOutcome,
)
from .encoder import GenericStateEncoder
from .engine import Paradigm, ReflexPolicy

__all__ = [
    "DeliberateDecision",
    "GenericStateEncoder",
    "Outcome",
    "Paradigm",
    "ParadigmState",
    "ReflexDecision",
    "ReflexPolicy",
    "TrustStatus",
    "VerifiedOutcome",
]
