from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from paradigm.p0 import environment_metadata, run_scenario
from paradigm.scenarios import all_core_p0_scenarios


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Paradigm Core P0 synthetic benchmark suite.")
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--output", type=Path, default=Path("results/core_p0/core_p0_suite.json"))
    args = parser.parse_args()

    payload: dict[str, object] = {
        "benchmark": "Paradigm Core P0",
        "claim_level": "synthetic research benchmark only",
        "environment": environment_metadata(),
        "seed": args.seed,
        "scenarios": {},
    }

    for offset, scenario in enumerate(all_core_p0_scenarios(seed=args.seed)):
        print(f"running {scenario.name}...")
        outcome = run_scenario(scenario.traces, seed=args.seed + 100 + offset)
        outcome["description"] = scenario.description
        payload["scenarios"][scenario.name] = outcome

    passes = [bool(v["go_no_go"]["quality_pass"]) for v in payload["scenarios"].values()]
    payload["summary"] = {
        "quality_scenarios_passed": int(sum(passes)),
        "quality_scenarios_total": len(passes),
        "all_quality_gates_pass": bool(all(passes)),
        "phase1_go": "pending_real_deliberative_baseline",
        "interpretation": (
            "Synthetic quality gates are necessary but not sufficient. Phase 1 still requires measured efficiency against a realistic deliberative path."
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, allow_nan=True) + "\n")
    print(json.dumps(payload["summary"], indent=2))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
