from __future__ import annotations

import platform
import time
from dataclasses import asdict, dataclass
from typing import Callable

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier

from .baselines import ExactCache, NearestNeighborCache
from .compiler import ReflexCompiler
from .evaluation import expected_calibration_error, multiclass_brier
from .model_selection import MinimalReflexSelector
from .schema import Trace
from .selection import select_confidence_threshold
from .synthetic import teacher


@dataclass(slots=True)
class MethodResult:
    accuracy: float
    selective_accuracy: float
    coverage: float
    system_accuracy_with_fallback: float
    threshold: float | None
    ece: float | None
    brier: float | None
    latency_us_per_item: float
    deliberation_calls_avoided: float
    normalized_compute_cost: float
    threshold_feasible: bool | None


def _matrix(traces: list[Trace]) -> tuple[np.ndarray, np.ndarray]:
    return np.stack([np.asarray(t.features, dtype=np.float64) for t in traces]), np.asarray([t.action for t in traces])


def _reference(x: np.ndarray) -> np.ndarray:
    return np.asarray([teacher(row) for row in x], dtype=str)


def _latency_us(fn: Callable[[np.ndarray], object], x: np.ndarray, repeats: int = 8) -> float:
    sample = x[: min(256, len(x))]
    fn(sample)
    start = time.perf_counter()
    for _ in range(repeats):
        fn(sample)
    elapsed = time.perf_counter() - start
    return float(elapsed / repeats / len(sample) * 1e6)


def _normalized_cost(coverage: float, reflex_cost: float = 1.0, deliberative_cost: float = 100.0) -> float:
    """Synthetic cost model used only to compare coverage policies.

    Every request pays one reflex unit. Rejected requests additionally pay the
    deliberative cost. The absolute numbers are assumptions and are reported as such.
    """

    return float((reflex_cost + (1.0 - coverage) * deliberative_cost) / deliberative_cost)


def _evaluate_probabilistic(
    *,
    probabilities_val: np.ndarray,
    probabilities_test: np.ndarray,
    classes: np.ndarray,
    y_val: np.ndarray,
    y_test: np.ndarray,
    ref_val: np.ndarray,
    ref_test: np.ndarray,
    latency_fn: Callable[[np.ndarray], object],
    x_test: np.ndarray,
    full_coverage: bool = False,
) -> MethodResult:
    classes = np.asarray(classes).astype(str)
    pred_test = classes[np.argmax(probabilities_test, axis=1)]
    confidence_test = np.max(probabilities_test, axis=1)

    if full_coverage:
        threshold = 0.0
        feasible = True
    else:
        selected = select_confidence_threshold(
            y_val,
            probabilities_val,
            classes,
            reference_predictions=ref_val,
            tolerance=0.01,
        )
        threshold = selected.threshold
        feasible = selected.feasible

    accepted = confidence_test >= threshold
    coverage = float(np.mean(accepted))
    selective = float(accuracy_score(y_test[accepted], pred_test[accepted])) if np.any(accepted) else float("nan")
    system_pred = np.where(accepted, pred_test, ref_test)

    return MethodResult(
        accuracy=float(accuracy_score(y_test, pred_test)),
        selective_accuracy=selective,
        coverage=coverage,
        system_accuracy_with_fallback=float(accuracy_score(y_test, system_pred)),
        threshold=float(threshold),
        ece=expected_calibration_error(y_test, probabilities_test, classes),
        brier=multiclass_brier(y_test, probabilities_test, classes),
        latency_us_per_item=_latency_us(latency_fn, x_test),
        deliberation_calls_avoided=coverage,
        normalized_compute_cost=_normalized_cost(coverage),
        threshold_feasible=bool(feasible),
    )


def split_traces(traces: list[Trace], seed: int) -> tuple[list[Trace], list[Trace], list[Trace]]:
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(traces))
    n_train = int(len(traces) * 0.60)
    n_val = int(len(traces) * 0.20)
    return (
        [traces[i] for i in order[:n_train]],
        [traces[i] for i in order[n_train : n_train + n_val]],
        [traces[i] for i in order[n_train + n_val :]],
    )


