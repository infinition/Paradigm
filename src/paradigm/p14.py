from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

import numpy as np

from .family_evolution import EvolutionProbe, FamilyEvolutionGuard
from .family_registry import FamilyDefinition, PersistentFamilyRegistry


def _unit(x: np.ndarray) -> np.ndarray:
    return x / (np.linalg.norm(x) + 1e-12)


def _definition(
    name: str,
    direction: np.ndarray,
    *,
    threshold: float,
    parent_lineage: str,
    risk: str = "medium",
) -> FamilyDefinition:
    d = _unit(direction)
    epsilon = {"low": 0.030, "medium": 0.015, "high": 0.0075}[risk]
    return FamilyDefinition(
        name=name,
        risk=risk,
        maximum_epsilon=epsilon,
        parameter_prototype=d.tolist(),
        parameter_threshold=float(threshold),
        behavior_prototype=d.tolist(),
        behavior_threshold=float(threshold),
        semantic_floors={
            "current_accuracy": 0.70,
            "protected_accuracy": 0.60,
            "minimum_class_accuracy": 0.50,
            "subgroup_accuracy": 0.50,
        },
        parent_lineage=parent_lineage,
        research_phase="P1.4",
    )


def _probes_around(
    direction: np.ndarray,
    *,
    family_id: str | None,
    rng: np.random.Generator,
    count: int = 16,
    noise: float = 0.012,
    label: str,
) -> list[EvolutionProbe]:
    d = _unit(direction)
    out: list[EvolutionProbe] = []
    for i in range(count):
        v = _unit(d + noise * rng.normal(size=d.shape))
        out.append(
            EvolutionProbe(
                parameter_signature=v.tolist(),
                behavior_signature=v.tolist(),
                expected_family_id=family_id,
                label=f"{label}-{i}",
            )
        )
    return out


def _negative_probe_suite(dim: int, rng: np.random.Generator) -> list[EvolutionProbe]:
    probes: list[EvolutionProbe] = []
    # Orthogonal directions remain stable, interpretable negative controls.
    for i in range(8, dim):
        v = np.eye(dim)[i]
        probes.append(EvolutionProbe(v.tolist(), v.tolist(), label=f"orthogonal-{i}"))
    # Dense directions exercise accidental widening from broad prototypes.
    for i in range(96):
        v = rng.normal(size=dim)
        v[:8] *= 0.15
        v = _unit(v)
        probes.append(EvolutionProbe(v.tolist(), v.tolist(), label=f"dense-negative-{i}"))
    return probes


def _capture_rate(registry: PersistentFamilyRegistry, probes: list[EvolutionProbe]) -> dict[str, float]:
    statuses: list[str] = []
    for probe in probes:
        p = np.asarray(probe.parameter_signature)
        b = np.asarray(probe.behavior_signature)
        statuses.append(registry.route(p, b).status)
    represented = float(np.mean([s == "represented" for s in statuses]))
    ambiguous = float(np.mean([s == "ambiguous" for s in statuses]))
    return {
        "represented": represented,
        "ambiguous": ambiguous,
        "unsafe_capture": represented + ambiguous,
        "unknown": float(np.mean([s == "unknown" for s in statuses])),
    }


