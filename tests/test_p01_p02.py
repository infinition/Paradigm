import numpy as np

from paradigm.deliberation import PerturbationDeliberator
from paradigm.ood import MahalanobisGate, NearestDistanceGate
from paradigm.p01 import run_measured_deliberation
from paradigm.p02 import run_trusted_compilation_benchmark
from paradigm.scenarios import deterministic_routing
from paradigm.trust_scenarios import make_trust_scenario


def test_deliberator_is_deterministic():
    solver = PerturbationDeliberator(probes=64, seed=3)
    x = np.asarray([0.2, 0.8, 0.1, 0.3, 0.9, 0.2])
    assert solver(x) == solver(x)


def test_measured_deliberation_pipeline_runs():
    scenario = deterministic_routing(n=900, seed=9)
    result = run_measured_deliberation(scenario.traces, seed=9, probes=64)
    assert result["metrics"]["coverage"] >= 0.0
    assert result["metrics"]["deliberative_latency_us"] > 0.0
    assert result["metrics"]["speedup_vs_deliberation"] > 0.0


def test_distance_gates_reject_far_shift():
    scenario = make_trust_scenario(n_train=700, n_test=240, seed=7)
    for gate in [NearestDistanceGate(0.99), MahalanobisGate(0.99)]:
        gate.fit(scenario.trusted_train)
        assert gate.accept(scenario.in_distribution).mean() > gate.accept(scenario.off_manifold_ood).mean()


def test_trusted_benchmark_runs():
    scenario = make_trust_scenario(n_train=800, n_test=220, seed=8)
    result = run_trusted_compilation_benchmark(scenario, seed=8)
    assert "pca_trusted_subspace" in result["methods"]
    assert result["methods"]["pca_trusted_subspace"]["ood_auroc"] >= 0.5
    assert result["poisoning_control"]["input_space_gate_expected_to_detect_label_poisoning"] is False


def test_reflex_signature_gate_and_p03_pipeline():
    from paradigm.p03 import run_reflex_space_benchmark
    from paradigm.reflex_space import PCASignatureGate
    from paradigm.reflex_space_scenarios import make_reflex_pool_scenario

    scenario = make_reflex_pool_scenario(
        trusted_fit_n=24,
        trusted_calibration_n=12,
        candidate_n=14,
        n_train=900,
        n_anchor=120,
        n_validation=260,
        n_weak_validation=240,
        seed=19,
    )
    gate = PCASignatureGate(variance=0.95, quantile=0.90).fit(
        scenario.parameter_signature(scenario.trusted_fit),
        scenario.parameter_signature(scenario.trusted_calibration),
    )
    assert gate.score(scenario.parameter_signature(scenario.clean_candidates)).shape == (14,)

    result = run_reflex_space_benchmark(
        scenario,
        seed=19,
        quantile=0.90,
        aligned_search_trials=500,
        behavior_control_trials=400,
    )
    assert result["parameter_space"]["poison_auroc"] >= 0.5
    assert result["behavior_space"]["poison_auroc"] >= 0.5
    assert "parameter_aligned_attack" in result
    assert "behavior_aligned_control" in result
