from __future__ import annotations

import argparse
from pathlib import Path

from paradigm.llm_controller import OpenAICompatibleCodingDeliberator
from paradigm.p23t import collect_trace_episodes, load_episodes, run_threshold_sweep, save_episodes, write_p23t_results


def main() -> int:
    parser = argparse.ArgumentParser(description="Paradigm P2.3T learning-threshold sweep with fixed certification")
    parser.add_argument("--model", action="append", required=True, help="model|api_style|base_url (repeatable)")
    parser.add_argument("--orderings", type=int, default=5)
    parser.add_argument("--output", default="results/core_p23t")
    args = parser.parse_args()
    root = Path(args.output)
    results = {}
    for spec in args.model:
        model, api_style, base_url = spec.split("|")
        trace_path = root / "traces" / f"{model.replace(':', '_')}__{api_style}.json"
        if trace_path.exists():
            episodes = load_episodes(trace_path)
            print(f"loaded {len(episodes)} trace episodes for {model}", flush=True)
        else:
            controller = OpenAICompatibleCodingDeliberator(base_url=base_url, model=model, api_style=api_style, timeout_s=180)
            episodes = collect_trace_episodes(controller)
            save_episodes(trace_path, episodes)
            print(f"collected {len(episodes)} trace episodes for {model} ({controller.usage.calls} LLM calls)", flush=True)
        results[model] = run_threshold_sweep(episodes, orderings=args.orderings)
        for c in results[model]["curve"]:
            print(model, c["novel_train_episodes"], f"cap {c['capability_accuracy_mean']:.2f} gate {c['gate_acceptance_mean']:.2f} promote {c['recent_promote_rate']:.0%}", flush=True)
    write_p23t_results(root, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
