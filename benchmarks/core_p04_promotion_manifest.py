from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from paradigm.p0 import environment_metadata
from paradigm.p04 import run_promotion_manifest_benchmark
from paradigm.reflex_space_scenarios import make_reflex_pool_scenario


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Paradigm Core P0.4 promotion manifest benchmark.")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--output", type=Path, default=Path("results/core_p04/core_p04_promotion.json"))
    parser.add_argument("--aligned-trials", type=int, default=10000)
    args = parser.parse_args()

    scenario = make_reflex_pool_scenario(seed=args.seed)
    payload = {
        "benchmark": "Paradigm Core P0.4 promotion manifest",
        "environment": environment_metadata(),
        "seed": args.seed,
        **run_promotion_manifest_benchmark(
            scenario,
            seed=args.seed,
            aligned_search_trials=args.aligned_trials,
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, allow_nan=True) + "\n")
    print(json.dumps({
        "expected": payload["expected_decisions"],
        "observed": payload["observed_decisions"],
    }, indent=2))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
