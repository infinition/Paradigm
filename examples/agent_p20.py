from paradigm.agent_scenarios import make_split
from paradigm.agent_vertical import ParadigmCodingAgent, ReferenceCodingDeliberator, compile_agent_reflex


deliberator = ReferenceCodingDeliberator(analysis_rounds=500)
train = make_split(0, 4)
validation = make_split(100, 2)
selection, gate, encoder, _ = compile_agent_reflex(train, validation, deliberator, random_state=20)

agent = ParadigmCodingAgent(deliberator, encoder=encoder, selection=selection, ood_gate=gate)
for task in make_split(200, 1, include_ood=True):
    episode = agent.run(task)
    print(task.family, episode.success, episode.reflex_calls, episode.deliberative_calls)
