"""Raw numbers of a D1 pilot attempt, read from its trace and nothing else.

Usage: python results/d1_experience/summarize_pilot.py <attempt dir>

Reports, in this order and before any interpretation: missions verified, model calls and
tokens, exploitable validated transitions, distinct action keys with their distribution
per domain. The diversity criterion of the pre-registration is evaluated last, from those
numbers, and printed as a verdict per clause.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

CAMERA_TOOLS = {"camera", "computer"}


def domain_of(row: dict) -> str:
    """Which pilot block a row belongs to, from the state, not from the run order."""
    actions = set(row.get("available_actions") or [])
    goal = row.get("goal_raw") or ""
    if "camera" in actions and "calc.py" not in goal:
        return "camera"
    return "code"


def main(attempt_dir: str) -> int:
    path = Path(attempt_dir) / "trace.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    steps = [r for r in rows if r["record"] == "step"]
    episodes = [r for r in rows if r["record"] == "episode"]

    by_episode: dict[int, list[dict]] = defaultdict(list)
    for s in steps:
        by_episode[s["stream_episode"]].append(s)
    episode_status = {e["stream_episode"]: e["episode_status"] for e in episodes}
    episode_domain = {}
    for ep, ss in by_episode.items():
        episode_domain[ep] = domain_of(ss[0])

    verified = sum(1 for e in episodes if e["episode_status"] == "success")
    calls = sum(int(s.get("model_calls", 0)) for s in steps)
    tokens_in = sum(int(s.get("input_tokens", 0)) for s in steps)
    tokens_out = sum(int(s.get("output_tokens", 0)) for s in steps)

    # Exploitable validated transition: a verified SUCCESS step inside an episode that
    # closed SUCCESS. Nothing else can become positive evidence.
    exploitable = [
        s for s in steps
        if s["verified_outcome"] == "success" and episode_status.get(s["stream_episode"]) == "success"
    ]
    keys_by_domain: dict[str, Counter] = {"code": Counter(), "camera": Counter()}
    for s in exploitable:
        keys_by_domain[episode_domain[s["stream_episode"]]][s["executed_action"].split("#")[0]] += 1
    all_keys = Counter()
    for s in exploitable:
        all_keys[s["executed_action"]] += 1

    print("=" * 72)
    print(f"D1 pilot raw numbers: {attempt_dir}")
    print("=" * 72)
    print()
    print(f"1. missions verified            {verified} / {len(episodes)} closed episodes")
    for dom in ("code", "camera"):
        eps = [ep for ep, d in episode_domain.items() if d == dom]
        ok = sum(1 for ep in eps if episode_status.get(ep) == "success")
        print(f"     {dom:<8} {ok} / {len(eps)}")
    print()
    print(f"2. model calls                  {calls}")
    print(f"   tokens                       {tokens_in + tokens_out}  (in {tokens_in}, out {tokens_out})")
    if by_episode:
        print(f"   per mission                  {calls / len(by_episode):.1f} calls, {(tokens_in + tokens_out) / len(by_episode):.0f} tokens")
    print()
    print(f"3. exploitable validated transitions   {len(exploitable)}")
    print(f"   (steps observed: {len(steps)}, of which success {sum(1 for s in steps if s['verified_outcome'] == 'success')},")
    print(f"    unknown {sum(1 for s in steps if s['verified_outcome'] == 'unknown')},")
    print(f"    failure {sum(1 for s in steps if s['verified_outcome'] == 'failure')})")
    print()
    print("4. distinct action keys (on exploitable transitions)")
    distinct_total = len({s["executed_action"].split("#")[0] for s in exploitable})
    print(f"   distinct tools               {distinct_total}")
    for dom in ("code", "camera"):
        c = keys_by_domain[dom]
        print(f"     {dom:<8} {len(c)} distinct: {dict(c)}")
    print(f"   distinct templated keys      {len(all_keys)}")
    for k, n in all_keys.most_common():
        print(f"     {n:>4}  {k}")
    print()

    print("-" * 72)
    print("pre-registered diversity criterion")
    print("-" * 72)
    n_code, n_cam = len(keys_by_domain["code"]), len(keys_by_domain["camera"])
    c1 = distinct_total >= 5 and n_code >= 2 and n_cam >= 2
    print(f"  >= 5 distinct action keys, >= 2 per domain      {distinct_total} total, code {n_code}, camera {n_cam}   {'PASS' if c1 else 'FAIL'}")

    # A structural negative: an episode that closed SUCCESS without the domain's trigger
    # action (code: no edit; camera: no capture), in a state distinguishable from the
    # positives of its domain.
    negatives = {"code": [], "camera": []}
    for ep, ss in by_episode.items():
        if episode_status.get(ep) != "success":
            continue
        tools = {s["executed_action"].split("#")[0] for s in ss}
        dom = episode_domain[ep]
        if dom == "code" and "file_edit" not in tools and "file_write" not in tools:
            negatives["code"].append(ep)
        if dom == "camera" and not any(s["outcome_evidence"].get("images") for s in ss):
            negatives["camera"].append(ep)
    c2 = all(negatives[d] for d in ("code", "camera"))
    print(f"  >= 1 structural negative per domain             code {len(negatives['code'])}, camera {len(negatives['camera'])}   {'PASS' if c2 else 'FAIL'}")

    top = all_keys.most_common(1)
    share = (top[0][1] / len(exploitable)) if exploitable and top else 1.0
    c3 = share <= 0.70
    print(f"  no action key > 70% of validated steps          max share {share:.0%}   {'PASS' if c3 else 'FAIL'}")
    print()
    print(f"  criterion: {'MET' if (c1 and c2 and c3) else 'NOT MET'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "results/d1_experience/attempts/d1-pilot-a1"))
