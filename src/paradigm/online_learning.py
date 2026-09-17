from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .agent_vertical import ACTIONS, AgentEpisode, AgentFeatureEncoder, ParadigmCodingAgent
from .bounded import SpectralDriftContract, softmax_gradient
from .evaluation import expected_calibration_error, multiclass_brier
from .family_scoped import FamilyCriteria, certify_families, materialized_contract, summarize_verdicts
from .model_selection import MinimalReflexSelector, ReflexSelection
from .ood import MahalanobisGate
from .reflex import CompiledReflex
from .schema import Trace
from .selection import select_confidence_threshold


@dataclass(slots=True)
class TrustedEpisode:
    task_id: str
    family: str
    traces: list[Trace]


class OnlineExperienceBuffer:
    """Outcome-filtered experience store for online reflex compilation.

    Only deliberative decisions from successful episodes are admitted by default.
    This avoids training the candidate on its own unverified predictions.
    """

    def __init__(self) -> None:
        self.episodes: list[TrustedEpisode] = []
        self.rejected_failed_episodes = 0
        self.ignored_self_labels = 0
        self.rejected_unvalidated_steps = 0

    def ingest(self, episode: AgentEpisode) -> int:
        if not episode.success:
            self.rejected_failed_episodes += 1
            return 0

        traces: list[Trace] = []
        for record in episode.records:
            if record.source != "deliberative":
                self.ignored_self_labels += 1
                continue
            if not getattr(record, "validated", True):
                # A deliberative step whose own outcome was not verified is not teacher evidence,
                # even inside a successful episode.
                self.rejected_unvalidated_steps += 1
                continue
            traces.append(
                Trace(
                    features=np.asarray(record.features, dtype=np.float64),
                    action=record.action,
                    valid=True,
                    metadata={
                        "task_id": episode.task_id,
                        "family": getattr(record, "family", None) or episode.family,
                        "source": "deliberative",
                    },
                )
            )
        if traces:
            self.episodes.append(TrustedEpisode(episode.task_id, episode.family, traces))
        return len(traces)

    @property
    def trusted_trace_count(self) -> int:
        return int(sum(len(ep.traces) for ep in self.episodes))

    def split(self, validation_fraction: float = 0.25) -> tuple[list[Trace], list[Trace]]:
        if len(self.episodes) < 2:
            return [], []
        n_val = max(1, int(round(len(self.episodes) * validation_fraction)))
        n_val = min(n_val, len(self.episodes) - 1)
        train_eps = self.episodes[:-n_val]
        val_eps = self.episodes[-n_val:]
        train = [trace for ep in train_eps for trace in ep.traces]
        validation = [trace for ep in val_eps for trace in ep.traces]
        return train, validation


@dataclass(slots=True)
class PromotionRecord:
    stream_episode: int
    version: int
    promoted: bool
    backend: str
    threshold: float
    validation_coverage: float
    validation_selective_accuracy: float
    validation_ece: float
    ood_acceptance: float
    train_traces: int
    validation_traces: int
    reason: str
    train_families: dict[str, int] = field(default_factory=dict)
    validation_families: dict[str, int] = field(default_factory=dict)
    ood_acceptance_by_family: dict[str, float] = field(default_factory=dict)
    outcome: str = ""
    certification: dict[str, Any] = field(default_factory=dict)
    shadow_certification: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RetentionProbeSet:
    """Small immutable set of validated deliberative traces for one mature family.

    Created once when the family is first promoted and never modified afterwards, so
    later candidates are always certified against the same retention evidence even
    after the family stops producing fresh teacher labels.
    """

    family: str
    traces: list[Trace]
    created_version: int
    created_stream_episode: int


@dataclass(slots=True)
class OnlineCompilerState:
    version: int = 0
    selection: ReflexSelection | None = None
    ood_gate: MahalanobisGate | None = None
    promotions: list[PromotionRecord] = field(default_factory=list)
    probes: dict[str, RetentionProbeSet] = field(default_factory=dict)
    # family_scoped mode: families authorized to act, each with its own confidence threshold.
    family_thresholds: dict[str, float] = field(default_factory=dict)


