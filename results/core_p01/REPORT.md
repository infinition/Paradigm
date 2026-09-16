# Core P0.1: measured deliberation surrogate

## Purpose

This benchmark replaces the assumed 100:1 cost ratio from Core P0 with a measured local fallback path. The fallback probes a neighborhood around each state and aggregates the reference policy over those probes. It is intentionally expensive and deterministic. It is a benchmark surrogate, not an LLM or production planner.

## Results

| Scenario | Reflex | Coverage | Selective accuracy | Deliberative accuracy | System accuracy | Measured speedup |
|---|---|---:|---:|---:|---:|---:|
| deterministic_routing | tree | 100.0% | 0.992 | 0.996 | 0.992 | 1045.0x |
| noisy_routing | calibrated_forest | 100.0% | 0.868 | 0.872 | 0.868 | 2.0x |
| distribution_shift | tree | 100.0% | 0.996 | 0.999 | 0.996 | 793.8x |
| repeated_workflows | tree | 100.0% | 0.924 | 0.926 | 0.924 | 573.2x |

All four synthetic scenarios pass the local benchmark gates in this run. The noisy task selects a calibrated forest and therefore has a much smaller efficiency margin than the tree-based cases.

## Interpretation

- The measured result confirms that repeated deterministic decisions can be collapsed into very small reflexes with large local latency savings.
- The noisy scenario is a warning against assuming that compilation is always worthwhile. Better calibration can require a heavier backend.
- This benchmark does not close Phase 1. A later benchmark still needs a real agent, planner, or domain-specific deliberative system.
- Coverage is 100% in this run because the selected models already satisfy the declared quality target without fallback. Separate selective and OOD experiments continue to exercise fallback behavior.

Raw data: `core_p01_measured.json`.
