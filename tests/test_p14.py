from __future__ import annotations

import numpy as np

from paradigm.family_evolution import EvolutionProbe, FamilyEvolutionGuard
from paradigm.family_registry import FamilyDefinition, PersistentFamilyRegistry


def _def(name: str, direction: np.ndarray, threshold: float = 0.92, parent: str = "p14") -> FamilyDefinition:
    d = direction / np.linalg.norm(direction)
    return FamilyDefinition(
        name=name,
        risk="medium",
        maximum_epsilon=0.015,
        parameter_prototype=d.tolist(),
        parameter_threshold=threshold,
        behavior_prototype=d.tolist(),
        behavior_threshold=threshold,
        semantic_floors={
            "current_accuracy": 0.5,
            "protected_accuracy": 0.4,
            "minimum_class_accuracy": 0.3,
            "subgroup_accuracy": 0.3,
        },
        parent_lineage=parent,
        research_phase="P1.4",
    )


def _probe(v: np.ndarray, expected: str | None = None) -> EvolutionProbe:
    d = v / np.linalg.norm(v)
    return EvolutionProbe(d.tolist(), d.tolist(), expected_family_id=expected)


def test_evolution_guard_rejects_overly_broad_family(tmp_path):
    registry = PersistentFamilyRegistry(tmp_path)
    e1 = np.eye(6)[0]
    base_id = registry.register(_def("base", e1))
    clean = [_probe(e1, base_id)]
    negatives = [_probe(v) for v in np.eye(6)[1:]]
    broad = _def("broad", np.ones(6), threshold=0.1)
    guard = FamilyEvolutionGuard(max_negative_capture_delta=0.0, max_clean_ambiguity_delta=0.0)
    decision = guard.guarded_register(registry, broad, clean_probes=clean, negative_probes=negatives)
    assert not decision.approved
    assert broad.family_id not in {fid for fid, _, _ in registry.list(include_inactive=True)}


def test_split_retires_parent_and_routes_children(tmp_path):
    registry = PersistentFamilyRegistry(tmp_path)
    a = np.array([1.0, 0.35, 0.0, 0.0])
    b = np.array([1.0, -0.35, 0.0, 0.0])
    parent = _def("parent", np.array([1.0, 0.0, 0.0, 0.0]), threshold=0.90)
    parent_id = registry.register(parent)
    child_a = _def("child-a", a, threshold=0.96, parent=parent_id)
    child_b = _def("child-b", b, threshold=0.96, parent=parent_id)
    child_ids = registry.split_family(parent_id, [child_a, child_b], reason="bimodal family")
    statuses = {fid: status for fid, _, status in registry.list(include_inactive=True)}
    assert statuses[parent_id] == "retired"
    assert all(statuses[cid] == "active" for cid in child_ids)
    assert registry.route(a, a).family_id == child_a.family_id
    assert registry.route(b, b).family_id == child_b.family_id


def test_reactivation_is_persistent(tmp_path):
    registry = PersistentFamilyRegistry(tmp_path)
    d = np.array([1.0, 0.0, 0.0])
    fid = registry.register(_def("x", d))
    registry.set_status(fid, "retired", reason="test")
    assert registry.route(d, d).status == "unknown"
    registry.set_status(fid, "active", reason="validated reactivation")
    reloaded = PersistentFamilyRegistry(tmp_path)
    assert reloaded.route(d, d).family_id == fid


def test_guarded_split_evaluates_replacement_topology(tmp_path):
    registry = PersistentFamilyRegistry(tmp_path)
    parent_direction = np.array([1.0, 0.0, 0.0, 0.0])
    parent = _def("parent", parent_direction, threshold=0.90)
    parent_id = registry.register(parent)
    a = np.array([1.0, 0.35, 0.0, 0.0])
    b = np.array([1.0, -0.35, 0.0, 0.0])
    ca = _def("a", a, threshold=0.96, parent=parent_id)
    cb = _def("b", b, threshold=0.96, parent=parent_id)
    clean = [_probe(a, ca.family_id), _probe(b, cb.family_id)]
    negatives = [_probe(np.array([0.0, 0.0, 1.0, 0.0]))]
    guard = FamilyEvolutionGuard(max_negative_capture_delta=0.0, max_clean_ambiguity_delta=0.0)
    decision, children = guard.guarded_split(
        registry,
        parent_id,
        [ca, cb],
        clean_probes=clean,
        negative_probes=negatives,
        reason="validated bimodality",
    )
    assert decision.approved
    assert set(children) == {ca.family_id, cb.family_id}
    assert registry.route(a, a).family_id == ca.family_id
    assert registry.route(b, b).family_id == cb.family_id


def test_p14_short_benchmark(tmp_path):
    from paradigm.p14 import run_p14_benchmark

    result = run_p14_benchmark(tmp_path / "store")
    observed = result["observed"]
    assert observed["guarded_split_approved"]
    assert observed["split_children_route_uniquely"]
    assert observed["bridge_routes_to_deliberation_as_ambiguous"]
    assert observed["overlapping_family_rejected"]
    assert observed["broad_family_rejected"]