def run_p14_benchmark(
    store_path: str | Path,
    *,
    reset_store: bool = True,
    seed: int = 20260916,
) -> dict[str, Any]:
    """Synthetic family-evolution benchmark for registry topology and guardrails."""

    store_path = Path(store_path)
    if reset_store and store_path.exists():
        shutil.rmtree(store_path)
    registry = PersistentFamilyRegistry(store_path)
    guard = FamilyEvolutionGuard(
        max_negative_capture_delta=0.01,
        max_clean_ambiguity_delta=0.02,
        max_clean_exact_drop=0.02,
    )
    rng = np.random.default_rng(seed)
    dim = 16
    basis = np.eye(dim)
    negatives = _negative_probe_suite(dim, rng)

    # One intentionally broad root family contains two distinct validated modes.
    parent_direction = basis[0]
    mode_a = _unit(basis[0] + 0.35 * basis[1])
    mode_b = _unit(basis[0] - 0.35 * basis[1])
    parent = _definition(
        "adaptive-root",
        parent_direction,
        threshold=0.90,
        parent_lineage="active-parent-p14",
    )
    parent_id = registry.register(parent, provenance={"phase": "P1.4", "role": "bimodal root"})
    parent_hash = registry.definition_hash(parent_id)
    pre_split_a = registry.route(mode_a, mode_a)
    pre_split_b = registry.route(mode_b, mode_b)

    # Split the broad root into two immutable successor families. The guard
    # evaluates the post-split topology, with the parent removed.
    child_a = _definition("adaptive-a", mode_a, threshold=0.93, parent_lineage=parent_id)
    child_b = _definition("adaptive-b", mode_b, threshold=0.93, parent_lineage=parent_id)
    split_clean = [
        *_probes_around(mode_a, family_id=child_a.family_id, rng=rng, label="split-a"),
        *_probes_around(mode_b, family_id=child_b.family_id, rng=rng, label="split-b"),
    ]
    split_decision, child_ids = guard.guarded_split(
        registry,
        parent_id,
        [child_a, child_b],
        clean_probes=split_clean,
        negative_probes=negatives,
        reason="validated bimodal behavior requires separate routing families",
        provenance={"phase": "P1.4", "control": "guarded split"},
    )
    post_split_a = registry.route(mode_a, mode_a)
    post_split_b = registry.route(mode_b, mode_b)
    bridge = _unit(mode_a + mode_b)
    bridge_route = registry.route(bridge, bridge)

    # Retire/reactivate is operational state only. The immutable child hash must
    # remain unchanged and the state must survive a registry reload.
    child_b_hash = registry.definition_hash(child_b.family_id)
    registry.set_status(child_b.family_id, "retired", reason="synthetic temporary retirement")
    retired_route = registry.route(mode_b, mode_b)
    registry.set_status(child_b.family_id, "active", reason="validated reactivation")
    reactivated_route = registry.route(mode_b, mode_b)
    child_b_hash_after = registry.definition_hash(child_b.family_id)

    capture_history: list[dict[str, Any]] = [
        {"stage": "after_split", **_capture_rate(registry, negatives)}
    ]

    # Add several narrow, orthogonal families through the evolution guard. This
    # is the long-run control: growth should not silently widen negative capture.
    known_clean: list[EvolutionProbe] = [
        *_probes_around(mode_a, family_id=child_a.family_id, rng=rng, label="known-a", count=10),
        *_probes_around(mode_b, family_id=child_b.family_id, rng=rng, label="known-b", count=10),
    ]
    narrow_additions: list[dict[str, Any]] = []
    narrow_ids: list[str] = []
    for i in range(2, 8):
        definition = _definition(
            f"narrow-{i}",
            basis[i],
            threshold=0.97,
            parent_lineage="active-parent-p14",
            risk="high" if i % 2 else "medium",
        )
        candidate_probes = _probes_around(
            basis[i],
            family_id=definition.family_id,
            rng=rng,
            label=f"candidate-{i}",
            count=10,
            noise=0.006,
        )
        decision = guard.guarded_register(
            registry,
            definition,
            clean_probes=[*known_clean, *candidate_probes],
            negative_probes=negatives,
            provenance={"phase": "P1.4", "sequence": i},
        )
        if decision.approved:
            narrow_ids.append(definition.family_id)
            known_clean.extend(candidate_probes)
        narrow_additions.append({"name": definition.name, **decision.to_dict()})
        capture_history.append({"stage": f"after_{definition.name}", **_capture_rate(registry, negatives)})

    # A near-duplicate successor would make an existing family ambiguous.
    overlap = _definition(
        "unsafe-overlap-a",
        _unit(mode_a + 0.015 * basis[2]),
        threshold=0.92,
        parent_lineage="active-parent-p14",
    )
    overlap_decision = guard.guarded_register(
        registry,
        overlap,
        clean_probes=known_clean,
        negative_probes=negatives,
        provenance={"phase": "P1.4", "control": "overlap rejection"},
    )

    # A deliberately broad family captures negatives and must be rejected.
    broad = _definition(
        "unsafe-broad",
        np.ones(dim),
        threshold=0.12,
        parent_lineage="active-parent-p14",
    )
    broad_decision = guard.guarded_register(
        registry,
        broad,
        clean_probes=known_clean,
        negative_probes=negatives,
        provenance={"phase": "P1.4", "control": "broad family rejection"},
    )
    final_capture = _capture_rate(registry, negatives)
    capture_history.append({"stage": "final", **final_capture})

    registry = PersistentFamilyRegistry(store_path)
    statuses = {fid: status for fid, _, status in registry.list(include_inactive=True)}
    active_ids = {fid for fid, _, status in registry.list(include_inactive=True) if status == "active"}
    max_capture = max(item["unsafe_capture"] for item in capture_history)

    observed = {
        "root_represents_both_modes_before_split": (
            pre_split_a.family_id == parent_id and pre_split_b.family_id == parent_id
        ),
        "guarded_split_approved": split_decision.approved and len(child_ids) == 2,
        "parent_retired_after_split": statuses.get(parent_id) == "retired",
        "split_children_route_uniquely": (
            post_split_a.family_id == child_a.family_id and post_split_b.family_id == child_b.family_id
        ),
        "bridge_routes_to_deliberation_as_ambiguous": bridge_route.status == "ambiguous",
        "retired_child_stops_routing": retired_route.status == "unknown",
        "reactivated_child_routes_again": reactivated_route.family_id == child_b.family_id,
        "reactivation_preserves_definition_hash": child_b_hash == child_b_hash_after,
        "all_narrow_additions_approved": all(item["approved"] for item in narrow_additions),
        "overlapping_family_rejected": not overlap_decision.approved,
        "broad_family_rejected": not broad_decision.approved,
        "rejected_families_not_active": (
            overlap.family_id not in active_ids and broad.family_id not in active_ids
        ),
        "negative_capture_does_not_increase": max_capture <= capture_history[0]["unsafe_capture"] + 1e-12,
        "parent_definition_hash_unchanged": registry.definition_hash(parent_id) == parent_hash,
    }

    return {
        "claim_level": "synthetic family-evolution and non-permissivity benchmark",
        "scope_note": (
            "P1.4 tests routing topology, split/retire/reactivate lifecycle, and a fixed-probe evolution guard. "
            "It does not establish semantic safety or universal OOD guarantees."
        ),
        "research_sources": {
            "z_manifold": "https://github.com/infinition/z-manifold",
            "z_manifold_paper": "https://arxiv.org/abs/2607.05300",
            "drift_contract": "https://github.com/infinition/drift-contract",
            "drift_preprint": "https://infinition.github.io/infinition/assets/papers/drift-bounded-spectral-updates.pdf",
        },
        "store_path": str(store_path),
        "split": {
            "parent_family_id": parent_id,
            "child_family_ids": child_ids,
            "decision": split_decision.to_dict(),
            "bridge_route": {
                "status": bridge_route.status,
                "match_count": len(bridge_route.matches),
                "matches": bridge_route.matches,
            },
        },
        "retire_reactivate": {
            "child_family_id": child_b.family_id,
            "retired_route_status": retired_route.status,
            "reactivated_route_status": reactivated_route.status,
            "definition_hash_unchanged": child_b_hash == child_b_hash_after,
        },
        "long_run": {
            "narrow_additions": narrow_additions,
            "capture_history": capture_history,
            "final_active_family_count": len(registry.list()),
            "all_family_count": len(registry.list(include_inactive=True)),
        },
        "unsafe_controls": {
            "overlap": overlap_decision.to_dict(),
            "broad": broad_decision.to_dict(),
        },
        "persistence": {
            "event_count": len(registry.events()),
            "statuses": statuses,
        },
        "observed": observed,
    }
