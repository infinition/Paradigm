from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from paradigm.p0 import environment_metadata
from paradigm.p01 import run_measured_deliberation
from paradigm.scenarios import deterministic_routing, noisy_routing, repeated_workflows, shifted_routing


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Paradigm Core P0.1 measured deliberation benchmark.")
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--probes", type=int, default=1024)
    parser.add_argument("--output", type=Path, default=Path("results/core_p01/core_p01_measured.json"))
    args = parser.parse_args()

    scenarios = [
        deterministic_routing(n=3600, seed=args.seed),
        noisy_routing(n=3600, seed=args.seed + 1),
        shifted_routing(n=3600, seed=args.seed + 2),
        repeated_workflows(n_workflows=120, repeats=30, seed=args.seed + 3),
    ]
    payload: dict[str, object] = {
        "benchmark": "Paradigm Core P0.1 measured deliberation",
        "environment": environment_metadata(),
        "scenarios": {},
    }
    for i, scenario in enumerate(scenarios):
        print(f"running {scenario.name}...")
        payload["scenarios"][scenario.name] = run_measured_deliberation(
            scenario.traces,
            seed=args.seed + 100 + i,
            probes=args.probes,
        )

    passes = [v["go_no_go"]["all_pass"] for v in payload["scenarios"].values()]
    payload["summary"] = {
        "scenarios_passed": int(sum(passes)),
        "scenarios_total": len(passes),
        "all_pass": bool(all(passes)),
        "scope": "measured local surrogate only",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, allow_nan=True) + "\n")
    print(json.dumps(payload["summary"], indent=2))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
