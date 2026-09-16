from __future__ import annotations

import argparse
import json
from pathlib import Path

from paradigm.p13 import run_p13_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Paradigm Core P1.3 persistent family lifecycle benchmark.")
    parser.add_argument("--store", type=Path, default=Path("results/core_p13/family_store"))
    parser.add_argument("--output", type=Path, default=Path("results/core_p13/core_p13_family_lifecycle.json"))
    parser.add_argument("--steps", type=int, default=75)
    args = parser.parse_args()
    result = run_p13_benchmark(args.store, steps=args.steps)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["observed"], indent=2, sort_keys=True))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
