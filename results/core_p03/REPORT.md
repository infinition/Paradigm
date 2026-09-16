# Core P0.3 report

## Question

Does a trusted space built from validated reflexes provide a more useful compilation signal than the input-space gates tested in P0.2?

P0.3 moves the experiment into two reflex-level representations:

1. **parameter space**, using the flattened weights and biases of small multinomial linear policies
2. **behavior space**, using class probabilities produced by each reflex on a fixed anchor suite

The experiment is synthetic and intentionally small. It tests the mechanism, not a general safety claim.

## Setup

A clean reference task defines three actions from an eight-dimensional state. Multiple reflexes are trained from bootstrap samples of the same valid task.

The validated pool is split into two disjoint sets:

- a fit pool that defines the PCA subspace
- a calibration pool that defines the residual threshold

Three candidate families are then evaluated:

- **clean candidates**, independently trained on the same valid task
- **poisoned candidates**, trained after corrupting 16% of their labels
- **weak-pool candidates**, still valid, but trained with additional shifted support that is poorly represented in the original trusted pool

The recorded run uses seed `1337`.

## Main result

| Space | Clean accepted | Poison accepted | Weak-pool valid accepted | Poison AUROC |
|---|---:|---:|---:|---:|
| Parameter | 98% | 0% | 74% | 1.000 |
| Behavior | 100% | 0% | 70% | 1.000 |

The poisoned reflexes remain reasonably capable on the ordinary validation set, with mean accuracy around 92.6%, but both reflex-level gates separate them completely from clean candidates in this controlled setup.

This is materially different from P0.2. Input-space gates could not detect label corruption because the inputs themselves remained valid. Reflex-level signatures expose the effect of that corruption.

## Weak-pool result

The same mechanism also reproduces the main limitation expected from a pool-relative trust model: legitimate behavior can be rejected when the trusted pool does not cover it.

Before pool expansion:

- parameter-space weak-pool acceptance: **74%**
- behavior-space weak-pool acceptance: **70%**

After adding part of the valid weak-pool family to the trusted fit and calibration pools:

| Space | Clean accepted | Poison accepted | Weak-pool valid accepted |
|---|---:|---:|---:|
| Parameter, augmented pool | 94% | 0% | 100% |
| Behavior, augmented pool | 92% | 0% | 100% |

This is the intended interpretation: rejection is evidence of incompatibility with the current trusted pool, not proof that a candidate is invalid.

## Adaptive parameter-space control

A separate stress test explicitly searches **inside the learned parameter subspace** for a candidate that preserves at least 90% overall accuracy while damaging a target slice.

Recorded candidate:

- overall accuracy: **95.9%**
- target-slice accuracy: **11.1%**
- parameter-space residual: effectively zero
- parameter gate: **accept**
- behavior gate: **reject**

The important point is not the exact target score. The candidate is generated inside the trusted parameter subspace by construction. A residual-only parameter gate therefore cannot reject it.

This rules out a strong interpretation of parameter-subspace membership. In Paradigm, membership can be one signal, but it cannot be treated as semantic certification.

## Behavior-space control

Behavior space catches the constructed parameter-aligned attack above, but it is not sufficient by itself either.

A second control creates a convex mixture of trusted probability signatures. The resulting signature remains a valid probability distribution and lies close to the trusted behavior family.

Recorded control:

- ensemble-mean target-slice accuracy: **94.4%**
- candidate target-slice accuracy: **72.2%**
- candidate overall anchor accuracy: **95.8%**
- behavior gate: **accept**

This control is deliberately labeled **signature-only**. It does not claim that the convex mixture corresponds to one trained executable reflex. Its role is narrower: it demonstrates that residual geometry alone cannot certify semantics, even in behavior space.

## Interpretation

P0.3 supports four limited conclusions:

1. **Reflex-level trust is more relevant than input-level trust for candidate compilation.** Label poisoning changes the reflex even when the input distribution remains ordinary.
2. **Behavior signatures are a useful independent view.** They reject the constructed parameter-aligned failure that parameter-space residual cannot see.
3. **Trusted pools are coverage dependent.** Valid new behavior can be rejected until representative validated reflexes are added.
4. **No subspace is a semantic certificate.** Parameter membership can be attacked directly, and behavior geometry can still hide subgroup failures.

The practical implication for Paradigm is a multi-signal promotion design:

```text
candidate reflex
    |
    +--> parameter/update compatibility
    +--> behavior compatibility on anchors
    +--> task quality and subgroup checks
    +--> calibration and OOD behavior
    +--> drift budget
    |
    `--> promote only if the declared manifest passes
```

## What this does not show

- It does not transfer the guarantees or threat model of z-manifold into Paradigm.
- It does not evaluate neural reflexes with millions of parameters.
- It does not show that PCA is the right long-term trusted representation.
- It does not solve adaptive attacks.
- It does not make a safety guarantee.

## Reproduce

```bash
python benchmarks/core_p03_reflex_space.py --seed 1337
```

Raw result:

`results/core_p03/core_p03_reflex_space.json`
