# ADR 006: online learning updates candidates, not the active reflex

## Decision

Paradigm may learn during normal use, but runtime learning does not mutate the active reflex in place.

Successful deliberative decisions enter an outcome-filtered experience buffer. Reflex predictions are not reused as teacher labels by default. At a compile boundary, the buffer is split by episode into training and recent shadow validation data. A candidate is trained separately and promoted only if the declared quality, calibration, and OOD checks pass.

The active reflex remains immutable between promotions.

## Rationale

Immediate gradient updates on the live policy make rollback, attribution, and regression analysis difficult. They also create a self-training loop in which an incorrect reflex can reinforce its own decision. Candidate-only learning preserves a clear lineage:

```text
active
  |
  +--> runtime decisions
  |
deliberative fallbacks
  |
validated outcomes
  |
trusted buffer
  |
candidate training
  |
shadow validation
  |
promotion or rejection
```

## P2.1 implementation

P2.1 uses supervised imitation from successful deliberative decisions. It is not reinforcement learning.

The production fast path still prefers the simplest feasible compiler. A separate linear softmax candidate is trained with Drift Contract updates to test bounded neural fine-tuning. That candidate is evaluated independently and is not promoted merely because its updates are small.

## Consequences

- learning can occur continuously while the agent is used
- promotion remains discrete and auditable
- failed episodes do not become trusted labels
- reflex self-labels do not create a feedback loop
- novel states remain deliberative until enough validated evidence exists
- a real external controller can replace the reference deliberator without changing the learning lifecycle
