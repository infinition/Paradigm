from __future__ import annotations

import numpy as np

from paradigm.compiler import ReflexCompiler
from paradigm.p05 import run_persistent_lifecycle_benchmark
from paradigm.persistent_registry import PersistentReflexRegistry
from paradigm.promotion import PromotionCheck, PromotionManifest
from paradigm.scenarios import deterministic_routing
from paradigm.storage import ReflexArtifactStore


def _passed_manifest(name: str) -> PromotionManifest:
    return PromotionManifest(
        candidate_name=name,
        checks=[PromotionCheck("quality", True, 1.0, ">= 0.9")],
    )


def test_content_addressed_artifact_round_trip(tmp_path):
    traces = deterministic_routing(n=500, seed=41).traces
    reflex = ReflexCompiler(backend="tree", random_state=41).fit(traces, name="round_trip")
    store = ReflexArtifactStore(tmp_path / "store")
    first = store.archive(reflex, provenance={"source": "test"})
    second = store.archive(reflex, provenance={"source": "test-repeat"})

    assert first.version_id == second.version_id
    loaded = store.load(first.version_id)
    x = np.stack([trace.features for trace in traces[:25]])
    assert np.allclose(reflex.predict_proba(x), loaded.predict_proba(x))
    assert len(store.provenance(first.version_id)) == 2


def test_persistent_registry_survives_reload_and_rolls_back(tmp_path):
    traces = deterministic_routing(n=600, seed=42).traces
    a = ReflexCompiler(backend="tree", random_state=1).fit(traces, name="a")
    b = ReflexCompiler(backend="tree", random_state=2).fit(traces, name="b")
    store_path = tmp_path / "registry"

    registry = PersistentReflexRegistry(ReflexArtifactStore(store_path))
    a_id = registry.bootstrap_active(a, provenance={"stage": "bootstrap"})
    b_id = registry.stage(b, provenance={"stage": "candidate"})
    registry.promote(_passed_manifest("b"))
    assert registry.active_version_id == b_id

    reopened = PersistentReflexRegistry(ReflexArtifactStore(store_path))
    assert reopened.active_version_id == b_id
    assert reopened.active_history[-1] == a_id
    restored = reopened.rollback(reason="test")
    assert restored == a_id

    reopened_again = PersistentReflexRegistry(ReflexArtifactStore(store_path))
    assert reopened_again.active_version_id == a_id
    assert any(event["event_type"] == "rollback" for event in reopened_again.store.events())


def test_p05_detects_delayed_regression_and_restores_clean_version(tmp_path):
    result = run_persistent_lifecycle_benchmark(
        tmp_path / "p05",
        seed=2026,
        reset_store=True,
    )
    assert result["observed"] == result["expected"]
    assert result["version_ids"]["final_active"] == result["version_ids"]["clean"]
    assert result["post_rollback"]["delayed_hidden_accuracy"] > 0.90
    assert result["bad_candidate_if_not_rolled_back"]["delayed_hidden_accuracy"] < 0.20
