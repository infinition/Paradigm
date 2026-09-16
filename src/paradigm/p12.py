from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .bounded import SpectralDriftContract, rms
from .p11 import (
    MLPParams,
    _accuracy,
    _adapt_sequence,
    _base_train,
    _delta_signature,
    _forward,
    _grads,
    _make_domains,
)


RISK_EPSILON = {
    "low": 0.030,
    "medium": 0.015,
    "high": 0.0075,
}


@dataclass(slots=True)
class CandidateEvidence:
    family: int
    seed: int
    epsilon: float
    parameter_signature: np.ndarray
    behavior_signature: np.ndarray
    current_accuracy: float
    protected_accuracy: float
    minimum_class_accuracy: float
    subgroup_accuracy: float
    max_step_drift: float


class CosinePrototypeGate:
    """Angular gate for normalized update or behavior signatures.

    The prototype is fitted on validated signatures from one behavior family.
    The acceptance threshold is calibrated on a disjoint validated set and
    includes a spread-derived margin. This is better matched to normalized
    directional deltas than Euclidean reconstruction residuals.
    """

    def __init__(self, *, quantile: float = 0.05, spread_margin: float = 2.0) -> None:
        self.quantile = float(quantile)
        self.spread_margin = float(spread_margin)
        self.prototype_: np.ndarray | None = None
        self.threshold_: float | None = None

    def fit(self, trusted_fit: np.ndarray, trusted_calibration: np.ndarray) -> "CosinePrototypeGate":
        fit = np.asarray(trusted_fit, dtype=np.float64)
        cal = np.asarray(trusted_calibration, dtype=np.float64)
        if fit.ndim != 2 or cal.ndim != 2 or fit.shape[1] != cal.shape[1]:
            raise ValueError("Expected two 2D signature arrays with matching dimensions.")
        proto = np.mean(fit, axis=0)
        proto /= np.linalg.norm(proto) + 1e-12
        self.prototype_ = proto
        sims = self.score(cal)
        self.threshold_ = float(np.quantile(sims, self.quantile) - self.spread_margin * np.std(sims))
        return self

    def score(self, signatures: np.ndarray) -> np.ndarray:
        if self.prototype_ is None:
            raise RuntimeError("Gate must be fitted before scoring.")
        x = np.asarray(signatures, dtype=np.float64)
        if x.ndim == 1:
            x = x[None, :]
        x = x / (np.linalg.norm(x, axis=1, keepdims=True) + 1e-12)
        return x @ self.prototype_

    def accept(self, signatures: np.ndarray) -> np.ndarray:
        if self.threshold_ is None:
            raise RuntimeError("Gate must be fitted before acceptance checks.")
        return self.score(signatures) >= self.threshold_


def _fixed_anchor_domains(*, n: int = 96, n_features: int = 24) -> list[np.ndarray]:
    """Return a common anchor suite with the same transforms as P1.1.

    Every candidate is evaluated on the same states. This avoids comparing
    behavior vectors whose coordinates refer to different examples.
    """

    task_rng = np.random.default_rng(20260916)
    anchor_rng = np.random.default_rng(12012026)
    latent = anchor_rng.normal(size=(n, n_features))
    # Consume the teacher draws used by _make_domains before generating transforms.
    task_rng.normal(size=(40, n_features))
    task_rng.normal(size=(4, 40))
    domains = [latent]
    current = np.eye(n_features)
    for _ in range(3):
        q, _ = np.linalg.qr(task_rng.normal(size=(n_features, n_features)))
        current = current @ q
        domains.append(latent @ current)
    return domains


def _behavior_delta_signature(
    before: MLPParams,
    after: MLPParams,
    anchors: list[np.ndarray],
    family: int,
) -> np.ndarray:
    """Behavior delta on both protected and family-specific anchor states."""

    pieces: list[np.ndarray] = []
    for domain in (0, family):
        _, _, pb = _forward(before, anchors[domain])
        _, _, pa = _forward(after, anchors[domain])
        pieces.append((pa - pb).ravel())
    delta = np.concatenate(pieces)
    norm = np.linalg.norm(delta)
    if norm > 1e-12:
        delta = delta / norm
    return delta


