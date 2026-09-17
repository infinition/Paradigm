import json
import threading
import urllib.request

import pytest

from paradigm.integration import (
    DeliberateDecision,
    Paradigm,
    ParadigmState,
    ReflexDecision,
    ReflexPolicy,
    VerifiedOutcome,
)
from paradigm.integration.laruche import LaRucheAdapter, LaRucheBridge
from paradigm.integration.service import ParadigmService, serve

ACTIONS = ("run_tests", "inspect_file", "apply_fix", "finish")
TEACHER = {"start": "run_tests", "failed": "inspect_file", "inspected": "apply_fix", "patched": "run_tests", "passed": "finish"}
TRANSITION = {
    ("start", "run_tests"): "failed",
    ("failed", "inspect_file"): "inspected",
    ("inspected", "apply_fix"): "patched",
    ("patched", "run_tests"): "passed",
    ("passed", "finish"): "done",
}


def make_state(phase, last, step, hist, goal="fix bug", family="demo_repair"):
    return ParadigmState(
        domain="demo",
        phase=phase,
        available_actions=ACTIONS,
        goal=goal,
        last_action=last,
        last_outcome="failure" if phase == "failed" else ("success" if last else "none"),
        recent_actions=tuple(hist[-3:]),
        step=step,
        family_hint=family,
    )


def run_episode(engine, *, goal="fix bug", episode_outcome=VerifiedOutcome.success("tests"), step_outcome=None):
    phase, last, step, hist, sources = "start", None, 0, [], []
    while phase != "done" and step < 8:
        state = make_state(phase, last, step, hist, goal=goal)
        decision = engine.decide(state)
        if isinstance(decision, ReflexDecision):
            action, source, meta = decision.action, "reflex", {}
        else:
            action, source, meta = TEACHER[phase], "deliberative", {"llm_tokens": 200, "llm_latency_ms": 700.0}
        sources.append(source)
        engine.observe(state, action, step_outcome or VerifiedOutcome.success("simulator"), source=source, metadata=meta)
        phase = TRANSITION[(phase, action)]
        last, step = action, step + 1
        hist.append(action)
    return engine.close_episode(episode_outcome), sources


def trained_engine(episodes=12):
    engine = Paradigm(policy=ReflexPolicy(allowed_actions=ACTIONS))
    for i in range(episodes):
        run_episode(engine, goal=f"fix bug {i % 3}")
    assert engine.compiler.state.version >= 1
    return engine


def test_trusted_reflex_after_verified_episodes():
    engine = trained_engine()
    _, sources = run_episode(engine)
    assert set(sources) == {"reflex"}
    state = make_state("failed", "run_tests", 1, ["run_tests"])
    decision = engine.decide(state)
    assert isinstance(decision, ReflexDecision)
    assert decision.action == "inspect_file" and decision.reflex_id == "v1"
    assert engine.trust_manifest() == {"demo_repair": "active"}


def test_deliberate_is_first_class_when_no_reflex():
    engine = Paradigm(policy=ReflexPolicy(allowed_actions=ACTIONS))
    decision = engine.decide(make_state("start", None, 0, []))
    assert isinstance(decision, DeliberateDecision)
    assert decision.reason == "no_active_reflex" and decision.trust_status == "no_reflex"


def test_capable_but_untrusted_state_deliberates_and_exposes_proposal():
    engine = trained_engine()
    state = make_state("failed", "run_tests", 1, ["run_tests"], goal="something else", family="other_family")
    info = engine.explain(state)
    decision = engine.decide(state)
    assert isinstance(decision, DeliberateDecision)
    assert decision.proposed_action == "inspect_file"
    assert decision.reflex_confidence is not None and decision.reflex_confidence > 0.5
    assert decision.reason in {"out_of_distribution", "family_not_trusted"}
    assert info["authorized"] is False


def test_reflex_policy_blocks_actions_outside_whitelist():
    engine = trained_engine()
    engine.policy = ReflexPolicy(allowed_actions=("run_tests", "finish"))
    state = make_state("failed", "run_tests", 1, ["run_tests"])
    decision = engine.decide(state)
    assert isinstance(decision, DeliberateDecision) and decision.reason == "action_not_in_reflex_policy"
    assert decision.proposed_action == "inspect_file"


