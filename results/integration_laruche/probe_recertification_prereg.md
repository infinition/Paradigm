# Pre-registration: probe-based re-certification of active families

Written before any code change or replay. Record of run 11 is frozen at tag `laruche-family-scoped-run11`.

## Hypothesis

For an already active family with no fresh deliberative validation traces, retention probes are sufficient for re-certification when all existing quality and regression safeguards pass. A candidate that fails those probes must remain rejected.

## Rule under test

In family-scoped certification, a family that is currently active, has frozen probes, and has no held-out deliberative trace in the current split is certified on its probes instead of being reported `insufficient`: coverage on probes at least the probe coverage floor (0.65), agreement at least the probe accuracy floor (0.95), no coverage regression beyond 0.10 against the incumbent, gate acceptance on probes at least 0.65, ECE on probes at most 0.10. Its confidence threshold is the incumbent's. A family with held-out traces is judged as before. No floor is changed.

A replacement artifact is adopted only if every active family re-certifies (on held-out traces or on probes) and at least one new family becomes active.

## Predictions on the frozen run 11 state

1. Compile point 20 stays rejected: `file_edit` agreed with its probes on 15 of 16 (0.9375, below 0.95). The rule relaxes nothing there.
2. Compile point 24 becomes a promotion (version 2): `start` re-certifies on its 5 probes, `file_edit` on its 16 (it passed 16 of 16 in the record), and `tests_passed` activates on its own held-out evidence as recorded (8 train, 3 held-out, ECE 0.095, acceptance 0.67).
3. With the rule off, the replay reproduces the recorded verdicts at 20 and 24 exactly (reproducibility check).
4. Negative control at 24: the same candidate trained with the `file_edit` family's labels replaced by another action is rejected by the `file_edit` probes. The verdict is discriminative only if the clean candidate is promoted and the damaged one rejected in the same protocol.

## Exploratory variable, read only

A per-family minimum count of validated training traces, swept over 1, 3, 5, 8, applied after the fact to the recorded per-family verdicts of run 11 and to the offline audit of the 32-mission record. Reported as which activations would have survived and when; nothing about run 11 is rewritten.

## Then

One fresh live run of 24 missions with the rule enabled from mission 1, same workspace, model, guard, canonicalization and thresholds. Predicted: a first promotion around mission 16, then at least one later version activating `tests_passed` or `tests_failed` without regression of `start` or `file_edit`, 24 of 24 verified, 0 false fast paths.
