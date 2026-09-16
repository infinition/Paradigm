from __future__ import annotations

import argparse
import json
from pathlib import Path

from paradigm.p11 import run_p11_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Paradigm Core P1.1 multi-layer continual benchmark.")
    parser.add_argument("--output", type=Path, default=Path("results/core_p11/core_p11_multilayer.json"))
    args = parser.parse_args()
    result = run_p11_benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "methods": {
            k: {
                "mean_seen": v["final_mean_seen_accuracy"]["mean"],
                "current": v["final_current_accuracy"]["mean"],
                "worst": v["final_worst_seen_accuracy"]["mean"],
                "seconds": v["total_adapt_seconds"]["mean"],
                "step_drift": None if v["mean_max_step_drift"] is None else v["mean_max_step_drift"]["mean"],
                "forgetting": v["final_mean_forgetting"]["mean"],
            }
            for k, v in result["continual_adaptation"].items()
        },
        "update_space": result["trusted_update_space"],
    }, indent=2, sort_keys=True))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
