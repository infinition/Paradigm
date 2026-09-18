"""S101-sim-lite: a purely kinematic arm, deterministic, no contact and no dynamics.

The action is a parameterized primitive, `approach(red)` and `approach(blue)` being
different actions, because the parameter is exactly what the goal has to determine. If the
label were only the primitive type, the goal would carry almost nothing and the benchmark
would answer itself.

States for the primary dataset are sampled independently of the goal, so the arm's pose
cannot encode an intention already being pursued.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

OBJECTS = ("red", "blue", "green")
ZONES = ("zone_A", "zone_B")
LINKS = (0.35, 0.30, 0.20)          # shoulder, elbow, wrist, in metres
LIMITS = ((-math.pi, math.pi), (-1.2, 1.2), (-1.8, 1.8), (-1.4, 1.4))
NEAR, ALIGNED = 0.12, 0.05          # metres

ACTIONS = tuple(
    [f"approach({o})" for o in OBJECTS] + [f"align({o})" for o in OBJECTS]
    + ["grasp", "lift"] + [f"approach({z})" for z in ZONES] + ["release", "retreat"]
)


@dataclass(frozen=True)
class ArmState:
    joints: tuple[float, float, float, float]
    holding: str | None
    objects: tuple[tuple[str, tuple[float, float, float]], ...]
    zones: tuple[tuple[str, tuple[float, float, float]], ...]

    def pose_of(self, name: str) -> tuple[float, float, float] | None:
        for n, p in self.objects + self.zones:
            if n == name:
                return p
        return None


def forward_kinematics(joints: tuple[float, float, float, float]) -> tuple[float, float, float]:
    base, sh, el, wr = joints
    reach, height = 0.0, 0.0
    angle = 0.0
    for link, delta in zip(LINKS, (sh, el, wr)):
        angle += delta
        reach += link * math.cos(angle)
        height += link * math.sin(angle)
    return (reach * math.cos(base), reach * math.sin(base), height)


def distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.dist(a, b)


def expert(state: ArmState, goal: tuple[str, str, str | None]) -> str:
    """Next primitive of a deterministic operator. The order of the tests is the policy."""
    kind, obj, zone = goal
    tip = forward_kinematics(state.joints)

    if kind == "PICK":
        if state.holding == obj:
            return "retreat"
        if state.holding is not None:
            return "release"
        target = state.pose_of(obj)
        d = distance(tip, target)
        if d > NEAR:
            return f"approach({obj})"
        if d > ALIGNED:
            return f"align({obj})"
        return "grasp"

    zone_pose = state.pose_of(zone)
    if state.holding == obj:
        if distance(tip, zone_pose) > NEAR:
            return "lift" if tip[2] < zone_pose[2] else f"approach({zone})"
        return "release"
    if state.holding is not None:
        return "release"
    if distance(state.pose_of(obj), zone_pose) <= ALIGNED:
        return "retreat"
    return expert(state, ("PICK", obj, None))


ALL_GOALS = tuple([("PICK", o, None) for o in OBJECTS] + [("PLACE", o, z) for o in OBJECTS for z in ZONES])


def goal_name(goal) -> str:
    kind, obj, zone = goal
    return f"{kind}({obj})" if zone is None else f"{kind}({obj},{zone})"


def sample_scene(rng: random.Random, y_band: tuple[float, float] = (0.0, 0.35)) -> tuple[tuple, tuple]:
    """Object and zone poses on a table in front of the arm. `y_band` bounds the absolute
    lateral offset, which is how a region of placements is held out of training."""
    lo, hi = y_band

    def pose() -> tuple[float, float, float]:
        y = rng.uniform(lo, hi) * rng.choice((-1.0, 1.0))
        return (rng.uniform(0.25, 0.70), y, rng.uniform(0.0, 0.10))
    objects = tuple((o, pose()) for o in OBJECTS)
    zones = tuple((z, pose()) for z in ZONES)
    return objects, zones


def sample_neutral_state(rng: random.Random, objects, zones) -> ArmState:
    """Joint angles and hand content drawn independently of any goal."""
    joints = tuple(rng.uniform(lo, hi) for lo, hi in LIMITS)
    # Holding is rare on purpose: with a hand full half the time, a third of the labels
    # became `release`, which a state-only policy can predict from the hand alone without
    # ever consulting the goal. Fixed here, before any training.
    holding = rng.choice([None] * 12 + list(OBJECTS))
    remaining = tuple((o, p) for o, p in objects if o != holding)
    # Random joint angles almost never put the tip near an object, which left the dataset
    # with no grasp and no align at all and reduced the task to choosing which object to
    # approach. Half the states therefore place one object near the tip. The object is
    # drawn at random and never from the goal, so the state stays goal-independent.
    if remaining and rng.random() < 0.5:
        tip = forward_kinematics(joints)
        radius = rng.choice([ALIGNED * 0.5, (ALIGNED + NEAR) / 2])
        theta, phi = rng.uniform(0, 2 * math.pi), rng.uniform(0, math.pi)
        near_pose = (
            tip[0] + radius * math.sin(phi) * math.cos(theta),
            tip[1] + radius * math.sin(phi) * math.sin(theta),
            tip[2] + radius * math.cos(phi),
        )
        chosen = rng.randrange(len(remaining))
        remaining = tuple(
            (o, near_pose if i == chosen else p) for i, (o, p) in enumerate(remaining)
        )
    return ArmState(joints=joints, holding=holding, objects=remaining, zones=zones)
