from __future__ import annotations

import argparse

from paradigm.p24 import run_p24_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description="Paradigm P2.4 Type B skill acquisition")
    parser.add_argument("--model", action="append", required=True, help="model|api_style|base_url (repeatable)")
    parser.add_argument("--orderings", type=int, default=5)
    parser.add_argument("--online", action="store_true", help="run the online loop when the offline sweep shows acquisition")
    parser.add_argument("--output", default="results/core_p24")
    args = parser.parse_args()
    run_p24_benchmark(models=args.model, orderings=args.orderings, online=args.online, output=args.output, log=lambda m: print(m, flush=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
