# Core P1.0 report: bounded plasticity

## Question

Can the matrix update rule from the Drift Contract research provide a measurable change budget when transferred to a small continual-reflex adaptation experiment?

Research source:

- https://github.com/infinition/drift-contract
- https://infinition.github.io/infinition/assets/papers/drift-bounded-spectral-updates.pdf

The Drift Contract manuscript is a public preprint with an arXiv submission pending approval.

## Scope boundary

The source work studies deep local learning with auxiliary losses. Paradigm P1.0 does **not** assume that its accuracy, depth, or learning-rate transfer results carry over to reflex adaptation.

This benchmark transfers only the mechanical update rule:

```text
m  = 0.95 m + gradient
O  = NewtonSchulz5(m)
lr = epsilon / RMS(input)
W  = W - lr * scale * O
```

Paradigm uses the exact shape scale `sqrt(d_out / d_in)` and the strict denominator `max(RMS_current, RMS_ema)` in the bound check.

## Bound verification

Seed: `2026`

The measured pre-activation change is compared with the stated conditional matrix bound `epsilon * ||O||_2`.

| Shape | Max drift / epsilon | Max drift / stated bound | Bound respected |
|---|---:|---:|---|
| 8 x 64 | 0.383 | 0.338 | yes |
| 64 x 64 | 0.896 | 0.780 | yes |
| 128 x 64 | 0.889 | 0.784 | yes |

All three tested shapes remain below the measured conditional bound.

This is a numerical mechanics check, not an independent proof of the theorem.

## Risk-conditioned budgets

The same gradient and input batch are updated with three budgets:

| Policy label | Epsilon | Measured pre-activation drift |
|---|---:|---:|
| high risk | 0.003 | 0.00159 |
| medium risk | 0.010 | 0.00530 |
| low risk | 0.030 | 0.01590 |

The low-risk budget produces almost exactly 10 times the measured change of the high-risk budget.

This is the first executable form of the Paradigm hypothesis that adaptation speed can be linked to an explicit risk class rather than hidden inside an optimizer learning rate.

## Distribution-shock adaptation

Five synthetic seeds are used. A linear reflex is trained on an initial mapping, then the input basis is rotated. The active mapping therefore becomes poor on the shifted observations and each adaptation method receives the same number of update steps.

Before adaptation:

- mean old-distribution accuracy: **98.3%**
- mean shifted accuracy: **20.3%**

Recorded means across five seeds:

| Method | Shifted accuracy | Old accuracy retained | Max step drift |
|---|---:|---:|---:|
| Adam | 67.7% | 38.4% | 0.0603 |
| Adam + replay | 63.0% | 43.8% | 0.0599 |
| Drift contract, fast budget | 69.3% | 38.9% | 0.0354 |
| Drift contract, conservative budget | 27.7% | 87.0% | 0.0100 |

In this small benchmark, the fast contract reaches similar shifted-task quality to Adam with a smaller largest per-step pre-activation change. The conservative contract strongly preserves the old mapping but adapts too slowly under the fixed step budget.

That tradeoff is the useful result. A smaller epsilon behaves as a real plasticity budget, not as a free accuracy improvement.

## Interpretation

P1.0 supports three narrow conclusions:

1. the exact-scaled matrix implementation numerically respects the tested conditional drift bound
2. epsilon controls measured update-induced change in a predictable way
3. on this synthetic shock, the budget exposes an explicit stability versus adaptation-speed tradeoff

It does not establish that Drift Contract is the best optimizer for Paradigm.

## Next controls

The next bounded-plasticity campaign should add:

- SGD with momentum
- EWC
- stronger replay ratios
- periodic full retraining
- neural reflexes rather than a single linear matrix
- explicit update-delta trusted spaces
- several task families and shift severities
- promotion decisions that combine the update budget with P0.4 and P0.5 evidence

## Reproduce

```bash
python benchmarks/core_p10_bounded_plasticity.py --seed 2026
```

Raw result:

`results/core_p10/core_p10_bounded_plasticity.json`
