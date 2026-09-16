from __future__ import annotations

import argparse
import json
from pathlib import Path

from paradigm.p05 import run_persistent_lifecycle_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Paradigm Core P0.5 persistent lifecycle benchmark.")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/core_p05/core_p05_lifecycle.json"),
    )
    parser.add_argument(
        "--store",
        type=Path,
        default=Path("results/core_p05/runtime_store"),
    )
    args = parser.parse_args()

    result = run_persistent_lifecycle_benchmark(args.store, seed=args.seed, reset_store=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["observed"], indent=2, sort_keys=True))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
