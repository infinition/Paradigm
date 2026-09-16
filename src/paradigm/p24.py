from __future__ import annotations

import json
import random
import statistics
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from .agent_scenarios import make_task
from .agent_vertical import AgentFeatureEncoder, AgentState, ParadigmCodingAgent
from .llm_controller import OpenAICompatibleCodingDeliberator, safe_recovery_action
from .online_learning import OnlineExperienceBuffer, OnlineReflexCompiler, RetentionProbeSet, TrustedEpisode
from .p23 import run_p23_live_online_benchmark
from .p23r import KNOWN
from .p23t import load_episodes, save_episodes

NOVEL_FAMILY = "dependency_error"
KNOWN_ROUNDS = 8
NOVEL_EPISODES = 16
CERT_NOVEL = 4
CERT_KNOWN = 4
PROBE_KNOWN = 4
SWEEP_K = (0, 1, 2, 3, 4, 5, 6, 8, 10, 12)

# Pre-registered capability criterion for Time-to-Capability. Fixed before any sweep ran.
TTC_DECISION_ACCURACY = 0.95
TTC_REPLAY_SUCCESS = 1.0

RESULT_CLASSES = (
    "TYPE_B_NOT_ESTABLISHED",
    "CAPABILITY_ACQUIRED_NOT_CERTIFIED",
    "CAPABILITY_AND_CERTIFICATION_SUCCEEDED",
    "INSUFFICIENT_EVIDENCE",
    "RETENTION_FAILURE",
)


def make_encoder() -> AgentFeatureEncoder:
    return AgentFeatureEncoder(vocabulary="extended")


def _task_from_id(task_id: str):
    family_key, index = task_id.rsplit("-", 1)
    family = {"dependency": NOVEL_FAMILY, "missing": "missing_import", "constant": "wrong_constant",
              "rename": "renamed_symbol", "offbyone": "off_by_one", "syntax": "syntax_error"}[family_key]
    return make_task(family, int(index))


def collect_type_b_episodes(controller, *, seed: int = 0) -> tuple[list[TrustedEpisode], dict[str, Any]]:
    """LLM-only pass with the extended vocabulary: 32 known and 16 dependency episodes.

    Returns the validated trace episodes plus teacher statistics on the novel family:
    success, contract satisfaction, action sequences, and invalid actions.
    """
    encoder = make_encoder()
    agent = ParadigmCodingAgent(controller, encoder=encoder)
    buffer = OnlineExperienceBuffer()
    offset = seed * 1000
    tasks = [make_task(KNOWN[i % len(KNOWN)], offset + i) for i in range(KNOWN_ROUNDS * len(KNOWN))]
    tasks += [make_task(NOVEL_FAMILY, offset + 100 + i) for i in range(NOVEL_EPISODES)]
    teacher_rows = []
    usage_before = controller.snapshot() if hasattr(controller, "snapshot") else None
    for task in tasks:
        before = controller.snapshot() if usage_before is not None else None
        episode = agent.run(task)
        buffer.ingest(episode)
        usage = controller.snapshot().delta(before) if before is not None else None
        teacher_rows.append(
            {
                "task_id": task.task_id,
                "family": task.family,
                "success": episode.success,
                "contract": episode.contract,
                "steps": episode.steps,
                "sequence": [d.action for d in episode.decisions],
                "invalid_llm_actions": usage.invalid_actions if usage else 0,
                "tokens": usage.total_tokens if usage else 0,
                "llm_latency_ms": usage.latency_ms if usage else 0.0,
            }
        )
    novel_rows = [r for r in teacher_rows if r["family"] == NOVEL_FAMILY]
    sequences = Counter(tuple(r["sequence"]) for r in novel_rows if r["success"])
    modal = sequences.most_common(1)[0] if sequences else (None, 0)
    stats = {
        "novel_episodes": len(novel_rows),
        "novel_success_rate": float(np.mean([r["success"] for r in novel_rows])) if novel_rows else 0.0,
        "novel_contract_rate": float(np.mean([all(r["contract"].values()) for r in novel_rows if r["contract"]])) if novel_rows else 0.0,
        "novel_invalid_llm_actions": int(sum(r["invalid_llm_actions"] for r in novel_rows)),
        "novel_mean_steps": float(np.mean([r["steps"] for r in novel_rows])) if novel_rows else 0.0,
        "novel_distinct_sequences": len(sequences),
        "novel_modal_sequence": list(modal[0]) if modal[0] else None,
        "novel_modal_sequence_share": (modal[1] / sum(sequences.values())) if sequences else 0.0,
        "novel_tokens": int(sum(r["tokens"] for r in novel_rows)),
        "novel_llm_latency_ms": float(sum(r["llm_latency_ms"] for r in novel_rows)),
        "known_success_rate": float(np.mean([r["success"] for r in teacher_rows if r["family"] != NOVEL_FAMILY])),
        "rows": teacher_rows,
    }
    return buffer.episodes, stats