def test_failed_and_unknown_episodes_are_not_ingested():
    engine = Paradigm(policy=ReflexPolicy(allowed_actions=ACTIONS))
    for _ in range(4):
        rec, _ = run_episode(engine, episode_outcome=VerifiedOutcome.failure("tests"))
        assert rec["ingested"] is False
    for _ in range(4):
        rec, _ = run_episode(engine, episode_outcome=VerifiedOutcome.unknown("timeout"))
        assert rec["ingested"] is False
    assert engine.compiler.buffer.trusted_trace_count == 0
    t = engine.telemetry()
    assert t["counters"]["episodes_rejected_failure"] == 4 and t["counters"]["episodes_rejected_unknown"] == 4


def test_unverified_steps_inside_successful_episode_are_not_teacher_labels():
    engine = Paradigm(policy=ReflexPolicy(allowed_actions=ACTIONS))
    run_episode(engine, step_outcome=VerifiedOutcome.unknown("no verifier"))
    assert engine.compiler.buffer.trusted_trace_count == 0
    assert engine.compiler.buffer.rejected_unvalidated_steps > 0


def test_reflex_steps_are_never_teacher_labels():
    engine = trained_engine()
    before = engine.compiler.buffer.trusted_trace_count
    ignored_before = engine.compiler.buffer.ignored_self_labels
    run_episode(engine)
    assert engine.compiler.buffer.trusted_trace_count == before
    assert engine.compiler.buffer.ignored_self_labels > ignored_before


def test_telemetry_fields_for_ui():
    engine = trained_engine()
    run_episode(engine)
    t = engine.telemetry()
    for key in ("reflex_decisions", "deliberative_decisions", "llm_calls_avoided", "llm_tokens_avoided_estimate", "active_families", "candidate_families", "deliberative_only_families", "trust_manifest"):
        assert key in t
    row = engine.decision_log(last=1)[0]
    for key in ("source", "family", "reflex_id", "confidence", "trust_status", "reason", "decision_latency_ms", "outcome"):
        assert key in row


def test_persistence_roundtrip(tmp_path):
    engine = trained_engine()
    engine.save(tmp_path / "state.pkl")
    loaded = Paradigm.load(tmp_path / "state.pkl", policy=ReflexPolicy(allowed_actions=ACTIONS))
    assert isinstance(loaded.decide(make_state("failed", "run_tests", 1, ["run_tests"])), ReflexDecision)


# --------------------------------------------------------------- LaRuche bridge

def laruche_episode(bridge, session, *, teacher, fin="Accomplie"):
    messages = [{"role": "Utilisateur", "contenu": "Run the test suite and report"}]
    schemas = [{"name": n} for n in ("file_read", "shell_exec", "file_write", "task_complete")]
    sources = []
    for _ in range(4):
        out = bridge.decide(session, messages, schemas)
        if "appel" in out:
            appel, source, usage = out["appel"], "reflex", None
        else:
            appel, source, usage = teacher(messages), "deliberative", {"entree": 150, "sortie": 20, "latency_ms": 600}
        sources.append(source)
        ok = appel["nom"] != "task_complete" or True
        result = {"ok": ok, "sortie": "3 passed" if appel["nom"] == "shell_exec" else "done", "images": [], "incertain": False}
        bridge.observe(session, appel, result, source=source, usage=usage)
        messages.append({"role": "Observation", "contenu": result["sortie"], "outil": appel["nom"]})
        if appel["nom"] == "task_complete":
            break
    return bridge.close(session, fin), sources


def fixture_teacher(messages):
    observations = [m for m in messages if m.get("role") == "Observation"]
    if not observations:
        return {"id": "a1", "nom": "shell_exec", "args": {"command": "pytest -q"}}
    if observations[-1]["outil"] == "shell_exec":
        return {"id": "a2", "nom": "file_read", "args": {"path": "README.md"}}
    return {"id": "a3", "nom": "task_complete", "args": {}}


