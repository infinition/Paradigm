from __future__ import annotations

import argparse
import json
from pathlib import Path

from paradigm.p10 import run_bounded_plasticity_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Paradigm Core P1.0 bounded-plasticity benchmark.")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/core_p10/core_p10_bounded_plasticity.json"),
    )
    args = parser.parse_args()
    result = run_bounded_plasticity_benchmark(seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "bound_check": {k: v["bound_respected"] for k, v in result["bound_check"].items()},
        "shock_methods": {
            k: {
                "new_acc": v["shifted_accuracy_after_adaptation"]["mean"],
                "old_acc": v["old_accuracy_after_adaptation"]["mean"],
                "max_step_drift": v["max_step_preactivation_drift"]["mean"],
            }
            for k, v in result["distribution_shock"]["methods"].items()
        },
    }, indent=2, sort_keys=True))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
