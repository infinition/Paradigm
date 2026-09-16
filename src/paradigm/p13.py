from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import numpy as np

from .family_registry import FamilyDefinition, PersistentFamilyRegistry
from .p11 import _base_train, _make_domains
from .p12 import (
    CandidateEvidence,
    CosinePrototypeGate,
    RISK_EPSILON,
    _adapt_family_candidate,
    _calibrated_floor,
    _fixed_anchor_domains,
)


def _candidate_update_id(candidate: CandidateEvidence) -> str:
    payload = np.concatenate([candidate.parameter_signature, candidate.behavior_signature]).astype(np.float64).tobytes()
    digest = hashlib.sha256(payload).hexdigest()
    return f"upd-{digest[:24]}"


def _extended_domains_and_anchors() -> tuple[list[np.ndarray], np.ndarray, list[np.ndarray]]:
    domains, y = _make_domains(4242)
    anchors = _fixed_anchor_domains()

    task_rng = np.random.default_rng(20260916)
    task_rng.normal(size=(40, 24))
    task_rng.normal(size=(4, 40))
    current = np.eye(24)
    for _ in range(3):
        q, _ = np.linalg.qr(task_rng.normal(size=(24, 24)))
        current = current @ q
    q4, _ = np.linalg.qr(task_rng.normal(size=(24, 24)))
    transform4 = current @ q4
    domains.append(domains[0] @ transform4)
    anchors.append(anchors[0] @ transform4)
    return domains, y, anchors


def _fit_family_definition(
    *,
    name: str,
    family: int,
    risk: str,
    candidates: list[CandidateEvidence],
    parent_lineage: str,
) -> FamilyDefinition:
    fit = candidates[:8]
    cal = candidates[8:14]
    pgate = CosinePrototypeGate().fit(
        np.stack([c.parameter_signature for c in fit]),
        np.stack([c.parameter_signature for c in cal]),
    )
    bgate = CosinePrototypeGate().fit(
        np.stack([c.behavior_signature for c in fit]),
        np.stack([c.behavior_signature for c in cal]),
    )
    floors = {
        "current_accuracy": _calibrated_floor([c.current_accuracy for c in cal]),
        "protected_accuracy": _calibrated_floor([c.protected_accuracy for c in cal]),
        "minimum_class_accuracy": _calibrated_floor([c.minimum_class_accuracy for c in cal]),
        "subgroup_accuracy": _calibrated_floor([c.subgroup_accuracy for c in cal]),
    }
    return FamilyDefinition(
        name=name,
        risk=risk,
        maximum_epsilon=RISK_EPSILON[risk],
        parameter_prototype=pgate.prototype_.tolist(),
        parameter_threshold=float(pgate.threshold_),
        behavior_prototype=bgate.prototype_.tolist(),
        behavior_threshold=float(bgate.threshold_),
        semantic_floors=floors,
        parent_lineage=parent_lineage,
    )


