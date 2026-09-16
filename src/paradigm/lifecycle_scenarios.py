from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .schema import Trace
from .shadow import ShadowWindow


@dataclass(slots=True)
class SequentialLifecycleScenario:
    bootstrap_traces: list[Trace]
    clean_candidate_traces: list[Trace]
    delayed_regression_traces: list[Trace]
    promotion_windows: list[ShadowWindow]
    delayed_window: ShadowWindow
    broad_future_window: ShadowWindow


def make_sequential_lifecycle_scenario(*, seed: int = 2026) -> SequentialLifecycleScenario:
    """Build a sequential task with a deliberately delayed hidden-slice regression.

    The second candidate is trained with corrupted labels only in a rare hidden
    region. The immediate promotion windows exclude that region, so shadow tests
    cannot see the defect. A later window concentrates on it and must trigger the
    persistent rollback path.
    """

    rng = np.random.default_rng(seed)
    n_features = 3

    def oracle(x: np.ndarray) -> np.ndarray:
        score = 0.9 * x[:, 0] - 0.5 * x[:, 1] + 0.25 * x[:, 2]
        labels = np.where(score > 0.7, "2", np.where(score < -0.7, "0", "1"))
        hidden = (x[:, 0] > 1.2) & (x[:, 1] > 0.7)
        labels[hidden] = "2"
        return labels.astype(str)

    def sample(
        n: int,
        *,
        local_seed: int,
        shift: tuple[float, float, float] | None = None,
        hidden_only: bool = False,
        exclude_hidden: bool = False,
    ) -> tuple[np.ndarray, np.ndarray]:
        local = np.random.default_rng(local_seed)
        shift_arr = np.asarray(shift, dtype=np.float64) if shift is not None else None
        if hidden_only:
            blocks: list[np.ndarray] = []
            total = 0
            while total < n:
                block = local.normal(size=(max(256, n), n_features))
                mask = (block[:, 0] > 1.2) & (block[:, 1] > 0.7)
                selected = block[mask]
                if len(selected):
                    blocks.append(selected)
                    total += len(selected)
            x = np.concatenate(blocks, axis=0)[:n]
        else:
            x = local.normal(size=(n, n_features))
            if shift_arr is not None:
                x += shift_arr
            if exclude_hidden:
                hidden = (x[:, 0] > 1.2) & (x[:, 1] > 0.7)
                while np.any(hidden):
                    replacement = local.normal(size=(int(np.sum(hidden)), n_features))
                    if shift_arr is not None:
                        replacement += shift_arr
                    x[hidden] = replacement
                    hidden = (x[:, 0] > 1.2) & (x[:, 1] > 0.7)
        return x, oracle(x)

    def traces(x: np.ndarray, y: np.ndarray, *, window_id: str) -> list[Trace]:
        return [
            Trace(
                features=row,
                action=str(label),
                valid=True,
                metadata={"window_id": window_id},
            )
            for row, label in zip(x, y)
        ]

    x_bootstrap, y_bootstrap = sample(5000, local_seed=seed + 1)
    x_clean, y_clean = sample(
        5000,
        local_seed=seed + 2,
        shift=(0.15, -0.10, 0.0),
    )
    x_delayed, y_delayed = sample(5000, local_seed=seed + 3)
    hidden_train = (x_delayed[:, 0] > 1.2) & (x_delayed[:, 1] > 0.7)
    y_delayed_corrupt = y_delayed.copy()
    y_delayed_corrupt[hidden_train] = "0"

    shadow_a_x, shadow_a_y = sample(
        1500,
        local_seed=seed + 10,
        exclude_hidden=True,
    )
    shadow_b_x, shadow_b_y = sample(
        1500,
        local_seed=seed + 11,
        shift=(0.25, -0.20, 0.0),
        exclude_hidden=True,
    )
    delayed_x, delayed_y = sample(1000, local_seed=seed + 12, hidden_only=True)
    future_x, future_y = sample(
        1500,
        local_seed=seed + 13,
        shift=(0.60, 0.50, 0.0),
    )

    return SequentialLifecycleScenario(
        bootstrap_traces=traces(x_bootstrap, y_bootstrap, window_id="bootstrap"),
        clean_candidate_traces=traces(x_clean, y_clean, window_id="clean_candidate"),
        delayed_regression_traces=traces(
            x_delayed,
            y_delayed_corrupt,
            window_id="delayed_regression_candidate",
        ),
        promotion_windows=[
            ShadowWindow(
                "shadow_a",
                shadow_a_x,
                shadow_a_y,
                metadata={"hidden_slice_excluded": True},
            ),
            ShadowWindow(
                "shadow_b",
                shadow_b_x,
                shadow_b_y,
                metadata={"hidden_slice_excluded": True, "distribution_shift": True},
            ),
        ],
        delayed_window=ShadowWindow(
            "delayed_hidden_slice",
            delayed_x,
            delayed_y,
            metadata={"hidden_slice_only": True},
        ),
        broad_future_window=ShadowWindow(
            "broad_future",
            future_x,
            future_y,
            metadata={"contains_hidden_slice": True, "distribution_shift": True},
        ),
    )
