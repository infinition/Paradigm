# C5 results: pre-defined sub-regions of `start`

Dataset sha256 `b5ce90ed8b40ee79dc61012363dc0207d683829397a196c46b27b252c40b055b`. Fused model k-NN (3) on A+S+T; pred_A and pred_S from independent k-NN on A and on S; density and gate fitted on each training fold. Criterion, unchanged: selector feasible inside the region (selective accuracy within 0.01 of the teacher at coverage at least 0.55 of the region), 0 hard-negative false fast paths under the gate, coverage above 0.

| region | size | share of positives / hard negatives | accuracy inside / outside (no gate) | selector: threshold, coverage, sel. acc., feasible | gate acc. inside | coverage under gate | sel. acc. under gate | FFP hard / all | positive recall under gate | ECE inside | certifiable |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | 176 (0.55) | 0.98 / 0.26 | 0.74 / 0.88 | 1.00, 0.53, 0.94, False | 0.49 | 0.32 | 0.96 | 2 / 2 | 0.46 | 0.08 | False |
| R2 | 88 (0.28) | 0.61 / 0.10 | 0.88 / 0.78 | 1.00, 0.70, 0.98, False | 0.61 | 0.49 | 0.98 | 1 / 1 | 0.33 | 0.02 | False |
| R3_p90 | 158 (0.49) | 0.98 / 0.25 | 0.78 / 0.83 | 1.00, 0.58, 0.93, False | 0.54 | 0.36 | 0.96 | 2 / 2 | 0.46 | 0.06 | False |
| R4_p90 | 82 (0.26) | 0.61 / 0.09 | 0.91 / 0.77 | 1.00, 0.74, 0.98, False | 0.66 | 0.52 | 0.98 | 1 / 1 | 0.33 | 0.05 | False |
| R3_p95 | 163 (0.51) | 0.98 / 0.26 | 0.78 / 0.83 | 1.00, 0.56, 0.93, False | 0.53 | 0.35 | 0.96 | 2 / 2 | 0.46 | 0.06 | False |
| R4_p95 | 85 (0.27) | 0.61 / 0.10 | 0.89 / 0.77 | 1.00, 0.72, 0.98, False | 0.64 | 0.51 | 0.98 | 1 / 1 | 0.33 | 0.04 | False |
| R3_p99 | 172 (0.54) | 0.98 / 0.26 | 0.76 / 0.86 | 1.00, 0.54, 0.94, False | 0.50 | 0.33 | 0.96 | 2 / 2 | 0.46 | 0.07 | False |
| R4_p99 | 88 (0.28) | 0.61 / 0.10 | 0.88 / 0.78 | 1.00, 0.70, 0.98, False | 0.61 | 0.49 | 0.98 | 1 / 1 | 0.33 | 0.02 | False |
| all | 320 (1.00) | 1.00 / 1.00 | 0.81 / n/a | 1.00, 0.66, 0.96, False | 0.54 | 0.40 | 0.97 | 2 / 2 | 0.46 | 0.06 | False |
