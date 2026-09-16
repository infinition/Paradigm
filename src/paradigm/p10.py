from __future__ import annotations

from dataclasses import asdict
from typing import Any

import numpy as np

from .bounded import (
    AdamMatrix,
    SpectralDriftContract,
    linear_accuracy,
    rms,
    softmax_gradient,
)


def _bound_check(seed: int, *, trials: int = 100, epsilon: float = 0.01) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    results: dict[str, Any] = {}
    for dout, din in [(8, 64), (64, 64), (128, 64)]:
        ratios_eps: list[float] = []
        ratios_bound: list[float] = []
        spectral_norms: list[float] = []
        for _ in range(trials):
            gradient = rng.normal(size=(dout, din))
            x = rng.normal(size=(512, din))
            contract = SpectralDriftContract(
                (dout, din),
                epsilon=epsilon,
                exact_scale=True,
                strict_denominator=True,
            )
            _, report = contract.step(gradient, x)
            ratios_eps.append(report.ratio_to_epsilon)
            ratios_bound.append(report.ratio_to_bound)
            spectral_norms.append(report.spectral_norm)
        key = f"{dout}x{din}"
        results[key] = {
            "mean_ratio_to_epsilon": float(np.mean(ratios_eps)),
            "p99_ratio_to_epsilon": float(np.quantile(ratios_eps, 0.99)),
            "max_ratio_to_epsilon": float(np.max(ratios_eps)),
            "mean_ratio_to_bound": float(np.mean(ratios_bound)),
            "p99_ratio_to_bound": float(np.quantile(ratios_bound, 0.99)),
            "max_ratio_to_bound": float(np.max(ratios_bound)),
            "mean_orthogonalized_spectral_norm": float(np.mean(spectral_norms)),
            "bound_respected": bool(np.max(ratios_bound) <= 1.0 + 1e-9),
        }
    return results


