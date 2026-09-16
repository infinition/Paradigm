import json
from pathlib import Path

from paradigm import cli
from paradigm.p24 import summarize_p24_payload

REPO = Path(__file__).resolve().parents[1]


def test_cli_from_cache_prints_recorded_p24_numbers(capsys):
    code = cli.main(["benchmark", "p24", "--from-cache", "--results", str(REPO / "results" / "core_p24")])
    out = capsys.readouterr().out
    assert code == 0
    assert "Paradigm P2.4 Type B" in out
    assert "reflex-only             8/8" in out
    assert "hybrid                  6/8" in out
    assert "LLM-only                6/8" in out
    assert "INSUFFICIENT_EVIDENCE" in out
    assert "CAPABILITY_AND_CERTIFICATION_SUCCEEDED" in out


def test_cli_from_cache_numbers_match_artifact():
    payload = json.loads((REPO / "results" / "core_p24" / "core_p24_type_b.json").read_text())
    text = summarize_p24_payload(payload)
    block = payload["models"]["qwen3:4b-instruct"]
    ps = block["online"]["recent"]["post_stream_exposure"]
    assert f"{ps['baseline_llm_calls']} -> {ps['llm_calls']}" in text
    assert f"TTC median              {block['sweep']['time_to_capability']['median']:.0f}" in text


def test_cli_live_without_model_fails_cleanly(capsys):
    code = cli.main(["benchmark", "p24"])
    err = capsys.readouterr().err
    assert code == 2
    assert "--from-cache" in err


def test_cli_from_cache_missing_artifact_fails_cleanly(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = cli.main(["benchmark", "p24", "--from-cache", "--results", str(tmp_path / "nowhere")])
    assert code == 2
    assert "No recorded P2.4 artifact" in capsys.readouterr().err
