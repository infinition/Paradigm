"""Three arms on the micro environment: does a policy need the goal, the state, or both.

Primary test: next-action accuracy on (goal, layout) pairs never seen together, where the
goal was seen with other layouts and the layout with other goals. Secondary: layouts never
seen at all, and confidence on states where the goal is impossible.
"""

from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.neural_network import MLPClassifier

sys.path.insert(0, str(Path(__file__).parent))
from env import ACTIONS, ALL_GOALS, COLORS, N, ZONES, Goal, make_layout, rollout  # noqa: E402

SEEN_LAYOUTS, UNSEEN_LAYOUTS, HOLDOUT_PAIR_RATE, SEEDS = 180, 20, 0.15, (0, 1, 2, 3, 4)


def encode_state(s) -> np.ndarray:
    v = [s.agent[0] / N, s.agent[1] / N]
    v += [1.0 if s.hand == c else 0.0 for c in COLORS] + [1.0 if s.hand is None else 0.0]
    for c in COLORS:
        p = s.position_of(c)
        v += [0.0, 0.0, 0.0] if p is None else [1.0, p[0] / N, p[1] / N]
    for z in ZONES:
        p = s.zone_position(z)
        v += [p[0] / N, p[1] / N]
    grid = np.zeros(N * N, dtype=np.float32)
    for (x, y) in s.obstacles:
        grid[y * N + x] = 1.0
    return np.concatenate([np.array(v, dtype=np.float32), grid])


def encode_goal(g: Goal) -> np.ndarray:
    v = np.zeros(len(ALL_GOALS), dtype=np.float32)
    v[[str(x) for x in ALL_GOALS].index(str(g))] = 1.0
    return v


def build():
    rows = []
    for layout_id in range(SEEN_LAYOUTS + UNSEEN_LAYOUTS):
        state0 = make_layout(layout_id)
        for g in ALL_GOALS:
            for s, action in rollout(state0, g):
                rows.append({"layout": layout_id, "goal": str(g), "gvec": encode_goal(g),
                             "svec": encode_state(s), "y": ACTIONS.index(action)})
    return rows


def arms(rows, train_idx, test_idx, seed):
    out = {}
    for name, use_goal, use_state in (("goal only", True, False), ("state only", False, True), ("goal + state", True, True)):
        def feats(i):
            parts = []
            if use_goal:
                parts.append(rows[i]["gvec"])
            if use_state:
                parts.append(rows[i]["svec"])
            return np.concatenate(parts)
        X_tr = np.stack([feats(i) for i in train_idx])
        y_tr = np.array([rows[i]["y"] for i in train_idx])
        X_te = np.stack([feats(i) for i in test_idx])
        y_te = np.array([rows[i]["y"] for i in test_idx])
        clf = MLPClassifier(hidden_layer_sizes=(64,), max_iter=400, random_state=seed)
        clf.fit(X_tr, y_tr)
        out[name] = float((clf.predict(X_te) == y_te).mean())
    return out


def main() -> int:
    rows = build()
    rng = random.Random(20260918)
    pairs = [(l, str(g)) for l in range(SEEN_LAYOUTS) for g in ALL_GOALS]
    holdout = set(rng.sample(pairs, int(len(pairs) * HOLDOUT_PAIR_RATE)))
    train, test_pair, test_layout = [], [], []
    for i, r in enumerate(rows):
        if r["layout"] >= SEEN_LAYOUTS:
            test_layout.append(i)
        elif (r["layout"], r["goal"]) in holdout:
            test_pair.append(i)
        else:
            train.append(i)

    maj = Counter(rows[i]["y"] for i in train).most_common(1)[0][0]
    print(f"samples {len(rows)}  train {len(train)}  unseen pairs {len(test_pair)}  unseen layouts {len(test_layout)}")
    print(f"goals {len(ALL_GOALS)}  layouts {SEEN_LAYOUTS}+{UNSEEN_LAYOUTS}  actions {len(ACTIONS)}")
    print(f"trivial baseline (majority action) on unseen pairs: "
          f"{np.mean([rows[i]['y'] == maj for i in test_pair]):.3f}")
    print()

    results = {}
    for split, idx in (("unseen goal/layout pairs", test_pair), ("unseen layouts", test_layout)):
        scores = {k: [] for k in ("goal only", "state only", "goal + state")}
        for seed in SEEDS:
            for k, v in arms(rows, train, idx, seed).items():
                scores[k].append(v)
        results[split] = {k: (float(np.mean(v)), float(np.std(v))) for k, v in scores.items()}
        print(f"--- {split} ---")
        for k, (m, s) in results[split].items():
            print(f"  {k:<14} {m:.3f} +/- {s:.3f}")
        print()

    Path("experiments/micro_env/results_b1.json").write_text(json.dumps(
        {"samples": len(rows), "train": len(train), "test_pair": len(test_pair),
         "test_layout": len(test_layout), "seeds": list(SEEDS), "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
