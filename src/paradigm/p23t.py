from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import numpy as np

from .agent_scenarios import make_task
from .agent_vertical import AgentFeatureEncoder, ParadigmCodingAgent
from .llm_controller import OpenAICompatibleCodingDeliberator
from .online_learning import OnlineExperienceBuffer, OnlineReflexCompiler, RetentionProbeSet, TrustedEpisode
from .p23 import NOVEL_FAMILY
from .p23r import KNOWN
from .schema import Trace

KNOWN_ROUNDS = 8
NOVEL_EPISODES = 12
CERTIFICATION_NOVEL_EPISODES = 4
CERTIFICATION_KNOWN_EPISODES = 4


def collect_trace_episodes(controller: OpenAICompatibleCodingDeliberator, *, seed: int = 0) -> list[TrustedEpisode]:
    """LLM-only pass over 32 known and 12 novel episodes, keeping validated deliberative traces."""
    encoder = AgentFeatureEncoder()
    agent = ParadigmCodingAgent(controller, encoder=encoder)
    buffer = OnlineExperienceBuffer()
    offset = seed * 1000
    tasks = [make_task(KNOWN[i % len(KNOWN)], offset + i) for i in range(KNOWN_ROUNDS * len(KNOWN))]
    tasks += [make_task(NOVEL_FAMILY, offset + 100 + i) for i in range(NOVEL_EPISODES)]
    for task in tasks:
        buffer.ingest(agent.run(task))
    return buffer.episodes


def save_episodes(path: Path, episodes: list[TrustedEpisode]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "task_id": ep.task_id,
            "family": ep.family,
            "traces": [
                {"features": t.features.tolist(), "action": t.action, "metadata": t.metadata} for t in ep.traces
            ],
        }
        for ep in episodes
    ]
    path.write_text(json.dumps(payload), encoding="utf-8")


def load_episodes(path: Path) -> list[TrustedEpisode]:
    payload = json.loads(path.read_text())
    return [
        TrustedEpisode(
            ep["task_id"],
            ep["family"],
            [Trace(features=np.asarray(t["features"]), action=t["action"], valid=True, metadata=t["metadata"]) for t in ep["traces"]],
        )
        for ep in payload
    ]