def _minimum_class_accuracy(p: MLPParams, x: np.ndarray, y: np.ndarray) -> float:
    _, _, probs = _forward(p, x)
    pred = np.argmax(probs, axis=1)
    values = []
    for cls in np.unique(y):
        mask = y == cls
        values.append(float(np.mean(pred[mask] == y[mask])))
    return float(np.min(values))


def _class_accuracy(p: MLPParams, x: np.ndarray, y: np.ndarray, cls: int = 0) -> float:
    mask = y == cls
    if not np.any(mask):
        return 0.0
    _, _, probs = _forward(p, x[mask])
    return float(np.mean(np.argmax(probs, axis=1) == y[mask]))


def _adapt_family_candidate(
    parent: MLPParams,
    domains: list[np.ndarray],
    y: np.ndarray,
    *,
    family: int,
    seed: int,
    epsilon: float,
    steps: int = 90,
    replay: bool = True,
    poison: bool = False,
    poison_fraction: float = 0.75,
    anchors: list[np.ndarray] | None = None,
) -> CandidateEvidence:
    """Adapt one shared parent into one family-specific candidate.

    Candidate seeds vary minibatch sampling only. All candidates in a family
    therefore belong to the same parameter lineage, matching the intended
    active -> candidate lifecycle more closely than independently initialized models.
    """

    train_idx = np.arange(0, 5000)
    eval_idx = np.arange(5000, 7000)
    p = parent.copy()
    rng = np.random.default_rng(seed)
    anchors = anchors or _fixed_anchor_domains()
    contracts = {
        "w1": SpectralDriftContract(p.w1.shape, epsilon=epsilon, exact_scale=True, strict_denominator=True),
        "w2": SpectralDriftContract(p.w2.shape, epsilon=epsilon, exact_scale=True, strict_denominator=True),
    }
    max_step_drift = 0.0

    for _ in range(steps):
        idx = rng.integers(0, len(train_idx), size=176)
        xb = domains[family][train_idx[idx]]
        yb = y[train_idx[idx]].copy()

        if poison:
            # Targeted corruption keeps most labels intact and concentrates damage
            # on one semantic subgroup instead of turning the whole task random.
            target = yb == 0
            corrupt = target & (rng.random(len(yb)) < poison_fraction)
            yb[corrupt] = 1

        if replay:
            ridx = rng.integers(0, len(train_idx), size=64)
            xb = np.concatenate([xb, domains[0][train_idx[ridx]]], axis=0)
            yb = np.concatenate([yb, y[train_idx[ridx]]], axis=0)

        g, layer_inputs = _grads(p, xb, yb)
        u1, r1 = contracts["w1"].step(g.w1, layer_inputs[0])
        u2, r2 = contracts["w2"].step(g.w2, layer_inputs[1])
        p.w1 += u1
        p.w2 += u2
        p.b1 += -0.002 * g.b1 / (rms(g.b1) + 1e-12)
        p.b2 += -0.002 * g.b2 / (rms(g.b2) + 1e-12)
        max_step_drift = max(
            max_step_drift,
            float(r1.measured_preactivation_drift),
            float(r2.measured_preactivation_drift),
        )

    x_current = domains[family][eval_idx]
    y_eval = y[eval_idx]
    x_protected = domains[0][eval_idx]
    return CandidateEvidence(
        family=int(family),
        seed=int(seed),
        epsilon=float(epsilon),
        parameter_signature=_delta_signature(parent, p),
        behavior_signature=_behavior_delta_signature(parent, p, anchors, family),
        current_accuracy=_accuracy(p, x_current, y_eval),
        protected_accuracy=_accuracy(p, x_protected, y_eval),
        minimum_class_accuracy=_minimum_class_accuracy(p, x_current, y_eval),
        subgroup_accuracy=_class_accuracy(p, x_current, y_eval, cls=0),
        max_step_drift=float(max_step_drift),
    )


