from __future__ import annotations

import argparse
import json
from pathlib import Path

from paradigm.p12 import run_p12_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Paradigm Core P1.2 family-conditioned trusted plasticity benchmark.")
    parser.add_argument("--output", type=Path, default=Path("results/core_p12/core_p12_family_trust.json"))
    parser.add_argument("--steps", type=int, default=90)
    args = parser.parse_args()
    result = run_p12_benchmark(steps=args.steps)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "family_conditioned_trust": {
            family: {
                "clean": value["heldout_clean"],
                "poison": value["targeted_poison"],
                "cross_family": value["cross_family"],
            }
            for family, value in result["family_conditioned_trust"].items()
        },
        "risk_conditioned_epsilon": result["risk_conditioned_epsilon"],
        "combined_baseline": result["combined_baseline"],
    }, indent=2, sort_keys=True))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
