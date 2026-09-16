# Paper plan

## Working title

**Paradigm: Continual Reflex Compilation with Calibrated Fallback**

The title should remain narrow until Structured or World results justify inclusion.

## Main question

Can recurring validated decisions be compiled into specialized reflexes that remove a meaningful fraction of deliberative compute while preserving target reliability through selective fallback?

## Minimum paper

A useful first paper does not need all three directions.

Core sections:

1. problem definition
2. reflex compilation lifecycle
3. selective runtime and fallback
4. active and candidate promotion
5. synthetic controlled benchmark
6. workflow or tool-routing benchmark
7. distribution-shift benchmark
8. trusted-space ablation
9. bounded-plasticity ablation
10. limitations

## Baselines

Required:

- direct deliberation
- exact and approximate cache where applicable
- decision tree
- random forest or gradient boosting
- ordinary supervised distillation
- confidence-only cascade
- periodic retraining

For continual adaptation:

- replay
- EWC
- ordinary Adam or SGD
- frozen model plus batch retraining

## Primary plots

1. selective accuracy versus coverage
2. expected latency versus target accuracy
3. fallback rate versus distribution shift
4. candidate regression versus adaptation gain
5. OOD false acceptance versus gate threshold
6. behavioral drift versus activation drift for bounded adaptation

## Claim gate

Do not write the central claim unless Paradigm beats the strongest simple baseline on at least one meaningful axis without hiding a regression on another.

Examples of acceptable outcomes:

- same target quality at lower expected compute
- higher selective reliability at the same coverage
- safer continual update under a matched adaptation budget

A negative result is also useful if it establishes that caching or trees already solve the intended regime.

## Structured extension

Add only after Core.

Use the boundary established in `ga-vs-scalarization` to test whether an architecture selector can choose a simple scalarized reflex for single-stage geometry and a geometric reflex for nested rotations.

## World extension

Add only after Core.

Use FluidWorld latent state or another matched predictive state source to test whether prediction improves execute-or-defer decisions. Keep the world model external to Core so a negative result does not invalidate the main architecture.

## Application study: Paradigm Agent

Use P2 as the first end-to-end application section only after replacing the deterministic reference deliberator with a genuine expensive controller. Report task success, fast-path coverage, fallback causes, token and latency savings, tool-safety violations, and OOD behavior. Keep the current P2.0 result as a systems integration baseline rather than the main empirical claim.
