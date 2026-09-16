from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def rms(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float64)
    return float(np.sqrt(np.mean(x * x)) + 1e-12)


def newton_schulz5(matrix: np.ndarray, *, steps: int = 5, eps: float = 1e-7) -> np.ndarray:
    """Quintic Newton-Schulz orthogonalization used by the Drift Contract work."""

    a, b, c = 3.4445, -4.7750, 2.0315
    x = np.asarray(matrix, dtype=np.float64)
    x = x / (np.linalg.norm(x) + eps)
    transpose = x.shape[0] > x.shape[1]
    if transpose:
        x = x.T
    for _ in range(int(steps)):
        aa = x @ x.T
        bb = b * aa + c * (aa @ aa)
        x = a * x + bb @ x
    return x.T if transpose else x


@dataclass(slots=True)
class SpectralStepReport:
    epsilon: float
    learning_rate: float
    input_rms: float
    ema_input_rms: float
    denominator_rms: float
    scale: float
    spectral_norm: float
    measured_preactivation_drift: float
    ratio_to_epsilon: float
    ratio_to_bound: float


class SpectralDriftContract:
    """Matrix-only spectral drift-budget update for controlled reflex adaptation.

    This is a direct mechanical transfer of the update geometry used in the
    Drift Contract research. Paradigm does not assume the original local-learning
    accuracy results transfer to reflex adaptation. The first use here is to test
    the per-step bound and the usefulness of an explicit change budget.
    """

    def __init__(
        self,
        shape: tuple[int, int],
        *,
        epsilon: float,
        momentum: float = 0.95,
        rms_ema_decay: float = 0.95,
        exact_scale: bool = True,
        strict_denominator: bool = True,
    ) -> None:
        if len(shape) != 2:
            raise ValueError("SpectralDriftContract requires a matrix parameter.")
        self.shape = tuple(int(v) for v in shape)
        self.epsilon = float(epsilon)
        self.momentum = float(momentum)
        self.rms_ema_decay = float(rms_ema_decay)
        self.exact_scale = bool(exact_scale)
        self.strict_denominator = bool(strict_denominator)
        self.m = np.zeros(self.shape, dtype=np.float64)
        self.ema_input_rms: float | None = None

        dout, din = self.shape
        if self.exact_scale:
            self.scale = float(np.sqrt(dout / din))
        else:
            self.scale = float(np.sqrt(max(1.0, dout / din)))

    def step(self, gradient: np.ndarray, input_batch: np.ndarray) -> tuple[np.ndarray, SpectralStepReport]:
        gradient = np.asarray(gradient, dtype=np.float64)
        input_batch = np.asarray(input_batch, dtype=np.float64)
        if gradient.shape != self.shape:
            raise ValueError(f"Gradient shape {gradient.shape} does not match {self.shape}.")
        if input_batch.ndim != 2 or input_batch.shape[1] != self.shape[1]:
            raise ValueError("Input batch shape is incompatible with the matrix input dimension.")

        self.m = self.momentum * self.m + gradient
        orth = newton_schulz5(self.m)
        current_rms = rms(input_batch)
        if self.ema_input_rms is None:
            self.ema_input_rms = current_rms
        else:
            self.ema_input_rms = (
                self.rms_ema_decay * self.ema_input_rms
                + (1.0 - self.rms_ema_decay) * current_rms
            )

        denominator = (
            max(current_rms, self.ema_input_rms)
            if self.strict_denominator
            else self.ema_input_rms
        )
        learning_rate = self.epsilon / max(denominator, 1e-12)
        update = -learning_rate * self.scale * orth

        spectral_norm = float(np.linalg.svd(orth, compute_uv=False)[0])
        dz = input_batch @ update.T
        measured = rms(dz)
        theoretical_bound = self.epsilon * spectral_norm
        report = SpectralStepReport(
            epsilon=self.epsilon,
            learning_rate=float(learning_rate),
            input_rms=current_rms,
            ema_input_rms=float(self.ema_input_rms),
            denominator_rms=float(denominator),
            scale=self.scale,
            spectral_norm=spectral_norm,
            measured_preactivation_drift=measured,
            ratio_to_epsilon=float(measured / max(self.epsilon, 1e-12)),
            ratio_to_bound=float(measured / max(theoretical_bound, 1e-12)),
        )
        return update, report


class AdamMatrix:
    def __init__(self, shape: tuple[int, int], *, learning_rate: float) -> None:
        self.m = np.zeros(shape, dtype=np.float64)
        self.v = np.zeros(shape, dtype=np.float64)
        self.t = 0
        self.learning_rate = float(learning_rate)

    def step(self, gradient: np.ndarray) -> np.ndarray:
        gradient = np.asarray(gradient, dtype=np.float64)
        self.t += 1
        self.m = 0.9 * self.m + 0.1 * gradient
        self.v = 0.999 * self.v + 0.001 * gradient * gradient
        mh = self.m / (1.0 - 0.9**self.t)
        vh = self.v / (1.0 - 0.999**self.t)
        return -self.learning_rate * mh / (np.sqrt(vh) + 1e-8)


def softmax_probabilities(weights: np.ndarray, x: np.ndarray) -> np.ndarray:
    logits = np.asarray(x, dtype=np.float64) @ np.asarray(weights, dtype=np.float64).T
    logits -= np.max(logits, axis=1, keepdims=True)
    exp = np.exp(logits)
    return exp / np.sum(exp, axis=1, keepdims=True)


def softmax_gradient(weights: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    probs = softmax_probabilities(weights, x)
    grad_logits = probs.copy()
    grad_logits[np.arange(len(y)), np.asarray(y, dtype=int)] -= 1.0
    return grad_logits.T @ np.asarray(x, dtype=np.float64) / len(y)


def linear_accuracy(weights: np.ndarray, x: np.ndarray, y: np.ndarray) -> float:
    pred = np.argmax(np.asarray(x, dtype=np.float64) @ np.asarray(weights, dtype=np.float64).T, axis=1)
    return float(np.mean(pred == np.asarray(y, dtype=int)))
