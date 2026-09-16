from __future__ import annotations

import numpy as np

from paradigm.p11 import _base_train, _make_domains
from paradigm.p12 import (
    RISK_EPSILON,
    _adapt_family_candidate,
    _behavior_delta_signature,
    _fixed_anchor_domains,
)


def test_p12_behavior_signature_is_normalized_and_fixed_shape():
    domains, y = _make_domains(4242, n=1200)
    parent = _base_train(5151, domains[0][:900], y[:900], steps=4)
    after = parent.copy()
    after.w1 += 0.001
    anchors = _fixed_anchor_domains(n=16)
    sig = _behavior_delta_signature(parent, after, anchors, 1)
    assert sig.ndim == 1
    assert len(sig) == 16 * 4 * 2
    assert np.isclose(np.linalg.norm(sig), 1.0)


def test_p12_risk_schedule_is_monotonic():
    assert RISK_EPSILON["low"] > RISK_EPSILON["medium"] > RISK_EPSILON["high"]


def test_p12_family_candidate_executes_short_run():
    domains, y = _make_domains(4242)
    parent = _base_train(5151, domains[0][:5000], y[:5000], steps=5)
    candidate = _adapt_family_candidate(
        parent,
        domains,
        y,
        family=1,
        seed=101,
        epsilon=RISK_EPSILON["low"],
        steps=2,
        replay=True,
    )
    assert 0.0 <= candidate.current_accuracy <= 1.0
    assert 0.0 <= candidate.protected_accuracy <= 1.0
    assert candidate.max_step_drift > 0.0
    assert np.isclose(np.linalg.norm(candidate.parameter_signature), 1.0)
    assert np.isclose(np.linalg.norm(candidate.behavior_signature), 1.0)
