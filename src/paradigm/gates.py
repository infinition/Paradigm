from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from .reflex import CompiledReflex


class TrustedSubspaceGate:
    """Experimental OOD gate built from validated feature vectors.

    This transfers the trusted-subspace principle into Paradigm input space.
    It is not equivalent to the adapter-space mechanism studied in z-manifold.
    """

    def __init__(self, variance: float = 0.95, quantile: float = 0.99) -> None:
        self.variance = variance
        self.quantile = quantile
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=variance, svd_solver="full")
        self.threshold_: float | None = None

    def fit(self, x: np.ndarray) -> "TrustedSubspaceGate":
        x = np.asarray(x, dtype=np.float64)
        z = self.scaler.fit_transform(x)
        self.pca.fit(z)
        residual = self._residual(z)
        self.threshold_ = float(np.quantile(residual, self.quantile))
        return self

    def _residual(self, z: np.ndarray) -> np.ndarray:
        projected = self.pca.inverse_transform(self.pca.transform(z))
        denom = np.linalg.norm(z, axis=1) + 1e-12
        return np.linalg.norm(z - projected, axis=1) / denom

    def score(self, x: np.ndarray) -> np.ndarray:
        if self.threshold_ is None:
            raise RuntimeError("Gate must be fitted before scoring.")
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x[None, :]
        return self._residual(self.scaler.transform(x))

    def accept(self, x: np.ndarray) -> np.ndarray:
        return self.score(x) <= float(self.threshold_)


@dataclass(slots=True)
class DriftReport:
    label_disagreement: float
    mean_total_variation: float
    accepted: bool


class BehaviorDriftGate:
    """Compare a candidate reflex against the active reflex on anchor states."""

    def __init__(self, max_disagreement: float = 0.05, max_total_variation: float = 0.08) -> None:
        self.max_disagreement = max_disagreement
        self.max_total_variation = max_total_variation

    def compare(
        self,
        active: CompiledReflex,
        candidate: CompiledReflex,
        x_anchor: np.ndarray,
    ) -> DriftReport:
        a_classes = active.classes_.astype(str)
        c_classes = candidate.classes_.astype(str)
        if set(a_classes) != set(c_classes):
            return DriftReport(1.0, 1.0, False)

        order = [int(np.where(c_classes == c)[0][0]) for c in a_classes]
        pa = active.predict_proba(x_anchor)
        pc = candidate.predict_proba(x_anchor)[:, order]

        pred_a = a_classes[np.argmax(pa, axis=1)]
        pred_c = a_classes[np.argmax(pc, axis=1)]
        disagreement = float(np.mean(pred_a != pred_c))
        tv = float(np.mean(0.5 * np.sum(np.abs(pa - pc), axis=1)))
        return DriftReport(
            label_disagreement=disagreement,
            mean_total_variation=tv,
            accepted=disagreement <= self.max_disagreement and tv <= self.max_total_variation,
        )
