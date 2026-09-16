from __future__ import annotations

import numpy as np

from paradigm.p11 import _adapt_sequence, _delta_signature, _init_mlp


def test_p11_all_adaptation_backends_execute_on_short_run():
    methods = {"sgd", "adam", "replay", "ewc", "periodic_retrain", "drift_contract"}
    for method in methods:
        result = _adapt_sequence(11, method, steps=3)
        assert 0.0 <= result["final_mean_seen_accuracy"] <= 1.0
        assert result["total_adapt_seconds"] >= 0.0
        assert len(result["history"]) == 3


def test_neural_delta_signature_is_normalized_and_shape_stable():
    rng = np.random.default_rng(7)
    before = _init_mlp(rng, 6, 5, 3)
    after = before.copy()
    after.w1 += 0.01
    sig = _delta_signature(before, after)
    assert sig.ndim == 1
    assert np.isclose(np.linalg.norm(sig), 1.0)
    assert len(sig) == before.w1.size + before.b1.size + before.w2.size + before.b2.size
