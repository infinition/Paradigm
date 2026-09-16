from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np

from .family_registry import FamilyDefinition, FamilyRoute, PersistentFamilyRegistry


def _normalized(x: np.ndarray | list[float]) -> np.ndarray:
    v = np.asarray(x, dtype=np.float64)
    return v / (np.linalg.norm(v) + 1e-12)


def _route_against_definitions(
    parameter_signature: np.ndarray,
    behavior_signature: np.ndarray,
    definitions: Iterable[tuple[str, FamilyDefinition]],
) -> FamilyRoute:
    p = _normalized(parameter_signature)
    b = _normalized(behavior_signature)
    matches: list[dict[str, object]] = []
    for family_id, definition in definitions:
        ps = float(p @ _normalized(definition.parameter_prototype))
        bs = float(b @ _normalized(definition.behavior_prototype))
        if ps >= definition.parameter_threshold and bs >= definition.behavior_threshold:
            matches.append(
                {
                    "family_id": family_id,
                    "family_name": definition.name,
                    "parameter_similarity": ps,
                    "behavior_similarity": bs,
                    "margin": min(ps - definition.parameter_threshold, bs - definition.behavior_threshold),
                }
            )
    if not matches:
        return FamilyRoute("unknown", None, None, "no active family accepts both signatures", [])
    matches.sort(key=lambda item: float(item["margin"]), reverse=True)
    if len(matches) > 1:
        return FamilyRoute("ambiguous", None, None, "multiple active families accept the candidate", matches)
    match = matches[0]
    return FamilyRoute(
        "represented",
        str(match["family_id"]),
        str(match["family_name"]),
        "single family match",
        matches,
    )


@dataclass(frozen=True, slots=True)
class EvolutionProbe:
    parameter_signature: list[float]
    behavior_signature: list[float]
    expected_family_id: str | None = None
    label: str = ""

    def arrays(self) -> tuple[np.ndarray, np.ndarray]:
        return (
            np.asarray(self.parameter_signature, dtype=np.float64),
            np.asarray(self.behavior_signature, dtype=np.float64),
        )


@dataclass(frozen=True, slots=True)
class EvolutionMetrics:
    represented_rate: float
    ambiguous_rate: float
    unknown_rate: float
    exact_family_rate: float | None


