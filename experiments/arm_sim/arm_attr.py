"""B2.1: objects described by attributes instead of identity.

An object is a hue, a size and a shape, and a goal names those attributes rather than a
name. The action refers to a slot, and slot order is shuffled per scene, so the policy
cannot learn a fixed mapping from goal to slot and has to match the goal's attributes
against what the scene contains. That matching is the semantic generalization being tested:
an unseen attribute value, an unseen combination, an unseen instance.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from arm import ALIGNED, LIMITS, NEAR, ZONES, distance, forward_kinematics

SHAPES = ("cube", "sphere", "cylinder")
SLOTS = 3
HUE_BUCKETS, SIZE_BUCKETS = 5, 3
ACTIONS = tuple(
    [f"approach(slot{i})" for i in range(SLOTS)] + [f"align(slot{i})" for i in range(SLOTS)]
    + ["grasp", "lift"] + [f"approach({z})" for z in ZONES] + ["release", "retreat"]
)


@dataclass(frozen=True)
class Attributes:
    hue: float
    size: float
    shape: str

    def signature(self) -> tuple[int, int, str]:
        return (min(int(self.hue * HUE_BUCKETS), HUE_BUCKETS - 1),
                min(int((self.size - 0.02) / 0.05 * SIZE_BUCKETS), SIZE_BUCKETS - 1),
                self.shape)

    def vector(self) -> list[float]:
        return [self.hue, self.size * 20.0] + [1.0 if self.shape == s else 0.0 for s in SHAPES]


@dataclass(frozen=True)
class Scene:
    joints: tuple[float, ...]
    slots: tuple[tuple[Attributes, tuple[float, float, float]] | None, ...]
    held: int | None                       # slot index of the object in the gripper
    zones: tuple[tuple[str, tuple[float, float, float]], ...]

    def zone_pose(self, zone: str) -> tuple[float, float, float]:
        return dict(self.zones)[zone]


def target_slot(scene: Scene, wanted: Attributes) -> int:
    """The slot whose attributes match the goal. The goal is always drawn from an object the
    scene contains, so the match is exact and the nearest slot is that object."""
    best, best_d = 0, float("inf")
    for i, entry in enumerate(scene.slots):
        if entry is None:
            continue
        attrs, _ = entry
        d = abs(attrs.hue - wanted.hue) + abs(attrs.size - wanted.size) * 20 + (0.0 if attrs.shape == wanted.shape else 1.0)
        if d < best_d:
            best, best_d = i, d
    return best


def expert(scene: Scene, goal: tuple[str, Attributes, str | None]) -> str:
    kind, wanted, zone = goal
    tip = forward_kinematics(scene.joints)
    slot = target_slot(scene, wanted)

    if kind == "PICK":
        if scene.held == slot:
            return "retreat"
        if scene.held is not None:
            return "release"
        pose = scene.slots[slot][1]
        d = distance(tip, pose)
        return f"approach(slot{slot})" if d > NEAR else (f"align(slot{slot})" if d > ALIGNED else "grasp")

    zone_pose = scene.zone_pose(zone)
    if scene.held == slot:
        if distance(tip, zone_pose) > NEAR:
            return "lift" if tip[2] < zone_pose[2] else f"approach({zone})"
        return "release"
    if scene.held is not None:
        return "release"
    if distance(scene.slots[slot][1], zone_pose) <= ALIGNED:
        return "retreat"
    return expert(scene, ("PICK", wanted, None))


def sample_scene(rng: random.Random, *, hue_band: tuple[float, float] = (0.0, 1.0)) -> Scene:
    joints = tuple(rng.uniform(lo, hi) for lo, hi in LIMITS)
    tip = forward_kinematics(joints)

    def pose() -> tuple[float, float, float]:
        return (rng.uniform(0.25, 0.70), rng.uniform(-0.35, 0.35), rng.uniform(0.0, 0.10))

    entries = []
    for _ in range(SLOTS):
        attrs = Attributes(rng.uniform(*hue_band), rng.uniform(0.02, 0.07), rng.choice(SHAPES))
        entries.append((attrs, pose()))
    # Half the scenes put one randomly chosen object within reach, so grasp and align exist.
    if rng.random() < 0.5:
        i = rng.randrange(SLOTS)
        radius = rng.choice([ALIGNED * 0.5, (ALIGNED + NEAR) / 2])
        entries[i] = (entries[i][0], (tip[0] + radius, tip[1], tip[2]))
    rng.shuffle(entries)                                  # slot order carries no meaning
    held = rng.randrange(SLOTS) if rng.random() < 0.2 else None
    zones = tuple((z, pose()) for z in ZONES)
    return Scene(joints=joints, slots=tuple(entries), held=held, zones=zones)


def encode_scene(scene: Scene) -> list[float]:
    tip = forward_kinematics(scene.joints)
    v = list(scene.joints) + list(tip) + [1.0 if scene.held is None else 0.0]
    for i, entry in enumerate(scene.slots):
        attrs, pose = entry
        v += attrs.vector() + list(pose) + [1.0 if scene.held == i else 0.0]
    for z in ZONES:
        v += list(scene.zone_pose(z))
    return v


def encode_goal(goal) -> list[float]:
    kind, wanted, zone = goal
    return ([1.0 if kind == "PICK" else 0.0, 1.0 if kind == "PLACE" else 0.0]
            + wanted.vector()
            + [1.0 if zone == z else 0.0 for z in ZONES]
            + [1.0 if zone is None else 0.0])
