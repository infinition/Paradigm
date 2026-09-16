# Core P1.2 report: family-conditioned trusted plasticity

P1.2 tests whether the negative global update-space result from P1.1 improves when trust is conditioned on a behavior family and evaluated within one shared active-to-candidate model lineage. It also adds fixed anchor behavior deltas, semantic subgroup checks, risk-conditioned plasticity budgets, and a replay plus Drift Contract baseline.

This is a synthetic benchmark. The result does not establish a general safety guarantee for neural updates.

## Setup

- reflex: NumPy MLP, 24 inputs, 48 hidden units, 4 outputs
- parent: one fixed active reflex shared by all family candidates
- families: three fixed representation shifts
- trusted clean candidates: 24 per family
- targeted poisoned candidates: 6 per family
- anchor behavior signature: normalized probability delta on a fixed protected domain plus the candidate family domain
- parameter signature: normalized flattened parameter delta from the shared parent
- trust geometry: cosine similarity to a family prototype, calibrated on a disjoint clean subset
- semantic checks: current accuracy, protected accuracy, minimum class accuracy, and target subgroup accuracy
- risk schedule: low epsilon 0.030, medium epsilon 0.015, high epsilon 0.0075

## Family-conditioned trust result

| Family | Risk | Clean geometry | Clean full manifest | Poison geometry | Poison full manifest | Cross-family geometry |
|---|---|---:|---:|---:|---:|---:|
| 1 | low | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% |
| 2 | medium | 100.0% | 83.3% | 0.0% | 0.0% | 0.0% |
| 3 | high | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% |

With the larger clean pool and a common parent lineage, the family-conditioned angular spaces separate the recorded families cleanly. Every held-out clean candidate passes the joint parameter and behavior geometry gate. Every targeted poisoned candidate and every clean candidate from another family is rejected by the joint geometry gate.

The complete promotion-style manifest is intentionally stricter than geometry. Family 2 accepts 5 of 6 held-out clean candidates because one candidate falls below a semantic calibration floor. This false rejection is retained. The current design prefers an explicit review or deliberative fallback over silently weakening the subgroup checks.

## Why the geometry changed from P1.1

P1.1 used one PCA residual space over heterogeneous normalized neural update deltas. That construction became permissive as the pool widened. P1.2 changes four assumptions rather than tuning the old result:

1. update trust is conditioned on a behavior family
2. candidates share the same parent parameters, so their update coordinates belong to one model lineage
3. normalized deltas are compared directionally with a cosine prototype instead of using Euclidean PCA reconstruction residual as the primary family gate
4. behavior deltas are measured independently on fixed anchor states

This is a narrower and more realistic use of update geometry. It still cannot approve a candidate by itself.

## Risk-conditioned epsilon

Controlled family 2 uses the same parent, data, minibatch seed, replay policy, and number of steps. Only epsilon changes.

| Risk | Epsilon | Current accuracy | Protected accuracy | Min class accuracy | Max step drift |
|---|---:|---:|---:|---:|---:|
| low | 0.0300 | 59.2% | 30.1% | 53.8% | 0.02863 |
| medium | 0.0150 | 53.8% | 37.7% | 45.5% | 0.01446 |
| high | 0.0075 | 33.1% | 59.9% | 28.6% | 0.00721 |

The measured change tracks the budget closely. Lower epsilon preserves more of the protected mapping but slows adaptation to the new family. This is the intended interpretation of epsilon in Paradigm: a plasticity budget, not a quality score.

## Replay plus Drift Contract

| Method | Current | Mean seen | Worst seen | Forgetting | Mean max step drift |
|---|---:|---:|---:|---:|---:|
| Replay | 65.8% | 41.0% | 25.5% | 30.8% | 0.0537 |
| Drift Contract | 66.5% | 39.0% | 22.6% | 36.8% | 0.0240 |
| Drift Contract + replay | 63.8% | 40.4% | 26.9% | 30.1% | 0.0241 |

The combination behaves as expected but does not dominate every metric. Drift Contract plus replay reduces forgetting relative to Drift Contract alone and retains the small local drift budget. Plain replay has slightly higher mean-seen accuracy in this run, while its measured per-step drift is more than twice as large. This keeps replay and bounded plasticity as complementary mechanisms rather than collapsing them into one claim.

## Consequence for Paradigm

P1.2 supports a narrower architecture:

```text
candidate update
      |
      +--> family identity
      |       |
      |       +--> parameter prototype gate
      |       +--> behavior prototype gate
      |
      +--> semantic subgroup manifest
      +--> risk-conditioned epsilon evidence
      |
      +--> all required checks pass -> eligible for shadow promotion
      `--> otherwise -> reject, defer, or create a new validated family
```

The important boundary remains unchanged: trusted geometry can reject, route, or identify an unrepresented family. It is not semantic proof that a candidate is safe or correct.

## Next step

P1.3 should connect this evidence directly to the persistent lifecycle from P0.5: family registry, unknown-family routing, manifest evidence stored with each immutable candidate, and post-promotion monitoring that can retire or split a family when its behavior distribution changes.

Raw results: `core_p12_family_trust.json`.
