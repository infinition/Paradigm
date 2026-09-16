# Core P0 synthetic benchmark report

This report records the first executed Paradigm Core benchmark. It is a synthetic result and is not a general project claim.

## Result

All 4 synthetic quality gates passed with the selected reflex. Phase 1 remains pending because the synthetic teacher is not a realistic expensive deliberative baseline.

The main finding is architectural: Paradigm should not force one reflex family. The selector chose a raw decision tree on three scenarios and a calibrated tree on the noisy scenario. The calibrated forest was never selected.

## Scenario summary

| Scenario | Selected backend | Coverage | Selective accuracy | ECE | Test latency, us/item | Reference accuracy | Quality gate |
|---|---|---:|---:|---:|---:|---:|---|
| `deterministic_routing` | `tree` | 1.000 | 0.993 | 0.007 | 0.265 | 1.000 | pass |
| `noisy_routing` | `calibrated_tree` | 0.995 | 0.848 | 0.044 | 7.146 | 0.855 | pass |
| `distribution_shift` | `tree` | 1.000 | 0.996 | 0.003 | 0.221 | 1.000 | pass |
| `repeated_workflows` | `tree` | 1.000 | 0.934 | 0.012 | 0.631 | 0.934 | pass |

Latency values are machine-specific and should only be compared within the same run.

## What changed after the first run

The initial reference compiler used a calibrated random forest. It passed three of four quality gates and failed calibration on repeated workflows. It was also much slower than a simple tree on these tabular tasks. That result is preserved in `core_p0_forest_reference.json`.

The compiler was then generalized to support multiple reflex backends and a `MinimalReflexSelector` was added. The selector evaluates candidates in increasing complexity order and stops as soon as a candidate satisfies coverage, selective accuracy, and calibration constraints.

## Current interpretation

The useful result is not that trees are universally better. The result is that the first Paradigm benchmark supports the project rule that model complexity must be conditional on measured need. On simple routing tasks, a tree is sufficient. Under ambiguity, calibration becomes useful.

## What is not established

- No real compute saving has been demonstrated against an expensive deliberative system.
- No trusted-subspace benefit has been established yet.
- No continual adaptation result has been established yet.
- No transfer from z-manifold, Drift Contract, GA vs Scalarization, or FluidWorld is assumed.

## Next experiment

Replace the synthetic teacher with a deliberately slower reference decision path that produces validated traces, then measure real wall-clock and compute savings as reflex coverage increases. In parallel, add OOD controls that compare confidence-only fallback against distance and trusted-subspace gates.