class OnlineReflexCompiler:
    """Safe online compiler with active/candidate separation.

    The active reflex is never updated in place. Successful fallback decisions are
    accumulated in an experience buffer. A candidate is periodically compiled and
    validated on held-out recent episodes. Only a candidate that satisfies both
    quality/calibration and OOD-coverage checks replaces the active reflex.
    """

    def __init__(
        self,
        *,
        min_episodes: int = 8,
        compile_every: int = 4,
        validation_fraction: float = 0.25,
        minimum_ood_acceptance: float = 0.70,
        random_state: int = 21,
        certification: str = "recent",
        probe_size: int = 20,
        probe_coverage_floor: float | None = None,
        probe_accuracy_floor: float = 0.95,
        probe_coverage_regression_tolerance: float = 0.10,
        min_family_validation_episodes: int = 1,
        shadow_certification: str | None = None,
        probe_recertification: bool = False,
        min_fresh_support: int = 1,
        triadic_veto: bool = False,
        equivalence=None,
    ) -> None:
        if certification not in {"recent", "family_aware", "family_scoped"}:
            raise ValueError(f"unknown certification mode: {certification!r}")
        self.min_episodes = int(min_episodes)
        self.compile_every = int(compile_every)
        self.validation_fraction = float(validation_fraction)
        self.minimum_ood_acceptance = float(minimum_ood_acceptance)
        self.random_state = int(random_state)
        self.certification = certification
        self.probe_size = int(probe_size)
        self.probe_coverage_floor = (
            float(minimum_ood_acceptance) if probe_coverage_floor is None else float(probe_coverage_floor)
        )
        self.probe_accuracy_floor = float(probe_accuracy_floor)
        self.probe_coverage_regression_tolerance = float(probe_coverage_regression_tolerance)
        self.min_family_validation_episodes = int(min_family_validation_episodes)
        self.shadow_certification = shadow_certification
        # family_scoped only: an active family without fresh held-out traces is
        # re-certified on its frozen probes instead of blocking the replacement.
        self.probe_recertification = bool(probe_recertification)
        self.min_fresh_support = int(min_fresh_support)
        self.triadic_veto = bool(triadic_veto)
        # Optional behavioral equivalence contract (paradigm.equivalence); None is identity.
        self.equivalence = equivalence
        self.buffer = OnlineExperienceBuffer()
        self.state = OnlineCompilerState()
        self._episodes_since_compile = 0

    def ingest(self, episode: AgentEpisode, *, stream_episode: int) -> PromotionRecord | None:
        added = self.buffer.ingest(episode)
        if added <= 0:
            return None
        self._episodes_since_compile += 1
        if len(self.buffer.episodes) < self.min_episodes:
            return None
        if self._episodes_since_compile < self.compile_every:
            return None
        self._episodes_since_compile = 0
        return self._compile_candidate(stream_episode)

    def _compile_candidate(self, stream_episode: int) -> PromotionRecord:
        train, validation = self.buffer.split(self.validation_fraction)
        if not train or not validation:
            record = PromotionRecord(
                stream_episode, self.state.version, False, "none", 1.0, 0.0, 0.0, 1.0, 0.0,
                len(train), len(validation), "insufficient_split",
            )
            self.state.promotions.append(record)
            return record
        if len(train) < 30:
            record = PromotionRecord(
                stream_episode, self.state.version, False, "none", 1.0, 0.0, 0.0, 1.0, 0.0,
                len(train), len(validation), "insufficient_validated_traces",
            )
            self.state.promotions.append(record)
            return record

        if self.certification == "family_scoped":
            return self._compile_family_scoped(stream_episode, train, validation)
        selection, gate, chosen = self.fit_candidate(train, validation)
        primary = self.certify_candidate(selection, gate, train, validation, mode=self.certification)
        shadow = (
            self.certify_candidate(selection, gate, train, validation, mode=self.shadow_certification)
            if self.shadow_certification
            else {}
        )
        promoted = primary["outcome"] == "promoted"
        if promoted:
            self.state.version += 1
            self.state.selection = selection
            self.state.ood_gate = gate
            if self.certification == "family_aware":
                self._create_probes(train, validation, stream_episode)

        record = PromotionRecord(
            stream_episode=stream_episode,
            version=self.state.version,
            promoted=promoted,
            backend=selection.backend,
            threshold=float(selection.threshold),
            validation_coverage=float(chosen.coverage),
            validation_selective_accuracy=float(chosen.selective_accuracy),
            validation_ece=float(chosen.ece),
            ood_acceptance=float(primary["overall_acceptance"]),
            train_traces=len(train),
            validation_traces=len(validation),
            reason=primary["reason"],
            train_families=primary["train_families"],
            validation_families=primary["validation_families"],
            ood_acceptance_by_family=primary["acceptance_by_family"],
            outcome=primary["outcome"],
            certification=primary,
            shadow_certification=shadow,
        )
        self.state.promotions.append(record)
        return record

    def family_thresholds(self) -> dict[str, float]:
        """Active families and their thresholds; states saved before this field existed get an empty map."""
        if not hasattr(self.state, "family_thresholds"):
            self.state.family_thresholds = {}
        return self.state.family_thresholds

    def _compile_family_scoped(self, stream_episode: int, train: list[Trace], validation: list[Trace]) -> PromotionRecord:
        """One plain tree, one verdict per family, adoption only without regression of active families."""
        self.family_thresholds()
        selection, gate, chosen = self.fit_candidate(train, validation, backends=("tree",))
        criteria = FamilyCriteria(
            minimum_ood_acceptance=self.minimum_ood_acceptance,
            probe_coverage_floor=self.probe_coverage_floor,
            probe_accuracy_floor=self.probe_accuracy_floor,
            probe_coverage_regression_tolerance=self.probe_coverage_regression_tolerance,
            min_validation_episodes=self.min_family_validation_episodes,
            probe_recertification=getattr(self, "probe_recertification", False),
            min_fresh_support=getattr(self, "min_fresh_support", 1),
            triadic_veto=getattr(self, "triadic_veto", False),
            equivalence=getattr(self, "equivalence", None),
        )
        incumbent = None
        if self.state.selection is not None and self.state.ood_gate is not None and self.state.family_thresholds:
            incumbent = (self.state.selection.reflex, self.state.ood_gate, dict(self.state.family_thresholds))
        verdicts = certify_families(
            selection.reflex, gate, train, validation,
            probes={f: p.traces for f, p in self.state.probes.items()},
            incumbent=incumbent, criteria=criteria,
        )
        summary = summarize_verdicts(verdicts)
        probe_traces = {f: p.traces for f, p in self.state.probes.items()}
        contract_record = materialized_contract(getattr(self, "equivalence", None), train, validation, probe_traces)
        active_now = {f: float(verdicts[f].threshold or 0.0) for f in summary["active"]}
        newly_active = {f: thr for f, thr in active_now.items() if f not in self.state.family_thresholds}
        # A replacement artifact must re-certify every active family. A family that is
        # served by the reflex stops producing deliberative held-out traces; without
        # probe_recertification it comes back "insufficient" here and blocks the
        # replacement (LaRuche run 11 record), with it the frozen probes are the evidence.
        regressed = [f for f in self.state.family_thresholds if verdicts.get(f) is None or verdicts[f].status != "active"]
        if regressed:
            outcome, reason = "rejected", "active_family_regressed:" + ",".join(sorted(regressed))
        elif newly_active:
            outcome, reason = "promoted", "families_activated:" + ",".join(sorted(newly_active))
        elif active_now:
            outcome, reason = "rejected", "no_new_family"
        elif summary["rejected"]:
            outcome, reason = "rejected", "no_family_passed"
        else:
            outcome, reason = "insufficient_evidence", "no_family_with_held_out_evidence"
        promoted = outcome == "promoted"
        if promoted:
            self.state.version += 1
            self.state.selection = selection
            self.state.ood_gate = gate
            self.state.family_thresholds = active_now
            self._create_probes_for(train, validation, stream_episode, families=set(newly_active))
        train_counts, _ = self._family_counts(train)
        val_counts, _ = self._family_counts(validation)
        record = PromotionRecord(
            stream_episode=stream_episode,
            version=self.state.version,
            promoted=promoted,
            backend=selection.backend,
            threshold=float(selection.threshold),
            validation_coverage=float(chosen.coverage),
            validation_selective_accuracy=float(chosen.selective_accuracy),
            validation_ece=float(chosen.ece),
            ood_acceptance=float(np.mean([v.gate_acceptance for v in verdicts.values() if v.gate_acceptance is not None] or [0.0])),
            train_traces=len(train),
            validation_traces=len(validation),
            reason=reason,
            train_families=train_counts,
            validation_families=val_counts,
            ood_acceptance_by_family={f: v.gate_acceptance for f, v in verdicts.items() if v.gate_acceptance is not None},
            outcome=outcome,
            certification={"mode": "family_scoped", "outcome": outcome, "reason": reason, "groups": summary["families"], "active_families": sorted(active_now) if promoted else sorted(self.state.family_thresholds), "probe_recertification": getattr(self, "probe_recertification", False), "min_fresh_support": getattr(self, "min_fresh_support", 1), "triadic_veto": getattr(self, "triadic_veto", False), "equivalence": contract_record},
        )
        self.state.promotions.append(record)
        return record

    def fit_candidate(self, train: list[Trace], validation: list[Trace], backends: tuple[str, ...] | None = None):
        reference = np.asarray([t.action for t in validation]).astype(str)
        labels, counts = np.unique(np.asarray([t.action for t in train]).astype(str), return_counts=True)
        min_class_count = int(np.min(counts)) if len(labels) else 0
        if backends is None:
            backends = ("tree", "calibrated_tree", "calibrated_forest") if min_class_count >= 3 else ("tree",)
        selector = MinimalReflexSelector(
            backends=backends,
            minimum_coverage=0.55,
            maximum_ece=0.10,
            accuracy_tolerance=0.01,
            random_state=self.random_state + self.state.version,
        )
        selection = selector.select(
            train,
            validation,
            reference_predictions=reference,
            name=f"online-agent-v{self.state.version + 1}",
        )
        x_train = np.stack([t.features for t in train])
        gate = MahalanobisGate(quantile=0.997).fit(x_train)
        chosen = next(c for c in selection.candidates if c.backend == selection.backend)
        return selection, gate, chosen

    @staticmethod
    def _family_counts(traces: list[Trace]) -> tuple[dict[str, int], dict[str, int]]:
        trace_counts: dict[str, int] = {}
        episode_ids: dict[str, set] = {}
        for t in traces:
            fam = str(t.metadata.get("family", "unknown"))
            trace_counts[fam] = trace_counts.get(fam, 0) + 1
            episode_ids.setdefault(fam, set()).add(str(t.metadata.get("task_id", "")))
        return trace_counts, {fam: len(ids) for fam, ids in episode_ids.items()}

    def certify_candidate(
        self,
        selection: ReflexSelection,
        gate: MahalanobisGate,
        train: list[Trace],
        validation: list[Trace],
        *,
        mode: str,
    ) -> dict[str, Any]:
        """Decide promoted / rejected / insufficient_evidence for a fitted candidate.

        ``recent`` is the P2.1 rule: quality on the recent held-out split plus overall shadow
        OOD acceptance. ``family_aware`` additionally requires every family in the validation
        split to have enough episodes and pass acceptance on its own, and every mature family
        to pass coverage and agreement on its immutable retention probes.
        """
        x_val = np.stack([t.features for t in validation])
        accepted = np.asarray(gate.accept(x_val), dtype=bool)
        overall = float(np.mean(accepted))
        val_families = np.asarray([str(t.metadata.get("family", "unknown")) for t in validation])
        by_family = {str(f): float(np.mean(accepted[val_families == f])) for f in sorted(set(val_families))}
        train_counts, _ = self._family_counts(train)
        val_counts, val_episodes = self._family_counts(validation)
        result: dict[str, Any] = {
            "mode": mode,
            "quality_feasible": bool(selection.feasible),
            "overall_acceptance": overall,
            "acceptance_by_family": by_family,
            "train_families": train_counts,
            "validation_families": val_counts,
            "validation_episodes_by_family": val_episodes,
            "probe_evaluations": 0,
            "groups": {},
        }
        if mode == "recent":
            promoted = bool(selection.feasible and overall >= self.minimum_ood_acceptance)
            result["outcome"] = "promoted" if promoted else "rejected"
            result["reason"] = "quality_and_trust_pass" if promoted else (
                "quality_or_calibration_failed" if not selection.feasible else "ood_shadow_coverage_failed"
            )
            return result
        if mode != "family_aware":
            raise ValueError(f"unknown certification mode: {mode!r}")

        groups: dict[str, dict[str, Any]] = {}
        for fam in sorted(set(val_families)):
            if fam in self.state.probes:
                continue
            episodes = val_episodes.get(fam, 0)
            if episodes < self.min_family_validation_episodes:
                groups[fam] = {"kind": "novel", "status": "insufficient", "episodes": episodes, "acceptance": by_family[fam]}
            elif by_family[fam] >= self.minimum_ood_acceptance:
                groups[fam] = {"kind": "novel", "status": "pass", "episodes": episodes, "acceptance": by_family[fam]}
            else:
                groups[fam] = {"kind": "novel", "status": "fail", "episodes": episodes, "acceptance": by_family[fam]}
        for fam in sorted(train_counts):
            if fam not in groups and fam not in self.state.probes:
                groups[fam] = {"kind": "novel", "status": "insufficient", "episodes": 0, "acceptance": None}
        for fam, probe in sorted(self.state.probes.items()):
            coverage, agreement = self._probe_scores(selection, gate, probe.traces)
            result["probe_evaluations"] += len(probe.traces)
            incumbent_coverage = None
            if self.state.selection is not None and self.state.ood_gate is not None:
                incumbent_coverage, _ = self._probe_scores(self.state.selection, self.state.ood_gate, probe.traces)
            regressed = (
                incumbent_coverage is not None
                and coverage < incumbent_coverage - self.probe_coverage_regression_tolerance
            )
            ok = coverage >= self.probe_coverage_floor and agreement >= self.probe_accuracy_floor and not regressed
            groups[fam] = {
                "kind": "retention",
                "status": "pass" if ok else "fail",
                "probes": len(probe.traces),
                "coverage": coverage,
                "incumbent_coverage": incumbent_coverage,
                "agreement": agreement,
            }
        result["groups"] = groups
        statuses = [g["status"] for g in groups.values()]
        if not selection.feasible:
            outcome, reason = "rejected", "quality_or_calibration_failed"
        elif any(st == "fail" for st in statuses):
            failed = sorted(f for f, g in groups.items() if g["status"] == "fail")
            outcome, reason = "rejected", "family_certification_failed:" + ",".join(failed)
        elif any(st == "insufficient" for st in statuses):
            missing = sorted(f for f, g in groups.items() if g["status"] == "insufficient")
            outcome, reason = "insufficient_evidence", "insufficient_family_evidence:" + ",".join(missing)
        else:
            outcome, reason = "promoted", "family_certification_pass"
        result["outcome"] = outcome
        result["reason"] = reason
        return result

    @staticmethod
    def _probe_scores(selection: ReflexSelection, gate: MahalanobisGate, traces: list[Trace]) -> tuple[float, float]:
        """Coverage (gate accept and confident) and agreement with the recorded action on covered probes."""
        x_p = np.stack([t.features for t in traces])
        y_p = np.asarray([t.action for t in traces]).astype(str)
        p_accept = np.asarray(gate.accept(x_p), dtype=bool)
        preds, confs = [], []
        for row in x_p:
            action, confidence, _ = selection.reflex.predict(row)
            preds.append(str(action))
            confs.append(float(confidence))
        covered = p_accept & (np.asarray(confs) >= float(selection.threshold))
        coverage = float(np.mean(covered))
        agreement = float(np.mean(np.asarray(preds)[covered] == y_p[covered])) if covered.any() else 0.0
        return coverage, agreement

    def _create_probes(self, train: list[Trace], validation: list[Trace], stream_episode: int) -> None:
        """Freeze retention probes for every family the promoted candidate now represents."""
        self._create_probes_for(train, validation, stream_episode, families=None)

    def _create_probes_for(self, train: list[Trace], validation: list[Trace], stream_episode: int, families: set[str] | None) -> None:
        by_family: dict[str, list[Trace]] = {}
        for t in validation + train:  # held-out traces first
            by_family.setdefault(str(t.metadata.get("family", "unknown")), []).append(t)
        for fam, traces in by_family.items():
            if fam in self.state.probes or (families is not None and fam not in families):
                continue
            self.state.probes[fam] = RetentionProbeSet(
                family=fam,
                traces=list(traces[: self.probe_size]),
                created_version=self.state.version,
                created_stream_episode=int(stream_episode),
            )

    def make_agent(self, deliberator, encoder: AgentFeatureEncoder) -> ParadigmCodingAgent:
        return ParadigmCodingAgent(
            deliberator,
            encoder=encoder,
            selection=self.state.selection,
            ood_gate=self.state.ood_gate,
        )