def _fit_signature_gate(signatures: list[np.ndarray]) -> tuple[CosinePrototypeGate, np.ndarray, np.ndarray]:
    x = np.stack(signatures)
    if len(x) < 8:
        raise ValueError("At least eight signatures are required for fit/calibration/test splits.")
    n_fit = max(4, len(x) // 2)
    n_cal = max(2, (len(x) - n_fit) // 2)
    fit = x[:n_fit]
    cal = x[n_fit:n_fit + n_cal]
    test = x[n_fit + n_cal:]
    if len(test) < 2:
        test = x[-2:]
    gate = CosinePrototypeGate().fit(fit, cal)
    return gate, cal, test


def _calibrated_floor(values: list[float], q: float = 0.05, spread_margin: float = 2.0) -> float:
    x = np.asarray(values, dtype=np.float64)
    floor = np.quantile(x, q) - spread_margin * np.std(x)
    return float(np.clip(floor, 0.0, 1.0))


def _family_trust_benchmark(*, steps: int = 90) -> dict[str, Any]:
    # One parent lineage is shared by all candidates. This is the natural unit
    # for comparing update deltas in an active/candidate system.
    domains, y = _make_domains(4242)
    train_idx = np.arange(0, 5000)
    parent = _base_train(5151, domains[0][train_idx], y[train_idx], steps=650)
    anchors = _fixed_anchor_domains()
    family_risk = {1: "low", 2: "medium", 3: "high"}
    clean_seeds = [
        101, 113, 127, 139, 151, 163, 179, 191, 211, 227, 239, 251,
        263, 277, 293, 307, 311, 331, 347, 359, 373, 389, 397, 409,
    ]
    poison_seeds = [431, 443, 457, 467, 479, 491]

    clean_by_family: dict[int, list[CandidateEvidence]] = {}
    poison_by_family: dict[int, list[CandidateEvidence]] = {}
    for family in (1, 2, 3):
        eps = RISK_EPSILON[family_risk[family]]
        clean_by_family[family] = [
            _adapt_family_candidate(
                parent,
                domains,
                y,
                family=family,
                seed=seed,
                epsilon=eps,
                steps=steps,
                replay=True,
                anchors=anchors,
            )
            for seed in clean_seeds
        ]
        poison_by_family[family] = [
            _adapt_family_candidate(
                parent,
                domains,
                y,
                family=family,
                seed=seed,
                epsilon=eps,
                steps=steps,
                replay=True,
                poison=True,
                anchors=anchors,
            )
            for seed in poison_seeds
        ]

    results: dict[str, Any] = {}
    for family in (1, 2, 3):
        clean = clean_by_family[family]
        poison = poison_by_family[family]
        pgate, pcal, ptest = _fit_signature_gate([c.parameter_signature for c in clean])
        bgate, bcal, btest = _fit_signature_gate([c.behavior_signature for c in clean])

        # Use the clean candidates that were not used to define the earliest fit
        # samples to calibrate semantic quality floors. The floor is intentionally
        # data-derived rather than hand-picked per family.
        # Match the semantic calibration pool to the middle calibration region
        # of the larger validated family sample. Held-out candidates remain unseen.
        semantic_pool = clean[12:18]
        floors = {
            "current_accuracy": _calibrated_floor([c.current_accuracy for c in semantic_pool]),
            "protected_accuracy": _calibrated_floor([c.protected_accuracy for c in semantic_pool]),
            "minimum_class_accuracy": _calibrated_floor([c.minimum_class_accuracy for c in semantic_pool]),
            "subgroup_accuracy": _calibrated_floor([c.subgroup_accuracy for c in semantic_pool]),
        }

        heldout = clean[-6:]
        cross = [c for f, candidates in clean_by_family.items() if f != family for c in candidates[-6:]]

        def gate_rates(candidates: list[CandidateEvidence]) -> dict[str, float]:
            ps = np.stack([c.parameter_signature for c in candidates])
            bs = np.stack([c.behavior_signature for c in candidates])
            pa = pgate.accept(ps)
            ba = bgate.accept(bs)
            semantic = np.asarray([
                c.current_accuracy >= floors["current_accuracy"]
                and c.protected_accuracy >= floors["protected_accuracy"]
                and c.minimum_class_accuracy >= floors["minimum_class_accuracy"]
                and c.subgroup_accuracy >= floors["subgroup_accuracy"]
                for c in candidates
            ], dtype=bool)
            return {
                "parameter_acceptance": float(np.mean(pa)),
                "behavior_acceptance": float(np.mean(ba)),
                "geometry_joint_acceptance": float(np.mean(pa & ba)),
                "semantic_acceptance": float(np.mean(semantic)),
                "full_manifest_acceptance": float(np.mean(pa & ba & semantic)),
            }

        results[f"family_{family}"] = {
            "risk": family_risk[family],
            "epsilon": RISK_EPSILON[family_risk[family]],
            "semantic_floors": floors,
            "parameter_gate": {
                "type": "cosine_prototype",
                "threshold": float(pgate.threshold_),
                "calibration_similarity_mean": float(np.mean(pgate.score(pcal))),
                "heldout_similarity_mean": float(np.mean(pgate.score(ptest))),
            },
            "behavior_gate": {
                "type": "cosine_prototype",
                "threshold": float(bgate.threshold_),
                "calibration_similarity_mean": float(np.mean(bgate.score(bcal))),
                "heldout_similarity_mean": float(np.mean(bgate.score(btest))),
            },
            "heldout_clean": gate_rates(heldout),
            "targeted_poison": gate_rates(poison),
            "cross_family": gate_rates(cross),
            "mean_metrics": {
                "current_accuracy": float(np.mean([c.current_accuracy for c in clean])),
                "protected_accuracy": float(np.mean([c.protected_accuracy for c in clean])),
                "minimum_class_accuracy": float(np.mean([c.minimum_class_accuracy for c in clean])),
                "subgroup_accuracy": float(np.mean([c.subgroup_accuracy for c in clean])),
                "max_step_drift": float(np.mean([c.max_step_drift for c in clean])),
            },
        }
    return results


def _risk_epsilon_sweep(*, steps: int = 90) -> dict[str, Any]:
    domains, y = _make_domains(4242)
    train_idx = np.arange(0, 5000)
    parent = _base_train(5151, domains[0][train_idx], y[train_idx], steps=650)
    anchors = _fixed_anchor_domains()
    family = 2
    out: dict[str, Any] = {}
    for risk, epsilon in RISK_EPSILON.items():
        candidate = _adapt_family_candidate(
            parent,
            domains,
            y,
            family=family,
            seed=909,
            epsilon=epsilon,
            steps=steps,
            replay=True,
            anchors=anchors,
        )
        out[risk] = {
            "epsilon": epsilon,
            "current_accuracy": candidate.current_accuracy,
            "protected_accuracy": candidate.protected_accuracy,
            "minimum_class_accuracy": candidate.minimum_class_accuracy,
            "max_step_drift": candidate.max_step_drift,
        }
    return {
        "controlled_family": family,
        "note": "Same parent, data, minibatch seed, replay policy, and steps. Only epsilon changes.",
        "results": out,
    }


def _drift_replay_sequence(seed: int, *, steps: int = 150, epsilon: float = 0.025) -> dict[str, Any]:
    domains, y = _make_domains(seed)
    rng = np.random.default_rng(seed + 1000)
    train_idx = np.arange(0, 5000)
    eval_idx = np.arange(5000, 7000)
    p = _base_train(seed + 2000, domains[0][train_idx], y[train_idx])
    previous_best = [_accuracy(p, domains[0][eval_idx], y[eval_idx])]
    replay_x: list[np.ndarray] = [domains[0][train_idx[:1200]]]
    replay_y: list[np.ndarray] = [y[train_idx[:1200]]]
    history: list[dict[str, float]] = []

    for task in range(1, 4):
        contracts = {
            "w1": SpectralDriftContract(p.w1.shape, epsilon=epsilon, exact_scale=True, strict_denominator=True),
            "w2": SpectralDriftContract(p.w2.shape, epsilon=epsilon, exact_scale=True, strict_denominator=True),
        }
        max_step_drift = 0.0
        for _ in range(steps):
            idx = rng.integers(0, len(train_idx), size=192)
            xb = domains[task][train_idx[idx]]
            yb = y[train_idx[idx]]
            rx, ry = [], []
            for _ in range(64):
                d = int(rng.integers(0, len(replay_x)))
                pos = int(rng.integers(0, len(replay_x[d])))
                rx.append(replay_x[d][pos])
                ry.append(replay_y[d][pos])
            xb = np.concatenate([xb, np.asarray(rx)], axis=0)
            yb = np.concatenate([yb, np.asarray(ry)], axis=0)
            g, layer_inputs = _grads(p, xb, yb)
            u1, r1 = contracts["w1"].step(g.w1, layer_inputs[0])
            u2, r2 = contracts["w2"].step(g.w2, layer_inputs[1])
            p.w1 += u1
            p.w2 += u2
            p.b1 += -0.002 * g.b1 / (rms(g.b1) + 1e-12)
            p.b2 += -0.002 * g.b2 / (rms(g.b2) + 1e-12)
            max_step_drift = max(
                max_step_drift,
                float(r1.measured_preactivation_drift),
                float(r2.measured_preactivation_drift),
            )

        replay_x.append(domains[task][train_idx[:1200]])
        replay_y.append(y[train_idx[:1200]])
        accs = [_accuracy(p, domains[j][eval_idx], y[eval_idx]) for j in range(task + 1)]
        while len(previous_best) < len(accs):
            previous_best.append(accs[len(previous_best)])
        forgetting = []
        for j, acc in enumerate(accs[:-1]):
            forgetting.append(max(0.0, previous_best[j] - acc))
            previous_best[j] = max(previous_best[j], acc)
        previous_best[-1] = max(previous_best[-1], accs[-1])
        history.append({
            "current_accuracy": float(accs[-1]),
            "mean_seen_accuracy": float(np.mean(accs)),
            "worst_seen_accuracy": float(np.min(accs)),
            "mean_forgetting": float(np.mean(forgetting)) if forgetting else 0.0,
            "max_step_preactivation_drift": float(max_step_drift),
        })

    return {
        "final_current_accuracy": history[-1]["current_accuracy"],
        "final_mean_seen_accuracy": history[-1]["mean_seen_accuracy"],
        "final_worst_seen_accuracy": history[-1]["worst_seen_accuracy"],
        "final_mean_forgetting": history[-1]["mean_forgetting"],
        "mean_max_step_drift": float(np.mean([h["max_step_preactivation_drift"] for h in history])),
        "history": history,
    }


def _combined_baseline(seeds: list[int], *, steps: int = 150) -> dict[str, Any]:
    methods: dict[str, list[dict[str, Any]]] = {
        "replay": [_adapt_sequence(seed, "replay", steps=steps) for seed in seeds],
        "drift_contract": [_adapt_sequence(seed, "drift_contract", steps=steps) for seed in seeds],
        "drift_contract_plus_replay": [_drift_replay_sequence(seed, steps=steps) for seed in seeds],
    }
    keys = [
        "final_current_accuracy",
        "final_mean_seen_accuracy",
        "final_worst_seen_accuracy",
        "final_mean_forgetting",
        "mean_max_step_drift",
    ]
    out: dict[str, Any] = {}
    for method, runs in methods.items():
        summary: dict[str, Any] = {}
        for key in keys:
            vals = np.asarray([r[key] for r in runs], dtype=np.float64)
            summary[key] = {"mean": float(vals.mean()), "std": float(vals.std())}
        out[method] = summary
    return out


def run_p12_benchmark(*, seeds: list[int] | None = None, steps: int = 90) -> dict[str, Any]:
    seeds = seeds or [11, 23, 41]
    return {
        "claim_level": "synthetic family-conditioned trusted plasticity benchmark",
        "scope_note": (
            "P1.2 tests family-conditioned parameter and behavior update spaces within one shared model lineage, "
            "semantic subgroup checks, risk-conditioned Drift Contract budgets, and a replay plus Drift Contract baseline. "
            "Geometry is used as rejection or routing evidence, never as a standalone promotion certificate."
        ),
        "research_sources": {
            "drift_contract": "https://github.com/infinition/drift-contract",
            "drift_preprint": "https://infinition.github.io/infinition/assets/papers/drift-bounded-spectral-updates.pdf",
            "z_manifold": "https://github.com/infinition/z-manifold",
            "z_manifold_paper": "https://arxiv.org/abs/2607.05300",
        },
        "family_conditioned_trust": _family_trust_benchmark(steps=steps),
        "risk_conditioned_epsilon": _risk_epsilon_sweep(steps=steps),
        "combined_baseline": _combined_baseline(seeds, steps=max(60, int(steps * 1.25))),
        "seeds": seeds,
    }
