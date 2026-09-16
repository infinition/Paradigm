from __future__ import annotations

import numpy as np

from paradigm.bounded import SpectralDriftContract
from paradigm.p10 import run_bounded_plasticity_benchmark


def test_exact_spectral_contract_respects_measured_bound():
    rng = np.random.default_rng(7)
    for shape in [(8, 64), (64, 64), (128, 64)]:
        contract = SpectralDriftContract(shape, epsilon=0.01, exact_scale=True, strict_denominator=True)
        gradient = rng.normal(size=shape)
        x = rng.normal(size=(1024, shape[1]))
        _, report = contract.step(gradient, x)
        assert report.ratio_to_bound <= 1.0 + 1e-9


def test_smaller_risk_budget_produces_smaller_step_drift():
    rng = np.random.default_rng(8)
    shape = (12, 40)
    gradient = rng.normal(size=shape)
    x = rng.normal(size=(512, shape[1]))
    low = SpectralDriftContract(shape, epsilon=0.003)
    high = SpectralDriftContract(shape, epsilon=0.03)
    _, low_report = low.step(gradient, x)
    _, high_report = high.step(gradient, x)
    assert high_report.measured_preactivation_drift > low_report.measured_preactivation_drift * 9.5


def test_p10_bound_checks_pass():
    result = run_bounded_plasticity_benchmark(seed=19)
    assert all(item["bound_respected"] for item in result["bound_check"].values())
