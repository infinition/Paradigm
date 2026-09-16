from __future__ import annotations

import argparse
import json
from pathlib import Path

from paradigm.llm_controller import OpenAICompatibleCodingDeliberator
from paradigm.p24 import (
    classify_offline,
    classify_offline_original_rule,
    collect_type_b_episodes,
    known_family_reference_accuracy,
    run_type_b_online,
    run_type_b_sweep,
    write_p24_results,
)
from paradigm.p23t import load_episodes, save_episodes


def main() -> int:
    parser = argparse.ArgumentParser(description="Paradigm P2.4 Type B skill acquisition")
    parser.add_argument("--model", action="append", required=True, help="model|api_style|base_url (repeatable)")
    parser.add_argument("--orderings", type=int, default=5)
    parser.add_argument("--online", action="store_true", help="run the online loop when the offline sweep shows acquisition")
    parser.add_argument("--output", default="results/core_p24")
    args = parser.parse_args()
    root = Path(args.output)
    payload_path = root / "core_p24_type_b.json"
    payload = json.loads(payload_path.read_text()) if payload_path.exists() else {"phase": "P2.4", "models": {}}

    for spec in args.model:
        model, api_style, base_url = spec.split("|")
        controller = OpenAICompatibleCodingDeliberator(base_url=base_url, model=model, api_style=api_style, timeout_s=180)
        key = model.replace(":", "_")
        trace_path = root / "traces" / f"{key}__{api_style}.json"
        stats_path = root / "traces" / f"{key}__{api_style}__teacher.json"
        if trace_path.exists() and stats_path.exists():
            episodes = load_episodes(trace_path)
            teacher = json.loads(stats_path.read_text())
            print(f"loaded {len(episodes)} trace episodes for {model}", flush=True)
        else:
            episodes, teacher = collect_type_b_episodes(controller)
            save_episodes(trace_path, episodes)
            stats_path.parent.mkdir(parents=True, exist_ok=True)
            stats_path.write_text(json.dumps(teacher, indent=2, default=float), encoding="utf-8")
            print(f"collected {len(episodes)} trace episodes for {model}: novel success {teacher['novel_success_rate']:.0%}", flush=True)
        block = payload["models"].get(model, {})
        block["teacher"] = teacher
        block["mature_reference_accuracy"] = known_family_reference_accuracy(episodes)
        sweep = run_type_b_sweep(episodes, orderings=args.orderings)
        block["sweep"] = sweep
        block["offline_class"] = classify_offline(sweep, block["mature_reference_accuracy"])
        block["offline_class_original_rule"] = classify_offline_original_rule(sweep, block["mature_reference_accuracy"])
        for c in sweep["curve"]:
            print(f"{model} k={c['novel_train_episodes']}: acc {c['decision_accuracy_mean']:.2f} replay {c['replay_success_mean']:.2f} gate {c['gate_acceptance_mean']:.2f} promote recent {c['recent_promote_rate']:.0%} fam {c['family_aware_promote_rate']:.0%}", flush=True)
        print(f"{model} TTC {sweep['time_to_capability']} class {block['offline_class']}", flush=True)
        block["final_class"] = block["offline_class"]
        if args.online and block["offline_class"] == "CAPABILITY_AND_CERTIFICATION_SUCCEEDED":
            block.setdefault("online", {})
            for mode in ("family_aware", "recent"):
                if mode in block["online"]:
                    print(f"{model} online {mode}: already recorded", flush=True)
                    continue
                result = run_type_b_online(controller, certification=mode)
                block["online"][mode] = result
                payload["models"][model] = block
                write_p24_results(root, payload)
                sig = result["signature_metrics"]
                print(f"{model} online {mode}: success {result['online']['success_rate']:.0%} calls -{result['llm_usage']['llm_call_reduction']:.0%} TTR {sig['time_to_reflex']['validated_episodes']} outcome {sig['time_to_reflex'].get('outcome')} novel success {result['novel_family']['overall']['success_rate']:.0%}", flush=True)
            fam = block["online"]["family_aware"]
            ttr = fam["signature_metrics"]["time_to_reflex"]
            if ttr.get("outcome") != "promoted":
                block["final_class"] = "INSUFFICIENT_EVIDENCE" if ttr.get("outcome") == "insufficient_evidence" else "CAPABILITY_ACQUIRED_NOT_CERTIFIED"
            elif fam["old_family_retention"]["known_after_representation"].get("success_rate", 1.0) < 1.0:
                block["final_class"] = "RETENTION_FAILURE"
        payload["models"][model] = block
        write_p24_results(root, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
