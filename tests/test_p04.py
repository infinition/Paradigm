import pytest

from paradigm.compiler import ReflexCompiler
from paradigm.p04 import run_promotion_manifest_benchmark
from paradigm.promotion import PromotionCheck, PromotionManifest
from paradigm.reflex_space_scenarios import make_reflex_pool_scenario
from paradigm.registry import ActiveCandidateRegistry
from paradigm.scenarios import deterministic_routing


def test_p04_manifest_decisions_match_expected_on_small_scenario():
    scenario = make_reflex_pool_scenario(
        trusted_fit_n=28,
        trusted_calibration_n=14,
        candidate_n=20,
        n_train=1000,
        n_anchor=160,
        n_validation=420,
        n_weak_validation=320,
        seed=29,
    )
    result = run_promotion_manifest_benchmark(
        scenario,
        seed=29,
        aligned_search_trials=800,
    )
    assert result["observed_decisions"]["clean"] is True
    assert result["observed_decisions"]["poisoned"] is False
    assert result["observed_decisions"]["parameter_aligned"] is False


def test_registry_blocks_failed_manifest_and_supports_rollback():
    traces = deterministic_routing(n=500, seed=5).traces
    a = ReflexCompiler(backend="tree", random_state=1).fit(traces, name="a")
    b = ReflexCompiler(backend="tree", random_state=2).fit(traces, name="b")
    c = ReflexCompiler(backend="tree", random_state=3).fit(traces, name="c")
    registry = ActiveCandidateRegistry(active=a)

    failed = PromotionManifest(
        candidate_name="b",
        checks=[PromotionCheck("quality", False, 0.5, ">= 0.9")],
    )
    registry.stage(b)
    with pytest.raises(RuntimeError):
        registry.promote(failed)
    assert registry.active is a

    registry.reject("failed manifest", failed)
    passed = PromotionManifest(
        candidate_name="c",
        checks=[PromotionCheck("quality", True, 0.99, ">= 0.9")],
    )
    registry.stage(c)
    registry.promote(passed)
    assert registry.active is c
    registry.rollback()
    assert registry.active is a
