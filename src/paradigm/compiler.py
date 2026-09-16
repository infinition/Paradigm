from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from .reflex import CompiledReflex
from .schema import Trace


class ReflexCompiler:
    """Compile validated traces into a compact probabilistic reflex.

    Paradigm does not assume one universal reflex architecture. This compiler
    exposes a small reference set used by the Core experiments.
    """

    BACKENDS = {"tree", "calibrated_tree", "calibrated_forest"}

    def __init__(
        self,
        *,
        backend: str = "calibrated_tree",
        tree_max_depth: int = 8,
        n_estimators: int = 200,
        calibration: str = "sigmoid",
        random_state: int = 0,
    ) -> None:
        if backend not in self.BACKENDS:
            raise ValueError(f"Unknown backend {backend!r}. Expected one of {sorted(self.BACKENDS)}.")
        self.backend = backend
        self.tree_max_depth = tree_max_depth
        self.n_estimators = n_estimators
        self.calibration = calibration
        self.random_state = random_state

    def _build_model(self) -> object:
        if self.backend == "tree":
            return DecisionTreeClassifier(
                max_depth=self.tree_max_depth,
                min_samples_leaf=4,
                random_state=self.random_state,
            )

        if self.backend == "calibrated_tree":
            base = DecisionTreeClassifier(
                max_depth=self.tree_max_depth,
                min_samples_leaf=4,
                random_state=self.random_state,
            )
            return CalibratedClassifierCV(base, method=self.calibration, cv=3)

        base = RandomForestClassifier(
            n_estimators=self.n_estimators,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=self.random_state,
            n_jobs=-1,
        )
        return CalibratedClassifierCV(base, method=self.calibration, cv=3)

    def fit(self, traces: Sequence[Trace], name: str = "candidate") -> CompiledReflex:
        valid = [t for t in traces if t.valid]
        if len(valid) < 30:
            raise ValueError("At least 30 validated traces are required for the reference compiler.")

        x = np.stack([np.asarray(t.features, dtype=np.float64) for t in valid])
        y = np.asarray([t.action for t in valid])
        weights = np.asarray([t.weight for t in valid], dtype=np.float64)

        if len(np.unique(y)) < 2:
            raise ValueError("Compilation requires at least two action classes.")

        model = self._build_model()
        model.fit(x, y, sample_weight=weights)
        return CompiledReflex(model=model, name=name, metadata={"backend": self.backend})
