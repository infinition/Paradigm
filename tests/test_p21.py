from paradigm.p21 import run_p21_benchmark


def test_p21_quick_learns_online_without_losing_success():
    result = run_p21_benchmark(quick=True)
    assert result["success_preserved"]
    assert result["online"]["success_rate"] >= 0.99
    assert result["deliberative_calls_avoided"] > 0
    assert result["active_version"] >= 1
    assert result["experience_buffer"]["failed_episode_added_traces"] == 0


def test_p21_novel_family_starts_more_deliberative_than_it_ends():
    result = run_p21_benchmark(quick=True)
    first = result["novel_family"]["first_half"]["fast_path_coverage"]
    second = result["novel_family"]["second_half"]["fast_path_coverage"]
    assert second >= first
