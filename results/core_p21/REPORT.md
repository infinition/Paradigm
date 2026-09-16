# P2.1 Online Agent Learning Report

P2.1 tests supervised learning during normal agent use. The active runtime is never updated in place. Only deliberative decisions from successful episodes enter the trusted experience buffer. Candidates are compiled periodically, evaluated on held-out recent episodes, and promoted only when quality, calibration, and OOD shadow coverage pass.

## End-to-end result

- Episodes: 69
- Baseline success: 100.0%
- Online success: 100.0%
- Online fast-path coverage: 60.6%
- Deliberative calls avoided: 217
- Deliberative call reduction: 60.6%
- Active reflex version at end: 4

## Novel family acquisition

- Novel-family first-half fast-path coverage: 0.0%
- Novel-family second-half fast-path coverage: 48.9%
- Novel-family overall success: 100.0%

The expected behavior is low fast-path coverage when the family first appears, followed by higher coverage only after enough successful fallback episodes have been admitted and a candidate passes shadow validation.

## Outcome filtering

- Failed control episode success: False
- Failed control episode admitted traces: 0
- Reflex self-labels are not used as teacher labels.

## Bounded neural candidate

- Feasible: True
- Selective accuracy: 100.0%
- Coverage: 100.0%
- ECE: 0.0001
- Maximum measured update drift: 0.022095
- Epsilon: 0.0300

## Interpretation

This phase is supervised imitation with outcome filtering, not RL. It fine-tunes a separate reflex candidate, not the deliberative controller. The primary fast path still prefers the simplest feasible compiled mechanism. The bounded softmax candidate exists to test whether Drift Contract can constrain neural reflex adaptation.
