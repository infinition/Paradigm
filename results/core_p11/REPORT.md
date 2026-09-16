# Core P1.1 report: multi-layer continual reflex adaptation

P1.1 moves the bounded-plasticity experiment from a single linear matrix to a two-layer neural reflex and compares it with ordinary continual-learning baselines across three successive representation shifts.

This is a synthetic benchmark. It is designed to expose tradeoffs and failure modes, not to establish a general advantage for any optimizer.

## Setup

- reflex: NumPy MLP, 24 inputs, 48 hidden units, 4 outputs
- task: fixed nonlinear latent teacher
- shift: three successive fixed orthogonal changes of input coordinates
- seeds: 11, 23, 41, 77
- online adaptation: 150 steps per shift
- methods: SGD, Adam, replay, diagonal EWC, periodic joint retraining, Drift Contract transfer
- Drift Contract epsilon: 0.025 on both matrix layers

The task geometry is fixed across seeds. Seeds change sampled examples and label noise. This is important for the update-space experiment because validated updates must belong to the same task family before a shared subspace is meaningful.

## Final continual-learning result

| Method | Current task | Mean seen | Worst seen | Mean forgetting | Mean adaptation time | Mean max step drift |
|---|---:|---:|---:|---:|---:|---:|
| SGD | 57.3% | 38.7% | 28.7% | 27.3% | 0.108 s | 0.0518 |
| Adam | 68.2% | 39.3% | 22.3% | 37.6% | 0.185 s | 0.0521 |
| Replay | 66.1% | 40.8% | 25.4% | 31.8% | 0.407 s | 0.0494 |
| EWC | 68.3% | 39.5% | 23.0% | 37.1% | 0.177 s | 0.0568 |
| Periodic joint retrain | 50.1% | **42.5%** | **32.7%** | **12.9%** | 0.519 s | not measured |
| Drift Contract | 67.4% | 39.0% | 22.7% | 37.6% | 0.387 s | **0.0241** |

Local wall-clock values are included only to show relative cost in this NumPy implementation. They are not hardware-independent performance results.

## Interpretation

The Drift Contract transfer approximately halves the largest measured per-step pre-activation change relative to Adam while reaching similar current-task accuracy. It does not, by itself, prevent catastrophic forgetting across successive shifts.

Replay improves mean retained performance over the ordinary online optimizers, while periodic joint retraining gives the strongest retention in this benchmark at higher adaptation cost and lower final current-task accuracy.

The result narrows the bounded-plasticity hypothesis:

> an explicit per-step drift budget controls update magnitude, but retention still requires information about previous behavior.

This is consistent with the scope of the Drift Contract preprint. A local matrix change bound is not a continual-learning guarantee.

## Explicit neural update-space test

P1.1 also replaces the compact linear-policy proxy from P0.3 with explicit neural parameter deltas.

Signature:

```text
candidate parameters after adaptation
          -
parameters before adaptation
          |
          v
flatten -> L2 normalize -> PCA residual gate
```

The initial trusted pool contains clean Drift Contract updates from the first two shifts.

Recorded result before pool expansion:

| Candidate family | Acceptance |
|---|---:|
| held-out clean update | 50% |
| poisoned update | 50% |
| legitimate unseen shift | 25% |

After adding validated updates from the previously unseen shift:

| Candidate family | Acceptance |
|---|---:|
| legitimate unseen shift | 75% |
| poisoned update | **100%** |

This is a negative result and is retained as such.

The parameter-delta PCA space is not a useful promotion gate in its current form. In this experiment, expanding a single global update subspace makes it broader and eventually admits every poisoned update in the recorded set.

This mirrors an important design boundary already visible in the z-manifold research: subspace membership is pool-relative and cannot be treated as semantic validity. Paradigm therefore must not merge heterogeneous validated update families into one increasingly broad trusted space and interpret membership as approval.

## Consequence for Paradigm

P1.2 should test a different construction rather than tune this result away:

1. family-conditioned trusted spaces instead of one global update PCA
2. behavior-delta signatures on fixed anchor suites
3. semantic subgroup checks in the promotion manifest
4. hybrid acceptance where update geometry can reject or route a candidate, but never promote it alone
5. risk-conditioned epsilon schedules linked to the manifest

The current P1.1 conclusion is deliberately modest:

- bounded plasticity controls local change
- replay or retraining is still needed for retention
- raw neural update geometry alone is insufficient for trusted promotion

Raw results: `core_p11_multilayer.json`.
