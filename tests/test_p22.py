import json

from paradigm.agent_scenarios import make_task
from paradigm.agent_vertical import AgentState
from paradigm.llm_controller import OpenAICompatibleCodingDeliberator
from paradigm.p22 import run_p22_live_benchmark


def reference_transport(url, payload, headers, timeout):
    state = json.loads(payload["messages"][1]["content"])
    allowed = state["allowed_actions"]
    phase = state["phase"]
    failure = state["failure_kind"]
    if state["tests_passed"]:
        action = "finish"
    elif phase == "start" or state["patched"]:
        action = "run_tests"
    elif phase == "failed":
        action = "search_symbol" if failure == "import_error" and not state["searched"] else "inspect_file"
    elif phase == "searched":
        action = "inspect_file"
    elif phase == "inspected":
        action = "apply_fix"
    else:
        action = allowed[0]
    assert action in allowed
    return {
        "choices": [{"message": {"content": json.dumps({"action": action, "reason": "test"})}}],
        "usage": {"prompt_tokens": 80, "completion_tokens": 8, "total_tokens": 88},
    }


def make_controller():
    return OpenAICompatibleCodingDeliberator(
        base_url="http://fixture/v1",
        model="fixture-controller",
        transport=reference_transport,
        input_cost_per_million=1.0,
        output_cost_per_million=2.0,
    )


def test_openai_compatible_controller_accounts_usage_and_returns_valid_action():
    controller = make_controller()
    state = AgentState(make_task("wrong_constant", 1))
    action = controller.decide(state)
    assert action == "run_tests"
    assert controller.usage.calls == 1
    assert controller.usage.total_tokens == 88
    assert controller.usage.estimated_cost_usd > 0


def test_p22_fixture_reduces_llm_calls_without_losing_success():
    result = run_p22_live_benchmark(make_controller(), quick=True)
    evaluation = result["evaluation"]
    assert result["executed_live_llm"]
    assert evaluation["baseline"]["success_rate"] >= 0.99
    assert evaluation["hybrid"]["success_rate"] >= 0.99
    assert evaluation["llm_call_reduction"] > 0
    assert evaluation["token_reduction"] > 0


def test_invalid_llm_action_is_counted_and_repaired_safely():
    def bad_transport(url, payload, headers, timeout):
        return {
            "choices": [{"message": {"content": '{"action":"apply_fix"}'}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 4, "total_tokens": 24},
        }

    controller = OpenAICompatibleCodingDeliberator(
        base_url="http://fixture/v1", model="bad-fixture", transport=bad_transport
    )
    state = AgentState(make_task("wrong_constant", 2))
    action = controller.decide(state)
    assert action == "run_tests"
    assert controller.usage.invalid_actions == 1
    assert controller.usage.repaired_actions == 1