def test_laruche_bridge_learns_and_routes_whitelisted_calls():
    adapter = LaRucheAdapter()
    engine = Paradigm(policy=adapter.policy())
    bridge = LaRucheBridge(engine, adapter)
    for i in range(20):
        laruche_episode(bridge, f"s{i}", teacher=fixture_teacher)
    assert engine.compiler.state.version >= 1
    _, sources = laruche_episode(bridge, "final", teacher=fixture_teacher)
    assert "reflex" in sources
    schemas = [{"name": n} for n in ("file_read", "shell_exec", "file_write", "task_complete")]
    out = bridge.decide("probe", [{"role": "Utilisateur", "contenu": "Run the test suite and report"}], schemas)
    assert out["decision"]["source"] == "reflex"
    assert out["appel"] == {"nom": "shell_exec", "args": {"command": "pytest -q"}}
    # A different tool set is a different state: the gate must not extend trust to it.
    other = bridge.decide("probe2", [{"role": "Utilisateur", "contenu": "Run the test suite and report"}], schemas[:2])
    assert other["decision"]["source"] == "deliberative" and other["decision"]["reason"] == "out_of_distribution"


def test_laruche_bridge_keeps_non_whitelisted_and_unsafe_shell_deliberative():
    adapter = LaRucheAdapter()
    assert adapter.reflex_capable("file_write", {"path": "x"}) is False
    assert adapter.reflex_capable("shell_exec", {"command": "rm -rf build"}) is False
    assert adapter.reflex_capable("shell_exec", {"command": "pytest -q"}) is True
    engine = Paradigm(policy=adapter.policy())
    bridge = LaRucheBridge(engine, adapter)
    rec = bridge.observe("s", {"id": "x", "nom": "file_write", "args": {"path": "a", "content": "b"}}, {"ok": True, "sortie": "written", "images": [], "incertain": False})
    assert rec["reflex_capable"] is False and rec["outcome"] == "unknown"


def test_laruche_outcome_mapping():
    adapter = LaRucheAdapter()
    assert adapter.outcome_from_result({"ok": True}).outcome.value == "success"
    assert adapter.outcome_from_result({"ok": False}).outcome.value == "failure"
    assert adapter.outcome_from_result({"ok": False, "incertain": True}).outcome.value == "unknown"
    assert adapter.outcome_from_fin("Accomplie").outcome.value == "success"
    assert adapter.outcome_from_fin("Erreur").outcome.value == "failure"
    assert adapter.outcome_from_fin("Interrompue").outcome.value == "unknown"


# ------------------------------------------------------------------- service

def _post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _get(url):
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())


