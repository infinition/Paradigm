"""B0 dataset: one decision per observed step, from a frozen D1 trace.

A decision is "which of the available actions did the teacher take in this state".
Every arm answers that same question on that same candidate set, so no arm is
favoured by its formulation.

Kept: every step of an episode that closed SUCCESS, writes included. A write is
learnable evidence about the procedure even though the adapter marks it not reflex
capable and it is never replayed; the two properties are recorded separately on
each row and never conflated.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

WRITE_TOOLS = {"file_edit", "file_write"}


@dataclass
class Decision:
    mission: int          # stream_episode, the grouping unit for the split
    step: int
    goal: str
    candidates: list[str]  # available tools in this state, the candidate set
    taken: str             # the tool the teacher used
    phase: str
    last_action: str
    last_outcome: str
    output_kind: str
    recent: list[str]
    consecutive_failures: int
    reflex_capable: bool   # recorded, never used to filter
    is_write: bool


def load(trace: Path) -> list[Decision]:
    rows = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines() if line.strip()]
    status = {r["stream_episode"]: r["episode_status"] for r in rows if r["record"] == "episode"}
    out: list[Decision] = []
    for r in rows:
        if r["record"] != "step" or status.get(r["stream_episode"]) != "success":
            continue
        st = r["state_raw"]
        tool = r["executed_action"].split("#")[0]
        candidates = list(r["available_actions"])
        if tool not in candidates:
            # The teacher used a tool the state did not advertise: the decision is not
            # answerable on this candidate set, so it is dropped and counted.
            continue
        out.append(
            Decision(
                mission=r["stream_episode"],
                step=r["step_id"],
                goal=r["goal_raw"],
                candidates=candidates,
                taken=tool,
                phase=st.get("phase", ""),
                last_action=st.get("last_action") or "none",
                last_outcome=st.get("last_outcome", "none"),
                output_kind=(st.get("features") or {}).get("last_output_kind", "none"),
                recent=list(st.get("recent_actions") or []),
                consecutive_failures=int((st.get("features") or {}).get("consecutive_failures", 0)),
                reflex_capable=r["verified_outcome"] == "success",
                is_write=tool in WRITE_TOOLS,
            )
        )
    return out


def report(decisions: list[Decision], trace: Path) -> str:
    rows = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines() if line.strip()]
    steps = [r for r in rows if r["record"] == "step"]
    status = {r["stream_episode"]: r["episode_status"] for r in rows if r["record"] == "episode"}
    learnable = [r for r in steps if status.get(r["stream_episode"]) == "success"]
    dropped = len(learnable) - len(decisions)
    taken = {d.taken for d in decisions}
    return (
        f"steps in SUCCESS episodes {len(learnable)}, decisions kept {len(decisions)}, "
        f"dropped as not in the candidate set {dropped}\n"
        f"missions {len(({d.mission for d in decisions}))}, candidate set size "
        f"{len(decisions[0].candidates)}, distinct taken tools {len(taken)}: {sorted(taken)}\n"
        f"writes kept {sum(d.is_write for d in decisions)}, "
        f"reflex-capable steps {sum(d.reflex_capable for d in decisions)}, "
        f"distinct goal texts {len({d.goal for d in decisions})}"
    )