@dataclass(frozen=True, slots=True)
class EvolutionDecision:
    approved: bool
    candidate_family_id: str
    baseline_negative_capture: float
    proposed_negative_capture: float
    negative_capture_delta: float
    baseline_clean_ambiguity: float
    proposed_clean_ambiguity: float
    clean_ambiguity_delta: float
    baseline_clean_exact: float
    proposed_clean_exact: float
    clean_exact_delta: float
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class FamilyEvolutionGuard:
    """Evaluate whether a new family makes routing materially more permissive.

    The guard never treats geometry as semantic proof. It only prevents a family
    map from silently widening its routing surface on a fixed probe suite.
    """

    def __init__(
        self,
        *,
        max_negative_capture_delta: float = 0.01,
        max_clean_ambiguity_delta: float = 0.02,
        max_clean_exact_drop: float = 0.02,
    ) -> None:
        self.max_negative_capture_delta = float(max_negative_capture_delta)
        self.max_clean_ambiguity_delta = float(max_clean_ambiguity_delta)
        self.max_clean_exact_drop = float(max_clean_exact_drop)

    @staticmethod
    def _definitions(registry: PersistentFamilyRegistry) -> list[tuple[str, FamilyDefinition]]:
        return [(fid, definition) for fid, definition, _ in registry.list(include_inactive=False)]

    @staticmethod
    def _measure(
        definitions: list[tuple[str, FamilyDefinition]],
        probes: list[EvolutionProbe],
    ) -> EvolutionMetrics:
        if not probes:
            return EvolutionMetrics(0.0, 0.0, 0.0, None)
        statuses: list[str] = []
        exact: list[bool] = []
        has_expected = any(p.expected_family_id is not None for p in probes)
        for probe in probes:
            p, b = probe.arrays()
            route = _route_against_definitions(p, b, definitions)
            statuses.append(route.status)
            if probe.expected_family_id is not None:
                exact.append(route.status == "represented" and route.family_id == probe.expected_family_id)
        return EvolutionMetrics(
            represented_rate=float(np.mean([s == "represented" for s in statuses])),
            ambiguous_rate=float(np.mean([s == "ambiguous" for s in statuses])),
            unknown_rate=float(np.mean([s == "unknown" for s in statuses])),
            exact_family_rate=float(np.mean(exact)) if has_expected and exact else None,
        )

    def evaluate_addition(
        self,
        registry: PersistentFamilyRegistry,
        candidate: FamilyDefinition,
        *,
        clean_probes: list[EvolutionProbe],
        negative_probes: list[EvolutionProbe],
    ) -> EvolutionDecision:
        baseline = self._definitions(registry)
        proposed = [*baseline, (candidate.family_id, candidate)]
        clean_base = self._measure(baseline, clean_probes)
        clean_new = self._measure(proposed, clean_probes)
        neg_base = self._measure(baseline, negative_probes)
        neg_new = self._measure(proposed, negative_probes)

        base_capture = neg_base.represented_rate + neg_base.ambiguous_rate
        new_capture = neg_new.represented_rate + neg_new.ambiguous_rate
        capture_delta = new_capture - base_capture
        ambiguity_delta = clean_new.ambiguous_rate - clean_base.ambiguous_rate
        base_exact = clean_base.exact_family_rate if clean_base.exact_family_rate is not None else 1.0
        new_exact = clean_new.exact_family_rate if clean_new.exact_family_rate is not None else 1.0
        exact_delta = new_exact - base_exact

        reasons: list[str] = []
        if capture_delta > self.max_negative_capture_delta + 1e-12:
            reasons.append(
                f"negative capture delta {capture_delta:.4f} exceeds {self.max_negative_capture_delta:.4f}"
            )
        if ambiguity_delta > self.max_clean_ambiguity_delta + 1e-12:
            reasons.append(
                f"clean ambiguity delta {ambiguity_delta:.4f} exceeds {self.max_clean_ambiguity_delta:.4f}"
            )
        if exact_delta < -self.max_clean_exact_drop - 1e-12:
            reasons.append(
                f"clean exact-family delta {exact_delta:.4f} is below {-self.max_clean_exact_drop:.4f}"
            )
        return EvolutionDecision(
            approved=not reasons,
            candidate_family_id=candidate.family_id,
            baseline_negative_capture=float(base_capture),
            proposed_negative_capture=float(new_capture),
            negative_capture_delta=float(capture_delta),
            baseline_clean_ambiguity=float(clean_base.ambiguous_rate),
            proposed_clean_ambiguity=float(clean_new.ambiguous_rate),
            clean_ambiguity_delta=float(ambiguity_delta),
            baseline_clean_exact=float(base_exact),
            proposed_clean_exact=float(new_exact),
            clean_exact_delta=float(exact_delta),
            reasons=tuple(reasons),
        )


    def evaluate_replacement(
        self,
        registry: PersistentFamilyRegistry,
        *,
        retire_family_ids: list[str],
        replacements: list[FamilyDefinition],
        clean_probes: list[EvolutionProbe],
        negative_probes: list[EvolutionProbe],
    ) -> EvolutionDecision:
        baseline = self._definitions(registry)
        retired = set(retire_family_ids)
        proposed = [(fid, definition) for fid, definition in baseline if fid not in retired]
        proposed.extend((definition.family_id, definition) for definition in replacements)

        clean_base = self._measure(baseline, clean_probes)
        clean_new = self._measure(proposed, clean_probes)
        neg_base = self._measure(baseline, negative_probes)
        neg_new = self._measure(proposed, negative_probes)

        base_capture = neg_base.represented_rate + neg_base.ambiguous_rate
        new_capture = neg_new.represented_rate + neg_new.ambiguous_rate
        capture_delta = new_capture - base_capture
        ambiguity_delta = clean_new.ambiguous_rate - clean_base.ambiguous_rate
        base_exact = clean_base.exact_family_rate if clean_base.exact_family_rate is not None else 1.0
        new_exact = clean_new.exact_family_rate if clean_new.exact_family_rate is not None else 1.0
        exact_delta = new_exact - base_exact

        reasons: list[str] = []
        if capture_delta > self.max_negative_capture_delta + 1e-12:
            reasons.append(
                f"negative capture delta {capture_delta:.4f} exceeds {self.max_negative_capture_delta:.4f}"
            )
        if ambiguity_delta > self.max_clean_ambiguity_delta + 1e-12:
            reasons.append(
                f"clean ambiguity delta {ambiguity_delta:.4f} exceeds {self.max_clean_ambiguity_delta:.4f}"
            )
        if exact_delta < -self.max_clean_exact_drop - 1e-12:
            reasons.append(
                f"clean exact-family delta {exact_delta:.4f} is below {-self.max_clean_exact_drop:.4f}"
            )
        replacement_id = "replace:" + ",".join(sorted(d.family_id for d in replacements))
        return EvolutionDecision(
            approved=not reasons,
            candidate_family_id=replacement_id,
            baseline_negative_capture=float(base_capture),
            proposed_negative_capture=float(new_capture),
            negative_capture_delta=float(capture_delta),
            baseline_clean_ambiguity=float(clean_base.ambiguous_rate),
            proposed_clean_ambiguity=float(clean_new.ambiguous_rate),
            clean_ambiguity_delta=float(ambiguity_delta),
            baseline_clean_exact=float(base_exact),
            proposed_clean_exact=float(new_exact),
            clean_exact_delta=float(exact_delta),
            reasons=tuple(reasons),
        )

    def guarded_split(
        self,
        registry: PersistentFamilyRegistry,
        parent_family_id: str,
        child_definitions: list[FamilyDefinition],
        *,
        clean_probes: list[EvolutionProbe],
        negative_probes: list[EvolutionProbe],
        reason: str,
        provenance: dict[str, object] | None = None,
    ) -> tuple[EvolutionDecision, list[str]]:
        decision = self.evaluate_replacement(
            registry,
            retire_family_ids=[parent_family_id],
            replacements=child_definitions,
            clean_probes=clean_probes,
            negative_probes=negative_probes,
        )
        registry.record_evolution(
            "family_split_evaluated",
            {
                "parent_family_id": parent_family_id,
                "child_family_ids": [d.family_id for d in child_definitions],
                "decision": decision.to_dict(),
            },
        )
        if not decision.approved:
            return decision, []
        child_ids = registry.split_family(
            parent_family_id,
            child_definitions,
            reason=reason,
            provenance={"evolution_guard": decision.to_dict(), **(provenance or {})},
        )
        return decision, child_ids
    def guarded_register(
        self,
        registry: PersistentFamilyRegistry,
        candidate: FamilyDefinition,
        *,
        clean_probes: list[EvolutionProbe],
        negative_probes: list[EvolutionProbe],
        provenance: dict[str, object] | None = None,
    ) -> EvolutionDecision:
        decision = self.evaluate_addition(
            registry,
            candidate,
            clean_probes=clean_probes,
            negative_probes=negative_probes,
        )
        registry.record_evolution(
            "family_addition_evaluated",
            {"candidate_family_id": candidate.family_id, "decision": decision.to_dict()},
        )
        if decision.approved:
            registry.register(candidate, provenance={"evolution_guard": decision.to_dict(), **(provenance or {})})
        return decision