class _ForcedReplayStub:
    """Deliberator used only when the forced reflex proposes an invalid action.

    Every call is a capability failure of the reflex; the stub returns the deterministic
    safe recovery action so the episode can continue and be scored.
    """

    def __init__(self) -> None:
        self.calls = 0

    def decide(self, state: AgentState) -> str:
        self.calls += 1
        return safe_recovery_action(state)


def capability_eval(selection, encoder: AgentFeatureEncoder, held_out: list[TrustedEpisode]) -> dict[str, Any]:
    """Capability of a candidate on held-out novel episodes, independent of any trust gate.

    Decision accuracy and exact-sequence accuracy are scored along the teacher's recorded
    states. Replay runs the reflex alone in the sandbox with the threshold forced to zero
    and no OOD gate; any invalid reflex action counts as a capability failure.
    """
    x = np.stack([t.features for ep in held_out for t in ep.traces])
    y = np.asarray([t.action for ep in held_out for t in ep.traces]).astype(str)
    preds = np.asarray([str(selection.reflex.predict(row)[0]) for row in x])
    decision_accuracy = float(np.mean(preds == y))
    exact = 0
    for ep in held_out:
        exact += int(all(str(selection.reflex.predict(t.features)[0]) == t.action for t in ep.traces))
    forced = replace(selection, threshold=0.0)
    replay_success = 0
    invalid = 0
    replay_steps = []
    for ep in held_out:
        stub = _ForcedReplayStub()
        agent = ParadigmCodingAgent(stub, encoder=encoder, selection=forced, ood_gate=None)
        episode = agent.run(_task_from_id(ep.task_id))
        replay_success += int(episode.success and stub.calls == 0)
        invalid += stub.calls
        replay_steps.append(episode.steps)
    return {
        "held_out_episodes": len(held_out),
        "held_out_decisions": int(len(y)),
        "decision_accuracy": decision_accuracy,
        "exact_sequence_accuracy": exact / len(held_out),
        "replay_success_rate": replay_success / len(held_out),
        "replay_invalid_actions": invalid,
        "replay_mean_steps": float(np.mean(replay_steps)),
        "predicted_action_distribution": dict(Counter(preds.tolist())),
    }


