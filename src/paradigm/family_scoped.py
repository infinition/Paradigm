"""Family-scoped certification: one compiled artifact, an authorization verdict per family.

Predicted by P2.3R-bis and confirmed in the real LaRuche loop: a single whole-candidate
verdict lets one unstable family block every stable one. Here the candidate is fitted
once on all validated traces, and each behavior family is then certified on its own with
the existing criteria, unchanged:

- quality: confidence threshold selected on that family's held-out traces by the same
  selector rule (selective accuracy within 0.01 of the teacher, coverage >= 0.55),
  ECE <= 0.10 on that family;
- trust: shadow OOD acceptance >= 0.65 on that family's held-out traces;
- retention: for a family with frozen probes, coverage and agreement floors and no
  coverage regression against the incumbent.

A family with no held-out evidence is ``insufficient``. Families that pass are active;
the others stay deliberative. Nothing is lowered.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .equivalence import EquivalenceContract, collapse_to_classes, same_class
from .evaluation import expected_calibration_error
from .ood import MahalanobisGate
from .schema import Trace
from .selection import select_confidence_threshold


@dataclass(slots=True)
class FamilyCriteria:
    minimum_coverage: float = 0.55
    maximum_ece: float = 0.10
    accuracy_tolerance: float = 0.01
    minimum_ood_acceptance: float = 0.65
    probe_coverage_floor: float = 0.65
    probe_accuracy_floor: float = 0.95
    probe_coverage_regression_tolerance: float = 0.10
    min_validation_episodes: int = 1
    # An active family with frozen probes and no held-out trace in the current split is
    # certified on its probes at the incumbent threshold instead of being "insufficient".
    probe_recertification: bool = False
    # Minimum number of fresh held-out traces for an active family before the held-out
    # rule alone decides; below it, the probes are the evidence (1 = only when none).
    min_fresh_support: int = 1
    # Probe branch only: classify each covered fresh disagreement against the incumbent.
    # A veto needs a candidate regression (incumbent agrees with the teacher, candidate
    # does not); a disagreement the incumbent shares, with a still-valid incumbent action,
    # is an alternative trajectory. Off: any covered disagreement is a veto.
    triadic_veto: bool = False
    # Behavioral equivalence for quality, calibration, probe agreement and the fresh
    # classification. None is literal identity.
    equivalence: EquivalenceContract | None = None


@dataclass(slots=True)
class FamilyVerdict:
    family: str
    status: str  # active | rejected | insufficient
    reason: str
    train_traces: int = 0
    validation_traces: int = 0
    validation_episodes: int = 0
    distinct_actions: int = 0
    threshold: float | None = None
    coverage: float | None = None
    selective_accuracy: float | None = None
    ece: float | None = None
    gate_acceptance: float | None = None
    retention: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "status": self.status,
            "reason": self.reason,
            "train_traces": self.train_traces,
            "validation_traces": self.validation_traces,
            "validation_episodes": self.validation_episodes,
            "distinct_actions": self.distinct_actions,
            "threshold": self.threshold,
            "coverage": self.coverage,
            "selective_accuracy": self.selective_accuracy,
            "ece": self.ece,
            "gate_acceptance": self.gate_acceptance,
            "retention": self.retention,
        }


def _family_of(trace: Trace) -> str:
    return str(trace.metadata.get("family", "unknown"))


def probe_scores(
    reflex, gate: MahalanobisGate, threshold: float, traces: list[Trace], contract: EquivalenceContract | None = None
) -> tuple[float, float]:
    coverage, agreement, _, _ = probe_report(reflex, gate, threshold, traces, contract)
    return coverage, agreement


def probe_report(
    reflex, gate: MahalanobisGate, threshold: float, traces: list[Trace], contract: EquivalenceContract | None = None
) -> tuple[float, float, float, float]:
    """Coverage, agreement, gate acceptance and ECE of one artifact on a probe set, in class
    space when a contract is given."""
    x = np.stack([t.features for t in traces])
    y = np.asarray([t.action for t in traces]).astype(str)
    accepted = np.asarray(gate.accept(x), dtype=bool)
    preds, confs = [], []
    for row in x:
        action, confidence, _ = reflex.predict(row)
        preds.append(str(action))
        confs.append(float(confidence))
    covered = accepted & (np.asarray(confs) >= threshold)
    coverage = float(np.mean(covered))
    hits = np.asarray([same_class(p, t, contract) for p, t in zip(preds, y)])
    agreement = float(np.mean(hits[covered])) if covered.any() else 0.0
    y_c, probs_c, classes_c = collapse_to_classes(y, reflex.predict_proba(x), reflex.classes_.astype(str), contract)
    ece = float(expected_calibration_error(y_c, probs_c, classes_c))
    return coverage, agreement, float(np.mean(accepted)), ece


def certify_families(
    reflex,
    gate: MahalanobisGate,
    train: list[Trace],
    validation: list[Trace],
    *,
    probes: dict[str, list[Trace]] | None = None,
    incumbent: tuple[Any, MahalanobisGate, dict[str, float]] | None = None,
    criteria: FamilyCriteria | None = None,
    probe_contracts: dict[str, dict[str, Any] | None] | None = None,
) -> dict[str, FamilyVerdict]:
    """Certify every family seen in train or validation independently.

    ``incumbent`` is (reflex, gate, thresholds_by_family) of the active artifact, used only
    for the coverage-regression check on probe families. ``probe_contracts`` gives, per
    family, the materialized contract its probe set was frozen under; a probe set is
    scored under that contract (identity when None), and rescored diagnostically under the
    current one when the two differ. Historical verdicts are never rewritten.
    """
    crit = criteria or FamilyCriteria()
    probes = probes or {}
    probe_contracts = probe_contracts or {}
    train_by: dict[str, list[Trace]] = {}
    for t in train:
        train_by.setdefault(_family_of(t), []).append(t)
    val_by: dict[str, list[Trace]] = {}
    for t in validation:
        val_by.setdefault(_family_of(t), []).append(t)

    verdicts: dict[str, FamilyVerdict] = {}
    for family in sorted(set(train_by) | set(val_by)):
        tr = train_by.get(family, [])
        va = val_by.get(family, [])
        distinct = len({t.action for t in tr + va})
        verdict = FamilyVerdict(family, "insufficient", "", len(tr), len(va), len({str(t.metadata.get("task_id")) for t in va}), distinct)
        inc_thr = incumbent[2].get(family) if incumbent is not None else None
        sparse = crit.probe_recertification and inc_thr is not None and bool(probes.get(family)) and len(va) < crit.min_fresh_support
        valid_actions = {str(t.action) for t in tr} | {str(t.action) for t in probes.get(family, [])}
        if sparse:
            verdicts[family] = _recertify_on_probes(
                verdict, reflex, gate, incumbent, float(inc_thr), probes[family], crit, fresh=va, valid_actions=valid_actions,
                probe_contract=probe_contracts.get(family),
            )
            continue
        if verdict.validation_episodes < crit.min_validation_episodes or not va:
            verdict.reason = "no_held_out_evidence"
            verdicts[family] = verdict
            continue
        x_val = np.stack([t.features for t in va])
        y_val = np.asarray([t.action for t in va]).astype(str)
        probs = reflex.predict_proba(x_val)
        classes = reflex.classes_.astype(str)
        y_s, probs_s, classes_s = collapse_to_classes(y_val, probs, classes, crit.equivalence)
        thr = select_confidence_threshold(
            y_s, probs_s, classes_s, reference_predictions=y_s, tolerance=crit.accuracy_tolerance, minimum_coverage=crit.minimum_coverage
        )
        ece = float(expected_calibration_error(y_s, probs_s, classes_s))
        literal_preds = classes[np.argmax(probs, axis=1)]
        verdict.retention["literal_agreement"] = float(np.mean(literal_preds == y_val))
        verdict.retention["equivalent_agreement"] = float(np.mean([same_class(p, t, crit.equivalence) for p, t in zip(literal_preds, y_val)]))
        accepted = np.asarray(gate.accept(x_val), dtype=bool)
        acceptance = float(np.mean(accepted))
        verdict.threshold = float(thr.threshold)
        verdict.coverage = float(thr.coverage)
        verdict.selective_accuracy = float(thr.selective_accuracy)
        verdict.ece = ece
        verdict.gate_acceptance = acceptance
        failures: list[str] = []
        if not thr.feasible:
            failures.append("quality")
        if ece > crit.maximum_ece:
            failures.append("calibration")
        if acceptance < crit.minimum_ood_acceptance:
            failures.append("trust")
        if family in probes and probes[family]:
            frozen = _frozen_contract(probe_contracts.get(family))
            coverage, agreement = probe_scores(reflex, gate, float(thr.threshold), probes[family], frozen)
            retention: dict[str, Any] = {**verdict.retention, "probes": len(probes[family]), "coverage": coverage, "agreement": agreement, "incumbent_coverage": None, "evidence": "held-out"}
            _diagnostic_rescoring(retention, reflex, gate, float(thr.threshold), probes[family], frozen, crit.equivalence, probe_contracts.get(family))
            # Reporting only: the same fresh observation summary as the probe branch, at the
            # incumbent threshold when there is one, so both branches are comparable.
            report_thr = float(inc_thr) if inc_thr is not None else float(thr.threshold)
            retention["fresh"] = fresh_report(reflex, gate, report_thr, va, incumbent[0] if incumbent is not None else None, valid_actions, crit.equivalence)
            if incumbent is not None:
                inc_reflex, inc_gate, inc_thresholds = incumbent
                inc_thr = inc_thresholds.get(family)
                if inc_thr is not None:
                    inc_cov, _ = probe_scores(inc_reflex, inc_gate, inc_thr, probes[family], frozen)
                    retention["incumbent_coverage"] = inc_cov
                    if coverage < inc_cov - crit.probe_coverage_regression_tolerance:
                        failures.append("retention_regression")
            if coverage < crit.probe_coverage_floor or agreement < crit.probe_accuracy_floor:
                failures.append("retention")
            verdict.retention = retention
        if failures:
            verdict.status = "rejected"
            verdict.reason = ",".join(failures)
        else:
            verdict.status = "active"
            verdict.reason = "quality_trust_retention_pass"
        verdicts[family] = verdict
    return verdicts


def fresh_report(
    reflex,
    gate: MahalanobisGate,
    threshold: float,
    fresh: list[Trace],
    incumbent_reflex=None,
    valid_actions: set[str] | None = None,
    contract: EquivalenceContract | None = None,
) -> dict[str, int]:
    """How many fresh traces the gate accepts, how many the candidate covers at ``threshold``,
    and on how many covered ones it disagrees with the verified teacher action. With an
    incumbent, each covered disagreement is also classified: ``candidate_regression``
    (incumbent agrees with the teacher, candidate does not), ``alternative_trajectory``
    (incumbent and candidate agree with each other, not with the teacher, and the shared
    action is in ``valid_actions``), else ``ambiguous``."""
    x = np.stack([t.features for t in fresh])
    y = np.asarray([t.action for t in fresh]).astype(str)
    accepted = np.asarray(gate.accept(x), dtype=bool)
    preds = np.asarray([str(reflex.predict(row)[0]) for row in x])
    confs = np.asarray([float(reflex.predict(row)[1]) for row in x])
    covered = accepted & (confs >= threshold)
    equal = np.asarray([same_class(p, t, contract) for p, t in zip(preds, y)])
    report = {
        "n": len(fresh), "gate_accepted": int(accepted.sum()), "covered": int(covered.sum()),
        "disagreements": int(np.sum(covered & ~equal)), "literal_disagreements": int(np.sum(covered & (preds != y))),
    }
    if incumbent_reflex is not None:
        inc = np.asarray([str(incumbent_reflex.predict(row)[0]) for row in x])
        valid = valid_actions or set()
        regression = alternative = ambiguous = 0
        for k in np.flatnonzero(covered & ~equal):
            if same_class(inc[k], y[k], contract):
                regression += 1
            elif same_class(preds[k], inc[k], contract) and inc[k] in valid:
                alternative += 1
            else:
                ambiguous += 1
        report.update({"candidate_regression": regression, "alternative_trajectory": alternative, "ambiguous": ambiguous})
    return report


def _frozen_contract(record: dict[str, Any] | None) -> EquivalenceContract | None:
    return EquivalenceContract.from_mapping(record)


def _diagnostic_rescoring(
    retention: dict[str, Any], reflex, gate, threshold: float, probe_traces: list[Trace],
    frozen: EquivalenceContract | None, current: EquivalenceContract | None, record: dict[str, Any] | None,
) -> None:
    """Report the probe agreement under the current contract when it differs from the one
    the probes were frozen under. Diagnostic only; the verdict uses the frozen contract."""
    retention["probe_contract"] = (record or {}).get("digest") if record else "identity"
    current_digest = current.materialize({str(t.action) for t in probe_traces})["digest"] if current is not None else "identity"
    if current_digest != retention["probe_contract"]:
        _, agreement = probe_scores(reflex, gate, threshold, probe_traces, current)
        retention["agreement_under_current_contract"] = agreement
        retention["current_contract"] = current_digest


def _recertify_on_probes(
    verdict: FamilyVerdict,
    reflex,
    gate: MahalanobisGate,
    incumbent: tuple[Any, MahalanobisGate, dict[str, float]],
    threshold: float,
    probe_traces: list[Trace],
    crit: FamilyCriteria,
    fresh: list[Trace] | None = None,
    valid_actions: set[str] | None = None,
    probe_contract: dict[str, Any] | None = None,
) -> FamilyVerdict:
    """Certify an active family on its frozen probes at the incumbent threshold.

    Every safeguard is applied to the probe set: coverage and agreement floors, no
    coverage regression against the incumbent, gate acceptance floor, ECE floor. The
    sparse fresh held-out traces, if any, are reported and a covered one on which the
    candidate disagrees with the teacher is a hard veto; a fresh state the gate rejects
    is reported, not counted as a regression.
    """
    frozen = _frozen_contract(probe_contract)
    coverage, agreement, acceptance, ece = probe_report(reflex, gate, threshold, probe_traces, frozen)
    inc_reflex, inc_gate, _ = incumbent
    inc_cov, _ = probe_scores(inc_reflex, inc_gate, threshold, probe_traces, frozen)
    verdict.threshold = threshold
    verdict.coverage = coverage
    verdict.selective_accuracy = agreement
    verdict.ece = ece
    verdict.gate_acceptance = acceptance
    verdict.retention = {"probes": len(probe_traces), "coverage": coverage, "agreement": agreement, "incumbent_coverage": inc_cov, "evidence": "probes_only"}
    _diagnostic_rescoring(verdict.retention, reflex, gate, threshold, probe_traces, frozen, crit.equivalence, probe_contract)
    failures: list[str] = []
    if fresh:
        report = fresh_report(reflex, gate, threshold, fresh, inc_reflex, valid_actions, crit.equivalence)
        verdict.retention["fresh"] = report
        if crit.triadic_veto:
            if report.get("candidate_regression", 0):
                failures.append("candidate_regression")
        elif report["disagreements"]:
            failures.append("fresh_disagreement")
    if coverage < crit.probe_coverage_floor or agreement < crit.probe_accuracy_floor:
        failures.append("retention")
    if coverage < inc_cov - crit.probe_coverage_regression_tolerance:
        failures.append("retention_regression")
    if acceptance < crit.minimum_ood_acceptance:
        failures.append("trust")
    if ece > crit.maximum_ece:
        failures.append("calibration")
    if failures:
        verdict.status, verdict.reason = "rejected", ",".join(failures)
    else:
        verdict.status, verdict.reason = "active", "probe_recertified"
    return verdict


def materialized_contract(contract: EquivalenceContract | None, train: list[Trace], validation: list[Trace], probes: dict[str, list[Trace]] | None) -> dict[str, Any]:
    """The explicit, hashed mapping of every action key in play at this certification."""
    keys = {str(t.action) for t in train} | {str(t.action) for t in validation}
    for traces in (probes or {}).values():
        keys |= {str(t.action) for t in traces}
    return (contract or EquivalenceContract()).materialize(keys)


def summarize_verdicts(verdicts: dict[str, FamilyVerdict]) -> dict[str, Any]:
    return {
        "active": sorted(f for f, v in verdicts.items() if v.status == "active"),
        "rejected": sorted(f for f, v in verdicts.items() if v.status == "rejected"),
        "insufficient": sorted(f for f, v in verdicts.items() if v.status == "insufficient"),
        "families": {f: v.to_dict() for f, v in verdicts.items()},
    }
