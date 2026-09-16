from __future__ import annotations

import argparse
from pathlib import Path

from paradigm.llm_controller import OpenAICompatibleCodingDeliberator
from paradigm.p23bis import aggregate_p23bis, run_p23bis_pair
from paradigm.p23r import ARRIVALS


def main() -> int:
    parser = argparse.ArgumentParser(description="Paradigm P2.3R-bis family-aware certification with retention probes")
    parser.add_argument("--model", required=True, help="model|api_style|base_url")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0])
    parser.add_argument("--arrivals", nargs="+", default=list(ARRIVALS), choices=ARRIVALS)
    parser.add_argument("--output", default="results/core_p23r_bis")
    parser.add_argument("--min-family-validation-episodes", type=int, default=1)
    args = parser.parse_args()
    model, api_style, base_url = args.model.split("|")
    controller = OpenAICompatibleCodingDeliberator(base_url=base_url, model=model, api_style=api_style, timeout_s=180)
    root = Path(args.output)
    for arrival in args.arrivals:
        for seed in args.seeds:
            run_p23bis_pair(
                controller,
                arrival=arrival,
                seed=seed,
                root=root,
                log=lambda m: print(m, flush=True),
                compiler_options={"min_family_validation_episodes": args.min_family_validation_episodes},
            )
    summary = aggregate_p23bis(root)
    print(f"pairs={len(summary['pairs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