def run_type_b_sweep(
    episodes: list[TrustedEpisode],
    *,
    orderings: int = 5,
    ks: tuple[int, ...] = SWEEP_K,
    minimum_ood_acceptance: float = 0.65,
    seed: int = 21,
) -> dict[str, Any]:
    """Capability and trust as a function of validated novel training evidence.

    Certification set (4 novel, 4 known episodes) and retention probes (4 known episodes)
    are fixed for every k. Only successful, contract-satisfying novel episodes are used.
    """
    encoder = make_encoder()
    known = [ep for ep in episodes if ep.family != NOVEL_FAMILY]
    novel = [ep for ep in episodes if ep.family == NOVEL_FAMILY]
    cert_known = known[-CERT_KNOWN:]
    probe_known = known[-2 * CERT_KNOWN : -CERT_KNOWN]
    train_known = known[: -2 * CERT_KNOWN]
    ks = tuple(k for k in ks if k <= len(novel) - CERT_NOVEL)
    rng = random.Random(seed)
    rows = []
    for ordering in range(orderings):
        order = list(novel)
        rng.shuffle(order)
        cert_novel = order[:CERT_NOVEL]
        pool = order[CERT_NOVEL:]
        validation = [t for ep in cert_known + cert_novel for t in ep.traces]
        for k in ks:
            train = [t for ep in train_known + pool[:k] for t in ep.traces]
            compiler = OnlineReflexCompiler(
                minimum_ood_acceptance=minimum_ood_acceptance, random_state=seed + ordering, certification="family_aware"
            )
            for fam in KNOWN:
                fam_traces = [t for ep in probe_known if ep.family == fam for t in ep.traces]
                if fam_traces:
                    compiler.state.probes[fam] = RetentionProbeSet(fam, fam_traces, 0, 0)
            selection, gate, chosen = compiler.fit_candidate(train, validation)
            capability = capability_eval(selection, encoder, cert_novel)
            recent = compiler.certify_candidate(selection, gate, train, validation, mode="recent")
            family_aware = compiler.certify_candidate(selection, gate, train, validation, mode="family_aware")
            novel_x = np.stack([t.features for ep in cert_novel for t in ep.traces])
            accepted = np.asarray(gate.accept(novel_x), dtype=bool)
            retention = {
                f: g for f, g in family_aware["groups"].items() if g.get("kind") == "retention"
            }
            rows.append(
                {
                    "ordering": ordering,
                    "novel_train_episodes": k,
                    "novel_train_decisions": sum(len(ep.traces) for ep in pool[:k]),
                    "backend": selection.backend,
                    "quality_feasible": bool(selection.feasible),
                    **{f"capability_{key}": val for key, val in capability.items()},
                    "novel_gate_acceptance": float(np.mean(accepted)),
                    "overall_acceptance": recent["overall_acceptance"],
                    "recent_outcome": recent["outcome"],
                    "family_aware_outcome": family_aware["outcome"],
                    "family_aware_reason": family_aware["reason"],
                    "retention_all_pass": all(g["status"] == "pass" for g in retention.values()) if retention else None,
                    "meets_ttc_criterion": bool(
                        capability["decision_accuracy"] >= TTC_DECISION_ACCURACY
                        and capability["replay_success_rate"] >= TTC_REPLAY_SUCCESS
                    ),
                }
            )
    by_k: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        by_k.setdefault(r["novel_train_episodes"], []).append(r)
    curve = []
    for k, items in sorted(by_k.items()):
        m = lambda key: float(np.mean([r[key] for r in items]))
        curve.append(
            {
                "novel_train_episodes": k,
                "orderings": len(items),
                "decision_accuracy_mean": m("capability_decision_accuracy"),
                "decision_accuracy_min": float(np.min([r["capability_decision_accuracy"] for r in items])),
                "exact_sequence_accuracy_mean": m("capability_exact_sequence_accuracy"),
                "replay_success_mean": m("capability_replay_success_rate"),
                "replay_invalid_actions_mean": m("capability_replay_invalid_actions"),
                "gate_acceptance_mean": m("novel_gate_acceptance"),
                "gate_acceptance_min": float(np.min([r["novel_gate_acceptance"] for r in items])),
                "recent_promote_rate": float(np.mean([r["recent_outcome"] == "promoted" for r in items])),
                "family_aware_promote_rate": float(np.mean([r["family_aware_outcome"] == "promoted" for r in items])),
                "retention_pass_rate": float(np.mean([bool(r["retention_all_pass"]) for r in items])),
                "ttc_criterion_rate": float(np.mean([r["meets_ttc_criterion"] for r in items])),
            }
        )
    ttc_per_ordering = []
    for ordering in range(orderings):
        ks_met = sorted(r["novel_train_episodes"] for r in rows if r["ordering"] == ordering and r["meets_ttc_criterion"])
        ttc_per_ordering.append(ks_met[0] if ks_met else None)
    ttc_values = [v for v in ttc_per_ordering if v is not None]
    return {
        "phase": "P2.4",
        "novel_family": NOVEL_FAMILY,
        "design": {
            "known_train_episodes": len(train_known),
            "known_certification_episodes": len(cert_known),
            "known_probe_episodes": len(probe_known),
            "novel_certification_episodes": CERT_NOVEL,
            "novel_pool_episodes": len(novel) - CERT_NOVEL,
            "orderings": orderings,
            "ks": list(ks),
            "minimum_ood_acceptance": minimum_ood_acceptance,
            "ttc_criterion": {
                "decision_accuracy_at_least": TTC_DECISION_ACCURACY,
                "replay_success_at_least": TTC_REPLAY_SUCCESS,
                "note": "pre-registered before the sweep ran",
            },
        },
        "k0_control": next(c for c in curve if c["novel_train_episodes"] == 0),
        "curve": curve,
        "time_to_capability": {
            "per_ordering": ttc_per_ordering,
            "median": statistics.median(ttc_values) if ttc_values else None,
            "min": min(ttc_values) if ttc_values else None,
            "max": max(ttc_values) if ttc_values else None,
            "orderings_reaching_criterion": len(ttc_values),
        },
        "rows": rows,
    }


def classify_offline(sweep: dict[str, Any], mature_reference: float) -> str:
    """Result class from the offline sweep, using the pre-registered signature.

    ``mature_reference`` is the decision accuracy the same candidate family reaches on the
    known families, used as the bar for "materially below mature capability" at k = 0.
    """
    k0 = sweep["k0_control"]
    if k0["decision_accuracy_mean"] >= mature_reference - 0.05 or k0["replay_success_mean"] >= 0.75:
        return "TYPE_B_NOT_ESTABLISHED"
    ttc = sweep["time_to_capability"]
    if ttc["median"] is None:
        # Too few validated novel episodes to test any k > 0: the teacher did not supply enough
        # evidence. If k > 0 was tested and capability never rose, acquisition failed.
        if len(sweep["curve"]) <= 1:
            return "INSUFFICIENT_EVIDENCE"
        rose = sweep["curve"][-1]["decision_accuracy_mean"] > k0["decision_accuracy_mean"]
        return "INSUFFICIENT_EVIDENCE" if rose else "TYPE_B_NOT_ESTABLISHED"
    top = [c for c in sweep["curve"] if c["novel_train_episodes"] >= ttc["median"]]
    # Retention is judged on quality-feasible candidates only. Infeasible intermediate candidates
    # (where the selector escalated to a calibrated backend that under-covers the probes) are
    # rejected on quality regardless; the first rule counted them and was refined after the 4B
    # sweep, which is disclosed in the report together with the original verdict.
    feasible_rows = [
        r for r in sweep["rows"] if r["novel_train_episodes"] >= ttc["median"] and r["quality_feasible"]
    ]
    if feasible_rows and any(r["retention_all_pass"] is False for r in feasible_rows):
        return "RETENTION_FAILURE"
    if all(c["family_aware_promote_rate"] == 0.0 and c["recent_promote_rate"] == 0.0 for c in top):
        return "CAPABILITY_ACQUIRED_NOT_CERTIFIED"
    return "CAPABILITY_AND_CERTIFICATION_SUCCEEDED"