def run_scenario(traces: list[Trace], seed: int = 0) -> dict[str, object]:
    train, val, test = split_traces(traces, seed=seed)
    x_train, y_train = _matrix(train)
    x_val, y_val = _matrix(val)
    x_test, y_test = _matrix(test)
    ref_val = _reference(x_val)
    ref_test = _reference(x_test)

    result: dict[str, object] = {
        "n_train": len(train),
        "n_validation": len(val),
        "n_test": len(test),
        "reference_accuracy": float(accuracy_score(y_test, ref_test)),
        "cost_model": {"reflex_unit": 1.0, "deliberative_unit": 100.0},
        "methods": {},
    }

    # Exact cache. Coverage is based on seen keys rather than a learned threshold.
    exact = ExactCache().fit(x_train, y_train)
    exact_pred, _, exact_accept = exact.predict_with_acceptance(x_test)
    exact_system = np.where(exact_accept, exact_pred, ref_test)
    exact_selective = (
        float(accuracy_score(y_test[exact_accept], exact_pred[exact_accept])) if np.any(exact_accept) else float("nan")
    )
    result["methods"]["exact_cache"] = asdict(
        MethodResult(
            accuracy=float(accuracy_score(y_test, np.where(exact_accept, exact_pred, ref_test))),
            selective_accuracy=exact_selective,
            coverage=float(np.mean(exact_accept)),
            system_accuracy_with_fallback=float(accuracy_score(y_test, exact_system)),
            threshold=None,
            ece=None,
            brier=None,
            latency_us_per_item=_latency_us(lambda x: exact.predict_with_acceptance(x), x_test),
            deliberation_calls_avoided=float(np.mean(exact_accept)),
            normalized_compute_cost=_normalized_cost(float(np.mean(exact_accept))),
            threshold_feasible=None,
        )
    )

    knn = NearestNeighborCache(n_neighbors=5).fit(x_train, y_train)
    result["methods"]["nearest_neighbor_cache"] = asdict(
        _evaluate_probabilistic(
            probabilities_val=knn.predict_proba(x_val),
            probabilities_test=knn.predict_proba(x_test),
            classes=knn.classes_,
            y_val=y_val,
            y_test=y_test,
            ref_val=ref_val,
            ref_test=ref_test,
            latency_fn=knn.predict_proba,
            x_test=x_test,
        )
    )

    tree = DecisionTreeClassifier(max_depth=8, min_samples_leaf=4, random_state=seed).fit(x_train, y_train)
    result["methods"]["decision_tree"] = asdict(
        _evaluate_probabilistic(
            probabilities_val=tree.predict_proba(x_val),
            probabilities_test=tree.predict_proba(x_test),
            classes=tree.classes_,
            y_val=y_val,
            y_test=y_test,
            ref_val=ref_val,
            ref_test=ref_test,
            latency_fn=tree.predict_proba,
            x_test=x_test,
        )
    )

    forest = RandomForestClassifier(
        n_estimators=80,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=seed,
        n_jobs=-1,
    ).fit(x_train, y_train)
    result["methods"]["random_forest_no_fallback"] = asdict(
        _evaluate_probabilistic(
            probabilities_val=forest.predict_proba(x_val),
            probabilities_test=forest.predict_proba(x_test),
            classes=forest.classes_,
            y_val=y_val,
            y_test=y_test,
            ref_val=ref_val,
            ref_test=ref_test,
            latency_fn=forest.predict_proba,
            x_test=x_test,
            full_coverage=True,
        )
    )

    forest_reflex = ReflexCompiler(
        backend="calibrated_forest", n_estimators=80, random_state=seed
    ).fit(train, name="core-p0:calibrated-forest")
    result["methods"]["calibrated_forest_reflex"] = asdict(
        _evaluate_probabilistic(
            probabilities_val=forest_reflex.predict_proba(x_val),
            probabilities_test=forest_reflex.predict_proba(x_test),
            classes=forest_reflex.classes_,
            y_val=y_val,
            y_test=y_test,
            ref_val=ref_val,
            ref_test=ref_test,
            latency_fn=forest_reflex.predict_proba,
            x_test=x_test,
        )
    )

    selector = MinimalReflexSelector(
        minimum_coverage=0.50,
        maximum_ece=0.05,
        accuracy_tolerance=0.01,
        random_state=seed,
    )
    selection = selector.select(
        train,
        val,
        reference_predictions=ref_val,
        name="core-p0:selected",
    )
    selected = selection.reflex
    selected_result = _evaluate_probabilistic(
        probabilities_val=selected.predict_proba(x_val),
        probabilities_test=selected.predict_proba(x_test),
        classes=selected.classes_,
        y_val=y_val,
        y_test=y_test,
        ref_val=ref_val,
        ref_test=ref_test,
        latency_fn=selected.predict_proba,
        x_test=x_test,
    )
    # Use the threshold selected during model selection rather than reselecting it.
    probs_test = selected.predict_proba(x_test)
    classes = selected.classes_.astype(str)
    pred_test = classes[np.argmax(probs_test, axis=1)]
    confidence_test = np.max(probs_test, axis=1)
    accepted = confidence_test >= selection.threshold
    system_pred = np.where(accepted, pred_test, ref_test)
    selected_result.threshold = selection.threshold
    selected_result.coverage = float(np.mean(accepted))
    selected_result.selective_accuracy = (
        float(accuracy_score(y_test[accepted], pred_test[accepted])) if np.any(accepted) else float("nan")
    )
    selected_result.system_accuracy_with_fallback = float(accuracy_score(y_test, system_pred))
    selected_result.deliberation_calls_avoided = selected_result.coverage
    selected_result.normalized_compute_cost = _normalized_cost(selected_result.coverage)
    selected_result.threshold_feasible = selection.feasible
    result["methods"]["selected_reflex"] = asdict(selected_result)
    result["selected_reflex"] = {
        "backend": selection.backend,
        "feasible": selection.feasible,
        "candidates": [asdict(candidate) for candidate in selection.candidates],
    }

    compiled = result["methods"]["selected_reflex"]
    target = result["reference_accuracy"] - 0.01
    result["go_no_go"] = {
        "minimum_coverage": 0.50,
        "minimum_selective_accuracy": max(0.0, target),
        "maximum_ece": 0.05,
        "coverage_pass": bool(compiled["coverage"] >= 0.50),
        "selective_accuracy_pass": bool(compiled["selective_accuracy"] >= max(0.0, target)),
        "calibration_pass": bool(compiled["ece"] <= 0.05),
        "efficiency_status": "pending_real_deliberative_baseline",
    }
    result["go_no_go"]["quality_pass"] = bool(
        result["go_no_go"]["coverage_pass"]
        and result["go_no_go"]["selective_accuracy_pass"]
        and result["go_no_go"]["calibration_pass"]
    )
    result["go_no_go"]["phase1_go"] = False
    return result


def environment_metadata() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
    }
