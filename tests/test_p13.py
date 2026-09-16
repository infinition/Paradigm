from __future__ import annotations

import numpy as np

from paradigm.family_registry import FamilyDefinition, PersistentFamilyRegistry


def _definition(name: str, direction: np.ndarray) -> FamilyDefinition:
    direction = direction / np.linalg.norm(direction)
    return FamilyDefinition(
        name=name,
        risk="medium",
        maximum_epsilon=0.015,
        parameter_prototype=direction.tolist(),
        parameter_threshold=0.95,
        behavior_prototype=direction.tolist(),
        behavior_threshold=0.95,
        semantic_floors={
            "current_accuracy": 0.5,
            "protected_accuracy": 0.4,
            "minimum_class_accuracy": 0.3,
            "subgroup_accuracy": 0.3,
        },
        parent_lineage="test-parent",
    )


def test_family_registry_routes_and_persists_quarantine(tmp_path):
    registry = PersistentFamilyRegistry(tmp_path)
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.0, 1.0, 0.0])
    aid = registry.register(_definition("a", a))
    registry.register(_definition("b", b))

    route = registry.route(a, a)
    assert route.family_id == aid

    registry.set_status(aid, "quarantined", reason="test")
    reloaded = PersistentFamilyRegistry(tmp_path)
    route2 = reloaded.route(a, a)
    assert route2.family_id != aid
    statuses = {fid: status for fid, _, status in reloaded.list(include_inactive=True)}
    assert statuses[aid] == "quarantined"


def test_family_manifest_keeps_geometry_and_semantics_separate(tmp_path):
    registry = PersistentFamilyRegistry(tmp_path)
    direction = np.array([1.0, 0.0, 0.0])
    fid = registry.register(_definition("a", direction))
    route = registry.route(direction, direction)
    assert route.family_id == fid

    good = registry.build_manifest(
        candidate_name="good",
        route=route,
        epsilon_used=0.01,
        current_accuracy=0.8,
        protected_accuracy=0.7,
        minimum_class_accuracy=0.6,
        subgroup_accuracy=0.6,
    )
    assert good.approved

    bad = registry.build_manifest(
        candidate_name="bad",
        route=route,
        epsilon_used=0.01,
        current_accuracy=0.8,
        protected_accuracy=0.7,
        minimum_class_accuracy=0.6,
        subgroup_accuracy=0.0,
    )
    assert not bad.approved
    assert any("subgroup" in reason for reason in bad.failure_reasons)


def test_unknown_family_returns_no_assignment(tmp_path):
    registry = PersistentFamilyRegistry(tmp_path)
    registry.register(_definition("a", np.array([1.0, 0.0, 0.0])))
    route = registry.route(np.array([0.0, 0.0, 1.0]), np.array([0.0, 0.0, 1.0]))
    assert route.status == "unknown"
    assert route.family_id is None