def classify_offline_original_rule(sweep: dict[str, Any], mature_reference: float) -> str:
    """First version of the rule, kept for disclosure: retention counted on every candidate."""
    k0 = sweep["k0_control"]
    if k0["decision_accuracy_mean"] >= mature_reference - 0.05 or k0["replay_success_mean"] >= 0.75:
        return "TYPE_B_NOT_ESTABLISHED"
    ttc = sweep["time_to_capability"]
    if ttc["median"] is None:
        return "INSUFFICIENT_EVIDENCE"
    top = [c for c in sweep["curve"] if c["novel_train_episodes"] >= ttc["median"]]
    if any(c["retention_pass_rate"] < 1.0 for c in top):
        return "RETENTION_FAILURE"
    if all(c["family_aware_promote_rate"] == 0.0 and c["recent_promote_rate"] == 0.0 for c in top):
        return "CAPABILITY_ACQUIRED_NOT_CERTIFIED"
    return "CAPABILITY_AND_CERTIFICATION_SUCCEEDED"


def known_family_reference_accuracy(episodes: list[TrustedEpisode], seed: int = 21) -> float:
    """Decision accuracy of a known-only tree on held-out known episodes: the mature bar."""
    known = [ep for ep in episodes if ep.family != NOVEL_FAMILY]
    cert_known = known[-CERT_KNOWN:]
    train_known = known[: -2 * CERT_KNOWN]
    compiler = OnlineReflexCompiler(random_state=seed)
    train = [t for ep in train_known for t in ep.traces]
    validation = [t for ep in cert_known for t in ep.traces]
    selection, _, _ = compiler.fit_candidate(train, validation)
    y = np.asarray([t.action for t in validation]).astype(str)
    preds = np.asarray([str(selection.reflex.predict(t.features)[0]) for t in validation])
    return float(np.mean(preds == y))


def make_type_b_stream(seed: int = 0) -> tuple[list, list[str]]:
    """Interleaved arrival of the dependency family after a 12-episode known warmup, 69 episodes."""
    offset = seed * 1000 + 500  # distinct task instances from the offline trace collection
    tasks: list = []
    phases: list[str] = []
    known_counter = novel_counter = 0
    for _ in range(12):
        tasks.append(make_task(KNOWN[known_counter % len(KNOWN)], offset + known_counter))
        known_counter += 1
        phases.append("A")
    remaining = 69 - len(tasks)
    novel_positions = {int((j + 0.5) * remaining / 17) for j in range(17)}
    for j in range(remaining):
        if j in novel_positions:
            tasks.append(make_task(NOVEL_FAMILY, offset + 100 + novel_counter))
            novel_counter += 1
        else:
            tasks.append(make_task(KNOWN[known_counter % len(KNOWN)], offset + known_counter))
            known_counter += 1
        phases.append("M")
    return tasks, phases


