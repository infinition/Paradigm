from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .schema import Trace


@dataclass(slots=True)
class TrustScenario:
    trusted_train: np.ndarray
    trusted_labels: np.ndarray
    in_distribution: np.ndarray
    in_distribution_labels: np.ndarray
    off_manifold_ood: np.ndarray
    weak_pool_valid: np.ndarray
    weak_pool_labels: np.ndarray
    near_manifold_invalid: np.ndarray
    basis: np.ndarray


def _action_from_latent(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=np.float64)
    out = np.full(len(z), "execute", dtype=object)
    out[(z[:, 0] + 0.45 * z[:, 1]) > 0.70] = "human_review"
    middle = (z[:, 2] - 0.35 * z[:, 0]) > 0.35
    out[middle & (out == "execute")] = "deliberate"
    return out.astype(str)


def make_trust_scenario(
    *,
    n_train: int = 2400,
    n_test: int = 900,
    ambient_dim: int = 12,
    latent_dim: int = 3,
    seed: int = 41,
) -> TrustScenario:
    """Create a low-rank trusted manifold with controlled novelty cases.

    Weak-pool novelty remains on the same latent manifold but shifts beyond the
    trusted latent range. Off-manifold OOD adds energy in orthogonal directions.
    Near-manifold invalid inputs remain visually trusted, demonstrating that
    input-space gates cannot detect semantic corruption by themselves.
    """

    rng = np.random.default_rng(seed)
    raw = rng.normal(size=(ambient_dim, latent_dim))
    basis, _ = np.linalg.qr(raw)
    basis = basis[:, :latent_dim]

    def embed(z: np.ndarray, noise: float = 0.025) -> np.ndarray:
        x = z @ basis.T
        x += rng.normal(0.0, noise, size=x.shape)
        return x

    z_train = rng.normal(0.0, 0.72, size=(n_train, latent_dim))
    z_train = np.clip(z_train, -1.35, 1.35)
    x_train = embed(z_train)
    y_train = _action_from_latent(z_train)

    z_id = rng.normal(0.0, 0.72, size=(n_test, latent_dim))
    z_id = np.clip(z_id, -1.35, 1.35)
    x_id = embed(z_id)
    y_id = _action_from_latent(z_id)

    # Build orthogonal basis for explicit off-manifold energy.
    q, _ = np.linalg.qr(np.concatenate([basis, rng.normal(size=(ambient_dim, ambient_dim - latent_dim))], axis=1))
    orth = q[:, latent_dim:]
    z_ood = rng.normal(0.0, 0.72, size=(n_test, latent_dim))
    x_ood = embed(z_ood)
    off = rng.normal(0.0, 1.0, size=(n_test, orth.shape[1])) @ orth.T
    x_ood = x_ood + 1.20 * off / (np.linalg.norm(off, axis=1, keepdims=True) + 1e-12)

    # Legitimate novelty. Same manifold, shifted latent support.
    z_weak = rng.normal(0.0, 0.45, size=(n_test, latent_dim))
    z_weak[:, 0] += 1.75
    z_weak[:, 2] -= 0.70
    x_weak = embed(z_weak)
    y_weak = _action_from_latent(z_weak)

    # Invalid points deliberately kept near the trusted input manifold.
    idx = rng.integers(0, len(x_id), size=n_test)
    x_near_invalid = x_id[idx] + rng.normal(0.0, 0.012, size=(n_test, ambient_dim))

    return TrustScenario(
        trusted_train=x_train,
        trusted_labels=y_train,
        in_distribution=x_id,
        in_distribution_labels=y_id,
        off_manifold_ood=x_ood,
        weak_pool_valid=x_weak,
        weak_pool_labels=y_weak,
        near_manifold_invalid=x_near_invalid,
        basis=basis,
    )


def traces_from_xy(x: np.ndarray, y: np.ndarray, *, valid: bool = True) -> list[Trace]:
    return [Trace(features=row, action=str(label), valid=valid) for row, label in zip(x, y)]
