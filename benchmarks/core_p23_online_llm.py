from __future__ import annotations

import argparse
from pathlib import Path

from paradigm.llm_controller import OpenAICompatibleCodingDeliberator
from paradigm.p22 import live_environment_available
from paradigm.p23 import run_p23_live_online_benchmark, write_p23_results, write_unexecuted_p23_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Paradigm P2.3 real LLM online acquisition benchmark")
    parser.add_argument("--quick", action="store_true", help="Use the smallest live stream")
    parser.add_argument("--output", default="results/core_p23", help="Output directory")
    args = parser.parse_args()
    root = Path(args.output)

    available, reason = live_environment_available()
    if not available:
        write_unexecuted_p23_report(root, reason)
        print(f"P2.3 not executed live: {reason}")
        return 2

    controller = OpenAICompatibleCodingDeliberator.from_env()
    result = run_p23_live_online_benchmark(controller, quick=args.quick)
    write_p23_results(root, result)
    usage = result["llm_usage"]
    novel = result["novel_family"]
    print(f"success baseline={result['baseline']['success_rate']:.1%} online={result['online']['success_rate']:.1%}")
    print(f"LLM call reduction={usage['llm_call_reduction']:.1%} token reduction={usage['token_reduction']:.1%}")
    print(
        f"novel family fast path: phase B={novel['phase_b'].get('fast_path_coverage', 0.0):.1%} "
        f"phase C={novel['phase_c'].get('fast_path_coverage', 0.0):.1%} "
        f"false fast path={novel['unknown_false_fast_path_rate']:.1%}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