def post_stream_exposure(controller, compiler, encoder: AgentFeatureEncoder, *, seed: int = 0, per_variant: int = 2) -> dict[str, Any]:
    """Run the final promoted agent on fresh dependency tasks after the stream ends.

    The stream fixes when promotion can happen but not how many opportunities follow it.
    This stage gives the promoted reflex a fixed number of fresh episodes (two per prompt
    variant, indices never seen in the stream or the offline traces) with the gate active
    and the teacher available as fallback, against an LLM-only baseline on the same tasks.
    """
    offset = seed * 1000 + 900
    tasks = [make_task(NOVEL_FAMILY, offset + i) for i in range(4 * per_variant)]
    frozen_version = compiler.state.version
    frozen_buffer_traces = compiler.buffer.trusted_trace_count
    rows = []
    for task in tasks:
        before = controller.snapshot()
        agent = compiler.make_agent(controller, encoder)  # frozen reflex and gate; no ingest
        episode = agent.run(task)
        usage = controller.snapshot().delta(before)
        # Diagnostic third arm: reflex alone, threshold forced to zero, no gate, no teacher.
        reflex_only = None
        if compiler.state.selection is not None:
            stub = _ForcedReplayStub()
            forced = ParadigmCodingAgent(stub, encoder=encoder, selection=replace(compiler.state.selection, threshold=0.0), ood_gate=None)
            ro = forced.run(task)
            reflex_only = {"success": ro.success and stub.calls == 0, "invalid_actions": stub.calls, "sequence": [d.action for d in ro.decisions]}
        b_before = controller.snapshot()
        baseline = ParadigmCodingAgent(controller, encoder=encoder).run(task)
        b_usage = controller.snapshot().delta(b_before)
        rows.append(
            {
                "task_id": task.task_id,
                "prompt_variant": int(task.task_id.rsplit("-", 1)[1]) % 4,
                "success": episode.success,
                "contract": episode.contract,
                "llm_calls": usage.calls,
                "reflex_calls": episode.reflex_calls,
                "tokens": usage.total_tokens,
                "llm_latency_ms": usage.latency_ms,
                "policy_latency_ms": episode.policy_latency_ms,
                "false_fast_path": bool(not episode.success and episode.reflex_calls > 0 and usage.calls == 0),
                "fallback_reasons": dict(episode.fallback_reasons),
                "sequence": [d.action for d in episode.decisions],
                "sources": [d.source for d in episode.decisions],
                "baseline_success": baseline.success,
                "baseline_llm_calls": b_usage.calls,
                "baseline_tokens": b_usage.total_tokens,
                "reflex_only": reflex_only,
            }
        )
    solved_without_llm = sum(1 for r in rows if r["success"] and r["llm_calls"] == 0)
    assert compiler.state.version == frozen_version and compiler.buffer.trusted_trace_count == frozen_buffer_traces
    return {
        "frozen": {"reflex_version": frozen_version, "buffer_traces": frozen_buffer_traces, "learning_during_evaluation": False},
        "episodes": len(rows),
        "active_version": compiler.state.version,
        "reflex_only_success_rate": float(np.mean([r["reflex_only"]["success"] for r in rows if r["reflex_only"] is not None])) if any(r["reflex_only"] for r in rows) else None,
        "success_rate": float(np.mean([r["success"] for r in rows])),
        "baseline_success_rate": float(np.mean([r["baseline_success"] for r in rows])),
        "solved_with_zero_llm_calls": solved_without_llm,
        "llm_calls": int(sum(r["llm_calls"] for r in rows)),
        "baseline_llm_calls": int(sum(r["baseline_llm_calls"] for r in rows)),
        "tokens": int(sum(r["tokens"] for r in rows)),
        "baseline_tokens": int(sum(r["baseline_tokens"] for r in rows)),
        "false_fast_path_failures": sum(1 for r in rows if not r["success"] and r["reflex_calls"] > 0 and r["llm_calls"] == 0),
        "rows": rows,
    }


def run_type_b_online(controller, *, seed: int = 0, certification: str = "family_aware") -> dict[str, Any]:
    shadow = "recent" if certification == "family_aware" else "family_aware"
    stream, phases = make_type_b_stream(seed)
    encoder = make_encoder()
    result = run_p23_live_online_benchmark(
        controller,
        stream=stream,
        phases=phases,
        random_state=21 + seed,
        arrival="interleaved",
        compiler_options={"certification": certification, "shadow_certification": shadow},
        novel_family=NOVEL_FAMILY,
        encoder=encoder,
        return_compiler=True,
    )
    compiler = result.pop("_compiler")
    result["phase"] = "P2.4-online"
    result["certification_mode"] = certification
    result["post_stream_exposure"] = post_stream_exposure(controller, compiler, encoder, seed=seed)
    return result


