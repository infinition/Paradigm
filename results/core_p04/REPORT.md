# Core P0.4 report

## Question

Can Paradigm turn the P0.3 findings into an explicit candidate promotion rule where no single trust signal is allowed to approve a reflex by itself?

P0.4 introduces a multi-signal promotion manifest. A candidate must satisfy all declared checks before promotion.

## Promotion policy

The recorded synthetic policy requires:

| Check | Requirement |
|---|---:|
| validation accuracy | >= 0.95 |
| ECE | <= 0.06 |
| trusted parameter space | accepted |
| trusted behavior space | accepted |
| anchor label disagreement | <= 0.06 |
| anchor total variation | <= 0.08 |
| minimum class accuracy | >= 0.80 |
| protected slice accuracy | >= 0.70 |

These values are benchmark thresholds, not universal deployment defaults.

## Recorded decisions

Seed: `1337`

| Candidate | Expected | Observed |
|---|---|---|
| clean | promote | promote |
| poisoned | reject | reject |
| valid weak-pool, before pool expansion | reject | reject |
| same valid weak-pool candidate, after pool expansion | promote | promote |
| parameter-aligned adaptive candidate | reject | reject |

All five recorded decisions match the declared expectation.

## Clean candidate

The selected clean candidate passes every check:

- accuracy: **96.9%**
- ECE: **0.024**
- parameter-space gate: pass
- behavior-space gate: pass
- anchor disagreement: **2.25%**
- mean total variation: **0.0186**
- minimum class accuracy: **83.8%**
- protected slice accuracy: **73.2%**

## Poisoned candidate

The poisoned candidate fails broadly rather than at one isolated signal:

- accuracy: **91.9%**
- ECE: **0.205**
- parameter-space gate: fail
- behavior-space gate: fail
- anchor disagreement: **6.75%**
- mean total variation: **0.252**
- minimum class accuracy: **39.4%**
- protected slice accuracy: **31.7%**

This is the simple case. Multiple independent checks agree that the candidate should not be promoted.

## Valid weak-pool candidate

The more important case is a candidate that is valid but not represented by the initial trusted pool.

Before pool expansion:

- accuracy: **98.1%**
- ECE: **0.028**
- minimum class accuracy: **87.9%**
- protected slice accuracy: **87.8%**
- parameter-space gate: fail
- behavior-space gate: fail

The manifest therefore rejects it for exactly two reasons: trusted-pool incompatibility in parameter and behavior space.

After adding validated examples from the missing family to the trusted pool, the same candidate keeps identical quality and drift metrics but both trust checks pass. The manifest then approves it.

This behavior is intentional. Paradigm records the distinction between:

```text
invalid candidate
```

and:

```text
valid candidate not represented by the current trusted pool
```

A trust rejection alone should trigger investigation or pool expansion, not an invalidity claim.

## Parameter-aligned adaptive candidate

The final executable candidate is searched directly inside the learned trusted parameter subspace.

Recorded metrics:

- accuracy: **94.9%**
- ECE: **0.0116**
- parameter-space gate: **pass**
- behavior-space gate: **fail**
- anchor disagreement: **3.75%**
- mean total variation: **0.0392**
- minimum class accuracy: **67.7%**
- protected slice accuracy: **48.8%**

The candidate is therefore rejected even though its calibration is good, its drift is small, and its parameter-space residual is accepted.

This is the central P0.4 result: **subspace membership is not enough to promote a reflex**.

## Registry changes

`ActiveCandidateRegistry` now supports:

- staging a candidate without mutating the active reflex
- attaching a promotion manifest
- blocking promotion when any manifest check fails
- keeping promotion evidence
- explicit rejection reasons
- rollback to the previous active reflex

The API still permits promotion without a manifest for backward compatibility in the research scaffold. Production use should require one.

## Interpretation

P0.4 turns the negative controls from P0.3 into an operational rule:

```text
candidate
  |
  +-- quality
  +-- calibration
  +-- parameter trust
  +-- behavior trust
  +-- drift
  +-- subgroup checks
  |
  `-- all pass -> promotion
       any fail -> remain candidate / reject / investigate
```

The design deliberately avoids a single scalar safety score. Each failure remains visible and attributable.

## What this does not show

- The thresholds are not validated outside this synthetic task.
- The benchmark does not yet use a neural reflex or real agent workload.
- Rollback is implemented in memory, not yet as a persistent version store.
- The registry does not yet assign immutable content-addressed version identifiers.
- The benchmark does not yet evaluate delayed failures after promotion.

## Reproduce

```bash
python benchmarks/core_p04_promotion_manifest.py --seed 1337
```

Raw result:

`results/core_p04/core_p04_promotion.json`
