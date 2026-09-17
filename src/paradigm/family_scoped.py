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


def probe_scores(reflex, gate: MahalanobisGate, threshold: float, traces: list[Trace]) -> tuple[float, float]:
    coverage, agreement, _, _ = probe_report(reflex, gate, threshold, traces)
    return coverage, agreement


def probe_report(reflex, gate: MahalanobisGate, threshold: float, traces: list[Trace]) -> tuple[float, float, float, float]:
    """Coverage, agreement, gate acceptance and ECE of one artifact on a probe set."""
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
    agreement = float(np.mean(np.asarray(preds)[covered] == y[covered])) if covered.any() else 0.0
    ece = float(expected_calibration_error(y, reflex.predict_proba(x), reflex.classes_.astype(str)))
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
) -> dict[str, FamilyVerdict]:
    """Certify every family seen in train or validation independently.

    ``incumbent`` is (reflex, gate, thresholds_by_family) of the active artifact, used only
    for the coverage-regression check on probe families.
    """
    crit = criteria or FamilyCriteria()
    probes = probes or {}
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
        if sparse:
            verdicts[family] = _recertify_on_probes(verdict, reflex, gate, incumbent, float(inc_thr), probes[family], crit, fresh=va)
            continue
        if verdict.validation_episodes < crit.min_validation_episodes or not va:
            verdict.reason = "no_held_out_evidence"
            verdicts[family] = verdict
            continue
        x_val = np.stack([t.features for t in va])
        y_val = np.asarray([t.action for t in va]).astype(str)
        probs = reflex.predict_proba(x_val)
        classes = reflex.classes_.astype(str)
        thr = select_confidence_threshold(
            y_val, probs, classes, reference_predictions=y_val, tolerance=crit.accuracy_tolerance, minimum_coverage=crit.minimum_coverage
        )
        ece = float(expected_calibration_error(y_val, probs, classes))
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
            coverage, agreement = probe_scores(reflex, gate, float(thr.threshold), probes[family])
            retention: dict[str, Any] = {"probes": len(probes[family]), "coverage": coverage, "agreement": agreement, "incumbent_coverage": None}
            if incumbent is not None:
                inc_reflex, inc_gate, inc_thresholds = incumbent
                inc_thr = inc_thresholds.get(family)
                if inc_thr is not None:
                    inc_cov, _ = probe_scores(inc_reflex, inc_gate, inc_thr, probes[family])
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


def _recertify_on_probes(
    verdict: FamilyVerdict,
    reflex,
    gate: MahalanobisGate,
    incumbent: tuple[Any, MahalanobisGate, dict[str, float]],
    threshold: float,
    probe_traces: list[Trace],
    crit: FamilyCriteria,
    fresh: list[Trace] | None = None,
) -> FamilyVerdict:
    """Certify an active family on its frozen probes at the incumbent threshold.

    Every safeguard is applied to the probe set: coverage and agreement floors, no
    coverage regression against the incumbent, gate acceptance floor, ECE floor. The
    sparse fresh held-out traces, if any, are reported and a covered one on which the
    candidate disagrees with the teacher is a hard veto; a fresh state the gate rejects
    is reported, not counted as a regression.
    """
    coverage, agreement, acceptance, ece = probe_report(reflex, gate, threshold, probe_traces)
    inc_reflex, inc_gate, _ = incumbent
    inc_cov, _ = probe_scores(inc_reflex, inc_gate, threshold, probe_traces)
    verdict.threshold = threshold
    verdict.coverage = coverage
    verdict.selective_accuracy = agreement
    verdict.ece = ece
    verdict.gate_acceptance = acceptance
    verdict.retention = {"probes": len(probe_traces), "coverage": coverage, "agreement": agreement, "incumbent_coverage": inc_cov, "evidence": "probes_only"}
    failures: list[str] = []
    if fresh:
        x = np.stack([t.features for t in fresh])
        y = np.asarray([t.action for t in fresh]).astype(str)
        accepted = np.asarray(gate.accept(x), dtype=bool)
        preds = np.asarray([str(reflex.predict(row)[0]) for row in x])
        confs = np.asarray([float(reflex.predict(row)[1]) for row in x])
        covered = accepted & (confs >= threshold)
        disagreements = int(np.sum(covered & (preds != y)))
        verdict.retention["fresh"] = {"n": len(fresh), "gate_accepted": int(accepted.sum()), "covered": int(covered.sum()), "disagreements": disagreements}
        if disagreements:
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


def summarize_verdicts(verdicts: dict[str, FamilyVerdict]) -> dict[str, Any]:
    return {
        "active": sorted(f for f, v in verdicts.items() if v.status == "active"),
        "rejected": sorted(f for f, v in verdicts.items() if v.status == "rejected"),
        "insufficient": sorted(f for f, v in verdicts.items() if v.status == "insufficient"),
        "families": {f: v.to_dict() for f, v in verdicts.items()},
    }
