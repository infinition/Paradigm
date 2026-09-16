from __future__ import annotations

import argparse
from pathlib import Path

from paradigm.llm_controller import OpenAICompatibleCodingDeliberator
from paradigm.p23r import ARRIVALS, run_p23r_matrix


def parse_model_spec(spec: str) -> tuple[str, OpenAICompatibleCodingDeliberator]:
    """Format: model|api_style|base_url, for example qwen3:8b|ollama|http://127.0.0.1:11434"""
    parts = spec.split("|")
    if len(parts) != 3:
        raise SystemExit(f"bad --model spec: {spec!r} (expected model|api_style|base_url)")
    model, api_style, base_url = parts
    return model, OpenAICompatibleCodingDeliberator(base_url=base_url, model=model, api_style=api_style, timeout_s=180)


def main() -> int:
    parser = argparse.ArgumentParser(description="Paradigm P2.3R replication across seeds, models, and arrival orders")
    parser.add_argument("--model", action="append", required=True, help="model|api_style|base_url (repeatable)")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--arrivals", nargs="+", default=list(ARRIVALS), choices=ARRIVALS)
    parser.add_argument("--output", default="results/core_p23r")
    args = parser.parse_args()

    controllers = dict(parse_model_spec(spec) for spec in args.model)
    summary = run_p23r_matrix(
        controllers=controllers, seeds=args.seeds, arrivals=args.arrivals, root=Path(args.output), log=lambda m: print(m, flush=True)
    )
    print(f"runs={summary['runs']} cells={len(summary['cells'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
