"""B2.2: does the correspondence survive when the attributes are no longer exact.

The world and the teacher are unchanged: labels come from true attributes and true poses.
Only what the policy observes is degraded, which is the realistic split between a world that
is what it is and a perception that is imperfect. Noise is applied to the observed scene and
to the goal's description alike, since both would come from an imperfect source.

Reported against the noise level: accuracy, and the rate at which the noise makes the target
genuinely ambiguous, that is when a non-target object becomes closer to the goal description
than the target itself. Accuracy cannot exceed what that ambiguity leaves.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np
from sklearn.neural_network import MLPClassifier

sys.path.insert(0, str(Path(__file__).parent))
from arm import ZONES  # noqa: E402
from arm_attr import (ACTIONS, SLOTS, Attributes, encode_goal, encode_scene, expert,  # noqa: E402
                      sample_scene)

SCENES, SEEDS = 2200, (0, 1, 2)
LEVELS = (0.0, 0.02, 0.05, 0.10, 0.20)      # sigma, in units of hue; size and pose scaled


def jitter(rng: np.random.Generator, sigma: float, attrs: Attributes, pose) -> tuple[list[float], list[float]]:
    """Noisy observation of one object: hue, size, shape confusion, and pose."""
    hue = float(np.clip(attrs.hue + rng.normal(0, sigma), 0.0, 1.0))
    size = float(np.clip(attrs.size + rng.normal(0, sigma * 0.05), 0.02, 0.07))
    shape = attrs.shape
    if rng.random() < sigma:                 # shape is occasionally misread
        shape = rng.choice(["cube", "sphere", "cylinder"])
    noisy = Attributes(hue, size, shape)
    noisy_pose = [float(p + rng.normal(0, sigma * 0.05)) for p in pose]
    return noisy.vector(), noisy_pose


def attr_distance(a: Attributes, b: Attributes) -> float:
    return abs(a.hue - b.hue) + abs(a.size - b.size) * 20 + (0.0 if a.shape == b.shape else 1.0)


def build(sigma: float, seed: int):
    rng_py = random.Random(20260918)
    rng = np.random.default_rng(seed)
    rows, ambiguous, total = [], 0, 0
    for _ in range(SCENES):
        scene = sample_scene(rng_py)
        observed = [jitter(rng, sigma, a, p) for a, p in scene.slots]
        tip_block = list(scene.joints) + list(__import__("arm").forward_kinematics(scene.joints))
        for slot in range(SLOTS):
            true_attrs = scene.slots[slot][0]
            # The goal description is itself observed, so it carries the same noise.
            gvec, _ = jitter(rng, sigma, true_attrs, scene.slots[slot][1])
            goal_obs = Attributes(gvec[0], gvec[1] / 20.0, ["cube", "sphere", "cylinder"][int(np.argmax(gvec[2:]))])
            obs_attrs = [Attributes(v[0], v[1] / 20.0, ["cube", "sphere", "cylinder"][int(np.argmax(v[2:]))])
                         for v, _ in observed]
            nearest = int(np.argmin([attr_distance(goal_obs, o) for o in obs_attrs]))
            total += 1
            ambiguous += int(nearest != slot)

            svec = tip_block + [1.0 if scene.held is None else 0.0]
            for i, (vec, pose) in enumerate(observed):
                svec += vec + pose + [1.0 if scene.held == i else 0.0]
            for z in ZONES:
                svec += list(scene.zone_pose(z))
            for goal in [("PICK", true_attrs, None)] + [("PLACE", true_attrs, z) for z in ZONES]:
                kind, _, zone = goal
                g = ([1.0 if kind == "PICK" else 0.0, 1.0 if kind == "PLACE" else 0.0] + gvec
                     + [1.0 if zone == z else 0.0 for z in ZONES] + [1.0 if zone is None else 0.0])
                rows.append({"g": np.array(g, dtype=np.float32), "s": np.array(svec, dtype=np.float32),
                             "y": ACTIONS.index(expert(scene, goal))})
    return rows, ambiguous / max(total, 1)


def main() -> int:
    out = {}
    print(f"{'sigma':>6}  {'ambiguity':>9}  {'state only':>11}  {'goal + state':>13}")
    for sigma in LEVELS:
        accs = {"state only": [], "goal + state": []}
        amb = 0.0
        for seed in SEEDS:
            rows, amb = build(sigma, seed)
            split = int(len(rows) * 0.8)
            tr, te = rows[:split], rows[split:]
            for name, use_goal in (("state only", False), ("goal + state", True)):
                def feats(r):
                    return np.concatenate(([r["g"]] if use_goal else []) + [r["s"]])
                clf = MLPClassifier(hidden_layer_sizes=(96,), max_iter=400, random_state=seed)
                clf.fit(np.stack([feats(r) for r in tr]), np.array([r["y"] for r in tr]))
                accs[name].append(float((clf.predict(np.stack([feats(r) for r in te]))
                                         == np.array([r["y"] for r in te])).mean()))
        out[sigma] = {"ambiguity": amb, **{k: (float(np.mean(v)), float(np.std(v))) for k, v in accs.items()}}
        print(f"{sigma:>6.2f}  {amb:>9.3f}  {np.mean(accs['state only']):>7.3f}      "
              f"{np.mean(accs['goal + state']):>9.3f} +/- {np.std(accs['goal + state']):.3f}")
    Path("experiments/arm_sim/results_b22.json").write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