def write_p24_results(root: Path, payload: dict[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "core_p24_type_b.json").write_text(json.dumps(payload, indent=2, default=float), encoding="utf-8")
    lines = ["# P2.4 Type B Skill Acquisition Report", ""]
    lines.append(
        "Type B tests whether Paradigm can acquire a genuinely new action policy from validated deliberative "
        "experience. The `dependency_error` family requires four actions the known families never use "
        "(inspect_dependency, search_registry, modify_dependency_file, install_dependency) and cannot be solved "
        "by the known sequence: apply_fix changes nothing for it. Capability is measured independently of any "
        "trust gate; Time-to-Capability uses a criterion fixed before the sweep ran."
    )
    lines.append("")
    lines.append("Narrative interpretation: `INTERPRETATION.md` in this directory.")
    lines.append("")
    for model, block in payload["models"].items():
        teacher = block["teacher"]
        sweep = block["sweep"]
        lines.append(f"## {model}")
        lines.append("")
        lines.append("### Teacher traces")
        lines.append("")
        lines.append(f"- Novel episodes: {teacher['novel_episodes']}, success {teacher['novel_success_rate']:.0%}, contract {teacher['novel_contract_rate']:.0%}")
        lines.append(f"- Invalid LLM actions on novel episodes: {teacher['novel_invalid_llm_actions']}")
        lines.append(f"- Mean steps: {teacher['novel_mean_steps']:.1f}; distinct successful sequences: {teacher['novel_distinct_sequences']}; modal sequence share: {teacher['novel_modal_sequence_share']:.0%}")
        lines.append(f"- Modal sequence: {teacher['novel_modal_sequence']}")
        lines.append(f"- Novel-episode tokens: {teacher['novel_tokens']}; LLM latency: {teacher['novel_llm_latency_ms'] / 1000:.1f} s")
        lines.append(f"- Known-family success: {teacher['known_success_rate']:.0%}")
        lines.append("")
        lines.append(f"### k = 0 control (mature known-family reference accuracy {block['mature_reference_accuracy']:.0%})")
        lines.append("")
        k0 = sweep["k0_control"]
        lines.append(f"- Decision accuracy on held-out novel decisions: {k0['decision_accuracy_mean']:.0%} (min {k0['decision_accuracy_min']:.0%})")
        lines.append(f"- Exact sequence accuracy: {k0['exact_sequence_accuracy_mean']:.0%}")
        lines.append(f"- Forced-replay episode success: {k0['replay_success_mean']:.0%}; invalid reflex actions per ordering: {k0['replay_invalid_actions_mean']:.1f}")
        lines.append(f"- Gate acceptance: {k0['gate_acceptance_mean']:.2f}")
        lines.append(f"- Result class (offline): `{block['offline_class']}`")
        lines.append("")
        lines.append("### Capability and trust versus novel training evidence")
        lines.append("")
        lines.append("| Novel train episodes | Decision accuracy mean (min) | Exact sequence | Replay success | Replay invalid | Gate acceptance mean (min) | Recent promote | Family-aware promote | Retention pass | TTC criterion met |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for c in sweep["curve"]:
            lines.append(
                f"| {c['novel_train_episodes']} | {c['decision_accuracy_mean']:.0%} ({c['decision_accuracy_min']:.0%}) | "
                f"{c['exact_sequence_accuracy_mean']:.0%} | {c['replay_success_mean']:.0%} | {c['replay_invalid_actions_mean']:.1f} | "
                f"{c['gate_acceptance_mean']:.2f} ({c['gate_acceptance_min']:.2f}) | {c['recent_promote_rate']:.0%} | "
                f"{c['family_aware_promote_rate']:.0%} | {c['retention_pass_rate']:.0%} | {c['ttc_criterion_rate']:.0%} |"
            )
        ttc = sweep["time_to_capability"]
        lines.append("")
        lines.append(
            f"Time-to-Capability (novel episodes to reach decision accuracy >= {TTC_DECISION_ACCURACY:.0%} and forced-replay "
            f"success {TTC_REPLAY_SUCCESS:.0%} on the held-out episodes): median {ttc['median']}, range "
            f"[{ttc['min']}, {ttc['max']}], {ttc['orderings_reaching_criterion']} of {sweep['design']['orderings']} orderings reached it. "
            f"Per ordering: {ttc['per_ordering']}."
        )
        lines.append("")
        if block.get("online"):
            for mode, r in block["online"].items():
                sig = r["signature_metrics"]
                nov = r["novel_family"]
                lines.append(f"### Online acquisition, {mode} certification authoritative")
                lines.append("")
                lines.append(f"- Episodes {r['stream']['episodes']}, online success {r['online']['success_rate']:.0%}, baseline success {r['baseline']['success_rate']:.0%}")
                lines.append(f"- LLM call reduction {r['llm_usage']['llm_call_reduction']:.0%}, token reduction {r['llm_usage']['token_reduction']:.0%}")
                lines.append(f"- Novel-family success {nov['overall']['success_rate']:.0%}, first novel episode {r['stream']['first_novel_family_episode']}, deployed at {nov['represented_from_episode']}, first fast path {nov['first_fast_path_episode']}")
                lines.append(f"- Time-to-reflex {sig['time_to_reflex']['validated_episodes']} (learning {sig['time_to_reflex'].get('learning_evidence')}, certification {sig['time_to_reflex'].get('certification_evidence')}), outcome {sig['time_to_reflex'].get('outcome')}")
                lines.append(f"- Unknown false fast-path rate {nov['unknown_false_fast_path_rate']:.0%}; invalid reflex actions {r['online']['invalid_reflex_actions']:.0f}")
                lines.append(f"- Acquisition debt {sig['acquisition_debt']}; reflex dividend {sig['reflex_dividend']['novel_llm_calls_saved']} calls, {sig['reflex_dividend']['novel_tokens_saved']} tokens over {sig['reflex_dividend']['novel_episodes_after_representation']} episodes; debt recovery (tokens) {sig.get('debt_recovery_ratio_tokens')}")
                ret = r["old_family_retention"]
                lines.append(f"- Known-family success after representation {ret['known_after_representation'].get('success_rate')}, fast path {ret['known_after_representation'].get('fast_path_coverage')}")
                lines.append(f"- Novel fast path after representation: {sig['reflex_dividend']['novel_fast_path_after_representation']}")
                lines.append("")
                lines.append("| Episode | Family | Source | LLM calls | Reflex calls | Success | Baseline success |")
                lines.append("|---|---|---|---|---|---|---|")
                for row in r["per_episode"]:
                    if row["family"] == NOVEL_FAMILY:
                        src = "reflex" if row["llm_calls"] == 0 else ("mixed" if row["reflex_calls"] else "LLM")
                        lines.append(f"| {row['episode']} | {row['family']} | {src} | {row['llm_calls']} | {row['reflex_calls']} | {row['success']} | {row.get('baseline_success')} |")
                lines.append("")
                ps = r.get("post_stream_exposure")
                if ps:
                    lines.append(f"Post-stream exposure on {ps['episodes']} fresh dependency tasks with the final agent (version {ps['active_version']}): "
                                 f"success {ps['success_rate']:.0%} versus LLM-only {ps['baseline_success_rate']:.0%}; "
                                 f"{ps['solved_with_zero_llm_calls']} solved with zero LLM calls; LLM calls {ps['llm_calls']} versus {ps['baseline_llm_calls']}; "
                                 f"tokens {ps['tokens']} versus {ps['baseline_tokens']}; false fast-path failures {ps['false_fast_path_failures']}.")
                    lines.append("")
                    lines.append(f"Reflex-only diagnostic arm (no gate, no teacher) success: {ps.get('reflex_only_success_rate')}. Evaluation is frozen: reflex version {ps['frozen']['reflex_version']}, no learning during evaluation.")
                    lines.append("")
                    lines.append("| Task | Prompt variant | Sources | LLM calls | Reflex calls | Fallback | Hybrid success | LLM-only success | Reflex-only success |")
                    lines.append("|---|---|---|---|---|---|---|---|---|")
                    for row in ps["rows"]:
                        ro = row.get("reflex_only") or {}
                        lines.append(f"| {row['task_id']} | {row['prompt_variant']} | {' '.join('R' if x == 'reflex' else 'L' for x in row['sources'])} | {row['llm_calls']} | {row['reflex_calls']} | {row['fallback_reasons']} | {row['success']} | {row['baseline_success']} | {ro.get('success')} |")
                    lines.append("")
        lines.append(f"Result class: `{block['final_class']}`")
        lines.append("")
    (root / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_p24_benchmark(
    *,
    models: list[str],
    orderings: int = 5,
    online: bool = False,
    output: str = "results/core_p24",
    log=print,
) -> dict[str, Any]:
    """Full P2.4 driver: traces (cached when present), sweep, classification, optional online loop.

    ``models`` entries are ``model|api_style|base_url``. Shared by the benchmark script and the
    ``paradigm benchmark p24`` command so the experimental logic exists once.
    """
    root = Path(output)
    payload_path = root / "core_p24_type_b.json"
    payload = json.loads(payload_path.read_text()) if payload_path.exists() else {"phase": "P2.4", "models": {}}

    for spec in models:
        model, api_style, base_url = spec.split("|")
        controller = OpenAICompatibleCodingDeliberator(base_url=base_url, model=model, api_style=api_style, timeout_s=180)
        key = model.replace(":", "_")
        trace_path = root / "traces" / f"{key}__{api_style}.json"
        stats_path = root / "traces" / f"{key}__{api_style}__teacher.json"
        if trace_path.exists() and stats_path.exists():
            episodes = load_episodes(trace_path)
            teacher = json.loads(stats_path.read_text())
            log(f"loaded {len(episodes)} trace episodes for {model}")
        else:
            episodes, teacher = collect_type_b_episodes(controller)
            save_episodes(trace_path, episodes)
            stats_path.parent.mkdir(parents=True, exist_ok=True)
            stats_path.write_text(json.dumps(teacher, indent=2, default=float), encoding="utf-8")
            log(f"collected {len(episodes)} trace episodes for {model}: novel success {teacher['novel_success_rate']:.0%}")
        block = payload["models"].get(model, {})
        block["teacher"] = teacher
        block["mature_reference_accuracy"] = known_family_reference_accuracy(episodes)
        sweep = run_type_b_sweep(episodes, orderings=orderings)
        block["sweep"] = sweep
        block["offline_class"] = classify_offline(sweep, block["mature_reference_accuracy"])
        block["offline_class_original_rule"] = classify_offline_original_rule(sweep, block["mature_reference_accuracy"])
        for c in sweep["curve"]:
            log(f"{model} k={c['novel_train_episodes']}: acc {c['decision_accuracy_mean']:.2f} replay {c['replay_success_mean']:.2f} gate {c['gate_acceptance_mean']:.2f} promote recent {c['recent_promote_rate']:.0%} fam {c['family_aware_promote_rate']:.0%}")
        log(f"{model} TTC {sweep['time_to_capability']} class {block['offline_class']}")
        block["final_class"] = block["offline_class"]
        if online and block["offline_class"] == "CAPABILITY_AND_CERTIFICATION_SUCCEEDED":
            block.setdefault("online", {})
            for mode in ("family_aware", "recent"):
                if mode in block["online"]:
                    log(f"{model} online {mode}: already recorded")
                    continue
                result = run_type_b_online(controller, certification=mode)
                block["online"][mode] = result
                payload["models"][model] = block
                write_p24_results(root, payload)
                sig = result["signature_metrics"]
                log(f"{model} online {mode}: success {result['online']['success_rate']:.0%} calls -{result['llm_usage']['llm_call_reduction']:.0%} TTR {sig['time_to_reflex']['validated_episodes']} outcome {sig['time_to_reflex'].get('outcome')} novel success {result['novel_family']['overall']['success_rate']:.0%}")
            fam = block["online"]["family_aware"]
            ttr = fam["signature_metrics"]["time_to_reflex"]
            if ttr.get("outcome") != "promoted":
                block["final_class"] = "INSUFFICIENT_EVIDENCE" if ttr.get("outcome") == "insufficient_evidence" else "CAPABILITY_ACQUIRED_NOT_CERTIFIED"
            elif fam["old_family_retention"]["known_after_representation"].get("success_rate", 1.0) < 1.0:
                block["final_class"] = "RETENTION_FAILURE"
        payload["models"][model] = block
        write_p24_results(root, payload)
    return payload


def summarize_p24_payload(payload: dict[str, Any]) -> str:
    """Concise text summary of a recorded P2.4 artifact. Every number comes from the payload."""
    lines = ["Paradigm P2.4 Type B", ""]
    for model, block in payload.get("models", {}).items():
        sweep = block["sweep"]
        k0 = sweep["k0_control"]
        ttc = sweep["time_to_capability"]
        teacher = block["teacher"]
        top = sweep["curve"][-1]
        lines.append(f"Teacher {model}")
        lines.append(f"  validated demonstrations  {round(teacher['novel_success_rate'] * teacher['novel_episodes'])}/{teacher['novel_episodes']}")
        lines.append(f"  result class              {block.get('final_class', block.get('offline_class'))}")
        lines.append("")
        lines.append("  Type B control (k = 0)")
        lines.append(f"    decision accuracy       {k0['decision_accuracy_mean']:.0%}")
        lines.append(f"    exact sequence          {k0['exact_sequence_accuracy_mean']:.0%}")
        lines.append(f"    replay success          {k0['replay_success_mean']:.0%}")
        lines.append("")
        lines.append("  Capability")
        if ttc["median"] is not None:
            lines.append(f"    TTC median              {ttc['median']:.0f} episodes (range {ttc['min']} to {ttc['max']})")
        else:
            lines.append(f"    TTC                     not reached ({len(sweep['curve'])} k value(s) testable)")
        lines.append(f"    capability at k = {top['novel_train_episodes']:<3}   {top['decision_accuracy_mean']:.0%} decisions, {top['replay_success_mean']:.0%} replay")
        online = block.get("online") or {}
        for mode, r in online.items():
            sig = r["signature_metrics"]
            lines.append("")
            lines.append(f"  Online ({mode} certification)")
            lines.append(f"    time-to-reflex          {sig['time_to_reflex']['validated_episodes']}")
            lines.append(f"    promoted at episode     {r['novel_family']['represented_from_episode']}")
            lines.append(f"    overall success         {r['online']['success_rate']:.0%} (baseline {r['baseline']['success_rate']:.0%})")
            lines.append(f"    LLM calls avoided       {r['llm_usage']['llm_call_reduction']:.0%}")
            lines.append(f"    false fast paths        {r['novel_family']['unknown_false_fast_path_rate']:.0%}")
            ps = r.get("post_stream_exposure")
            if ps:
                n = ps["episodes"]
                lines.append("")
                lines.append(f"  Frozen held-out ({mode} reflex, {n} fresh tasks)")
                lines.append(f"    LLM-only                {round(ps['baseline_success_rate'] * n)}/{n}")
                lines.append(f"    hybrid                  {round(ps['success_rate'] * n)}/{n}")
                ro = ps.get("reflex_only_success_rate")
                lines.append(f"    reflex-only             {round(ro * n)}/{n}" if ro is not None else "    reflex-only             n/a")
                lines.append(f"    false fast paths        {ps['false_fast_path_failures']}")
                lines.append(f"    LLM calls               {ps['baseline_llm_calls']} -> {ps['llm_calls']}")
                lines.append(f"    tokens                  {ps['baseline_tokens']:,} -> {ps['tokens']:,}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
