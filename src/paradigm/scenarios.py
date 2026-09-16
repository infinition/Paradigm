from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .schema import Trace
from .synthetic import FEATURE_NAMES, teacher


ACTIONS = np.asarray(["execute", "deliberate", "human_review"], dtype=str)


@dataclass(slots=True)
class Scenario:
    name: str
    traces: list[Trace]
    description: str


def _flip_label(label: str, rng: np.random.Generator) -> str:
    choices = ACTIONS[ACTIONS != label]
    return str(rng.choice(choices))


def _boundary_distance(x: np.ndarray) -> float:
    risk, reversibility, novelty, cost, success, pressure = x
    distances = [
        abs(risk - 0.78),
        abs(risk - 0.58),
        abs(reversibility - 0.30),
        abs(novelty - 0.70),
        abs(success - 0.42),
        abs(pressure - 0.80),
        abs(cost - 0.55),
    ]
    return float(min(distances))


def deterministic_routing(n: int = 6000, seed: int = 0) -> Scenario:
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.0, 1.0, size=(n, len(FEATURE_NAMES)))
    traces = [Trace(features=row, action=teacher(row), metadata={"scenario": "deterministic"}) for row in x]
    return Scenario(
        name="deterministic_routing",
        traces=traces,
        description="IID deterministic routing with a stable reference policy.",
    )


def noisy_routing(n: int = 6000, seed: int = 1, base_noise: float = 0.01, boundary_noise: float = 0.32) -> Scenario:
    """Routing with ambiguity concentrated near policy boundaries.

    The hidden variation is intentional. It tests whether confidence fallback
    concentrates acceptance on stable regions rather than maximizing raw coverage.
    """

    rng = np.random.default_rng(seed)
    x = rng.uniform(0.0, 1.0, size=(n, len(FEATURE_NAMES)))
    traces: list[Trace] = []
    for row in x:
        clean = teacher(row)
        d = _boundary_distance(row)
        p = min(0.45, base_noise + boundary_noise * np.exp(-d / 0.045))
        observed = _flip_label(clean, rng) if rng.random() < p else clean
        traces.append(
            Trace(
                features=row,
                action=observed,
                metadata={"scenario": "noisy", "reference_action": clean, "noise_probability": float(p)},
            )
        )
    return Scenario(
        name="noisy_routing",
        traces=traces,
        description="Routing with label ambiguity concentrated near decision boundaries.",
    )


def shifted_routing(n: int = 6000, seed: int = 2) -> Scenario:
    """Covariate shift that remains semantically valid under the same teacher."""

    rng = np.random.default_rng(seed)
    x = rng.uniform(0.0, 1.0, size=(n, len(FEATURE_NAMES)))
    # Bias the later portion toward higher risk, novelty, and resource pressure.
    split = int(n * 0.65)
    x[split:, 0] = rng.beta(5.0, 1.5, size=n - split)
    x[split:, 2] = rng.beta(4.0, 1.8, size=n - split)
    x[split:, 5] = rng.beta(5.0, 1.4, size=n - split)
    x[split:, 4] = rng.beta(1.8, 4.0, size=n - split)

    traces = [
        Trace(
            features=row,
            action=teacher(row),
            metadata={"scenario": "shifted", "shifted": bool(i >= split)},
        )
        for i, row in enumerate(x)
    ]
    return Scenario(
        name="distribution_shift",
        traces=traces,
        description="Train-like prefix followed by a valid but risk-heavy covariate shift.",
    )


def repeated_workflows(
    n_workflows: int = 180,
    repeats: int = 36,
    seed: int = 3,
    unstable_fraction: float = 0.18,
) -> Scenario:
    """Repeated workflows with stable and deliberately unstable patterns."""

    rng = np.random.default_rng(seed)
    prototypes = rng.uniform(0.0, 1.0, size=(n_workflows, len(FEATURE_NAMES)))
    unstable_ids = set(rng.choice(n_workflows, size=max(1, int(n_workflows * unstable_fraction)), replace=False).tolist())

    traces: list[Trace] = []
    for workflow_id, proto in enumerate(prototypes):
        clean = teacher(proto)
        for _ in range(repeats):
            observed = clean
            if workflow_id in unstable_ids and rng.random() < 0.35:
                observed = _flip_label(clean, rng)
            traces.append(
                Trace(
                    features=proto.copy(),
                    action=observed,
                    metadata={
                        "scenario": "repeated_workflow",
                        "workflow_id": int(workflow_id),
                        "stable": bool(workflow_id not in unstable_ids),
                        "reference_action": clean,
                    },
                )
            )
    rng.shuffle(traces)
    return Scenario(
        name="repeated_workflows",
        traces=traces,
        description="Repeated exact workflows with a minority of hidden unstable behaviors.",
    )


def all_core_p0_scenarios(seed: int = 11) -> list[Scenario]:
    return [
        deterministic_routing(seed=seed),
        noisy_routing(seed=seed + 1),
        shifted_routing(seed=seed + 2),
        repeated_workflows(seed=seed + 3),
    ]