def _risk_budget_check(seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    shape = (16, 48)
    gradient = rng.normal(size=shape)
    x = rng.normal(size=(1024, shape[1]))
    records: dict[str, Any] = {}
    for label, epsilon in [("high_risk", 0.003), ("medium_risk", 0.01), ("low_risk", 0.03)]:
        contract = SpectralDriftContract(shape, epsilon=epsilon, exact_scale=True)
        _, report = contract.step(gradient, x)
        records[label] = asdict(report)
    records["drift_ratio_low_to_high"] = (
        records["low_risk"]["measured_preactivation_drift"]
        / records["high_risk"]["measured_preactivation_drift"]
    )
    return records


def _train_base_linear(
    rng: np.random.Generator,
    x: np.ndarray,
    y: np.ndarray,
    *,
    n_classes: int,
    steps: int = 700,
) -> np.ndarray:
    weights = rng.normal(scale=0.01, size=(n_classes, x.shape[1]))
    optimizer = AdamMatrix(weights.shape, learning_rate=0.03)
    for _ in range(steps):
        idx = rng.integers(0, len(x), size=256)
        weights += optimizer.step(softmax_gradient(weights, x[idx], y[idx]))
    return weights


def _shock_adaptation_single(seed: int, *, steps: int = 300) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    n_features = 32
    n_classes = 4
    n = 12000
    teacher = rng.normal(size=(n_classes, n_features))
    latent = rng.normal(size=(n, n_features))
    y = np.argmax(latent @ teacher.T, axis=1)
    old_x = latent
    q, _ = np.linalg.qr(rng.normal(size=(n_features, n_features)))
    new_x = latent @ q

    base = _train_base_linear(rng, old_x, y, n_classes=n_classes)
    eval_n = 3000
    baseline = {
        "old_accuracy": linear_accuracy(base, old_x[:eval_n], y[:eval_n]),
        "shifted_accuracy_before_adaptation": linear_accuracy(base, new_x[:eval_n], y[:eval_n]),
    }

    methods: dict[str, Any] = {}
    for method in ["adam", "adam_replay", "contract_fast", "contract_conservative"]:
        weights = base.copy()
        max_step_drift = 0.0
        mean_step_drift: list[float] = []
        max_ratio_to_bound = 0.0
        if method.startswith("adam"):
            optimizer: Any = AdamMatrix(weights.shape, learning_rate=0.01)
        else:
            epsilon = 0.10 if method == "contract_fast" else 0.03
            optimizer = SpectralDriftContract(
                weights.shape,
                epsilon=epsilon,
                exact_scale=True,
                strict_denominator=True,
            )

        for _ in range(steps):
            idx_new = rng.integers(0, n, size=256)
            if method == "adam_replay":
                idx_old = rng.integers(0, n, size=64)
                x_batch = np.concatenate([new_x[idx_new], old_x[idx_old]], axis=0)
                y_batch = np.concatenate([y[idx_new], y[idx_old]], axis=0)
                update = optimizer.step(softmax_gradient(weights, x_batch, y_batch))
                drift_input = new_x[idx_new]
                step_drift = rms(drift_input @ update.T)
            elif method.startswith("contract"):
                x_batch = new_x[idx_new]
                y_batch = y[idx_new]
                update, report = optimizer.step(
                    softmax_gradient(weights, x_batch, y_batch),
                    x_batch,
                )
                step_drift = report.measured_preactivation_drift
                max_ratio_to_bound = max(max_ratio_to_bound, report.ratio_to_bound)
            else:
                x_batch = new_x[idx_new]
                y_batch = y[idx_new]
                update = optimizer.step(softmax_gradient(weights, x_batch, y_batch))
                step_drift = rms(x_batch @ update.T)
            weights += update
            max_step_drift = max(max_step_drift, float(step_drift))
            mean_step_drift.append(float(step_drift))

        methods[method] = {
            "shifted_accuracy_after_adaptation": linear_accuracy(weights, new_x[:eval_n], y[:eval_n]),
            "old_accuracy_after_adaptation": linear_accuracy(weights, old_x[:eval_n], y[:eval_n]),
            "max_step_preactivation_drift": float(max_step_drift),
            "mean_step_preactivation_drift": float(np.mean(mean_step_drift)),
            "max_ratio_to_theoretical_bound": float(max_ratio_to_bound) if method.startswith("contract") else None,
        }
    return {"baseline": baseline, "methods": methods}


def _aggregate_shock_runs(seeds: list[int]) -> dict[str, Any]:
    runs = [_shock_adaptation_single(seed) for seed in seeds]
    names = list(runs[0]["methods"].keys())
    summary: dict[str, Any] = {}
    for name in names:
        metrics: dict[str, Any] = {}
        for key in [
            "shifted_accuracy_after_adaptation",
            "old_accuracy_after_adaptation",
            "max_step_preactivation_drift",
            "mean_step_preactivation_drift",
        ]:
            values = np.asarray([run["methods"][name][key] for run in runs], dtype=np.float64)
            metrics[key] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
            }
        if name.startswith("contract"):
            values = np.asarray(
                [run["methods"][name]["max_ratio_to_theoretical_bound"] for run in runs],
                dtype=np.float64,
            )
            metrics["max_ratio_to_theoretical_bound"] = {
                "mean": float(np.mean(values)),
                "max": float(np.max(values)),
            }
        summary[name] = metrics

    baseline_old = np.asarray([run["baseline"]["old_accuracy"] for run in runs])
    baseline_shift = np.asarray([run["baseline"]["shifted_accuracy_before_adaptation"] for run in runs])
    return {
        "seeds": seeds,
        "baseline": {
            "old_accuracy_mean": float(np.mean(baseline_old)),
            "shifted_accuracy_before_adaptation_mean": float(np.mean(baseline_shift)),
        },
        "methods": summary,
        "runs": runs,
    }


def run_bounded_plasticity_benchmark(*, seed: int = 2026) -> dict[str, Any]:
    shock_seeds = [11, 23, 41, 77, 101]
    return {
        "claim_level": "synthetic mechanical transfer test of Drift Contract geometry to reflex adaptation",
        "research_source": {
            "repository": "https://github.com/infinition/drift-contract",
            "preprint": "https://infinition.github.io/infinition/assets/papers/drift-bounded-spectral-updates.pdf",
            "status": "public preprint; arXiv submission pending approval",
        },
        "scope_note": (
            "The original work studies deep local learning. This benchmark does not transfer its accuracy claims. "
            "It tests the matrix update rule, the stated per-step drift bound, and a small continual-reflex adaptation hypothesis."
        ),
        "bound_check": _bound_check(seed),
        "risk_conditioned_budget": _risk_budget_check(seed + 1),
        "distribution_shock": _aggregate_shock_runs(shock_seeds),
    }
