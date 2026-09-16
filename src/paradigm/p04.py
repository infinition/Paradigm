from __future__ import annotations

import numpy as np

from .evaluation import expected_calibration_error
from .promotion import PromotionManifest, PromotionPolicy
from .reflex_space import PCASignatureGate
from .reflex_space_scenarios import ReflexPoolScenario


def _candidate_metrics(
    scenario: ReflexPoolScenario,
    active_vector: np.ndarray,
    candidate_vector: np.ndarray,
    parameter_gate: PCASignatureGate,
    behavior_gate: PCASignatureGate,
    protected_idx: np.ndarray,
) -> dict[str, float | bool]:
    probabilities = scenario.probabilities(candidate_vector, scenario.validation_x)[0]
    predictions = np.argmax(probabilities, axis=1)
    classes = np.arange(scenario.n_classes).astype(str)

    accuracy = float(np.mean(predictions == scenario.validation_y))
    ece = expected_calibration_error(
        scenario.validation_y.astype(str), probabilities, classes
    )

    active_prob = scenario.probabilities(active_vector, scenario.anchor_x)[0]
    candidate_prob = scenario.probabilities(candidate_vector, scenario.anchor_x)[0]
    active_pred = np.argmax(active_prob, axis=1)
    candidate_pred = np.argmax(candidate_prob, axis=1)
    disagreement = float(np.mean(active_pred != candidate_pred))
    total_variation = float(np.mean(0.5 * np.sum(np.abs(active_prob - candidate_prob), axis=1)))

    class_accuracy = []
    for class_id in range(scenario.n_classes):
        mask = scenario.validation_y == class_id
        class_accuracy.append(float(np.mean(predictions[mask] == class_id)))

    protected_accuracy = float(
        np.mean(predictions[protected_idx] == scenario.validation_y[protected_idx])
    )

    return {
        "accuracy": accuracy,
        "ece": float(ece),
        "parameter_space_accepted": bool(
            parameter_gate.accept(scenario.parameter_signature(candidate_vector))[0]
        ),
        "behavior_space_accepted": bool(
            behavior_gate.accept(scenario.behavior_signature(candidate_vector))[0]
        ),
        "label_disagreement": disagreement,
        "total_variation": total_variation,
        "minimum_class_accuracy": float(min(class_accuracy)),
        "protected_slice_accuracy": protected_accuracy,
    }


def _manifest_from_metrics(
    policy: PromotionPolicy,
    name: str,
    metrics: dict[str, float | bool],
    **metadata: object,
) -> PromotionManifest:
    return policy.build_manifest(
        candidate_name=name,
        accuracy=float(metrics["accuracy"]),
        ece=float(metrics["ece"]),
        parameter_space_accepted=bool(metrics["parameter_space_accepted"]),
        behavior_space_accepted=bool(metrics["behavior_space_accepted"]),
        label_disagreement=float(metrics["label_disagreement"]),
        total_variation=float(metrics["total_variation"]),
        minimum_class_accuracy=float(metrics["minimum_class_accuracy"]),
        protected_slice_accuracy=float(metrics["protected_slice_accuracy"]),
        metadata=metadata,
    )


