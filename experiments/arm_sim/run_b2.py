"""B2: the same three arms on a kinematic arm, with primitives as actions.

Splits, each reported separately so it is visible which one breaks:
  unseen poses          object and zone placements drawn from a region never used in train
  unseen scenes         whole scenes never seen
  compositional         object and zone both seen, that pairing never seen together

The goal is encoded in parts, kind and object and zone, so a pairing never seen in train is
still made of parts that were. Holding out an object identity is not attempted: with
identity encoding its dimension would never be active in train and the failure would be by
construction, not a measure of generalization. It needs objects described by attributes,
and is left for that.
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
from arm import (ACTIONS, ALL_GOALS, OBJECTS, ZONES, expert, forward_kinematics,  # noqa: E402
                 goal_name, sample_neutral_state, sample_scene)

SCENES, STATES_PER_SCENE, SEEDS = 1400, 3, (0, 1, 2, 3, 4)
HELD_OUT_PAIRS = {("red", "zone_A"), ("blue", "zone_B")}   # compositional split
POSE_REGION_Y = 0.20                                        # y above this is the held-out region


def encode_state(s) -> np.ndarray:
    tip = forward_kinematics(s.joints)
    v = list(s.joints) + list(tip)
    v += [1.0 if s.holding == o else 0.0 for o in OBJECTS] + [1.0 if s.holding is None else 0.0]
    for o in OBJECTS:
        p = s.pose_of(o)
        v += [0.0, 0.0, 0.0, 0.0] if p is None else [1.0, *p]
    for z in ZONES:
        v += list(s.pose_of(z))
    return np.array(v, dtype=np.float32)


def encode_goal(goal) -> np.ndarray:
    kind, obj, zone = goal
    v = [1.0 if kind == "PICK" else 0.0, 1.0 if kind == "PLACE" else 0.0]
    v += [1.0 if obj == o else 0.0 for o in OBJECTS]
    v += [1.0 if zone == z else 0.0 for z in ZONES] + [1.0 if zone is None else 0.0]
    return np.array(v, dtype=np.float32)


def build():
    """Scenes are drawn by type rather than filtered after the fact: filtering on "any
    object outside the band" put 94% of scenes in the held-out region and left a train set
    smaller than any test set."""
    rng = random.Random(20260918)
    rows = []
    for scene_id in range(SCENES):
        kind = "pose_ood" if scene_id % 20 < 3 else ("scene_ood" if scene_id % 20 < 6 else "train")
        band = (POSE_REGION_Y, 0.35) if kind == "pose_ood" else (0.0, POSE_REGION_Y)
        objects, zones = sample_scene(rng, y_band=band)
        in_region = kind == "pose_ood"
        for _ in range(STATES_PER_SCENE):
            state = sample_neutral_state(rng, objects, zones)
            svec = encode_state(state)
            for goal in ALL_GOALS:
                kind, obj, zone = goal
                rows.append({
                    "scene": scene_id, "region": in_region,
                    "pair": (obj, zone) if kind == "PLACE" else None,
                    "gvec": encode_goal(goal), "svec": svec,
                    "y": ACTIONS.index(expert(state, goal)),
                })
    return rows


def arm_scores(rows, train_idx, test_idx, seed):
    out = {}
    for name, use_goal, use_state in (("goal only", True, False), ("state only", False, True), ("goal + state", True, True)):
        def feats(i):
            parts = ([rows[i]["gvec"]] if use_goal else []) + ([rows[i]["svec"]] if use_state else [])
            return np.concatenate(parts)
        clf = MLPClassifier(hidden_layer_sizes=(96,), max_iter=400, random_state=seed)
        clf.fit(np.stack([feats(i) for i in train_idx]), np.array([rows[i]["y"] for i in train_idx]))
        pred = clf.predict(np.stack([feats(i) for i in test_idx]))
        out[name] = float((pred == np.array([rows[i]["y"] for i in test_idx])).mean())
    return out


def main() -> int:
    rows = build()
    unseen_scenes = {s for s in range(SCENES) if 3 <= s % 20 < 6}
    train, t_pose, t_scene, t_comp = [], [], [], []
    for i, r in enumerate(rows):
        if r["scene"] in unseen_scenes:
            t_scene.append(i)
        elif r["pair"] in HELD_OUT_PAIRS:
            t_comp.append(i)
        elif r["region"]:
            t_pose.append(i)
        else:
            train.append(i)

    maj = Counter(rows[i]["y"] for i in train).most_common(1)[0][0]
    print(f"samples {len(rows)}  train {len(train)}  unseen poses {len(t_pose)}  "
          f"unseen scenes {len(t_scene)}  compositional {len(t_comp)}")
    print(f"actions {len(ACTIONS)}  goals {len(ALL_GOALS)}  scenes {SCENES}")
    for label, idx in (("unseen poses", t_pose), ("unseen scenes", t_scene), ("compositional", t_comp)):
        print(f"  trivial baseline on {label}: {np.mean([rows[i]['y'] == maj for i in idx]):.3f}")
    print()

    results = {}
    for label, idx in (("unseen poses", t_pose), ("unseen scenes", t_scene), ("compositional pairing", t_comp)):
        scores = {k: [] for k in ("goal only", "state only", "goal + state")}
        for seed in SEEDS:
            for k, v in arm_scores(rows, train, idx, seed).items():
                scores[k].append(v)
        results[label] = {k: (float(np.mean(v)), float(np.std(v))) for k, v in scores.items()}
        print(f"--- {label} ---")
        for k, (m, s) in results[label].items():
            print(f"  {k:<14} {m:.3f} +/- {s:.3f}")
        print()

    Path("experiments/arm_sim/results_b2.json").write_text(json.dumps(
        {"samples": len(rows), "train": len(train), "seeds": list(SEEDS), "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
