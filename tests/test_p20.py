from paradigm.agent_scenarios import make_task
from paradigm.agent_vertical import AgentFeatureEncoder, ParadigmCodingAgent, ReferenceCodingDeliberator
from paradigm.p20 import run_p20_benchmark


def test_reference_agent_repairs_supported_task():
    agent = ParadigmCodingAgent(ReferenceCodingDeliberator(analysis_rounds=1), encoder=AgentFeatureEncoder())
    episode = agent.run(make_task("missing_import", 1))
    assert episode.success
    assert episode.deliberative_calls > 0


def test_p20_quick_preserves_success_and_uses_fast_path():
    result = run_p20_benchmark(quick=True)
    assert result["success_preserved"]
    assert result["ood_success_preserved"]
    assert result["known_only"]["fast_path_coverage"] > 0.35
    assert result["deliberative_calls_avoided"] > 0
    assert result["hybrid"]["invalid_reflex_actions"] == 0
