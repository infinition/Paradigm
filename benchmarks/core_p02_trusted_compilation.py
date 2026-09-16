from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from paradigm.p0 import environment_metadata
from paradigm.p02 import run_trusted_compilation_benchmark
from paradigm.trust_scenarios import make_trust_scenario


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Paradigm Core P0.2 trusted compilation benchmark.")
    parser.add_argument("--seed", type=int, default=41)
    parser.add_argument("--output", type=Path, default=Path("results/core_p02/core_p02_trust.json"))
    args = parser.parse_args()

    scenario = make_trust_scenario(seed=args.seed)
    payload = {
        "benchmark": "Paradigm Core P0.2 trusted compilation",
        "environment": environment_metadata(),
        "seed": args.seed,
        **run_trusted_compilation_benchmark(scenario, seed=args.seed),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, allow_nan=True) + "\n")
    print(json.dumps(payload["tradeoff_gates"], indent=2))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
