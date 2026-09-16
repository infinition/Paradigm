import json

from paradigm.llm_controller import OpenAICompatibleCodingDeliberator
from paradigm.p24 import (
    classify_offline,
    collect_type_b_episodes,
    known_family_reference_accuracy,
    make_type_b_stream,
    run_type_b_online,
    run_type_b_sweep,
)


def reference_transport(url, payload, headers, timeout):
    state = json.loads(payload["messages"][1]["content"])
    allowed = state["allowed_actions"]
    phase, failure = state["phase"], state["failure_kind"]
    if state["tests_passed"]:
        action = "finish"
    elif phase == "start" or state["patched"]:
        action = "run_tests"
    elif phase == "failed":
        if failure == "missing_module":
            action = "inspect_dependency"
        elif failure == "import_error" and not state["searched"]:
            action = "search_symbol"
        else:
            action = "inspect_file"
    elif phase == "searched":
        action = "inspect_file"
    elif phase == "inspected":
        action = "apply_fix"
    elif phase == "dep_inspected":
        action = "search_registry"
    elif phase == "registry_searched":
        action = "modify_dependency_file"
    elif phase == "dep_modified":
        action = "install_dependency"
    else:
        action = allowed[0]
    assert action in allowed, (action, allowed, phase, failure)
    return {
        "choices": [{"message": {"content": json.dumps({"action": action, "reason": "test"})}}],
        "usage": {"prompt_tokens": 80, "completion_tokens": 8, "total_tokens": 88},
    }


def make_controller():
    return OpenAICompatibleCodingDeliberator(
        base_url="http://fixture/v1", model="fixture-controller", transport=reference_transport
    )


def test_type_b_family_is_not_solved_at_k0_and_is_learned_with_evidence():
    episodes, teacher = collect_type_b_episodes(make_controller())
    assert teacher["novel_success_rate"] == 1.0 and teacher["novel_contract_rate"] == 1.0
    sweep = run_type_b_sweep(episodes, orderings=2, ks=(0, 1, 2, 4, 6))
    k0 = sweep["k0_control"]
    assert k0["replay_success_mean"] == 0.0
    assert k0["decision_accuracy_mean"] < 0.9
    last = sweep["curve"][-1]
    assert last["decision_accuracy_mean"] > k0["decision_accuracy_mean"]
    reference = known_family_reference_accuracy(episodes)
    assert classify_offline(sweep, reference) != "TYPE_B_NOT_ESTABLISHED"


def test_type_b_stream_shape():
    tasks, phases = make_type_b_stream(0)
    assert len(tasks) == 69 and sum(1 for t in tasks if t.family == "dependency_error") == 17
    assert all(t.family != "dependency_error" for t in tasks[:12])
