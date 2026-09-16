from __future__ import annotations

import time
from dataclasses import asdict, dataclass

import numpy as np
from sklearn.metrics import accuracy_score

from .deliberation import PerturbationDeliberator
from .model_selection import MinimalReflexSelector
from .p0 import split_traces
from .schema import Trace


@dataclass(slots=True)
class P01Result:
    selected_backend: str
    threshold: float
    coverage: float
    reflex_accuracy: float
    selective_accuracy: float
    deliberative_accuracy: float
    system_accuracy: float
    reflex_latency_us: float
    deliberative_latency_us: float
    measured_system_latency_us: float
    estimated_system_latency_us: float
    speedup_vs_deliberation: float
    fallback_rate: float


def _xy(traces: list[Trace]) -> tuple[np.ndarray, np.ndarray]:
    return np.stack([t.features for t in traces]), np.asarray([t.action for t in traces], dtype=str)


def _batch_latency_us(fn, x: np.ndarray, repeats: int = 6) -> float:
    sample = x[: min(256, len(x))]
    fn(sample)
    start = time.perf_counter()
    for _ in range(repeats):
        fn(sample)
    return float((time.perf_counter() - start) / repeats / len(sample) * 1e6)


def run_measured_deliberation(
    traces: list[Trace],
    *,
    seed: int = 0,
    probes: int = 1024,
    sigma: float = 0.018,
) -> dict[str, object]:
    train, val, test = split_traces(traces, seed=seed)
    x_val, y_val = _xy(val)
    x_test, y_test = _xy(test)

    deliberator = PerturbationDeliberator(probes=probes, sigma=sigma, seed=seed)
    ref_val = deliberator.predict(x_val)
    ref_test = deliberator.predict(x_test)

    selector = MinimalReflexSelector(
        minimum_coverage=0.50,
        maximum_ece=0.05,
        accuracy_tolerance=0.01,
        random_state=seed,
    )
    selection = selector.select(train, val, reference_predictions=ref_val, name="core-p01:selected")
    reflex = selection.reflex

    probs = reflex.predict_proba(x_test)
    classes = reflex.classes_.astype(str)
    pred = classes[np.argmax(probs, axis=1)]
    confidence = np.max(probs, axis=1)
    accepted = confidence >= selection.threshold

    system_pred = pred.copy()
    fallback_idx = np.flatnonzero(~accepted)
    if len(fallback_idx):
        system_pred[fallback_idx] = deliberator.predict(x_test[fallback_idx])

    reflex_latency = _batch_latency_us(reflex.predict_proba, x_test)

    # Deliberation is intentionally measured on a smaller fixed slice because it
    # is the expensive path. The same implementation is used for fallbacks.
    deliberation_sample = x_test[: min(96, len(x_test))]
    start = time.perf_counter()
    deliberator.predict(deliberation_sample)
    deliberative_latency = float((time.perf_counter() - start) / len(deliberation_sample) * 1e6)

    # Measure the actual batch runtime: reflex for all, deliberation for rejects.
    runtime_sample = x_test[: min(384, len(x_test))]
    start = time.perf_counter()
    p = reflex.predict_proba(runtime_sample)
    conf = np.max(p, axis=1)
    reject = conf < selection.threshold
    if np.any(reject):
        deliberator.predict(runtime_sample[reject])
    measured_system = float((time.perf_counter() - start) / len(runtime_sample) * 1e6)

    coverage = float(np.mean(accepted))
    estimated_system = float(reflex_latency + (1.0 - coverage) * deliberative_latency)
    speedup = float(deliberative_latency / measured_system) if measured_system > 0 else float("inf")

    result = P01Result(
        selected_backend=selection.backend,
        threshold=float(selection.threshold),
        coverage=coverage,
        reflex_accuracy=float(accuracy_score(y_test, pred)),
        selective_accuracy=float(accuracy_score(y_test[accepted], pred[accepted])) if np.any(accepted) else float("nan"),
        deliberative_accuracy=float(accuracy_score(y_test, ref_test)),
        system_accuracy=float(accuracy_score(y_test, system_pred)),
        reflex_latency_us=reflex_latency,
        deliberative_latency_us=deliberative_latency,
        measured_system_latency_us=measured_system,
        estimated_system_latency_us=estimated_system,
        speedup_vs_deliberation=speedup,
        fallback_rate=float(1.0 - coverage),
    )

    quality_target = max(0.0, result.deliberative_accuracy - 0.01)
    gates = {
        "coverage_pass": bool(result.coverage >= 0.50),
        "selective_quality_pass": bool(result.selective_accuracy >= quality_target),
        "efficiency_pass": bool(result.speedup_vs_deliberation >= 2.0),
        "system_quality_pass": bool(result.system_accuracy >= result.deliberative_accuracy - 0.01),
    }
    gates["all_pass"] = bool(all(gates.values()))

    return {
        "configuration": {"probes": probes, "sigma": sigma, "seed": seed},
        "metrics": asdict(result),
        "go_no_go": gates,
        "note": (
            "Measured local deliberative surrogate. It establishes real local compute savings, "
            "but does not substitute for a later agent, planner, or domain-specific reference benchmark."
        ),
    }
