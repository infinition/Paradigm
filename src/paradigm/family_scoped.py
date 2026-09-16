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
    return coverage, agreement


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


def summarize_verdicts(verdicts: dict[str, FamilyVerdict]) -> dict[str, Any]:
    return {
        "active": sorted(f for f, v in verdicts.items() if v.status == "active"),
        "rejected": sorted(f for f, v in verdicts.items() if v.status == "rejected"),
        "insufficient": sorted(f for f, v in verdicts.items() if v.status == "insufficient"),
        "families": {f: v.to_dict() for f, v in verdicts.items()},
    }
