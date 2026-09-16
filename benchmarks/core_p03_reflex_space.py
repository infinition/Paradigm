from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from paradigm.p0 import environment_metadata
from paradigm.p03 import run_reflex_space_benchmark
from paradigm.reflex_space_scenarios import make_reflex_pool_scenario


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Paradigm Core P0.3 trusted reflex-space benchmark.")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--output", type=Path, default=Path("results/core_p03/core_p03_reflex_space.json"))
    parser.add_argument("--aligned-trials", type=int, default=8000)
    parser.add_argument("--behavior-trials", type=int, default=6000)
    args = parser.parse_args()

    scenario = make_reflex_pool_scenario(seed=args.seed)
    payload = {
        "benchmark": "Paradigm Core P0.3 trusted reflex/update space",
        "environment": environment_metadata(),
        "seed": args.seed,
        **run_reflex_space_benchmark(
            scenario,
            seed=args.seed,
            aligned_search_trials=args.aligned_trials,
            behavior_control_trials=args.behavior_trials,
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, allow_nan=True) + "\n")

    summary = {
        "parameter_space": {
            "clean_accept": payload["parameter_space"]["clean_accept_rate"],
            "poison_false_accept": payload["parameter_space"]["poison_false_accept_rate"],
            "weak_pool_accept": payload["parameter_space"]["weak_pool_valid_accept_rate"],
        },
        "behavior_space": {
            "clean_accept": payload["behavior_space"]["clean_accept_rate"],
            "poison_false_accept": payload["behavior_space"]["poison_false_accept_rate"],
            "weak_pool_accept": payload["behavior_space"]["weak_pool_valid_accept_rate"],
        },
        "parameter_aligned_attack": payload["parameter_aligned_attack"],
    }
    print(json.dumps(summary, indent=2))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
