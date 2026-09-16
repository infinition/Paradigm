from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.tree import DecisionTreeClassifier

from .gates import TrustedSubspaceGate
from .ood import AutoencoderOODGate, MahalanobisGate, NearestDistanceGate
from .trust_scenarios import TrustScenario


@dataclass(slots=True)
class GateResult:
    id_accept_rate: float
    off_manifold_false_accept_rate: float
    weak_pool_valid_accept_rate: float
    near_manifold_invalid_false_accept_rate: float
    ood_auroc: float


def _evaluate_gate(gate, scenario: TrustScenario) -> GateResult:
    id_accept = gate.accept(scenario.in_distribution)
    ood_accept = gate.accept(scenario.off_manifold_ood)
    weak_accept = gate.accept(scenario.weak_pool_valid)
    near_accept = gate.accept(scenario.near_manifold_invalid)

    score_id = np.asarray(gate.score(scenario.in_distribution), dtype=np.float64)
    score_ood = np.asarray(gate.score(scenario.off_manifold_ood), dtype=np.float64)
    y = np.concatenate([np.zeros(len(score_id)), np.ones(len(score_ood))])
    score = np.concatenate([score_id, score_ood])

    return GateResult(
        id_accept_rate=float(np.mean(id_accept)),
        off_manifold_false_accept_rate=float(np.mean(ood_accept)),
        weak_pool_valid_accept_rate=float(np.mean(weak_accept)),
        near_manifold_invalid_false_accept_rate=float(np.mean(near_accept)),
        ood_auroc=float(roc_auc_score(y, score)),
    )


def _confidence_baseline(scenario: TrustScenario, seed: int) -> tuple[GateResult, DecisionTreeClassifier, float]:
    model = DecisionTreeClassifier(max_depth=7, min_samples_leaf=6, random_state=seed)
    model.fit(scenario.trusted_train, scenario.trusted_labels)
    train_conf = np.max(model.predict_proba(scenario.trusted_train), axis=1)
    threshold = float(np.quantile(train_conf, 0.01))

    def accept(x: np.ndarray) -> np.ndarray:
        return np.max(model.predict_proba(x), axis=1) >= threshold

    def novelty_score(x: np.ndarray) -> np.ndarray:
        return 1.0 - np.max(model.predict_proba(x), axis=1)

    id_accept = accept(scenario.in_distribution)
    ood_accept = accept(scenario.off_manifold_ood)
    weak_accept = accept(scenario.weak_pool_valid)
    near_accept = accept(scenario.near_manifold_invalid)
    score_id = novelty_score(scenario.in_distribution)
    score_ood = novelty_score(scenario.off_manifold_ood)
    y = np.concatenate([np.zeros(len(score_id)), np.ones(len(score_ood))])
    score = np.concatenate([score_id, score_ood])

    return (
        GateResult(
            id_accept_rate=float(np.mean(id_accept)),
            off_manifold_false_accept_rate=float(np.mean(ood_accept)),
            weak_pool_valid_accept_rate=float(np.mean(weak_accept)),
            near_manifold_invalid_false_accept_rate=float(np.mean(near_accept)),
            ood_auroc=float(roc_auc_score(y, score)),
        ),
        model,
        threshold,
    )


def _poisoning_test(scenario: TrustScenario, seed: int, poison_fraction: float = 0.12) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    x = scenario.trusted_train.copy()
    y = scenario.trusted_labels.copy()
    poison_n = int(len(y) * poison_fraction)
    idx = rng.choice(len(y), size=poison_n, replace=False)
    classes = np.unique(y)
    for i in idx:
        alternatives = classes[classes != y[i]]
        y[i] = str(rng.choice(alternatives))

    clean = DecisionTreeClassifier(max_depth=7, min_samples_leaf=6, random_state=seed).fit(
        scenario.trusted_train, scenario.trusted_labels
    )
    poisoned = DecisionTreeClassifier(max_depth=7, min_samples_leaf=6, random_state=seed).fit(x, y)
    clean_acc = float(accuracy_score(scenario.in_distribution_labels, clean.predict(scenario.in_distribution)))
    poisoned_acc = float(accuracy_score(scenario.in_distribution_labels, poisoned.predict(scenario.in_distribution)))
    return {
        "poison_fraction": poison_fraction,
        "clean_accuracy": clean_acc,
        "poisoned_accuracy": poisoned_acc,
        "accuracy_drop": clean_acc - poisoned_acc,
        "input_space_gate_expected_to_detect_label_poisoning": False,
    }


def run_trusted_compilation_benchmark(scenario: TrustScenario, *, seed: int = 0) -> dict[str, object]:
    gates = {
        "nearest_distance": NearestDistanceGate(quantile=0.99).fit(scenario.trusted_train),
        "mahalanobis": MahalanobisGate(quantile=0.99).fit(scenario.trusted_train),
        "pca_trusted_subspace": TrustedSubspaceGate(variance=0.90, quantile=0.99).fit(scenario.trusted_train),
        "nonlinear_autoencoder": AutoencoderOODGate(
            bottleneck=3, quantile=0.99, random_state=seed, max_iter=700
        ).fit(scenario.trusted_train),
    }

    results = {name: asdict(_evaluate_gate(gate, scenario)) for name, gate in gates.items()}
    confidence, _, confidence_threshold = _confidence_baseline(scenario, seed)
    results["classifier_confidence"] = asdict(confidence)

    # A useful trusted gate should catch explicit off-manifold shifts without
    # rejecting most legitimate weak-pool novelty. Near-manifold invalid inputs
    # are a deliberate hard control and are not expected to be caught reliably.
    tradeoff = {}
    for name, metrics in results.items():
        tradeoff[name] = {
            "off_manifold_pass": bool(metrics["off_manifold_false_accept_rate"] <= 0.10),
            "weak_pool_pass": bool(metrics["weak_pool_valid_accept_rate"] >= 0.70),
            "id_retention_pass": bool(metrics["id_accept_rate"] >= 0.95),
        }
        tradeoff[name]["balanced_pass"] = bool(all(tradeoff[name].values()))

    return {
        "claim_level": "synthetic input-space OOD benchmark",
        "methods": results,
        "confidence_threshold": confidence_threshold,
        "tradeoff_gates": tradeoff,
        "poisoning_control": _poisoning_test(scenario, seed=seed + 17),
        "interpretation": (
            "Input-space trusted gates are proxies only. The benchmark tests whether they add OOD information beyond "
            "classifier confidence. It does not transfer the adapter-space guarantees or threat model of z-manifold."
        ),
    }
