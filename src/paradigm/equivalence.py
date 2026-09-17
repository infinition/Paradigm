"""Behavioral equivalence contract for certification scoring.

The core scores a reflex against the teacher's action. When several actions are
verified to have the same procedural effect in a state, literal identity is the wrong
target: a reflex replaying a certified action is scored wrong because the teacher
chose an equivalent one. An adapter may declare equivalence classes derived from
rules it already enforces; the core never infers them. The default contract is
identity, which leaves every existing score unchanged.

The contract is materialized per certification as an explicit mapping of the action
keys in play, versioned and hashed, so a recorded verdict stays reproducible even if
the adapter's classes change later.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np


@dataclass(slots=True)
class EquivalenceContract:
    version: str = "identity"
    class_of: Callable[[str], str] = field(default=lambda key: key)

    @classmethod
    def from_mapping(cls, record: dict[str, Any] | None) -> "EquivalenceContract | None":
        """Rebuild a contract from a materialized record; keys outside the mapping are literal.
        None (a record frozen before contracts existed) is identity."""
        if not record:
            return None
        mapping = dict(record.get("mapping") or {})
        return cls(version=str(record.get("version", "identity")), class_of=lambda key: mapping.get(key, key))

    def materialize(self, keys: set[str]) -> dict[str, Any]:
        mapping = {k: str(self.class_of(k)) for k in sorted(keys)}
        digest = hashlib.sha256(json.dumps({"version": self.version, "mapping": mapping}, sort_keys=True).encode("utf-8")).hexdigest()
        return {"version": self.version, "mapping": mapping, "digest": digest}


IDENTITY = EquivalenceContract()


def collapse_to_classes(
    y_true: np.ndarray, probs: np.ndarray, classes: np.ndarray, contract: EquivalenceContract | None
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Map labels and probabilities into class space: the confidence of a class is the sum of
    the probabilities of its member actions. With no contract, returns the inputs."""
    if contract is None:
        return y_true, probs, classes
    classes = np.asarray(classes).astype(str)
    names = [str(contract.class_of(c)) for c in classes]
    uniq = sorted(set(names) | {str(contract.class_of(str(v))) for v in np.asarray(y_true).astype(str)})
    index = {n: i for i, n in enumerate(uniq)}
    out = np.zeros((np.asarray(probs).shape[0], len(uniq)), dtype=np.float64)
    for j, n in enumerate(names):
        out[:, index[n]] += np.asarray(probs, dtype=np.float64)[:, j]
    y_c = np.asarray([str(contract.class_of(str(v))) for v in np.asarray(y_true).astype(str)])
    return y_c, out, np.asarray(uniq)


def same_class(a: str, b: str, contract: EquivalenceContract | None) -> bool:
    if contract is None:
        return str(a) == str(b)
    return str(contract.class_of(str(a))) == str(contract.class_of(str(b)))
