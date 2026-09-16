import numpy as np

from paradigm import ParadigmRuntime, ReflexCompiler, TrustedSubspaceGate, evaluate_reflex
from paradigm.synthetic import make_traces, make_xy, teacher


def test_compile_and_evaluate():
    reflex = ReflexCompiler(n_estimators=80, random_state=1).fit(make_traces(1200, seed=1))
    x, y = make_xy(400, seed=2)
    report = evaluate_reflex(reflex, x, y, accept_threshold=0.80)
    assert report.accuracy > 0.90
    assert 0.0 <= report.ece <= 1.0
    assert 0.0 <= report.coverage <= 1.0


def test_runtime_fallback():
    traces = make_traces(1200, seed=3)
    reflex = ReflexCompiler(n_estimators=80, random_state=3).fit(traces)
    x = np.stack([t.features for t in traces])
    gate = TrustedSubspaceGate(variance=0.95, quantile=0.99).fit(x)
    runtime = ParadigmRuntime(reflex, teacher, confidence_threshold=0.9999, ood_gate=gate)
    out = runtime.decide(x[0])
    assert out.source == "deliberative"
