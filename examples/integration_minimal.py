"""Minimal integration: a toy agent loop with a fixture deliberator and Paradigm in front of it.

Run: PYTHONPATH=src python examples/integration_minimal.py

The deliberator is a fixed procedure standing in for a language model. Paradigm learns only
from episodes the application verifies as SUCCESS, then answers whitelisted decisions itself.
"""

from paradigm.integration import Paradigm, ParadigmState, ReflexDecision, ReflexPolicy, VerifiedOutcome

ACTIONS = ("run_tests", "inspect_file", "apply_fix", "finish")
PROCEDURE = {"start": "run_tests", "failed": "inspect_file", "inspected": "apply_fix", "patched": "run_tests", "passed": "finish"}
TRANSITION = {("start", "run_tests"): "failed", ("failed", "inspect_file"): "inspected", ("inspected", "apply_fix"): "patched", ("patched", "run_tests"): "passed", ("passed", "finish"): "done"}


def deliberate(state: ParadigmState) -> tuple[str, dict]:
    """Stand-in for the model: returns the action and its usage."""
    return PROCEDURE[state.phase], {"llm_tokens": 240, "llm_latency_ms": 780.0}


def run_episode(paradigm: Paradigm, goal: str) -> list[str]:
    phase, last, step, history, log = "start", None, 0, [], []
    while phase != "done":
        state = ParadigmState(domain="demo", phase=phase, available_actions=ACTIONS, goal=goal, last_action=last, last_outcome="failure" if phase == "failed" else ("success" if last else "none"), recent_actions=tuple(history[-3:]), step=step, family_hint="demo_repair")
        decision = paradigm.decide(state)
        if isinstance(decision, ReflexDecision):
            action, source, meta = decision.action, "reflex", {}
            log.append(f"{action:<14} PARADIGM   {decision.latency_ms:.2f} ms")
        else:
            action, meta = deliberate(state)
            source = "deliberative"
            log.append(f"{action:<14} MODEL      ({decision.reason})")
        paradigm.observe(state, action, VerifiedOutcome.success("simulator"), source=source, metadata=meta)
        phase = TRANSITION[(phase, action)]
        last, step = action, step + 1
        history.append(action)
    paradigm.close_episode(VerifiedOutcome.success("tests_passed"))
    return log


def main() -> None:
    paradigm = Paradigm(policy=ReflexPolicy(allowed_actions=ACTIONS))
    for i in range(10):
        log = run_episode(paradigm, goal=f"fix bug {i % 3}")
        print(f"episode {i + 1}")
        for line in log:
            print("  " + line)
    t = paradigm.telemetry()
    print()
    print(f"reflex decisions      {t['reflex_decisions']}")
    print(f"deliberative          {t['deliberative_decisions']}")
    print(f"LLM calls avoided     {t['llm_calls_avoided']}")
    print(f"tokens avoided (est.) {t['llm_tokens_avoided_estimate']}")
    print(f"trust manifest        {t['trust_manifest']}")
    unknown = ParadigmState(domain="demo", phase="failed", available_actions=ACTIONS, goal="rotate the logs", last_action="run_tests", last_outcome="failure", step=1, family_hint="log_rotation")
    print(f"unknown family        {paradigm.explain(unknown)}")


if __name__ == "__main__":
    main()
