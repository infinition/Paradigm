"""Feature construction and the small head, shared by the four B0 arms.

Arms without the candidate action emit a distribution over the candidate set.
Arms with it score one candidate at a time and the argmax over the same set is
the decision. Both routes therefore answer the same question and are scored by
top-1 on the same candidates.
"""

from __future__ import annotations

import numpy as np
from sklearn.neural_network import MLPClassifier

PHASES = ("start", "after_tool")
OUTCOMES = ("none", "success", "failure", "uncertain")
KINDS = ("none", "other", "tests_passed", "tests_failed", "missing_module", "syntax_error", "name_error", "import_error", "not_found", "image")


def _onehot(value: str, vocabulary: tuple[str, ...]) -> np.ndarray:
    v = np.zeros(len(vocabulary) + 1, dtype=np.float32)
    v[vocabulary.index(value) if value in vocabulary else len(vocabulary)] = 1.0
    return v


def state_features(d, tools: list[str]) -> np.ndarray:
    """Structured state only. No text, no candidate action."""
    recent = np.zeros(len(tools), dtype=np.float32)
    for t in d.recent:
        if t in tools:
            recent[tools.index(t)] = 1.0
    return np.concatenate([
        _onehot(d.phase, PHASES),
        _onehot(d.last_action, tuple(tools)),
        _onehot(d.last_outcome, OUTCOMES),
        _onehot(d.output_kind, KINDS),
        recent,
        np.array([d.step / 10.0, d.consecutive_failures / 3.0], dtype=np.float32),
    ])


def build(decisions, goal_vectors, tools, *, use_state: bool, use_action: bool):
    """Returns (X, y, groups) for a multi-class arm, or (X, y, groups, index) for a
    per-candidate scoring arm, where index maps each row to its decision."""
    goals = sorted({d.goal for d in decisions})
    contexts = []
    for d in decisions:
        parts = [goal_vectors[goals.index(d.goal)]]
        if use_state:
            parts.append(state_features(d, tools))
        contexts.append(np.concatenate(parts))
    groups = np.array([d.mission for d in decisions])

    if not use_action:
        X = np.stack(contexts)
        y = np.array([tools.index(d.taken) for d in decisions])
        return X, y, groups, None

    rows, labels, row_groups, index = [], [], [], []
    for i, (d, ctx) in enumerate(zip(decisions, contexts)):
        for t in tools:
            rows.append(np.concatenate([ctx, _onehot(t, tuple(tools))]))
            labels.append(1 if t == d.taken else 0)
            row_groups.append(d.mission)
            index.append(i)
    return np.stack(rows), np.array(labels), np.array(row_groups), np.array(index)


def head(seed: int) -> MLPClassifier:
    """One small MLP, identical for every arm."""
    return MLPClassifier(hidden_layer_sizes=(64,), max_iter=800, random_state=seed, early_stopping=False)
