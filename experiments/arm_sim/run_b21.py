"""B2.1: does the policy generalize to objects it has never seen described that way.

Held out of training, each tested separately:
  unseen hue         a band of hue absent from every training scene
  unseen combination a shape and size pairing absent from training, both seen apart
  unseen scene       a scene never seen, attributes in distribution (control)

Goals name attributes, slot order is shuffled per scene, so the policy has to match the
goal against the scene rather than memorise an identity.
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
from arm import ZONES  # noqa: E402
from arm_attr import (ACTIONS, SLOTS, Attributes, Scene, encode_goal, encode_scene,  # noqa: E402
                      expert, sample_scene)

SCENES, SEEDS = 2600, (0, 1, 2, 3, 4)
HUE_BAND = (0.60, 0.80)
FORBIDDEN_COMBO = ("sphere", 2)          # shape, size bucket


def in_band(a: Attributes) -> bool:
    return HUE_BAND[0] <= a.hue < HUE_BAND[1]


def is_combo(a: Attributes) -> bool:
    return a.shape == FORBIDDEN_COMBO[0] and a.signature()[1] == FORBIDDEN_COMBO[1]


def clean_scene(rng: random.Random) -> Scene:
    """A scene whose objects avoid the held-out hue band and the held-out combination."""
    while True:
        sc = sample_scene(rng)
        if not any(in_band(a) or is_combo(a) for a, _ in sc.slots):
            return sc


def ood_scene(rng: random.Random, mode: str) -> tuple[Scene, int]:
    """A scene where exactly one slot carries the held-out property, and its index."""
    while True:
        sc = sample_scene(rng)
        hits = [i for i, (a, _) in enumerate(sc.slots)
                if (in_band(a) if mode == "hue" else is_combo(a))]
        others = [i for i in range(SLOTS) if i not in hits]
        if len(hits) == 1 and all(not (in_band(a) or is_combo(a)) for i, (a, _) in enumerate(sc.slots) if i in others):
            return sc, hits[0]


def rows_for(scene: Scene, slots: list[int]) -> list[dict]:
    out = []
    for i in slots:
        attrs = scene.slots[i][0]
        for goal in [("PICK", attrs, None)] + [("PLACE", attrs, z) for z in ZONES]:
            out.append({"gvec": np.array(encode_goal(goal), dtype=np.float32),
                        "svec": np.array(encode_scene(scene), dtype=np.float32),
                        "y": ACTIONS.index(expert(scene, goal))})
    return out


def build():
    rng = random.Random(20260918)
    train, t_hue, t_combo, t_scene = [], [], [], []
    for i in range(SCENES):
        bucket = i % 20
        if bucket < 3:
            sc, slot = ood_scene(rng, "hue")
            t_hue += rows_for(sc, [slot])
        elif bucket < 6:
            sc, slot = ood_scene(rng, "combo")
            t_combo += rows_for(sc, [slot])
        elif bucket < 9:
            t_scene += rows_for(clean_scene(rng), list(range(SLOTS)))
        else:
            train += rows_for(clean_scene(rng), list(range(SLOTS)))
    return train, {"unseen hue": t_hue, "unseen combination": t_combo, "unseen scene": t_scene}


def score(train, test, seed):
    out = {}
    for name, use_goal, use_state in (("goal only", True, False), ("state only", False, True), ("goal + state", True, True)):
        def feats(r):
            return np.concatenate(([r["gvec"]] if use_goal else []) + ([r["svec"]] if use_state else []))
        clf = MLPClassifier(hidden_layer_sizes=(96,), max_iter=400, random_state=seed)
        clf.fit(np.stack([feats(r) for r in train]), np.array([r["y"] for r in train]))
        pred = clf.predict(np.stack([feats(r) for r in test]))
        out[name] = float((pred == np.array([r["y"] for r in test])).mean())
    return out


def main() -> int:
    train, tests = build()
    maj = Counter(r["y"] for r in train).most_common(1)[0][0]
    print(f"train {len(train)}  " + "  ".join(f"{k} {len(v)}" for k, v in tests.items()))
    for k, v in tests.items():
        print(f"  trivial baseline on {k}: {np.mean([r['y'] == maj for r in v]):.3f}")
    print()
    results = {}
    for label, test in tests.items():
        acc = {k: [] for k in ("goal only", "state only", "goal + state")}
        for seed in SEEDS:
            for k, v in score(train, test, seed).items():
                acc[k].append(v)
        results[label] = {k: (float(np.mean(v)), float(np.std(v))) for k, v in acc.items()}
        print(f"--- {label} ---")
        for k, (m, s) in results[label].items():
            print(f"  {k:<14} {m:.3f} +/- {s:.3f}")
        print()
    Path("experiments/arm_sim/results_b21.json").write_text(json.dumps(
        {"train": len(train), "tests": {k: len(v) for k, v in tests.items()},
         "seeds": list(SEEDS), "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
