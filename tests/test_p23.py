import json

from paradigm.llm_controller import OpenAICompatibleCodingDeliberator
from paradigm.p23 import run_p23_live_online_benchmark


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
        base_url="http://fixture/v1", model="fixture-controller", transport=reference_transport
    )


def test_p23_fixture_learns_novel_family_online():
    result = run_p23_live_online_benchmark(make_controller(), quick=True)
    novel = result["novel_family"]
    assert result["success_preserved"]
    assert result["online"]["success_rate"] >= 0.99
    assert result["llm_usage"]["llm_call_reduction"] > 0
    assert result["active_version"] >= 1
    assert novel["unknown_false_fast_path_rate"] == 0.0
    assert novel["phase_c"]["fast_path_coverage"] >= novel["phase_b"]["fast_path_coverage"]
    assert result["experience_buffer"]["failed_episode_added_traces"] == 0
    assert result["amortization"]["compile_llm_tokens"] == 0
    ttr = novel["time_to_reflex"]
    assert ttr["validated_episodes"] is None or ttr["validated_episodes"] >= 1
    rows = result["per_episode"]
    assert len(rows) == result["stream"]["episodes"]
    assert rows[-1]["cumulative_tokens_saved"] == (
        rows[-1]["cumulative_tokens_baseline"] - rows[-1]["cumulative_tokens_online"]
    )


def test_p23r_arrival_streams_have_expected_shape():
    from paradigm.p23r import ARRIVALS, make_arrival_stream

    for arrival in ARRIVALS:
        tasks, phases = make_arrival_stream(arrival, seed=1)
        assert len(tasks) == 69 == len(phases)
        novel = sum(1 for t in tasks if t.family == "syntax_error")
        assert {"burst": 17, "interleaved": 17, "periodic": 12, "rare": 7}[arrival] == novel
        assert all(t.family != "syntax_error" for t in tasks[:12])
    a, _ = make_arrival_stream("burst", seed=0)
    b, _ = make_arrival_stream("burst", seed=1)
    assert [t.task_id for t in a] != [t.task_id for t in b]


def test_p23r_matrix_runs_and_aggregates(tmp_path):
    from paradigm.p23r import run_p23r_matrix

    summary = run_p23r_matrix(
        controllers={"fixture": make_controller()}, seeds=[0], arrivals=["interleaved"], root=tmp_path, log=lambda m: None
    )
    assert summary["runs"] == 1
    cell = summary["cells"][0]
    assert cell["online_success"]["mean"] >= 0.99
    assert cell["unknown_false_fast_path_rate"]["mean"] == 0.0
    assert (tmp_path / "REPORT.md").exists()
    # resumable: second call skips the existing run
    again = run_p23r_matrix(
        controllers={"fixture": make_controller()}, seeds=[0], arrivals=["interleaved"], root=tmp_path, log=lambda m: None
    )
    assert again["runs"] == 1


def test_p23_promotion_audit_reconstructs_recorded_split_sizes():
    from paradigm.p23 import derive_promotion_audit

    result = run_p23_live_online_benchmark(make_controller(), quick=True)
    audit = derive_promotion_audit(result)
    assert audit, "quick fixture stream should produce at least one promotion attempt"
    assert all(a["reconstruction_matches_record"] for a in audit)
    promoted = [a for a in audit if a["promoted"]]
    assert promoted and all(a["novel_shadow_acceptance"] is not None or a["validation_traces"]["novel"] == 0 for a in promoted)


def test_p23bis_family_aware_certification_and_negative_control(tmp_path):
    from paradigm.p23bis import aggregate_p23bis, run_p23bis_pair

    out = run_p23bis_pair(make_controller(), arrival="interleaved", seed=0, root=tmp_path, log=lambda m: None)
    fam = out["family_aware"]
    assert fam["online"]["success_rate"] >= 0.99
    assert fam["novel_family"]["unknown_false_fast_path_rate"] == 0.0
    assert fam["retention_probes"], "promotion should freeze retention probes"
    outcomes = {p["outcome"] for p in fam["promotions"]}
    assert outcomes <= {"promoted", "rejected", "insufficient_evidence"}
    nc = fam["negative_control"]
    assert nc["feasible"]
    assert nc["poisoned_traces"] > 0
    assert nc["clean_candidate"]["family_aware"]["outcome"] in {"promoted", "insufficient_evidence"}
    assert nc["poisoned_candidate"]["family_aware"]["outcome"] == "rejected"
    summary = aggregate_p23bis(tmp_path)
    assert len(summary["pairs"]) == 1 and (tmp_path / "REPORT.md").exists()


def test_p23t_threshold_sweep_with_fixture_traces(tmp_path):
    from paradigm.p23t import collect_trace_episodes, load_episodes, run_threshold_sweep, save_episodes

    episodes = collect_trace_episodes(make_controller())
    save_episodes(tmp_path / "traces.json", episodes)
    episodes = load_episodes(tmp_path / "traces.json")
    result = run_threshold_sweep(episodes, orderings=2, max_k=6)
    ks = [c["novel_train_episodes"] for c in result["curve"]]
    assert ks == list(range(0, 7))
    assert result["curve"][0]["recent_promote_rate"] == 0.0
    assert result["curve"][-1]["capability_accuracy_mean"] >= 0.95
