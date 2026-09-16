from __future__ import annotations

import argparse
from pathlib import Path

from paradigm.llm_controller import OpenAICompatibleCodingDeliberator
from paradigm.p22 import live_environment_available, run_p22_live_benchmark, write_p22_results, write_unexecuted_p22_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Paradigm P2.2 real LLM control-policy benchmark")
    parser.add_argument("--quick", action="store_true", help="Use the smallest live benchmark")
    parser.add_argument("--output", default="results/core_p22", help="Output directory")
    args = parser.parse_args()
    root = Path(args.output)

    available, reason = live_environment_available()
    if not available:
        write_unexecuted_p22_report(root, reason)
        print(f"P2.2 not executed live: {reason}")
        return 2

    controller = OpenAICompatibleCodingDeliberator.from_env()
    result = run_p22_live_benchmark(controller, quick=args.quick)
    write_p22_results(root, result)
    evaluation = result["evaluation"]
    print(f"success baseline={evaluation['baseline']['success_rate']:.1%} hybrid={evaluation['hybrid']['success_rate']:.1%}")
    print(f"LLM call reduction={evaluation['llm_call_reduction']:.1%}")
    print(f"token reduction={evaluation['token_reduction']:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