def run_threshold_sweep(
    episodes: list[TrustedEpisode],
    *,
    orderings: int = 5,
    max_k: int = 8,
    minimum_ood_acceptance: float = 0.65,
    seed: int = 21,
) -> dict[str, Any]:
    """Fit candidates with k novel episodes in train against a fixed certification set.

    The certification set is the same for every k: four held-out novel episodes and four
    held-out known episodes. Retention probes come from a further four known episodes.
    Novel episode order is shuffled per ordering so k counts episodes, not a fixed prefix.
    """
    known = [ep for ep in episodes if ep.family != NOVEL_FAMILY]
    novel = [ep for ep in episodes if ep.family == NOVEL_FAMILY]
    if len(novel) < CERTIFICATION_NOVEL_EPISODES + max_k:
        max_k = len(novel) - CERTIFICATION_NOVEL_EPISODES
    cert_known = known[-CERTIFICATION_KNOWN_EPISODES:]
    probe_known = known[-2 * CERTIFICATION_KNOWN_EPISODES : -CERTIFICATION_KNOWN_EPISODES]
    train_known = known[: -2 * CERTIFICATION_KNOWN_EPISODES]
    rng = random.Random(seed)
    rows = []
    for ordering in range(orderings):
        order = list(novel)
        rng.shuffle(order)
        cert_novel = order[:CERTIFICATION_NOVEL_EPISODES]
        pool = order[CERTIFICATION_NOVEL_EPISODES:]
        validation = [t for ep in cert_known + cert_novel for t in ep.traces]
        for k in range(0, max_k + 1):
            train = [t for ep in train_known + pool[:k] for t in ep.traces]
            compiler = OnlineReflexCompiler(
                minimum_ood_acceptance=minimum_ood_acceptance,
                random_state=seed + ordering,
                certification="family_aware",
            )
            for fam in KNOWN:
                fam_traces = [t for ep in probe_known if ep.family == fam for t in ep.traces]
                if fam_traces:
                    compiler.state.probes[fam] = RetentionProbeSet(fam, fam_traces, 0, 0)
            selection, gate, chosen = compiler.fit_candidate(train, validation)
            recent = compiler.certify_candidate(selection, gate, train, validation, mode="recent")
            family_aware = compiler.certify_candidate(selection, gate, train, validation, mode="family_aware")
            novel_x = np.stack([t.features for ep in cert_novel for t in ep.traces])
            novel_y = np.asarray([t.action for ep in cert_novel for t in ep.traces]).astype(str)
            preds = np.asarray([str(selection.reflex.predict(x)[0]) for x in novel_x])
            confs = np.asarray([float(selection.reflex.predict(x)[1]) for x in novel_x])
            accepted = np.asarray(gate.accept(novel_x), dtype=bool)
            covered = accepted & (confs >= float(selection.threshold))
            rows.append(
                {
                    "ordering": ordering,
                    "novel_train_episodes": k,
                    "novel_train_decisions": sum(len(ep.traces) for ep in pool[:k]),
                    "backend": selection.backend,
                    "quality_feasible": bool(selection.feasible),
                    "novel_capability_accuracy": float(np.mean(preds == novel_y)),
                    "novel_gate_acceptance": float(np.mean(accepted)),
                    "novel_coverage": float(np.mean(covered)),
                    "novel_selective_accuracy": float(np.mean(preds[covered] == novel_y[covered])) if covered.any() else None,
                    "overall_acceptance": recent["overall_acceptance"],
                    "recent_outcome": recent["outcome"],
                    "family_aware_outcome": family_aware["outcome"],
                    "family_aware_reason": family_aware["reason"],
                }
            )
    by_k: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        by_k.setdefault(r["novel_train_episodes"], []).append(r)
    curve = []
    for k, items in sorted(by_k.items()):
        curve.append(
            {
                "novel_train_episodes": k,
                "orderings": len(items),
                "capability_accuracy_mean": float(np.mean([r["novel_capability_accuracy"] for r in items])),
                "capability_accuracy_min": float(np.min([r["novel_capability_accuracy"] for r in items])),
                "gate_acceptance_mean": float(np.mean([r["novel_gate_acceptance"] for r in items])),
                "gate_acceptance_min": float(np.min([r["novel_gate_acceptance"] for r in items])),
                "gate_acceptance_max": float(np.max([r["novel_gate_acceptance"] for r in items])),
                "recent_promote_rate": float(np.mean([r["recent_outcome"] == "promoted" for r in items])),
                "family_aware_promote_rate": float(np.mean([r["family_aware_outcome"] == "promoted" for r in items])),
            }
        )
    return {
        "phase": "P2.3T",
        "design": {
            "known_train_episodes": len(train_known),
            "known_certification_episodes": len(cert_known),
            "known_probe_episodes": len(probe_known),
            "novel_certification_episodes": CERTIFICATION_NOVEL_EPISODES,
            "orderings": orderings,
            "max_k": max_k,
            "minimum_ood_acceptance": minimum_ood_acceptance,
        },
        "curve": curve,
        "rows": rows,
    }


def write_p23t_results(root: Path, results_by_model: dict[str, dict[str, Any]]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "core_p23t_threshold.json").write_text(json.dumps(results_by_model, indent=2), encoding="utf-8")
    lines = ["# P2.3T Learning Threshold Sweep", ""]
    lines.append(
        "Candidates are fitted offline from LLM-only traces with k novel-family episodes in the train split, "
        "while the certification set (four held-out novel episodes plus four held-out known episodes) and the "
        "retention probes (four further known episodes) stay fixed for every k. Novel episode order is shuffled "
        "per ordering. Capability accuracy is the candidate's raw agreement with the teacher on the held-out novel "
        "decisions, independent of the gate. Gate acceptance is the shadow OOD acceptance of those decisions. "
        "This separates what the tree can reproduce from what the certification gate will admit."
    )
    lines.append("")
    lines.append("Narrative interpretation: `INTERPRETATION.md` in this directory.")
    lines.append("")
    for model, res in results_by_model.items():
        d = res["design"]
        lines.append(f"## {model}")
        lines.append("")
        lines.append(
            f"Known train episodes {d['known_train_episodes']}, certification {d['known_certification_episodes']} known + "
            f"{d['novel_certification_episodes']} novel episodes, probes {d['known_probe_episodes']} known episodes, "
            f"{d['orderings']} orderings, acceptance floor {d['minimum_ood_acceptance']}."
        )
        lines.append("")
        lines.append("| Novel train episodes | Capability accuracy mean (min) | Gate acceptance mean [min, max] | Recent promote rate | Family-aware promote rate |")
        lines.append("|---|---|---|---|---|")
        for c in res["curve"]:
            lines.append(
                f"| {c['novel_train_episodes']} | {c['capability_accuracy_mean']:.0%} ({c['capability_accuracy_min']:.0%}) | "
                f"{c['gate_acceptance_mean']:.2f} [{c['gate_acceptance_min']:.2f}, {c['gate_acceptance_max']:.2f}] | "
                f"{c['recent_promote_rate']:.0%} | {c['family_aware_promote_rate']:.0%} |"
            )
        lines.append("")
    (root / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