@pytest.fixture
def service_url(tmp_path):
    adapter = LaRucheAdapter()
    engine = Paradigm(policy=adapter.policy())
    adapter.templates = engine.action_templates
    service = ParadigmService(engine, state_file=tmp_path / "state.pkl", adapter=adapter)
    server = serve(service, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def test_service_generic_and_laruche_routes(service_url, tmp_path):
    assert _get(f"{service_url}/v1/health")["ok"] is True
    state = make_state("start", None, 0, []).to_dict()
    d = _post(f"{service_url}/v1/decide", {"state": state})
    assert d["decision"]["source"] == "deliberative"
    rec = _post(f"{service_url}/v1/observe", {"state": state, "action": "run_tests", "outcome": "success", "source": "deliberative"})
    assert rec["outcome"] == "success"
    closed = _post(f"{service_url}/v1/episode/close", {"outcome": {"outcome": "success", "verifier": "tests"}})
    assert closed["ingested"] is True
    assert (tmp_path / "state.pkl").exists()
    out = _post(f"{service_url}/v1/laruche/decide", {"session": "a", "messages": [{"role": "Utilisateur", "contenu": "hi"}], "schemas": [{"name": "shell_exec"}]})
    assert out["decision"]["source"] == "deliberative"
    obs = _post(f"{service_url}/v1/laruche/observe", {"session": "a", "appel": {"id": "1", "nom": "shell_exec", "args": {"command": "pytest -q"}}, "result": {"ok": True, "sortie": "ok", "images": [], "incertain": False}, "usage": {"entree": 10, "sortie": 2}})
    assert obs["reflex_capable"] is True
    closed = _post(f"{service_url}/v1/laruche/close", {"session": "a", "fin": "Accomplie"})
    assert closed["outcome"] == "success"
    t = _get(f"{service_url}/v1/telemetry")
    assert t["deliberative_decisions"] == 2
    assert _get(f"{service_url}/v1/log?last=5")["decisions"]


# ------------------------------------------------------- family-scoped activation

def _mixed_episode(engine, i, *, flaky_reads):
    """A consistent 'start' decision followed by an inconsistent read step, then a consistent finish."""
    hist = []
    for phase, options in (("start", ["run_tests"]), ("failed", ["inspect_file", "apply_fix"] if flaky_reads else ["inspect_file"]), ("inspected", ["finish"])):
        state = ParadigmState(domain="demo", phase=phase, available_actions=ACTIONS, goal="fix", last_action=hist[-1] if hist else None, last_outcome="failure" if phase == "failed" else "none", recent_actions=tuple(hist[-3:]), step=len(hist), family_hint=f"fam:{phase}")
        decision = engine.decide(state)
        if isinstance(decision, ReflexDecision):
            action, source = decision.action, "reflex"
        else:
            action, source = options[i % len(options)], "deliberative"
        engine.observe(state, action, VerifiedOutcome.success("sim"), source=source)
        hist.append(action)
    return engine.close_episode(VerifiedOutcome.success("tests"))


def test_family_scoped_activates_only_families_that_pass_on_their_own():
    from paradigm.online_learning import OnlineReflexCompiler

    compiler = OnlineReflexCompiler(min_episodes=8, compile_every=4, validation_fraction=0.25, minimum_ood_acceptance=0.65, certification="family_scoped")
    engine = Paradigm(policy=ReflexPolicy(allowed_actions=ACTIONS), compiler=compiler)
    for i in range(24):
        _mixed_episode(engine, i, flaky_reads=True)
    assert compiler.state.version >= 1
    active = set(compiler.state.family_thresholds)
    assert "fam:start" in active and "fam:inspected" in active
    assert "fam:failed" not in active
    last = compiler.state.promotions[-1].certification
    assert last["groups"]["fam:failed"]["status"] in {"rejected", "insufficient"}
    assert engine.trust_status("fam:failed").value == "candidate"
    start_state = ParadigmState(domain="demo", phase="start", available_actions=ACTIONS, goal="fix", family_hint="fam:start")
    assert isinstance(engine.decide(start_state), ReflexDecision)
    failed_state = ParadigmState(domain="demo", phase="failed", available_actions=ACTIONS, goal="fix", last_action="run_tests", last_outcome="failure", step=1, recent_actions=("run_tests",), family_hint="fam:failed")
    d = engine.decide(failed_state)
    assert isinstance(d, DeliberateDecision) and d.reason in {"family_not_trusted", "low_confidence", "out_of_distribution"}


def test_family_scoped_rejects_candidate_that_regresses_an_active_family():
    from paradigm.family_scoped import FamilyCriteria, certify_families
    from paradigm.online_learning import OnlineReflexCompiler
    from paradigm.schema import Trace

    compiler = OnlineReflexCompiler(min_episodes=8, compile_every=4, validation_fraction=0.25, minimum_ood_acceptance=0.65, certification="family_scoped")
    engine = Paradigm(policy=ReflexPolicy(allowed_actions=ACTIONS), compiler=compiler)
    for i in range(16):
        _mixed_episode(engine, i, flaky_reads=False)
    assert "fam:start" in compiler.state.family_thresholds
    train, validation = compiler.buffer.split(0.25)
    poisoned = [Trace(features=t.features, action="finish" if t.metadata["family"] == "fam:start" else t.action, valid=True, metadata=dict(t.metadata)) for t in train]
    selection, gate, _ = compiler.fit_candidate(poisoned, validation, backends=("tree",))
    verdicts = certify_families(selection.reflex, gate, poisoned, validation, probes={f: p.traces for f, p in compiler.state.probes.items()}, incumbent=(compiler.state.selection.reflex, compiler.state.ood_gate, dict(compiler.state.family_thresholds)), criteria=FamilyCriteria(minimum_ood_acceptance=0.65))
    assert verdicts["fam:start"].status == "rejected"


def _fam_trace(family, action, seed, task):
    import numpy as np
    from paradigm.schema import Trace

    rng = np.random.default_rng(seed)
    return Trace(features=rng.normal(size=6) + (3.0 if family == "a" else -3.0), action=action, valid=True, metadata={"family": family, "task_id": task})


def _certified_pair():
    """A tree and gate trained on two clean families, used as candidate and incumbent."""
    import numpy as np
    from paradigm.ood import MahalanobisGate
    from paradigm.reflex import CompiledReflex

    from sklearn.tree import DecisionTreeClassifier

    train = [_fam_trace("a", "x", s, f"t{s}") for s in range(20)] + [_fam_trace("b", "y", 100 + s, f"u{s}") for s in range(20)]
    x = np.stack([t.features for t in train])
    reflex = CompiledReflex(model=DecisionTreeClassifier(random_state=0).fit(x, np.asarray([t.action for t in train])), metadata={"backend": "tree"})
    gate = MahalanobisGate(quantile=0.997).fit(x)
    return reflex, gate, train


def test_sparse_fresh_evidence_falls_back_to_probes_and_keeps_the_disagreement_veto():
    from paradigm.family_scoped import FamilyCriteria, certify_families

    reflex, gate, train = _certified_pair()
    probes = {"a": [_fam_trace("a", "x", 500 + s, f"p{s}") for s in range(10)]}
    incumbent = (reflex, gate, {"a": 0.0})
    fresh_ok = [_fam_trace("a", "x", 900, "f1")]
    fresh_bad = [_fam_trace("a", "y", 900, "f1")]
    crit = FamilyCriteria(probe_recertification=True, min_fresh_support=2)

    v = certify_families(reflex, gate, train, fresh_ok, probes=probes, incumbent=incumbent, criteria=crit)["a"]
    assert v.status == "active" and v.reason == "probe_recertified"
    assert v.retention["evidence"] == "probes_only" and v.retention["fresh"]["n"] == 1 and v.retention["fresh"]["disagreements"] == 0

    v = certify_families(reflex, gate, train, fresh_bad, probes=probes, incumbent=incumbent, criteria=crit)["a"]
    assert v.status == "rejected" and "fresh_disagreement" in v.reason

    # With the control value, one fresh trace is judged on held-out evidence as before.
    v = certify_families(reflex, gate, train, fresh_ok, probes=probes, incumbent=incumbent, criteria=FamilyCriteria(probe_recertification=True, min_fresh_support=1))["a"]
    assert v.retention.get("evidence") != "probes_only"


def test_shadow_sampling_routes_eligible_decisions_to_the_teacher_deterministically():
    from paradigm.integration.shadow import ShadowSampler
    from paradigm.online_learning import OnlineReflexCompiler

    sampler = ShadowSampler.parse("17-40:1.0", seed=7)
    assert sampler.rate(16) == 0.0 and sampler.rate(17) == 1.0
    assert sampler.draw(3, "fam:start", 0) == sampler.draw(3, "fam:start", 0)
    assert sampler.draw(3, "fam:start", 0) != sampler.draw(4, "fam:start", 0)

    compiler = OnlineReflexCompiler(min_episodes=8, compile_every=4, validation_fraction=0.25, minimum_ood_acceptance=0.65, certification="family_scoped")
    engine = Paradigm(policy=ReflexPolicy(allowed_actions=ACTIONS), compiler=compiler, shadow_sampler=sampler)
    for i in range(24):
        _mixed_episode(engine, i, flaky_reads=False)
    assert compiler.state.version >= 1
    rows = engine.decision_log()
    sampled = [r for r in rows if r["reason"] == "shadow_sample"]
    assert sampled, "after activation, every eligible decision from episode 17 on is a shadow sample"
    assert all(r["source"] == "deliberative" for r in sampled)
    tel = engine.telemetry()
    assert tel["shadow_sample_model_calls"] == len(sampled)
    assert tel["net_calls_avoided_after_sampling"] == tel["reflex_decisions"] - len(sampled)
    assert tel["natural_model_calls"] + tel["shadow_sample_model_calls"] == tel["deliberative_decisions"]
    # Shadow-sampled steps are deliberative teacher evidence: the buffer keeps growing after activation.
    assert compiler.buffer.trusted_trace_count > 0


def test_triadic_veto_distinguishes_candidate_regression_from_alternative_trajectory():
    import numpy as np
    from sklearn.tree import DecisionTreeClassifier
    from paradigm.family_scoped import FamilyCriteria, certify_families
    from paradigm.reflex import CompiledReflex

    reflex, gate, train = _certified_pair()
    probes = {"a": [_fam_trace("a", "x", 500 + s, f"p{s}") for s in range(10)]}
    x = np.stack([t.features for t in train])
    # A damaged candidate that predicts "y" on family a (the incumbent predicts "x").
    damaged = CompiledReflex(model=DecisionTreeClassifier(random_state=0).fit(x, np.asarray(["y" for _ in train])), metadata={"backend": "tree"})
    incumbent = (reflex, gate, {"a": 0.0})
    crit = FamilyCriteria(probe_recertification=True, min_fresh_support=8, triadic_veto=True)

    # Teacher did x, incumbent says x, damaged candidate says y: candidate regression, veto.
    v = certify_families(damaged, gate, train, [_fam_trace("a", "x", 900, "f1")], probes=probes, incumbent=incumbent, criteria=crit)["a"]
    assert v.retention["fresh"]["candidate_regression"] == 1 and "candidate_regression" in v.reason

    # Teacher did z, incumbent and candidate both say x (a verified action of the family): alternative trajectory, no veto.
    v = certify_families(reflex, gate, train, [_fam_trace("a", "z", 900, "f1")], probes=probes, incumbent=incumbent, criteria=crit)["a"]
    assert v.retention["fresh"] == {**v.retention["fresh"], "alternative_trajectory": 1, "candidate_regression": 0}
    assert v.status == "active" and v.reason == "probe_recertified"

    # Same observation under the naive veto: rejected.
    v = certify_families(reflex, gate, train, [_fam_trace("a", "z", 900, "f1")], probes=probes, incumbent=incumbent, criteria=FamilyCriteria(probe_recertification=True, min_fresh_support=8))["a"]
    assert "fresh_disagreement" in v.reason


def test_equivalence_contract_scores_equivalent_actions_as_correct_and_keeps_literal_agreement():
    import numpy as np
    from sklearn.tree import DecisionTreeClassifier
    from paradigm.equivalence import EquivalenceContract, collapse_to_classes
    from paradigm.family_scoped import FamilyCriteria, certify_families
    from paradigm.ood import MahalanobisGate
    from paradigm.reflex import CompiledReflex

    contract = EquivalenceContract(version="t", class_of=lambda k: "TEST" if k in ("pytest", "pytest_cat") else k)
    y, p, c = collapse_to_classes(np.array(["pytest_cat", "read"]), np.array([[0.7, 0.15, 0.15], [0.1, 0.1, 0.8]]), np.array(["pytest", "pytest_cat", "read"]), contract)
    assert list(c) == ["TEST", "read"] and list(y) == ["TEST", "read"]
    assert np.allclose(p, [[0.85, 0.15], [0.2, 0.8]])
    m = contract.materialize({"pytest", "pytest_cat", "read"})
    assert m["mapping"] == {"pytest": "TEST", "pytest_cat": "TEST", "read": "read"} and len(m["digest"]) == 64

    # Family a always did "pytest" in training; held-out has one "pytest_cat" among 7.
    train = [_fam_trace("a", "pytest", s, f"t{s}") for s in range(20)] + [_fam_trace("b", "read", 100 + s, f"u{s}") for s in range(20)]
    x = np.stack([t.features for t in train])
    reflex = CompiledReflex(model=DecisionTreeClassifier(random_state=0).fit(x, np.asarray([t.action for t in train])), metadata={"backend": "tree"})
    gate = MahalanobisGate(quantile=0.997).fit(x)
    fresh = [_fam_trace("a", "pytest", 900 + s, f"f{s}") for s in range(6)] + [_fam_trace("a", "pytest_cat", 950, "f6")]

    literal = certify_families(reflex, gate, train, fresh, criteria=FamilyCriteria())["a"]
    scored = certify_families(reflex, gate, train, fresh, criteria=FamilyCriteria(equivalence=contract))["a"]
    assert literal.status == "rejected" and literal.retention["literal_agreement"] < 1.0
    assert scored.status == "active" and scored.selective_accuracy == 1.0 and scored.ece == 0.0
    assert scored.retention["literal_agreement"] == literal.retention["literal_agreement"] and scored.retention["equivalent_agreement"] == 1.0
