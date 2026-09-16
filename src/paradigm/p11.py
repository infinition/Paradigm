from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np

from .bounded import AdamMatrix, SpectralDriftContract, rms
from .reflex_space import PCASignatureGate


@dataclass
class MLPParams:
    w1: np.ndarray
    b1: np.ndarray
    w2: np.ndarray
    b2: np.ndarray

    def copy(self) -> "MLPParams":
        return MLPParams(self.w1.copy(), self.b1.copy(), self.w2.copy(), self.b2.copy())


def _init_mlp(rng: np.random.Generator, n_features: int, hidden: int, n_classes: int) -> MLPParams:
    return MLPParams(
        rng.normal(scale=np.sqrt(2.0 / n_features), size=(hidden, n_features)),
        np.zeros(hidden, dtype=np.float64),
        rng.normal(scale=np.sqrt(2.0 / hidden), size=(n_classes, hidden)),
        np.zeros(n_classes, dtype=np.float64),
    )


def _forward(p: MLPParams, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    z1 = x @ p.w1.T + p.b1
    h = np.maximum(z1, 0.0)
    logits = h @ p.w2.T + p.b2
    logits -= np.max(logits, axis=1, keepdims=True)
    exp = np.exp(logits)
    probs = exp / np.sum(exp, axis=1, keepdims=True)
    return z1, h, probs


def _grads(p: MLPParams, x: np.ndarray, y: np.ndarray) -> tuple[MLPParams, tuple[np.ndarray, np.ndarray]]:
    z1, h, probs = _forward(p, x)
    dl = probs.copy()
    dl[np.arange(len(y)), y.astype(int)] -= 1.0
    dl /= len(y)
    gw2 = dl.T @ h
    gb2 = np.sum(dl, axis=0)
    dh = dl @ p.w2
    dz1 = dh * (z1 > 0.0)
    gw1 = dz1.T @ x
    gb1 = np.sum(dz1, axis=0)
    return MLPParams(gw1, gb1, gw2, gb2), (x, h)


def _accuracy(p: MLPParams, x: np.ndarray, y: np.ndarray) -> float:
    _, _, probs = _forward(p, x)
    return float(np.mean(np.argmax(probs, axis=1) == y))


def _flatten(p: MLPParams) -> np.ndarray:
    return np.concatenate([p.w1.ravel(), p.b1.ravel(), p.w2.ravel(), p.b2.ravel()])


def _delta_signature(before: MLPParams, after: MLPParams) -> np.ndarray:
    d = _flatten(after) - _flatten(before)
    norm = np.linalg.norm(d)
    if norm > 1e-12:
        d = d / norm
    return d


def _make_domains(seed: int, *, n: int = 7000, n_features: int = 24, n_classes: int = 4) -> tuple[list[np.ndarray], np.ndarray]:
    # The task geometry is fixed across seeds. Seeds change sampled examples and label noise,
    # not the teacher or domain transforms. This matters for update-space experiments: a
    # trusted pool should represent repeated solutions to the same task family.
    task_rng = np.random.default_rng(20260916)
    data_rng = np.random.default_rng(seed)
    latent = data_rng.normal(size=(n, n_features))
    t1 = task_rng.normal(size=(40, n_features))
    t2 = task_rng.normal(size=(n_classes, 40))
    hidden = np.tanh(latent @ t1.T)
    y = np.argmax(hidden @ t2.T + 0.15 * data_rng.normal(size=(n, n_classes)), axis=1)

    domains = [latent]
    current = np.eye(n_features)
    for _ in range(3):
        q, _ = np.linalg.qr(task_rng.normal(size=(n_features, n_features)))
        current = current @ q
        domains.append(latent @ current)
    return domains, y.astype(int)


def _base_train(seed: int, x: np.ndarray, y: np.ndarray, *, hidden: int = 48, steps: int = 700) -> MLPParams:
    rng = np.random.default_rng(seed)
    p = _init_mlp(rng, x.shape[1], hidden, int(np.max(y)) + 1)
    opts = {
        "w1": AdamMatrix(p.w1.shape, learning_rate=0.006),
        "b1": AdamMatrix((1, len(p.b1)), learning_rate=0.006),
        "w2": AdamMatrix(p.w2.shape, learning_rate=0.006),
        "b2": AdamMatrix((1, len(p.b2)), learning_rate=0.006),
    }
    for _ in range(steps):
        idx = rng.integers(0, len(x), size=256)
        g, _ = _grads(p, x[idx], y[idx])
        p.w1 += opts["w1"].step(g.w1)
        p.b1 += opts["b1"].step(g.b1[None, :])[0]
        p.w2 += opts["w2"].step(g.w2)
        p.b2 += opts["b2"].step(g.b2[None, :])[0]
    return p


def _importance(p: MLPParams, x: np.ndarray, y: np.ndarray, rng: np.random.Generator, *, batches: int = 12) -> MLPParams:
    acc = MLPParams(np.zeros_like(p.w1), np.zeros_like(p.b1), np.zeros_like(p.w2), np.zeros_like(p.b2))
    for _ in range(batches):
        idx = rng.integers(0, len(x), size=256)
        g, _ = _grads(p, x[idx], y[idx])
        acc.w1 += g.w1 * g.w1
        acc.b1 += g.b1 * g.b1
        acc.w2 += g.w2 * g.w2
        acc.b2 += g.b2 * g.b2
    for a in [acc.w1, acc.b1, acc.w2, acc.b2]:
        a /= batches
        a /= float(np.mean(a) + 1e-12)
    return acc


def _add_ewc(g: MLPParams, p: MLPParams, ref: MLPParams, imp: MLPParams, strength: float) -> None:
    g.w1 += strength * imp.w1 * (p.w1 - ref.w1)
    g.b1 += strength * imp.b1 * (p.b1 - ref.b1)
    g.w2 += strength * imp.w2 * (p.w2 - ref.w2)
    g.b2 += strength * imp.b2 * (p.b2 - ref.b2)


def _adapt_sequence(seed: int, method: str, *, steps: int = 150) -> dict[str, Any]:
    domains, y = _make_domains(seed)
    rng = np.random.default_rng(seed + 1000)
    train_idx = np.arange(0, 5000)
    eval_idx = np.arange(5000, 7000)
    base = _base_train(seed + 2000, domains[0][train_idx], y[train_idx])
    p = base.copy()
    history: list[dict[str, Any]] = []
    deltas: list[np.ndarray] = []
    previous_best = [_accuracy(p, domains[0][eval_idx], y[eval_idx])]
    replay_x: list[np.ndarray] = [domains[0][train_idx[:1200]]]
    replay_y: list[np.ndarray] = [y[train_idx[:1200]]]

    ewc_ref = p.copy()
    ewc_imp = _importance(p, domains[0][train_idx], y[train_idx], rng)

    for task in range(1, 4):
        before = p.copy()
        t0 = perf_counter()
        max_step_drift = 0.0

        if method == "periodic_retrain":
            # Refit from the original initialization distribution on all seen domains.
            xs = np.concatenate([domains[j][train_idx] for j in range(task + 1)], axis=0)
            ys = np.concatenate([y[train_idx] for _ in range(task + 1)], axis=0)
            p = _base_train(seed + 3000 + task, xs, ys, steps=steps * 3)
        else:
            adam = None
            if method in {"adam", "replay", "ewc"}:
                adam = {
                    "w1": AdamMatrix(p.w1.shape, learning_rate=0.004),
                    "b1": AdamMatrix((1, len(p.b1)), learning_rate=0.004),
                    "w2": AdamMatrix(p.w2.shape, learning_rate=0.004),
                    "b2": AdamMatrix((1, len(p.b2)), learning_rate=0.004),
                }
            contracts = None
            if method == "drift_contract":
                contracts = {
                    "w1": SpectralDriftContract(p.w1.shape, epsilon=0.025, exact_scale=True, strict_denominator=True),
                    "w2": SpectralDriftContract(p.w2.shape, epsilon=0.025, exact_scale=True, strict_denominator=True),
                }

            for _ in range(steps):
                idx = rng.integers(0, len(train_idx), size=192)
                xb = domains[task][train_idx[idx]]
                yb = y[train_idx[idx]]
                if method == "replay":
                    ridx_domain = rng.integers(0, len(replay_x), size=64)
                    # Draw a balanced small replay set across prior domains.
                    rx_parts, ry_parts = [], []
                    for d in ridx_domain:
                        pos = rng.integers(0, len(replay_x[d]))
                        rx_parts.append(replay_x[d][pos])
                        ry_parts.append(replay_y[d][pos])
                    xb = np.concatenate([xb, np.asarray(rx_parts)], axis=0)
                    yb = np.concatenate([yb, np.asarray(ry_parts)], axis=0)

                g, layer_inputs = _grads(p, xb, yb)
                if method == "ewc":
                    _add_ewc(g, p, ewc_ref, ewc_imp, strength=0.006)

                if method == "sgd":
                    lr = 0.025
                    u1, u2 = -lr * g.w1, -lr * g.w2
                    ub1, ub2 = -lr * g.b1, -lr * g.b2
                    step_drift = max(rms(layer_inputs[0] @ u1.T), rms(layer_inputs[1] @ u2.T))
                elif method == "drift_contract":
                    assert contracts is not None
                    u1, r1 = contracts["w1"].step(g.w1, layer_inputs[0])
                    u2, r2 = contracts["w2"].step(g.w2, layer_inputs[1])
                    # Biases are bounded separately as a small fraction of epsilon.
                    ub1 = -0.002 * g.b1 / (rms(g.b1) + 1e-12)
                    ub2 = -0.002 * g.b2 / (rms(g.b2) + 1e-12)
                    step_drift = max(r1.measured_preactivation_drift, r2.measured_preactivation_drift)
                else:
                    assert adam is not None
                    u1 = adam["w1"].step(g.w1)
                    ub1 = adam["b1"].step(g.b1[None, :])[0]
                    u2 = adam["w2"].step(g.w2)
                    ub2 = adam["b2"].step(g.b2[None, :])[0]
                    step_drift = max(rms(layer_inputs[0] @ u1.T), rms(layer_inputs[1] @ u2.T))
                p.w1 += u1
                p.b1 += ub1
                p.w2 += u2
                p.b2 += ub2
                max_step_drift = max(max_step_drift, float(step_drift))

        seconds = perf_counter() - t0
        deltas.append(_delta_signature(before, p))
        accs = [_accuracy(p, domains[j][eval_idx], y[eval_idx]) for j in range(task + 1)]
        while len(previous_best) < len(accs):
            previous_best.append(accs[len(previous_best)])
        forgetting = []
        for j, acc in enumerate(accs[:-1]):
            forgetting.append(max(0.0, previous_best[j] - acc))
            previous_best[j] = max(previous_best[j], acc)
        previous_best[-1] = max(previous_best[-1], accs[-1])
        history.append({
            "task": task,
            "accuracies_seen": [float(v) for v in accs],
            "current_accuracy": float(accs[-1]),
            "mean_seen_accuracy": float(np.mean(accs)),
            "worst_seen_accuracy": float(np.min(accs)),
            "mean_forgetting": float(np.mean(forgetting)) if forgetting else 0.0,
            "max_step_preactivation_drift": None if method == "periodic_retrain" else float(max_step_drift),
            "adapt_seconds": float(seconds),
        })

        if method == "replay":
            replay_x.append(domains[task][train_idx[:1200]])
            replay_y.append(y[train_idx[:1200]])
        if method == "ewc":
            ewc_ref = p.copy()
            ewc_imp = _importance(p, domains[task][train_idx], y[train_idx], rng)

    return {
        "base_accuracy": float(_accuracy(base, domains[0][eval_idx], y[eval_idx])),
        "history": history,
        "final_mean_seen_accuracy": history[-1]["mean_seen_accuracy"],
        "final_current_accuracy": history[-1]["current_accuracy"],
        "final_worst_seen_accuracy": history[-1]["worst_seen_accuracy"],
        "total_adapt_seconds": float(sum(h["adapt_seconds"] for h in history)),
        "mean_max_step_drift": (
            None
            if method == "periodic_retrain"
            else float(np.mean([h["max_step_preactivation_drift"] for h in history]))
        ),
        "final_mean_forgetting": float(history[-1]["mean_forgetting"]),
        "delta_signatures": [d.tolist() for d in deltas],
    }


def _aggregate_methods(seeds: list[int]) -> dict[str, Any]:
    methods = ["sgd", "adam", "replay", "ewc", "periodic_retrain", "drift_contract"]
    out: dict[str, Any] = {}
    for method in methods:
        runs = [_adapt_sequence(seed, method) for seed in seeds]
        summary: dict[str, Any] = {}
        for key in [
            "final_mean_seen_accuracy",
            "final_current_accuracy",
            "final_worst_seen_accuracy",
            "final_mean_forgetting",
            "total_adapt_seconds",
        ]:
            vals = np.asarray([r[key] for r in runs], dtype=np.float64)
            summary[key] = {"mean": float(vals.mean()), "std": float(vals.std())}
        if method == "periodic_retrain":
            summary["mean_max_step_drift"] = None
        else:
            vals = np.asarray([r["mean_max_step_drift"] for r in runs], dtype=np.float64)
            summary["mean_max_step_drift"] = {"mean": float(vals.mean()), "std": float(vals.std())}
        summary["runs"] = [
            {key: value for key, value in run.items() if key != "delta_signatures"}
            for run in runs
        ]
        out[method] = summary
    return out


def _poisoned_contract_delta(seed: int, *, poison_fraction: float = 0.35) -> np.ndarray:
    domains, y = _make_domains(seed)
    train_idx = np.arange(0, 5000)
    base = _base_train(seed + 2000, domains[0][train_idx], y[train_idx])
    p = base.copy()
    rng = np.random.default_rng(seed + 9000)
    contracts = {
        "w1": SpectralDriftContract(p.w1.shape, epsilon=0.025, exact_scale=True, strict_denominator=True),
        "w2": SpectralDriftContract(p.w2.shape, epsilon=0.025, exact_scale=True, strict_denominator=True),
    }
    for _ in range(150):
        idx = rng.integers(0, len(train_idx), size=192)
        xb = domains[1][train_idx[idx]]
        yb = y[train_idx[idx]].copy()
        mask = rng.random(len(yb)) < poison_fraction
        yb[mask] = (yb[mask] + rng.integers(1, 4, size=np.sum(mask))) % 4
        g, layer_inputs = _grads(p, xb, yb)
        u1, _ = contracts["w1"].step(g.w1, layer_inputs[0])
        u2, _ = contracts["w2"].step(g.w2, layer_inputs[1])
        p.w1 += u1
        p.w2 += u2
        p.b1 += -0.002 * g.b1 / (rms(g.b1) + 1e-12)
        p.b2 += -0.002 * g.b2 / (rms(g.b2) + 1e-12)
    return _delta_signature(base, p)


def _trusted_update_space(seeds: list[int]) -> dict[str, Any]:
    # Explicit neural update deltas. Pool uses clean Drift Contract updates only.
    clean: list[np.ndarray] = []
    weak: list[np.ndarray] = []
    for seed in seeds:
        run = _adapt_sequence(seed, "drift_contract")
        ds = [np.asarray(v, dtype=np.float64) for v in run["delta_signatures"]]
        clean.extend(ds[:2])
        weak.append(ds[2])
    poisoned = [_poisoned_contract_delta(seed) for seed in seeds]

    clean_arr = np.stack(clean)
    weak_arr = np.stack(weak)
    poison_arr = np.stack(poisoned)
    # Deterministic split of validated clean deltas into fit/calibration/test.
    fit = clean_arr[: max(4, len(clean_arr) // 2)]
    cal = clean_arr[max(4, len(clean_arr) // 2): -2]
    if len(cal) < 2:
        cal = clean_arr[-4:-2]
    test = clean_arr[-2:]
    gate = PCASignatureGate(variance=0.95, quantile=0.99).fit(fit, cal)

    def rate(x: np.ndarray) -> float:
        return float(np.mean(gate.accept(x)))

    before = {
        "clean_heldout_acceptance": rate(test),
        "poison_acceptance": rate(poison_arr),
        "novel_shift_acceptance": rate(weak_arr),
        "report": {
            "threshold": gate.report().threshold,
            "n_components": gate.report().n_components,
            "variance_retained": gate.report().variance_retained,
        },
    }

    # Simulate validated pool expansion with part of the legitimate novel shift.
    weak_for_fit = weak_arr[:-2] if len(weak_arr) > 2 else weak_arr[:1]
    expanded = np.concatenate([clean_arr, weak_for_fit], axis=0)
    # Keep at least two calibration samples whenever the pool size permits it.
    n_cal = 4 if len(expanded) >= 8 else 2
    split = max(2, len(expanded) - n_cal)
    gate2 = PCASignatureGate(variance=0.95, quantile=0.99).fit(expanded[:split], expanded[split:])
    after = {
        "novel_shift_acceptance": float(np.mean(gate2.accept(weak_arr))),
        "poison_acceptance": float(np.mean(gate2.accept(poison_arr))),
    }
    return {
        "signature": "L2-normalized flattened neural parameter delta",
        "trusted_pool": "clean Drift Contract task-1/task-2 updates",
        "before_pool_expansion": before,
        "after_pool_expansion": after,
    }


def run_p11_benchmark(*, seeds: list[int] | None = None) -> dict[str, Any]:
    seeds = seeds or [11, 23, 41, 77]
    return {
        "claim_level": "synthetic multi-layer continual reflex benchmark",
        "scope_note": (
            "P1.1 compares common continual-adaptation baselines with a Drift Contract transfer on a small NumPy MLP. "
            "The update-space experiment uses explicit neural parameter deltas and is evidence for Paradigm only, not a transferred guarantee from z-manifold."
        ),
        "research_sources": {
            "drift_contract": "https://github.com/infinition/drift-contract",
            "drift_preprint": "https://infinition.github.io/infinition/assets/papers/drift-bounded-spectral-updates.pdf",
            "z_manifold": "https://github.com/infinition/z-manifold",
            "z_manifold_paper": "https://arxiv.org/abs/2607.05300",
        },
        "seeds": seeds,
        "continual_adaptation": _aggregate_methods(seeds),
        "trusted_update_space": _trusted_update_space(seeds),
    }
