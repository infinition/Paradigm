from __future__ import annotations

import numpy as np
from sklearn.model_selection import train_test_split

from paradigm import ParadigmRuntime, ReflexCompiler, TrustedSubspaceGate, evaluate_reflex
from paradigm.synthetic import make_traces, teacher


traces = make_traces(4000, seed=7)
train, test = train_test_split(traces, test_size=0.25, random_state=7, stratify=[t.action for t in traces])

reflex = ReflexCompiler(random_state=7).fit(train, name="synthetic-v1")
x_test = np.stack([t.features for t in test])
y_test = np.asarray([t.action for t in test])
report = evaluate_reflex(reflex, x_test, y_test, accept_threshold=0.90)

x_train = np.stack([t.features for t in train])
gate = TrustedSubspaceGate(variance=0.95, quantile=0.995).fit(x_train)
runtime = ParadigmRuntime(reflex, teacher, confidence_threshold=0.90, ood_gate=gate)

print(report)
print(runtime.decide(x_test[0]))
