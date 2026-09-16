from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

from .compiler import ReflexCompiler
from .evaluation import evaluate_reflex
from .lifecycle_scenarios import make_sequential_lifecycle_scenario
from .persistent_registry import PersistentReflexRegistry
from .shadow import ShadowPolicy
from .storage import ReflexArtifactStore


def run_persistent_lifecycle_benchmark(
    store_path: str | Path,
    *,
    seed: int = 2026,
    reset_store: bool = True,
) -> dict[str, Any]:
    store_path = Path(store_path)
    if reset_store and store_path.exists():
        shutil.rmtree(store_path)

    scenario = make_sequential_lifecycle_scenario(seed=seed)
    store = ReflexArtifactStore(store_path)
    registry = PersistentReflexRegistry(store)
    compiler = ReflexCompiler(backend="tree", tree_max_depth=8, random_state=seed)
    policy = ShadowPolicy(
        minimum_accuracy=0.90,
        maximum_ece=0.15,
        maximum_accuracy_regression=0.02,
        minimum_windows=2,
    )

    bootstrap = compiler.fit(scenario.bootstrap_traces, name="bootstrap_active")
    bootstrap_id = registry.bootstrap_active(
        bootstrap,
        provenance={
            "phase": "P0.5",
            "role": "bootstrap",
            "training_window": "bootstrap",
            "seed": seed,
        },
    )

    clean = ReflexCompiler(backend="tree", tree_max_depth=8, random_state=seed + 1).fit(
        scenario.clean_candidate_traces,
        name="clean_candidate",
    )
    clean_id = registry.stage(
        clean,
        provenance={
            "phase": "P0.5",
            "training_window": "clean_candidate",
            "seed": seed + 1,
        },
    )
    clean_manifest = policy.evaluate(
        candidate_name=clean.name,
        candidate=clean,
        active=registry.active,
        windows=scenario.promotion_windows,
        metadata={"candidate_version_id": clean_id},
    )
    registry.record_shadow_observation(clean_manifest.to_dict())
    registry.promote(clean_manifest)

    # Re-open the registry from disk to verify the lifecycle is not memory-only.
    registry = PersistentReflexRegistry(ReflexArtifactStore(store_path))
    clean_reloaded_id = registry.active_version_id

    delayed = ReflexCompiler(backend="tree", tree_max_depth=8, random_state=seed + 2).fit(
        scenario.delayed_regression_traces,
        name="delayed_regression_candidate",
    )
    delayed_id = registry.stage(
        delayed,
        provenance={
            "phase": "P0.5",
            "training_window": "delayed_regression_candidate",
            "known_control": "hidden-slice label corruption for delayed-regression benchmark",
            "seed": seed + 2,
        },
    )
    delayed_manifest = policy.evaluate(
        candidate_name=delayed.name,
        candidate=delayed,
        active=registry.active,
        windows=scenario.promotion_windows,
        metadata={"candidate_version_id": delayed_id},
    )
    registry.record_shadow_observation(delayed_manifest.to_dict())
    registry.promote(delayed_manifest)

    promoted_delayed_id = registry.active_version_id

    # Simulate a later process/session before delayed monitoring.
    registry = PersistentReflexRegistry(ReflexArtifactStore(store_path))
    current = registry.active
    previous = registry.store.load(registry.active_history[-1])
    delayed_monitor = policy.delayed_regression_manifest(
        active_name=current.name,
        active=current,
        reference=previous,
        window=scenario.delayed_window,
        metadata={
            "active_version_id": registry.active_version_id,
            "reference_version_id": registry.active_history[-1],
        },
    )
    registry.record_shadow_observation(delayed_monitor.to_dict())

    rollback_triggered = not delayed_monitor.approved
    restored_id = None
    if rollback_triggered:
        restored_id = registry.rollback(reason="delayed shadow regression")

    # Re-open once more and evaluate the actually restored artifact.
    registry = PersistentReflexRegistry(ReflexArtifactStore(store_path))
    restored = registry.active
    delayed_report_after_rollback = evaluate_reflex(
        restored,
        scenario.delayed_window.x,
        scenario.delayed_window.y,
        accept_threshold=0.0,
    )
    future_report_after_rollback = evaluate_reflex(
        restored,
        scenario.broad_future_window.x,
        scenario.broad_future_window.y,
        accept_threshold=0.0,
    )
    bad_delayed_report = evaluate_reflex(
        registry.store.load(delayed_id),
        scenario.delayed_window.x,
        scenario.delayed_window.y,
        accept_threshold=0.0,
    )
    bad_future_report = evaluate_reflex(
        registry.store.load(delayed_id),
        scenario.broad_future_window.x,
        scenario.broad_future_window.y,
        accept_threshold=0.0,
    )

    events = registry.store.events()
    provenance_counts = {
        version_id: len(registry.store.provenance(version_id))
        for version_id in [bootstrap_id, clean_id, delayed_id]
    }

    return {
        "claim_level": "synthetic persistent sequential lifecycle benchmark",
        "store_path": str(store_path),
        "version_ids": {
            "bootstrap": bootstrap_id,
            "clean": clean_id,
            "delayed_regression": delayed_id,
            "clean_after_reload": clean_reloaded_id,
            "delayed_after_promotion": promoted_delayed_id,
            "restored_after_rollback": restored_id,
            "final_active": registry.active_version_id,
        },
        "promotion": {
            "clean": clean_manifest.to_dict(),
            "delayed_regression_candidate": delayed_manifest.to_dict(),
        },
        "delayed_monitor": delayed_monitor.to_dict(),
        "rollback_triggered": rollback_triggered,
        "post_rollback": {
            "delayed_hidden_accuracy": delayed_report_after_rollback.accuracy,
            "broad_future_accuracy": future_report_after_rollback.accuracy,
        },
        "bad_candidate_if_not_rolled_back": {
            "delayed_hidden_accuracy": bad_delayed_report.accuracy,
            "broad_future_accuracy": bad_future_report.accuracy,
        },
        "persistence": {
            "event_count": len(events),
            "event_types": [event["event_type"] for event in events],
            "provenance_record_counts": provenance_counts,
            "active_history": list(registry.active_history),
        },
        "expected": {
            "clean_promoted": True,
            "delayed_candidate_initially_promoted": True,
            "delayed_regression_detected": True,
            "rollback_to_clean": True,
        },
        "observed": {
            "clean_promoted": clean_manifest.approved and clean_reloaded_id == clean_id,
            "delayed_candidate_initially_promoted": delayed_manifest.approved
            and promoted_delayed_id == delayed_id,
            "delayed_regression_detected": rollback_triggered,
            "rollback_to_clean": registry.active_version_id == clean_id,
        },
    }