def _search_parameter_aligned_candidate(
    scenario: ReflexPoolScenario,
    gate: PCASignatureGate,
    protected_idx: np.ndarray,
    *,
    seed: int,
    trials: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    mean_vector = np.mean(scenario.trusted_fit, axis=0)
    z_mean = gate.pca.transform(mean_vector[None, :])[0]
    z_cal = gate.pca.transform(scenario.trusted_calibration)
    radius = np.linalg.norm(z_cal - z_mean[None, :], axis=1)
    radius_95 = float(np.quantile(radius, 0.95))

    best = mean_vector.copy()
    best_protected = 1.0
    for _ in range(int(trials)):
        direction = rng.normal(size=gate.pca.n_components_)
        direction /= np.linalg.norm(direction) + 1e-12
        distance = rng.uniform(0.20 * radius_95, 1.20 * radius_95)
        z = z_mean + distance * direction
        vector = gate.pca.inverse_transform(z.reshape(1, -1))[0]
        prediction = scenario.predict(vector, scenario.validation_x)[0]
        overall = float(np.mean(prediction == scenario.validation_y))
        if overall < 0.94:
            continue
        protected = float(np.mean(prediction[protected_idx] == scenario.validation_y[protected_idx]))
        if protected < best_protected:
            best = vector
            best_protected = protected
    return best


def _select_clean_candidate(
    scenario: ReflexPoolScenario,
    active_vector: np.ndarray,
    parameter_gate: PCASignatureGate,
    behavior_gate: PCASignatureGate,
    protected_idx: np.ndarray,
    policy: PromotionPolicy,
) -> tuple[np.ndarray, PromotionManifest, dict[str, float | bool]]:
    fallback: tuple[np.ndarray, PromotionManifest, dict[str, float | bool]] | None = None
    for vector in scenario.clean_candidates:
        metrics = _candidate_metrics(
            scenario, active_vector, vector, parameter_gate, behavior_gate, protected_idx
        )
        manifest = _manifest_from_metrics(policy, "clean_candidate", metrics)
        if fallback is None:
            fallback = (vector, manifest, metrics)
        if manifest.approved:
            return vector, manifest, metrics
    if fallback is None:
        raise RuntimeError("No clean candidates are available.")
    return fallback


def _select_valid_weak_reject(
    scenario: ReflexPoolScenario,
    active_vector: np.ndarray,
    parameter_gate: PCASignatureGate,
    behavior_gate: PCASignatureGate,
    protected_idx: np.ndarray,
    policy: PromotionPolicy,
) -> tuple[int, np.ndarray, PromotionManifest, dict[str, float | bool]]:
    for idx, vector in enumerate(scenario.weak_pool_candidates):
        metrics = _candidate_metrics(
            scenario, active_vector, vector, parameter_gate, behavior_gate, protected_idx
        )
        quality_pass = (
            float(metrics["accuracy"]) >= policy.minimum_accuracy
            and float(metrics["ece"]) <= policy.maximum_ece
            and float(metrics["minimum_class_accuracy"]) >= policy.minimum_class_accuracy
            and float(metrics["protected_slice_accuracy"]) >= policy.minimum_protected_slice_accuracy
        )
        trust_fail = not (
            bool(metrics["parameter_space_accepted"]) and bool(metrics["behavior_space_accepted"])
        )
        if quality_pass and trust_fail:
            return idx, vector, _manifest_from_metrics(policy, "weak_pool_valid", metrics), metrics
    raise RuntimeError("No valid weak-pool candidate was rejected by the current trust gates.")


def run_promotion_manifest_benchmark(
    scenario: ReflexPoolScenario,
    *,
    seed: int = 1337,
    aligned_search_trials: int = 10000,
) -> dict[str, object]:
    policy = PromotionPolicy()
    active_vector = np.mean(scenario.trusted_fit, axis=0)

    parameter_gate = PCASignatureGate(variance=0.95, quantile=0.95).fit(
        scenario.parameter_signature(scenario.trusted_fit),
        scenario.parameter_signature(scenario.trusted_calibration),
    )
    behavior_gate = PCASignatureGate(variance=0.95, quantile=0.95).fit(
        scenario.behavior_signature(scenario.trusted_fit),
        scenario.behavior_signature(scenario.trusted_calibration),
    )

    protected_idx = np.where(
        (scenario.validation_y == 2) & (scenario.validation_x[:, 0] > 0.0)
    )[0]
    if len(protected_idx) < 20:
        raise RuntimeError("Protected slice is too small for the benchmark.")

    _, clean_manifest, clean_metrics = _select_clean_candidate(
        scenario, active_vector, parameter_gate, behavior_gate, protected_idx, policy
    )

    poison_vector = scenario.poisoned_candidates[0]
    poison_metrics = _candidate_metrics(
        scenario, active_vector, poison_vector, parameter_gate, behavior_gate, protected_idx
    )
    poison_manifest = _manifest_from_metrics(policy, "poisoned_candidate", poison_metrics)

    weak_idx, weak_vector, weak_manifest, weak_metrics = _select_valid_weak_reject(
        scenario, active_vector, parameter_gate, behavior_gate, protected_idx, policy
    )

    split_a = max(1, len(scenario.weak_pool_candidates) // 3)
    split_b = max(split_a + 1, len(scenario.weak_pool_candidates) // 2)
    augmented_parameter_gate = PCASignatureGate(variance=0.95, quantile=0.95).fit(
        scenario.parameter_signature(
            np.concatenate([scenario.trusted_fit, scenario.weak_pool_candidates[:split_a]], axis=0)
        ),
        scenario.parameter_signature(
            np.concatenate(
                [scenario.trusted_calibration, scenario.weak_pool_candidates[split_a:split_b]], axis=0
            )
        ),
    )
    augmented_behavior_gate = PCASignatureGate(variance=0.95, quantile=0.95).fit(
        scenario.behavior_signature(
            np.concatenate([scenario.trusted_fit, scenario.weak_pool_candidates[:split_a]], axis=0)
        ),
        scenario.behavior_signature(
            np.concatenate(
                [scenario.trusted_calibration, scenario.weak_pool_candidates[split_a:split_b]], axis=0
            )
        ),
    )
    weak_recheck_metrics = _candidate_metrics(
        scenario,
        active_vector,
        weak_vector,
        augmented_parameter_gate,
        augmented_behavior_gate,
        protected_idx,
    )
    weak_recheck_manifest = _manifest_from_metrics(
        policy,
        "weak_pool_valid_after_pool_expansion",
        weak_recheck_metrics,
        original_candidate_index=weak_idx,
    )

    aligned_vector = _search_parameter_aligned_candidate(
        scenario,
        parameter_gate,
        protected_idx,
        seed=seed + 211,
        trials=aligned_search_trials,
    )
    aligned_metrics = _candidate_metrics(
        scenario, active_vector, aligned_vector, parameter_gate, behavior_gate, protected_idx
    )
    aligned_manifest = _manifest_from_metrics(
        policy, "parameter_aligned_candidate", aligned_metrics
    )

    return {
        "claim_level": "synthetic multi-signal promotion manifest benchmark",
        "policy": {
            "minimum_accuracy": policy.minimum_accuracy,
            "maximum_ece": policy.maximum_ece,
            "maximum_label_disagreement": policy.maximum_label_disagreement,
            "maximum_total_variation": policy.maximum_total_variation,
            "minimum_class_accuracy": policy.minimum_class_accuracy,
            "minimum_protected_slice_accuracy": policy.minimum_protected_slice_accuracy,
        },
        "protected_slice_size": int(len(protected_idx)),
        "cases": {
            "clean": {"metrics": clean_metrics, "manifest": clean_manifest.to_dict()},
            "poisoned": {"metrics": poison_metrics, "manifest": poison_manifest.to_dict()},
            "weak_pool_before_expansion": {
                "candidate_index": int(weak_idx),
                "metrics": weak_metrics,
                "manifest": weak_manifest.to_dict(),
            },
            "weak_pool_after_expansion": {
                "candidate_index": int(weak_idx),
                "metrics": weak_recheck_metrics,
                "manifest": weak_recheck_manifest.to_dict(),
            },
            "parameter_aligned": {
                "metrics": aligned_metrics,
                "manifest": aligned_manifest.to_dict(),
            },
        },
        "expected_decisions": {
            "clean": True,
            "poisoned": False,
            "weak_pool_before_expansion": False,
            "weak_pool_after_expansion": True,
            "parameter_aligned": False,
        },
        "observed_decisions": {
            "clean": clean_manifest.approved,
            "poisoned": poison_manifest.approved,
            "weak_pool_before_expansion": weak_manifest.approved,
            "weak_pool_after_expansion": weak_recheck_manifest.approved,
            "parameter_aligned": aligned_manifest.approved,
        },
    }