def run_p13_benchmark(
    store_path: str | Path,
    *,
    reset_store: bool = True,
    steps: int = 75,
) -> dict[str, Any]:
    store_path = Path(store_path)
    if reset_store and store_path.exists():
        shutil.rmtree(store_path)
    registry = PersistentFamilyRegistry(store_path)

    domains, y, anchors = _extended_domains_and_anchors()
    train_idx = np.arange(0, 5000)
    parent = _base_train(5151, domains[0][train_idx], y[train_idx], steps=650)
    parent_lineage = "active-parent-p13-fixed"
    family_risk = {1: "low", 2: "medium", 3: "high", 4: "medium"}
    train_seeds = [101, 113, 127, 139, 151, 163, 179, 191, 211, 227, 239, 251, 263, 277]
    heldout_seed = {1: 601, 2: 607, 3: 613, 4: 619}

    family_candidates: dict[int, list[CandidateEvidence]] = {}
    family_ids: dict[int, str] = {}
    for family in (1, 2, 3):
        risk = family_risk[family]
        candidates = [
            _adapt_family_candidate(
                parent,
                domains,
                y,
                family=family,
                seed=seed,
                epsilon=RISK_EPSILON[risk],
                steps=steps,
                replay=True,
                anchors=anchors,
            )
            for seed in train_seeds
        ]
        family_candidates[family] = candidates
        definition = _fit_family_definition(
            name=f"shift-family-{family}",
            family=family,
            risk=risk,
            candidates=candidates,
            parent_lineage=parent_lineage,
        )
        family_ids[family] = registry.register(
            definition,
            provenance={"phase": "P1.3", "family": family, "validated_candidates": len(candidates)},
        )

    initial_hashes = {family: registry.definition_hash(fid) for family, fid in family_ids.items()}

    heldout: dict[int, CandidateEvidence] = {}
    routes: dict[str, Any] = {}
    manifests: dict[str, Any] = {}
    for family in (1, 2, 3):
        risk = family_risk[family]
        candidate = _adapt_family_candidate(
            parent,
            domains,
            y,
            family=family,
            seed=heldout_seed[family],
            epsilon=RISK_EPSILON[risk],
            steps=steps,
            replay=True,
            anchors=anchors,
        )
        heldout[family] = candidate
        route = registry.route(candidate.parameter_signature, candidate.behavior_signature)
        manifest = registry.build_manifest(
            candidate_name=f"heldout-family-{family}",
            route=route,
            epsilon_used=candidate.epsilon,
            current_accuracy=candidate.current_accuracy,
            protected_accuracy=candidate.protected_accuracy,
            minimum_class_accuracy=candidate.minimum_class_accuracy,
            subgroup_accuracy=candidate.subgroup_accuracy,
        )
        update_id = _candidate_update_id(candidate)
        registry.record_manifest(update_id, manifest)
        routes[f"family_{family}"] = {
            "status": route.status,
            "family_id": route.family_id,
            "expected_family_id": family_ids[family],
            "correct": route.family_id == family_ids[family],
        }
        manifests[f"family_{family}"] = manifest.to_dict()

    # Unknown-family control. No existing threshold is changed to accommodate it.
    unknown_candidates = [
        _adapt_family_candidate(
            parent,
            domains,
            y,
            family=4,
            seed=seed,
            epsilon=RISK_EPSILON[family_risk[4]],
            steps=steps,
            replay=True,
            anchors=anchors,
        )
        for seed in train_seeds
    ]
    unknown_heldout = _adapt_family_candidate(
        parent,
        domains,
        y,
        family=4,
        seed=heldout_seed[4],
        epsilon=RISK_EPSILON[family_risk[4]],
        steps=steps,
        replay=True,
        anchors=anchors,
    )
    before_route = registry.route(unknown_heldout.parameter_signature, unknown_heldout.behavior_signature)

    new_definition = _fit_family_definition(
        name="shift-family-4",
        family=4,
        risk=family_risk[4],
        candidates=unknown_candidates,
        parent_lineage=parent_lineage,
    )
    family4_id = registry.register(
        new_definition,
        provenance={"phase": "P1.3", "family": 4, "reason": "validated unknown-family expansion"},
    )
    after_hashes = {family: registry.definition_hash(fid) for family, fid in family_ids.items()}
    after_route = registry.route(unknown_heldout.parameter_signature, unknown_heldout.behavior_signature)

    # Geometry can pass while semantics fail. This uses the same clean signatures
    # and only alters the evidence supplied to the manifest.
    family2 = heldout[2]
    route2 = registry.route(family2.parameter_signature, family2.behavior_signature)
    semantic_failure = registry.build_manifest(
        candidate_name="family-2-semantic-regression-control",
        route=route2,
        epsilon_used=family2.epsilon,
        current_accuracy=family2.current_accuracy,
        protected_accuracy=family2.protected_accuracy,
        minimum_class_accuracy=family2.minimum_class_accuracy,
        subgroup_accuracy=0.0,
        metadata={"control": "semantic evidence failure with unchanged geometry"},
    )
    registry.record_manifest("upd-semantic-regression-control", semantic_failure)

    # Risk-policy control. A high-risk family candidate must not use a low-risk budget.
    family3 = heldout[3]
    route3 = registry.route(family3.parameter_signature, family3.behavior_signature)
    epsilon_failure = registry.build_manifest(
        candidate_name="family-3-epsilon-violation-control",
        route=route3,
        epsilon_used=RISK_EPSILON["low"],
        current_accuracy=family3.current_accuracy,
        protected_accuracy=family3.protected_accuracy,
        minimum_class_accuracy=family3.minimum_class_accuracy,
        subgroup_accuracy=family3.subgroup_accuracy,
        metadata={"control": "plasticity budget violation"},
    )
    registry.record_manifest("upd-epsilon-violation-control", epsilon_failure)

    # Post-promotion family quarantine. The immutable definition remains on disk,
    # but routing stops assigning new candidates to it.
    family2_hash_before_quarantine = registry.definition_hash(family_ids[2])
    registry.set_status(family_ids[2], "quarantined", reason="synthetic delayed subgroup regression")
    quarantined_route = registry.route(family2.parameter_signature, family2.behavior_signature)
    family2_hash_after_quarantine = registry.definition_hash(family_ids[2])

    # Reload the registry to verify operational state is persistent.
    registry = PersistentFamilyRegistry(store_path)
    reloaded_status = {fid: status for fid, _, status in registry.list(include_inactive=True)}

    return {
        "claim_level": "synthetic persistent family lifecycle benchmark",
        "scope_note": (
            "P1.3 persists immutable family definitions and mutable operational status separately. "
            "Unknown or quarantined families route to deliberation. Family geometry remains auxiliary evidence."
        ),
        "research_sources": {
            "drift_contract": "https://github.com/infinition/drift-contract",
            "drift_preprint": "https://infinition.github.io/infinition/assets/papers/drift-bounded-spectral-updates.pdf",
            "z_manifold": "https://github.com/infinition/z-manifold",
            "z_manifold_paper": "https://arxiv.org/abs/2607.05300",
        },
        "store_path": str(store_path),
        "initial_family_ids": {str(k): v for k, v in family_ids.items()},
        "heldout_routing": routes,
        "heldout_manifests": manifests,
        "unknown_family": {
            "before_validation": {"status": before_route.status, "family_id": before_route.family_id},
            "registered_family_id": family4_id,
            "after_validation": {"status": after_route.status, "family_id": after_route.family_id},
            "existing_family_hashes_unchanged": initial_hashes == after_hashes,
        },
        "semantic_failure_control": semantic_failure.to_dict(),
        "epsilon_violation_control": epsilon_failure.to_dict(),
        "quarantine": {
            "family_id": family_ids[2],
            "route_after_quarantine": {
                "status": quarantined_route.status,
                "family_id": quarantined_route.family_id,
            },
            "definition_hash_unchanged": family2_hash_before_quarantine == family2_hash_after_quarantine,
            "status_after_reload": reloaded_status.get(family_ids[2]),
        },
        "persistence": {
            "event_count": len(registry.events()),
            "active_family_count": len(registry.list()),
            "all_family_count": len(registry.list(include_inactive=True)),
        },
        "observed": {
            "represented_families_route_correctly": all(item["correct"] for item in routes.values()),
            "unknown_routes_to_deliberation": before_route.status == "unknown",
            "validated_new_family_routes_after_registration": after_route.family_id == family4_id,
            "family_expansion_does_not_modify_existing_definitions": initial_hashes == after_hashes,
            "semantic_failure_blocks_manifest": not semantic_failure.approved,
            "epsilon_violation_blocks_manifest": not epsilon_failure.approved,
            "quarantine_removes_family_from_routing": quarantined_route.family_id != family_ids[2],
            "quarantine_persists_after_reload": reloaded_status.get(family_ids[2]) == "quarantined",
        },
    }
