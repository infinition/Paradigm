import numpy as np

from paradigm.baselines import ExactCache
from paradigm.p0 import run_scenario
from paradigm.scenarios import deterministic_routing, repeated_workflows
from paradigm.selection import select_confidence_threshold


def test_threshold_selection_maximizes_coverage_at_target():
    y = np.asarray(["a", "a", "b", "b"])
    classes = np.asarray(["a", "b"])
    probs = np.asarray(
        [
            [0.95, 0.05],
            [0.70, 0.30],
            [0.45, 0.55],
            [0.10, 0.90],
        ]
    )
    reference = y.copy()
    selected = select_confidence_threshold(y, probs, classes, reference_predictions=reference, tolerance=0.0)
    assert selected.feasible
    assert selected.selective_accuracy == 1.0
    assert selected.coverage >= 0.5


def test_exact_cache_has_high_coverage_on_repeated_workflows():
    scenario = repeated_workflows(n_workflows=30, repeats=20, seed=5)
    x = np.stack([t.features for t in scenario.traces])
    y = np.asarray([t.action for t in scenario.traces])
    cache = ExactCache().fit(x[:400], y[:400])
    _, _, accepted = cache.predict_with_acceptance(x[400:])
    assert accepted.mean() > 0.75


def test_core_p0_deterministic_scenario_runs():
    scenario = deterministic_routing(n=1200, seed=7)
    outcome = run_scenario(scenario.traces, seed=7)
    assert "selected_reflex" in outcome["methods"]
    assert 0.0 <= outcome["methods"]["selected_reflex"]["coverage"] <= 1.0
    assert 0.0 <= outcome["methods"]["selected_reflex"]["ece"] <= 1.0