class BoundedSoftmaxModel:
    """Small neural-style linear reflex trained with Drift Contract updates.

    This is intentionally separate from the production fast path in P2.1. It lets
    Paradigm test bounded supervised fine-tuning without assuming that the neural
    candidate should replace a simpler compiled tree.
    """

    def __init__(self, input_dim: int, *, weights: np.ndarray | None = None, temperature: float = 1.0) -> None:
        self.classes_ = np.asarray(ACTIONS, dtype=object)
        self.weights = (
            np.zeros((len(ACTIONS), input_dim), dtype=np.float64)
            if weights is None
            else np.asarray(weights, dtype=np.float64).copy()
        )
        self.temperature = float(temperature)

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x[None, :]
        logits = x @ self.weights.T / max(self.temperature, 1e-6)
        logits -= np.max(logits, axis=1, keepdims=True)
        exp = np.exp(logits)
        return exp / np.sum(exp, axis=1, keepdims=True)


@dataclass(slots=True)
class BoundedCandidateReport:
    feasible: bool
    threshold: float
    coverage: float
    selective_accuracy: float
    ece: float
    brier: float
    max_step_drift: float
    mean_step_drift: float
    epochs: int
    epsilon: float


def train_bounded_softmax_candidate(
    train: list[Trace],
    validation: list[Trace],
    *,
    epsilon: float = 0.03,
    epochs: int = 60,
    batch_size: int = 64,
    seed: int = 21,
    initial_weights: np.ndarray | None = None,
) -> tuple[CompiledReflex, BoundedCandidateReport]:
    if not train or not validation:
        raise ValueError("train and validation traces are required")
    x_train = np.stack([t.features for t in train])
    y_labels = np.asarray([t.action for t in train]).astype(str)
    x_val = np.stack([t.features for t in validation])
    y_val = np.asarray([t.action for t in validation]).astype(str)
    class_to_idx = {label: i for i, label in enumerate(ACTIONS)}
    y_train = np.asarray([class_to_idx[label] for label in y_labels], dtype=int)

    model = BoundedSoftmaxModel(x_train.shape[1], weights=initial_weights)
    contract = SpectralDriftContract(
        model.weights.shape,
        epsilon=epsilon,
        exact_scale=True,
        strict_denominator=True,
    )
    rng = np.random.default_rng(seed)
    drifts: list[float] = []
    for _ in range(int(epochs)):
        order = rng.permutation(len(x_train))
        for start in range(0, len(order), batch_size):
            idx = order[start : start + batch_size]
            xb = x_train[idx]
            yb = y_train[idx]
            grad = softmax_gradient(model.weights, xb, yb)
            update, report = contract.step(grad, xb)
            model.weights += update
            drifts.append(float(report.measured_preactivation_drift))

    # Temperature calibration is fitted only on the held-out validation split.
    best_t = 1.0
    best_nll = float("inf")
    for temperature in np.geomspace(0.35, 4.0, 31):
        model.temperature = float(temperature)
        probs = model.predict_proba(x_val)
        idx = np.asarray([class_to_idx[label] for label in y_val], dtype=int)
        nll = float(-np.mean(np.log(np.clip(probs[np.arange(len(idx)), idx], 1e-12, 1.0))))
        if nll < best_nll:
            best_nll = nll
            best_t = float(temperature)
    model.temperature = best_t

    probs = model.predict_proba(x_val)
    threshold = select_confidence_threshold(
        y_val,
        probs,
        model.classes_,
        reference_predictions=y_val,
        tolerance=0.01,
        minimum_coverage=0.50,
    )
    ece = expected_calibration_error(y_val, probs, model.classes_)
    report = BoundedCandidateReport(
        feasible=bool(threshold.feasible and ece <= 0.10),
        threshold=float(threshold.threshold),
        coverage=float(threshold.coverage),
        selective_accuracy=float(threshold.selective_accuracy),
        ece=float(ece),
        brier=float(multiclass_brier(y_val, probs, model.classes_)),
        max_step_drift=float(max(drifts) if drifts else 0.0),
        mean_step_drift=float(np.mean(drifts) if drifts else 0.0),
        epochs=int(epochs),
        epsilon=float(epsilon),
    )
    reflex = CompiledReflex(model=model, name="bounded-online-softmax", metadata={"temperature": best_t})
    return reflex, report
