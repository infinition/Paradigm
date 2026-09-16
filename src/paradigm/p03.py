from __future__ import annotations

from dataclasses import asdict

import numpy as np
from sklearn.metrics import roc_auc_score

from .reflex_space import PCASignatureGate
from .reflex_space_scenarios import ReflexPoolScenario


def _space_metrics(
    scenario: ReflexPoolScenario,
    *,
    signature: str,
    variance: float,
    quantile: float,
    augment_weak: bool = False,
) -> tuple[dict[str, object], PCASignatureGate]:
    transform = scenario.parameter_signature if signature == "parameter" else scenario.behavior_signature

    fit_pool = scenario.trusted_fit
    calibration_pool = scenario.trusted_calibration
    weak_eval = scenario.weak_pool_candidates
    if augment_weak:
        split_a = max(1, len(scenario.weak_pool_candidates) // 3)
        split_b = max(split_a + 1, len(scenario.weak_pool_candidates) // 2)
        fit_pool = np.concatenate([fit_pool, scenario.weak_pool_candidates[:split_a]], axis=0)
        calibration_pool = np.concatenate(
            [calibration_pool, scenario.weak_pool_candidates[split_a:split_b]], axis=0
        )
        weak_eval = scenario.weak_pool_candidates[split_b:]

    gate = PCASignatureGate(variance=variance, quantile=quantile).fit(
        transform(fit_pool), transform(calibration_pool)
    )

    def acceptance(vectors: np.ndarray) -> float:
        return float(np.mean(gate.accept(transform(vectors))))

    clean_score = gate.score(transform(scenario.clean_candidates))
    poison_score = gate.score(transform(scenario.poisoned_candidates))
    auc = roc_auc_score(
        np.concatenate([np.zeros(len(clean_score)), np.ones(len(poison_score))]),
        np.concatenate([clean_score, poison_score]),
    )

    metrics: dict[str, object] = {
        "gate": asdict(gate.report()),
        "clean_accept_rate": acceptance(scenario.clean_candidates),
        "poison_false_accept_rate": acceptance(scenario.poisoned_candidates),
        "weak_pool_valid_accept_rate": acceptance(weak_eval),
        "poison_auroc": float(auc),
        "mean_clean_accuracy": float(np.mean(scenario.accuracy(scenario.clean_candidates))),
        "mean_poisoned_accuracy": float(np.mean(scenario.accuracy(scenario.poisoned_candidates))),
        "mean_weak_pool_accuracy": float(np.mean(scenario.accuracy(weak_eval, weak=True))),
        "augmented_with_weak_pool": bool(augment_weak),
    }
    return metrics, gate


def _parameter_aligned_attack(
    scenario: ReflexPoolScenario,
    gate: PCASignatureGate,
    behavior_gate: PCASignatureGate,
    *,
    seed: int,
    search_trials: int = 8000,
) -> dict[str, object]:
    """Search inside the trusted parameter subspace for a targeted failure.

    This is an adaptive stress control. The candidate is explicitly generated
    inside the fitted parameter subspace, so a residual-only parameter gate is
    expected to accept it. We then ask whether an independent behavior-space
    gate notices the resulting behavioral shift.
    """

    rng = np.random.default_rng(seed)
    mean_vector = np.mean(scenario.trusted_fit, axis=0)
    z_mean = gate.pca.transform(mean_vector[None, :])[0]
    z_cal = gate.pca.transform(scenario.trusted_calibration)
    radii = np.linalg.norm(z_cal - z_mean[None, :], axis=1)
    radius_95 = float(np.quantile(radii, 0.95))

    mean_prob = scenario.probabilities(mean_vector, scenario.validation_x)[0]
    sorted_prob = np.sort(mean_prob, axis=1)
    margin = sorted_prob[:, -1] - sorted_prob[:, -2]
    target_idx = np.where((scenario.validation_y == 0) & (margin < 0.40))[0]
    if len(target_idx) < 5:
        target_idx = np.where((scenario.validation_y == 0) & (margin < 0.60))[0]

    best_vector = mean_vector
    best_target_accuracy = 1.0
    best_overall_accuracy = float(scenario.accuracy(mean_vector)[0])

    for _ in range(int(search_trials)):
        direction = rng.normal(size=gate.pca.n_components_)
        direction /= np.linalg.norm(direction) + 1e-12
        radius = rng.uniform(0.20 * radius_95, 1.15 * radius_95)
        z = z_mean + radius * direction
        vector = gate.pca.inverse_transform(z.reshape(1, -1))[0]
        overall = float(scenario.accuracy(vector)[0])
        if overall < 0.90:
            continue
        pred = scenario.predict(vector, scenario.validation_x[target_idx])[0]
        target_accuracy = float(np.mean(pred == scenario.validation_y[target_idx]))
        if target_accuracy < best_target_accuracy:
            best_target_accuracy = target_accuracy
            best_overall_accuracy = overall
            best_vector = vector

    parameter_score = float(gate.score(best_vector)[0])
    behavior_signature = scenario.behavior_signature(best_vector)
    behavior_score = float(behavior_gate.score(behavior_signature)[0])
    return {
        "target_size": int(len(target_idx)),
        "overall_accuracy": best_overall_accuracy,
        "target_slice_accuracy": best_target_accuracy,
        "parameter_score": parameter_score,
        "parameter_threshold": float(gate.threshold_),
        "parameter_gate_accepts": bool(parameter_score <= float(gate.threshold_)),
        "behavior_score": behavior_score,
        "behavior_threshold": float(behavior_gate.threshold_),
        "behavior_gate_accepts": bool(behavior_score <= float(behavior_gate.threshold_)),
    }


def _behavior_aligned_control(
    scenario: ReflexPoolScenario,
    behavior_gate: PCASignatureGate,
    *,
    seed: int,
    search_trials: int = 6000,
) -> dict[str, object]:
    """Construct a valid-probability signature from trusted behaviors only.

    Convex mixtures of trusted probability vectors remain inside the affine
    trusted family and are valid probability distributions. The control asks
    whether such an accepted signature can still hide a weak subgroup. It does
    not claim that the mixture corresponds to one trained executable model.
    """

    rng = np.random.default_rng(seed)
    trusted_prob = scenario.probabilities(scenario.trusted_fit, scenario.anchor_x)
    mean_prob = np.mean(trusted_prob, axis=0)
    sorted_prob = np.sort(mean_prob, axis=1)
    margin = sorted_prob[:, -1] - sorted_prob[:, -2]
    target_idx = np.where((scenario.anchor_y == 0) & (margin < 0.60))[0]
    baseline_target = float(np.mean(np.argmax(mean_prob[target_idx], axis=1) == scenario.anchor_y[target_idx]))

    best_signature = mean_prob.reshape(-1)
    best_target = baseline_target
    best_overall = float(np.mean(np.argmax(mean_prob, axis=1) == scenario.anchor_y))

    for _ in range(int(search_trials)):
        size = min(5, len(trusted_prob))
        idx = rng.choice(len(trusted_prob), size=size, replace=False)
        weights = rng.dirichlet(np.full(size, 0.25))
        mixture = np.tensordot(weights, trusted_prob[idx], axes=(0, 0))
        pred = np.argmax(mixture, axis=1)
        overall = float(np.mean(pred == scenario.anchor_y))
        if overall < 0.93:
            continue
        target = float(np.mean(pred[target_idx] == scenario.anchor_y[target_idx]))
        if target < best_target:
            best_target = target
            best_overall = overall
            best_signature = mixture.reshape(-1)

    score = float(behavior_gate.score(best_signature)[0])
    return {
        "signature_only_control": True,
        "target_size": int(len(target_idx)),
        "ensemble_mean_target_accuracy": baseline_target,
        "candidate_target_slice_accuracy": best_target,
        "candidate_overall_anchor_accuracy": best_overall,
        "behavior_score": score,
        "behavior_threshold": float(behavior_gate.threshold_),
        "behavior_gate_accepts": bool(score <= float(behavior_gate.threshold_)),
        "interpretation": (
            "A residual-only behavior subspace is not a semantic certificate. This control uses a convex mixture "
            "of trusted probability signatures and may not correspond to a single executable trained reflex."
        ),
    }


def run_reflex_space_benchmark(
    scenario: ReflexPoolScenario,
    *,
    seed: int = 1337,
    variance: float = 0.95,
    quantile: float = 0.95,
    aligned_search_trials: int = 8000,
    behavior_control_trials: int = 6000,
) -> dict[str, object]:
    parameter, parameter_gate = _space_metrics(
        scenario, signature="parameter", variance=variance, quantile=quantile
    )
    behavior, behavior_gate = _space_metrics(
        scenario, signature="behavior", variance=variance, quantile=quantile
    )
    parameter_augmented, _ = _space_metrics(
        scenario, signature="parameter", variance=variance, quantile=quantile, augment_weak=True
    )
    behavior_augmented, _ = _space_metrics(
        scenario, signature="behavior", variance=variance, quantile=quantile, augment_weak=True
    )

    return {
        "claim_level": "synthetic trusted reflex parameter/behavior-space benchmark",
        "parameter_space": parameter,
        "behavior_space": behavior,
        "weak_pool_recovery": {
            "parameter_space": parameter_augmented,
            "behavior_space": behavior_augmented,
        },
        "parameter_aligned_attack": _parameter_aligned_attack(
            scenario,
            parameter_gate,
            behavior_gate,
            seed=seed + 71,
            search_trials=aligned_search_trials,
        ),
        "behavior_aligned_control": _behavior_aligned_control(
            scenario,
            behavior_gate,
            seed=seed + 97,
            search_trials=behavior_control_trials,
        ),
        "interpretation": (
            "Moving trust from input space to reflex signatures makes label-poisoned candidates visible in this "
            "synthetic task. The result also reproduces the weak-pool problem: valid novel reflexes can be rejected "
            "until the trusted pool is expanded. Parameter-subspace membership alone is not sufficient, because an "
            "adaptive candidate can be generated inside the parameter subspace while harming a target slice. "
            "Behavior-space residuals catch that constructed parameter-space attack here, but the signature-only "
            "control shows that behavior-space geometry is not a semantic certificate either."
        ),
    }
