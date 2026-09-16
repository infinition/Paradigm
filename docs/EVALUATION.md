# Evaluation

Paradigm is a selective decision system. Raw accuracy alone is insufficient.

## Core metrics

### Accuracy

Accuracy across all test examples.

### Coverage

Fraction of examples accepted by the reflex instead of deferred.

### Selective accuracy

Accuracy only on accepted reflex decisions.

This is a primary metric. A reflex that accepts 95% of cases at 90% accuracy and one that accepts 50% at 99.9% accuracy serve different purposes.

### Expected Calibration Error

Measures whether confidence tracks observed correctness.

### Brier score

Measures probability quality and strongly penalizes confident errors.

### OOD false accept rate

Fraction of designated out-of-distribution inputs that still pass the reflex gate.

### Weak-pool valid acceptance

Fraction of legitimate but underrepresented inputs accepted by the trust gate. This prevents an OOD mechanism from appearing strong only because it rejects unfamiliar valid behavior.

### Near-manifold invalid false accept rate

Fraction of deliberately invalid inputs that remain close to the trusted input manifold and still pass. This is a hard control for geometric trust mechanisms. A high value means the gate detects novelty, not semantic validity.

### Behavioral drift

At minimum:

- label disagreement between active and candidate
- mean total variation distance between predicted class distributions

Later phases should compare this external drift with the activation-level quantities studied in Drift Contract.

### Delayed regression

A promoted reflex is re-evaluated on later windows. Record absolute quality, regression versus the previous archived active version, the evidence window that triggered rollback, and the version identifier restored.

### Update-induced pre-activation drift

For bounded-plasticity experiments, measure `RMS(input @ delta_W.T)` per matrix update and compare it with the declared epsilon budget and the conditional spectral bound. This is an optimizer-level quantity and must not be presented as a behavioral safety guarantee.

### System cost

Report:

- reflex latency
- fallback latency
- mean end-to-end latency
- fraction of decisions requiring deliberation
- memory footprint
- training cost

## Promotion manifest

A candidate promotion should record explicit thresholds, for example:

```yaml
minimum_selective_accuracy: 0.99
minimum_coverage: 0.50
maximum_ece: 0.05
maximum_ood_false_accept_rate: 0.02
maximum_anchor_disagreement: 0.05
maximum_mean_total_variation: 0.08
```

These are example values, not project defaults. Thresholds are domain-specific and must be justified by the experiment.

## Continual adaptation metrics

P1.1 adds metrics that should be reported separately rather than collapsed into one score:

- current-task accuracy
- mean accuracy over all seen domains
- worst seen-domain accuracy
- mean forgetting relative to each domain's previous best
- measured per-step pre-activation drift
- adaptation wall-clock time for the local reference implementation

A method that reduces update drift but forgets previous behavior has not solved continual learning. A method that retains behavior through replay or retraining has paid an explicit memory or compute cost that should remain visible.

## Update-space evaluation

Trusted update spaces must report at least three acceptance rates:

- held-out validated updates from represented families
- poisoned or otherwise invalid updates
- legitimate updates from an unseen family

After pool expansion, all three must be re-measured. Improved novelty acceptance is not a success if invalid-update acceptance rises at the same time.


## Family-conditioned update evaluation

P1.2 adds family-aware measurements for neural candidate updates:

- held-out clean acceptance within the declared family
- targeted-poison acceptance within the same family
- cross-family acceptance for valid updates from another represented family
- joint parameter and behavior geometry acceptance
- semantic manifest acceptance after geometry
- false rejection rate for valid held-out candidates

A family gate is not useful if it rejects poison only by rejecting ordinary valid variation. Report clean coverage and invalid acceptance together. Unknown-family rejection must route to deliberation or family creation, not be interpreted as semantic failure.

Risk-conditioned epsilon experiments must report adaptation quality, protected behavior, subgroup quality, and measured step drift separately. Epsilon is a plasticity budget and must not be treated as a confidence score.


## Family lifecycle evaluation

P1.3 adds stateful family metrics:

- represented-family routing accuracy
- unknown-family forced-assignment rate
- ambiguous-family routing rate
- family-definition hash stability across expansion and quarantine
- manifest rejection reason by signal class
- quarantine persistence after reload
- active versus historical family counts

Unknown and ambiguous candidates should be counted as deferred, not as successful family matches. A new validated family must be added without mutating the thresholds of existing immutable families.


## Family evolution evaluation

P1.4 adds topology-level metrics that must be measured before activating a new family map:

- negative probe capture rate, counting represented and ambiguous probes as captured
- clean ambiguity rate
- exact clean-family routing rate
- delta of each metric relative to the current topology
- family-definition hash stability across operational state changes
- rejected proposal count and explicit rejection reasons

A family map should not be called safer because it rejects more inputs. Clean coverage, ambiguity, and negative capture must be reported together. Fixed probe suites are only a regression control and do not establish coverage of future semantic failures.

## Agent vertical evaluation

P2 adds controller-level metrics that must be reported together:

- end-to-end task success
- total policy decisions
- reflex policy decisions
- deliberative policy decisions
- fast-path coverage
- deliberative-call reduction relative to the same tasks under deliberation-only control
- policy latency separately from tool latency
- invalid reflex actions blocked before tool execution
- fallback reason distribution
- success and fast-path coverage split by represented versus OOD task families

A call reduction is not useful if task success falls. OOD deferral is not useful if the benchmark encodes family identity directly into the reflex features. P2.0 therefore excludes the explicit task-family label from the feature vector and withholds one failure type from compilation.

When a real LLM is connected, add input and output tokens, provider latency, monetary cost where applicable, and the fraction of saved LLM calls. Those metrics must not be inferred from the deterministic reference deliberator.

## P2.2 real LLM metrics

When a real language-model controller is attached, report compilation cost separately from evaluation savings.

Required evaluation metrics:

- task success
- LLM calls
- reflex calls
- fast-path coverage
- prompt tokens
- completion tokens
- total tokens
- accumulated LLM wall-clock latency
- optional estimated monetary cost
- invalid LLM actions
- deterministic repairs
- withheld OOD fast-path coverage

A fixture transport can validate accounting and control flow, but it is not evidence of LLM savings.
