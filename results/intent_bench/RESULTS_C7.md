# C7 results: language-aware trust gating (exploratory)

Frozen decision model of C6R (threshold 0.6179); version 1 scored out of fold (leave-one-group-out refit of the same configuration), version 2 scored by the frozen model. G2 thresholds (mean distance to 3 nearest v1 sentences in S): p90 0.763, p95 0.838, p99 1.152. G3-exp thresholds on out-of-fold nonconformity: alpha 0.05 -> 0.539, alpha 0.1 -> 0.439. PRIMARY slices (ambiguous excluded).

## Version 1, out of fold

| gate | acc. positives | acc. hard negatives | coverage | sel. acc. | hard FFP | FFP all | positive reflex coverage | fired | hard fired as CAPTURE by transformation (neg, temp, past, obj, insp, cond) |
|---|---|---|---|---|---|---|---|---|---|
| G0 | 1.00 | 1.00 | 0.85 | 0.94 | 2 | 2 | 0.78 | 271 | 0, 1, 0, 1, 0, 0 |
| G1 | 0.93 | 0.89 | 0.79 | 1.00 | 0 | 0 | 0.76 | 252 | 0, 0, 0, 0, 0, 0 |
| G2_p90 | 1.00 | 1.00 | 0.84 | 0.94 | 2 | 2 | 0.78 | 269 | 0, 1, 0, 1, 0, 0 |
| G2_p95 | 1.00 | 1.00 | 0.85 | 0.94 | 2 | 2 | 0.78 | 272 | 0, 1, 0, 1, 0, 0 |
| G2_p99 | 1.00 | 1.00 | 0.85 | 0.94 | 2 | 2 | 0.78 | 272 | 0, 1, 0, 1, 0, 0 |
| G4 | 0.93 | 0.19 | 0.40 | 1.00 | 0 | 0 | 0.76 | 128 | 0, 0, 0, 0, 0, 0 |
| G3exp_a0.05 | 0.96 | 0.96 | 0.85 | 0.94 | 2 | 2 | 0.78 | 272 | 0, 1, 0, 1, 0, 0 |
| G3exp_a0.1 | 0.85 | 0.95 | 0.85 | 0.94 | 2 | 2 | 0.78 | 272 | 0, 1, 0, 1, 0, 0 |

## Version 2, frozen model (the C6R record)

| gate | acc. positives | acc. hard negatives | coverage | sel. acc. | hard FFP | FFP all | positive reflex coverage | fired | hard fired as CAPTURE by transformation (neg, temp, past, obj, insp, cond) |
|---|---|---|---|---|---|---|---|---|---|
| G0 | 0.27 | 0.06 | 0.08 | 0.89 | 0 | 0 | 0.17 | 19 | 0, 0, 0, 0, 0, 0 |
| G1 | 0.00 | 0.02 | 0.01 | 1.00 | 0 | 0 | 0.00 | 3 | 0, 0, 0, 0, 0, 0 |
| G2_p90 | 0.90 | 0.60 | 0.49 | 0.87 | 2 | 3 | 0.67 | 120 | 0, 2, 0, 0, 0, 0 |
| G2_p95 | 0.97 | 0.74 | 0.60 | 0.85 | 2 | 3 | 0.70 | 146 | 0, 2, 0, 0, 0, 0 |
| G2_p99 | 1.00 | 1.00 | 0.78 | 0.87 | 2 | 3 | 0.70 | 189 | 0, 2, 0, 0, 0, 0 |
| G4 | 0.00 | 0.00 | 0.00 | n/a | 0 | 0 | 0.00 | 0 | 0, 0, 0, 0, 0, 0 |
| G3exp_a0.05 | 0.80 | 0.94 | 0.78 | 0.87 | 2 | 3 | 0.70 | 189 | 0, 2, 0, 0, 0, 0 |
| G3exp_a0.1 | 0.77 | 0.88 | 0.78 | 0.87 | 2 | 3 | 0.70 | 189 | 0, 2, 0, 0, 0, 0 |

## Version 2 by source, positive reflex coverage / selective accuracy / hard FFP

| gate | chatgpt | claude | synthetic_user_style |
|---|---|---|---|
| G0 | 0.10 / 0.80 / 0 | 0.00 / 0.50 / 0 | 0.40 / 1.00 / 0 |
| G1 | 0.00 / 1.00 / 0 | 0.00 / n/a / 0 | 0.00 / 1.00 / 0 |
| G2_p90 | 0.70 / 0.91 / 0 | 0.40 / 0.81 / 0 | 0.90 / 0.86 / 2 |
| G2_p95 | 0.70 / 0.90 / 0 | 0.50 / 0.80 / 0 | 0.90 / 0.83 / 2 |
| G2_p99 | 0.70 / 0.91 / 0 | 0.50 / 0.85 / 0 | 0.90 / 0.84 / 2 |
| G4 | 0.00 / n/a / 0 | 0.00 / n/a / 0 | 0.00 / n/a / 0 |
| G3exp_a0.05 | 0.70 / 0.91 / 0 | 0.50 / 0.85 / 0 | 0.90 / 0.84 / 2 |
| G3exp_a0.1 | 0.70 / 0.91 / 0 | 0.50 / 0.85 / 0 | 0.90 / 0.84 / 2 |
