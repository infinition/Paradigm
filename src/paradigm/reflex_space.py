from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.decomposition import PCA


@dataclass(slots=True)
class SignatureGateReport:
    threshold: float
    n_components: int
    variance_retained: float


class PCASignatureGate:
    """Residual gate for validated reflex signatures.

    The gate is intentionally generic. A signature can be a parameter/update
    vector or a behavior vector measured on a fixed anchor suite. PCA is fitted
    on one validated pool and the acceptance threshold is calibrated on a
    disjoint validated pool to avoid using reconstruction error on the same
    samples that define the subspace.
    """

    def __init__(self, *, variance: float = 0.95, quantile: float = 0.95) -> None:
        if not 0.0 < variance <= 1.0:
            raise ValueError("variance must be in (0, 1].")
        if not 0.0 < quantile < 1.0:
            raise ValueError("quantile must be in (0, 1).")
        self.variance = float(variance)
        self.quantile = float(quantile)
        self.pca = PCA(n_components=self.variance, svd_solver="full")
        self.threshold_: float | None = None

    def fit(self, trusted_fit: np.ndarray, trusted_calibration: np.ndarray) -> "PCASignatureGate":
        trusted_fit = _as_2d(trusted_fit)
        trusted_calibration = _as_2d(trusted_calibration)
        if trusted_fit.shape[1] != trusted_calibration.shape[1]:
            raise ValueError("Fit and calibration signatures must have the same dimension.")
        self.pca.fit(trusted_fit)
        calibration_score = self.score(trusted_calibration, require_threshold=False)
        self.threshold_ = float(np.quantile(calibration_score, self.quantile))
        return self

    def score(self, signatures: np.ndarray, *, require_threshold: bool = True) -> np.ndarray:
        if not hasattr(self.pca, "components_"):
            raise RuntimeError("Gate must be fitted before scoring.")
        if require_threshold and self.threshold_ is None:
            raise RuntimeError("Gate threshold has not been calibrated.")
        x = _as_2d(signatures)
        reconstructed = self.pca.inverse_transform(self.pca.transform(x))
        return np.linalg.norm(x - reconstructed, axis=1)

    def accept(self, signatures: np.ndarray) -> np.ndarray:
        if self.threshold_ is None:
            raise RuntimeError("Gate must be fitted before acceptance checks.")
        return self.score(signatures) <= self.threshold_

    def report(self) -> SignatureGateReport:
        if self.threshold_ is None:
            raise RuntimeError("Gate must be fitted before reporting.")
        return SignatureGateReport(
            threshold=float(self.threshold_),
            n_components=int(self.pca.n_components_),
            variance_retained=float(np.sum(self.pca.explained_variance_ratio_)),
        )


def _as_2d(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[None, :]
    if x.ndim != 2:
        raise ValueError("Expected a 1D or 2D array.")
    return x
