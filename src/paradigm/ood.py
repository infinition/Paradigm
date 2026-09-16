from __future__ import annotations

import numpy as np
from sklearn.covariance import LedoitWolf
from sklearn.neighbors import NearestNeighbors
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler


class NearestDistanceGate:
    """Accept points whose nearest trusted neighbor is sufficiently close."""

    def __init__(self, quantile: float = 0.99) -> None:
        self.quantile = float(quantile)
        self.scaler = StandardScaler()
        self.nn = NearestNeighbors(n_neighbors=2)
        self.threshold_: float | None = None

    def fit(self, x: np.ndarray) -> "NearestDistanceGate":
        x = np.asarray(x, dtype=np.float64)
        z = self.scaler.fit_transform(x)
        self.nn.fit(z)
        distances, _ = self.nn.kneighbors(z, n_neighbors=2)
        self.threshold_ = float(np.quantile(distances[:, 1], self.quantile))
        return self

    def score(self, x: np.ndarray) -> np.ndarray:
        if self.threshold_ is None:
            raise RuntimeError("Gate must be fitted before scoring.")
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x[None, :]
        z = self.scaler.transform(x)
        distances, _ = self.nn.kneighbors(z, n_neighbors=1)
        return distances[:, 0]

    def accept(self, x: np.ndarray) -> np.ndarray:
        return self.score(x) <= float(self.threshold_)


class MahalanobisGate:
    """Global density gate using shrinkage covariance."""

    def __init__(self, quantile: float = 0.99) -> None:
        self.quantile = float(quantile)
        self.scaler = StandardScaler()
        self.cov = LedoitWolf()
        self.threshold_: float | None = None

    def fit(self, x: np.ndarray) -> "MahalanobisGate":
        x = np.asarray(x, dtype=np.float64)
        z = self.scaler.fit_transform(x)
        self.cov.fit(z)
        score = self.score_transformed(z)
        self.threshold_ = float(np.quantile(score, self.quantile))
        return self

    def score_transformed(self, z: np.ndarray) -> np.ndarray:
        delta = z - self.cov.location_
        precision = self.cov.precision_
        return np.sqrt(np.einsum("ij,jk,ik->i", delta, precision, delta))

    def score(self, x: np.ndarray) -> np.ndarray:
        if self.threshold_ is None:
            raise RuntimeError("Gate must be fitted before scoring.")
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x[None, :]
        return self.score_transformed(self.scaler.transform(x))

    def accept(self, x: np.ndarray) -> np.ndarray:
        return self.score(x) <= float(self.threshold_)


class AutoencoderOODGate:
    """Small nonlinear reconstruction gate for experimental comparison.

    scikit-learn's MLPRegressor is used only to keep the research scaffold
    dependency-light. This is not presented as a production autoencoder.
    """

    def __init__(
        self,
        *,
        bottleneck: int = 3,
        quantile: float = 0.99,
        random_state: int = 0,
        max_iter: int = 700,
    ) -> None:
        self.bottleneck = int(bottleneck)
        self.quantile = float(quantile)
        self.random_state = int(random_state)
        self.max_iter = int(max_iter)
        self.scaler = StandardScaler()
        self.model: MLPRegressor | None = None
        self.threshold_: float | None = None

    def fit(self, x: np.ndarray) -> "AutoencoderOODGate":
        x = np.asarray(x, dtype=np.float64)
        z = self.scaler.fit_transform(x)
        hidden = max(self.bottleneck * 2, 4)
        self.model = MLPRegressor(
            hidden_layer_sizes=(hidden, self.bottleneck, hidden),
            activation="tanh",
            solver="adam",
            alpha=1e-4,
            learning_rate_init=2e-3,
            max_iter=self.max_iter,
            tol=1e-3,
            random_state=self.random_state,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=30,
        )
        self.model.fit(z, z)
        residual = self._score_transformed(z)
        self.threshold_ = float(np.quantile(residual, self.quantile))
        return self

    def _score_transformed(self, z: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("Gate must be fitted before scoring.")
        reconstruction = self.model.predict(z)
        return np.mean((z - reconstruction) ** 2, axis=1)

    def score(self, x: np.ndarray) -> np.ndarray:
        if self.threshold_ is None:
            raise RuntimeError("Gate must be fitted before scoring.")
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x[None, :]
        return self._score_transformed(self.scaler.transform(x))

    def accept(self, x: np.ndarray) -> np.ndarray:
        return self.score(x) <= float(self.threshold_)
