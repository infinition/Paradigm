"""B0: does the state carry the procedure, on the frozen a3-code-1 trace.

Four arms, one decision, one candidate set, one metric: which of the available
actions was taken. Leave one mission out, five seeds, mean and standard deviation.
No tuning after seeing a result; the protocol is in
results/d1_experience/a3_code_prereg.md.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from dataset_builder import load, report  # noqa: E402
from model import build, head  # noqa: E402

TRACE = Path("results/d1_experience/attempts/a3-code-1/trace.jsonl")
SEEDS = (0, 1, 2, 3, 4)
ARMS = {
    "B0-A  goal": dict(use_state=False, use_action=False),
    "B0-B  goal + state": dict(use_state=True, use_action=False),
    "B0-C  goal + action": dict(use_state=False, use_action=True),
    "B0-D  goal + state + action": dict(use_state=True, use_action=True),
}


def goal_vectors(decisions):
    """Frozen sentence encoder, on the distinct goal texts only."""
    from sentence_transformers import SentenceTransformer

    goals = sorted({d.goal for d in decisions})
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
    return np.asarray(model.encode(goals, normalize_embeddings=True), dtype=np.float32)


def run_arm(decisions, vectors, tools, seed, *, use_state, use_action):
    X, y, groups, index = build(decisions, vectors, tools, use_state=use_state, use_action=use_action)
    missions = sorted(set(groups))
    correct = 0
    for held in missions:  # leave one mission out
        train, test = groups != held, groups == held
        clf = head(seed)
        if len(set(y[train])) < 2:
            continue
        clf.fit(X[train], y[train])
        if not use_action:
            pred = clf.predict(X[test])
            correct += int((pred == y[test]).sum())
        else:
            # Score every candidate of a decision, take the argmax over the same set.
            proba = clf.predict_proba(X[test])
            positive = list(clf.classes_).index(1) if 1 in clf.classes_ else None
            scores = proba[:, positive] if positive is not None else np.zeros(len(proba))
            idx = index[test]
            for d_i in sorted(set(idx)):
                mask = idx == d_i
                chosen = tools[int(np.argmax(scores[mask]))]
                correct += int(chosen == decisions[d_i].taken)
    return correct / len(decisions)


def main() -> int:
    decisions = load(TRACE)
    print(report(decisions, TRACE))
    tools = sorted(decisions[0].candidates)
    majority = Counter(d.taken for d in decisions).most_common(1)[0]
    print(f"trivial baseline, always {majority[0]}: {majority[1] / len(decisions):.3f}")
    print(f"uniform over {len(tools)} candidates: {1 / len(tools):.3f}")
    print()

    vectors = goal_vectors(decisions)
    results = {}
    for name, cfg in ARMS.items():
        scores = [run_arm(decisions, vectors, tools, s, **cfg) for s in SEEDS]
        results[name] = (float(np.mean(scores)), float(np.std(scores)), scores)
        print(f"{name:<30} top-1 {np.mean(scores):.3f} +/- {np.std(scores):.3f}   {[round(s, 3) for s in scores]}")

    Path("experiments/decision_model_v0/results_b0.json").write_text(
        json.dumps(
            {
                "trace": str(TRACE),
                "decisions": len(decisions),
                "missions": len(set(d.mission for d in decisions)),
                "candidates": len(tools),
                "majority_baseline": majority[1] / len(decisions),
                "seeds": list(SEEDS),
                "arms": {k: {"mean": v[0], "std": v[1], "per_seed": v[2]} for k, v in results.items()},
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
