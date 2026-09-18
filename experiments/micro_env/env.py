"""A small deterministic grid world for testing goal conditioning.

Principle one, which the whole benchmark rests on: the same goal must be reachable
from many states, and the same state must serve many goals. If either fails, one arm
wins by construction and the benchmark answers itself, which is how the two previous
attempts at this question failed.

Everything here is deterministic: the layouts come from a seeded generator and the
expert policy has a fixed tie-break, so a label never depends on chance.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, replace

N = 6
COLORS = ("red", "blue", "green")
ZONES = ("zone_A", "zone_B")
# Fixed order, and the tie-break of the planner: a shortest path is always the same one.
ACTIONS = ("move_N", "move_S", "move_E", "move_W", "pick", "drop", "no_op")
DELTA = {"move_N": (0, -1), "move_S": (0, 1), "move_E": (1, 0), "move_W": (-1, 0)}


@dataclass(frozen=True)
class State:
    agent: tuple[int, int]
    objects: tuple[tuple[str, tuple[int, int]], ...]  # colors still on the grid
    hand: str | None
    obstacles: frozenset[tuple[int, int]]
    zones: tuple[tuple[str, tuple[int, int]], ...]

    def object_at(self, pos: tuple[int, int]) -> str | None:
        return next((c for c, p in self.objects if p == pos), None)

    def position_of(self, color: str) -> tuple[int, int] | None:
        return next((p for c, p in self.objects if c == color), None)

    def zone_position(self, zone: str) -> tuple[int, int]:
        return dict(self.zones)[zone]


@dataclass(frozen=True)
class Goal:
    kind: str           # "PICK" or "PLACE"
    color: str
    zone: str | None = None

    def __str__(self) -> str:
        return f"{self.kind}({self.color})" if self.zone is None else f"{self.kind}({self.color},{self.zone})"


ALL_GOALS = tuple(
    [Goal("PICK", c) for c in COLORS] + [Goal("PLACE", c, z) for c in COLORS for z in ZONES]
)


def free(state: State, pos: tuple[int, int]) -> bool:
    x, y = pos
    return 0 <= x < N and 0 <= y < N and pos not in state.obstacles


def step(state: State, action: str) -> State:
    if action in DELTA:
        dx, dy = DELTA[action]
        target = (state.agent[0] + dx, state.agent[1] + dy)
        return replace(state, agent=target) if free(state, target) else state
    if action == "pick":
        here = state.object_at(state.agent)
        if here is not None and state.hand is None:
            return replace(state, hand=here, objects=tuple((c, p) for c, p in state.objects if c != here))
        return state
    if action == "drop":
        if state.hand is not None and state.object_at(state.agent) is None:
            return replace(state, hand=None, objects=tuple(sorted(state.objects + ((state.hand, state.agent),))))
        return state
    return state


def _first_step_towards(state: State, target: tuple[int, int]) -> str | None:
    """Breadth-first search with the fixed action order as its tie-break."""
    if state.agent == target:
        return None
    seen = {state.agent}
    queue = deque([(state.agent, None)])
    while queue:
        pos, first = queue.popleft()
        for action in ("move_N", "move_S", "move_E", "move_W"):
            dx, dy = DELTA[action]
            nxt = (pos[0] + dx, pos[1] + dy)
            if nxt in seen or not free(state, nxt):
                continue
            step_taken = first or action
            if nxt == target:
                return step_taken
            seen.add(nxt)
            queue.append((nxt, step_taken))
    return None


def expert(state: State, goal: Goal) -> str:
    """The action an optimal, deterministic operator takes next. `no_op` means the goal
    is reached, or is impossible in this state, and those two cases are separable by
    `goal_satisfied`."""
    if goal.kind == "PICK":
        if state.hand == goal.color:
            return "no_op"
        if state.hand is not None:
            return "drop" if state.object_at(state.agent) is None else (_first_step_towards(state, _free_cell(state)) or "no_op")
        target = state.position_of(goal.color)
        if target is None:
            return "no_op"
        return "pick" if state.agent == target else (_first_step_towards(state, target) or "no_op")

    zone_pos = state.zone_position(goal.zone)
    if state.hand == goal.color:
        return "drop" if state.agent == zone_pos else (_first_step_towards(state, zone_pos) or "no_op")
    if state.position_of(goal.color) == zone_pos and state.hand is None:
        return "no_op"
    return expert(state, Goal("PICK", goal.color))


def _free_cell(state: State) -> tuple[int, int]:
    for y in range(N):
        for x in range(N):
            if free(state, (x, y)) and state.object_at((x, y)) is None:
                return (x, y)
    return state.agent


def goal_satisfied(state: State, goal: Goal) -> bool:
    if goal.kind == "PICK":
        return state.hand == goal.color
    return state.position_of(goal.color) == state.zone_position(goal.zone) and state.hand is None


def goal_possible(state: State, goal: Goal) -> bool:
    return goal_satisfied(state, goal) or state.position_of(goal.color) is not None or state.hand == goal.color


def make_layout(seed: int, *, drop_color: str | None = None) -> State:
    """One layout: obstacles, object and zone positions, and where the agent starts.
    `drop_color` removes a colour from the grid, which makes goals about it impossible
    and gives the calibration test its ambiguous states."""
    rng = random.Random(seed)
    cells = [(x, y) for y in range(N) for x in range(N)]
    rng.shuffle(cells)
    obstacles = frozenset(cells[:4])
    rest = [c for c in cells[4:]]
    zones = tuple((z, rest[i]) for i, z in enumerate(ZONES))
    objects = tuple(sorted((c, rest[len(ZONES) + i]) for i, c in enumerate(COLORS) if c != drop_color))
    agent = rest[len(ZONES) + len(COLORS)]
    return State(agent=agent, objects=objects, hand=None, obstacles=obstacles, zones=zones)


def rollout(state: State, goal: Goal, limit: int = 40) -> list[tuple[State, str]]:
    """The expert's trajectory, as (state, next action) pairs. Stops when the goal is
    reached, so `no_op` labels do not flood the dataset."""
    out: list[tuple[State, str]] = []
    for _ in range(limit):
        if goal_satisfied(state, goal):
            break
        action = expert(state, goal)
        out.append((state, action))
        if action == "no_op":
            break
        state = step(state, action)
    return out
