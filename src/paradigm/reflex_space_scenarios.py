from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression


@dataclass(slots=True)
class ReflexPoolScenario:
    trusted_fit: np.ndarray
    trusted_calibration: np.ndarray
    clean_candidates: np.ndarray
    poisoned_candidates: np.ndarray
    weak_pool_candidates: np.ndarray
    anchor_x: np.ndarray
    anchor_y: np.ndarray
    validation_x: np.ndarray
    validation_y: np.ndarray
    weak_validation_x: np.ndarray
    weak_validation_y: np.ndarray
    n_features: int
    n_classes: int

    def probabilities(self, vectors: np.ndarray, x: np.ndarray) -> np.ndarray:
        vectors = np.asarray(vectors, dtype=np.float64)
        if vectors.ndim == 1:
            vectors = vectors[None, :]
        x = np.asarray(x, dtype=np.float64)
        weight_size = self.n_classes * self.n_features
        w = vectors[:, :weight_size].reshape(-1, self.n_classes, self.n_features)
        b = vectors[:, weight_size:].reshape(-1, self.n_classes)
        logits = np.einsum("nd,mkd->mnk", x, w) + b[:, None, :]
        logits -= np.max(logits, axis=2, keepdims=True)
        exp = np.exp(logits)
        return exp / np.sum(exp, axis=2, keepdims=True)

    def predict(self, vectors: np.ndarray, x: np.ndarray) -> np.ndarray:
        return np.argmax(self.probabilities(vectors, x), axis=2)

    def parameter_signature(self, vectors: np.ndarray) -> np.ndarray:
        vectors = np.asarray(vectors, dtype=np.float64)
        return vectors[None, :] if vectors.ndim == 1 else vectors

    def behavior_signature(self, vectors: np.ndarray) -> np.ndarray:
        p = self.probabilities(vectors, self.anchor_x)
        return p.reshape(p.shape[0], -1)

    def accuracy(self, vectors: np.ndarray, *, weak: bool = False) -> np.ndarray:
        x = self.weak_validation_x if weak else self.validation_x
        y = self.weak_validation_y if weak else self.validation_y
        pred = self.predict(vectors, x)
        return np.mean(pred == y[None, :], axis=1)


def make_reflex_pool_scenario(
    *,
    trusted_fit_n: int = 60,
    trusted_calibration_n: int = 30,
    candidate_n: int = 50,
    n_train: int = 1800,
    n_anchor: int = 400,
    n_validation: int = 1000,
    n_weak_validation: int = 900,
    n_features: int = 8,
    n_classes: int = 3,
    poison_fraction: float = 0.16,
    seed: int = 1337,
) -> ReflexPoolScenario:
    """Create validated reflex pools and controlled candidate families.

    Every reflex is a small multinomial linear policy. Trusted and clean pools
    are trained from bootstrap samples of the same valid task. Poisoned
    candidates receive label corruption. Weak-pool candidates remain valid but
    are trained with additional shifted support that the original trusted pool
    does not cover well.
    """

    if n_classes != 3:
        raise ValueError("The current P0.3 scenario is defined for exactly three classes.")
    rng = np.random.default_rng(seed)
    true_w = rng.normal(size=(n_classes, n_features))
    true_b = rng.normal(scale=0.25, size=n_classes)

    def oracle(x: np.ndarray) -> np.ndarray:
        return np.argmax(x @ true_w.T + true_b, axis=1)

    def sample(n: int, shift: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
        x = rng.normal(size=(n, n_features))
        if shift is not None:
            x += shift
        return x, oracle(x)

    x_train, y_train = sample(n_train)
    x_anchor, y_anchor = sample(n_anchor)
    x_validation, y_validation = sample(n_validation)
    shift = np.zeros(n_features, dtype=np.float64)
    shift[: min(3, n_features)] = np.asarray([1.0, -0.6, 0.4])[: min(3, n_features)]
    x_weak, y_weak = sample(n_weak_validation, shift=shift)

    def fit_vector(x: np.ndarray, y: np.ndarray, model_seed: int, c: float) -> np.ndarray:
        model = LogisticRegression(C=float(c), max_iter=600, random_state=int(model_seed))
        model.fit(x, y)
        if len(model.classes_) != n_classes:
            raise RuntimeError("A bootstrap sample lost a class; increase the scenario sample size.")
        return np.concatenate([model.coef_.reshape(-1), model.intercept_]).astype(np.float64)

    def make_pool(count: int, *, base_seed: int, mode: str) -> np.ndarray:
        vectors: list[np.ndarray] = []
        for i in range(count):
            if mode == "weak":
                core_idx = rng.choice(len(x_train), size=min(900, len(x_train)), replace=True)
                weak_idx = rng.choice(len(x_weak), size=min(700, len(x_weak)), replace=True)
                x = np.concatenate([x_train[core_idx], x_weak[weak_idx]], axis=0)
                y = np.concatenate([y_train[core_idx], y_weak[weak_idx]], axis=0)
            else:
                bootstrap_n = min(1200, max(500, int(0.67 * len(x_train))))
                idx = rng.choice(len(x_train), size=bootstrap_n, replace=True)
                x = x_train[idx]
                y = y_train[idx].copy()
                if mode == "poison":
                    poison_n = max(1, int(poison_fraction * len(y)))
                    poison_idx = rng.choice(len(y), size=poison_n, replace=False)
                    offsets = rng.integers(1, n_classes, size=poison_n)
                    y[poison_idx] = (y[poison_idx] + offsets) % n_classes
            c = float(np.exp(rng.normal(np.log(3.0), 0.10)))
            vectors.append(fit_vector(x, y, base_seed + i, c))
        return np.stack(vectors)

    return ReflexPoolScenario(
        trusted_fit=make_pool(trusted_fit_n, base_seed=0, mode="clean"),
        trusted_calibration=make_pool(trusted_calibration_n, base_seed=100, mode="clean"),
        clean_candidates=make_pool(candidate_n, base_seed=1000, mode="clean"),
        poisoned_candidates=make_pool(candidate_n, base_seed=2000, mode="poison"),
        weak_pool_candidates=make_pool(candidate_n, base_seed=3000, mode="weak"),
        anchor_x=x_anchor,
        anchor_y=y_anchor,
        validation_x=x_validation,
        validation_y=y_validation,
        weak_validation_x=x_weak,
        weak_validation_y=y_weak,
        n_features=n_features,
        n_classes=n_classes,
    )
