# C6 results: goal x candidate action

Dataset sha256 `b5ce90ed8b40ee79dc61012363dc0207d683829397a196c46b27b252c40b055b`. Scorers frozen: NLI median 837 ms per sentence (5 contracts), reranker median 1085 ms, CPU.

## Raw `camera.capture` scores by sentence type, before any classifier

| sentences | n | NLI entailment mean / share > 0.5 | reranker yes mean / share > 0.5 |
|---|---|---|---|
| positives | 46 | 0.18 / 0.17 | 0.98 / 1.00 |
| negation | 35 | 0.02 / 0.03 | 0.61 / 0.71 |
| temporal | 37 | 0.05 / 0.05 | 0.62 / 0.59 |
| past_question | 37 | 0.31 / 0.30 | 0.50 / 0.51 |
| object_change | 24 | 0.05 / 0.04 | 0.56 / 0.58 |
| inspection_only | 37 | 0.02 / 0.03 | 0.47 / 0.51 |

## H1, under the gate

| representation | model | unseen positive recall | FFP hard | per transformation: negation, temporal, past_question, object_change, inspection_only | coverage | sel. acc. | feasible | H1 vs A+S+T | H1 vs A+S |
|---|---|---|---|---|---|---|---|---|---|
| A+S | prototype | 0.02 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False |  |  |
| A+S | knn3 | 0.37 | 4 | 0, 3, 1, 0, 0 | 0.43 | 0.93 | False |  |  |
| A+S | logreg | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False |  |  |
| A+S | tree | 0.43 | 8 | 1, 2, 2, 2, 1 | 0.72 | 0.76 | False |  |  |
| A+S+T | prototype | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False |  |  |
| A+S+T | knn3 | 0.46 | 2 | 0, 1, 0, 1, 0 | 0.66 | 0.96 | False |  |  |
| A+S+T | logreg | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False |  |  |
| A+S+T | tree | 0.59 | 3 | 0, 1, 0, 1, 1 | 0.81 | 0.83 | False |  |  |
| E_NLI | prototype | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False | False |
| E_NLI | knn3 | 0.11 | 3 | 0, 1, 0, 2, 0 | 0.34 | 0.76 | False | False | False |
| E_NLI | logreg | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False | False |
| E_NLI | tree | 0.15 | 3 | 0, 3, 0, 0, 0 | 0.59 | 0.79 | False | False | False |
| A+E_NLI | prototype | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False | False |
| A+E_NLI | knn3 | 0.37 | 3 | 0, 3, 0, 0, 0 | 0.36 | 0.85 | False | False | False |
| A+E_NLI | logreg | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False | False |
| A+E_NLI | tree | 0.41 | 4 | 0, 2, 1, 1, 0 | 0.69 | 0.78 | False | False | False |
| S+E_NLI | prototype | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False | False |
| S+E_NLI | knn3 | 0.41 | 4 | 0, 3, 0, 1, 0 | 0.59 | 0.93 | False | False | True |
| S+E_NLI | logreg | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False | False |
| S+E_NLI | tree | 0.50 | 5 | 0, 3, 1, 1, 0 | 0.76 | 0.75 | False | False | True |
| A+S+E_NLI+T | prototype | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False | False |
| A+S+E_NLI+T | knn3 | 0.46 | 2 | 0, 1, 0, 1, 0 | 0.66 | 0.95 | False | False | True |
| A+S+E_NLI+T | logreg | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False | False |
| A+S+E_NLI+T | tree | 0.54 | 4 | 0, 1, 0, 3, 0 | 0.83 | 0.83 | False | False | True |
| E_RERANK | prototype | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False | False |
| E_RERANK | knn3 | 0.22 | 4 | 1, 3, 0, 0, 0 | 0.38 | 0.75 | False | False | False |
| E_RERANK | logreg | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 0.00 | False | False | False |
| E_RERANK | tree | 0.52 | 2 | 0, 2, 0, 0, 0 | 0.34 | 0.81 | False | False | True |
| A+E_RERANK | prototype | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False | False |
| A+E_RERANK | knn3 | 0.39 | 5 | 0, 3, 2, 0, 0 | 0.43 | 0.85 | False | False | False |
| A+E_RERANK | logreg | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False | False |
| A+E_RERANK | tree | 0.59 | 5 | 1, 2, 1, 1, 0 | 0.42 | 0.73 | False | False | True |
| S+E_RERANK | prototype | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False | False |
| S+E_RERANK | knn3 | 0.39 | 2 | 0, 1, 1, 0, 0 | 0.61 | 0.94 | False | False | True |
| S+E_RERANK | logreg | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False | False |
| S+E_RERANK | tree | 0.63 | 5 | 1, 2, 0, 2, 0 | 0.79 | 0.82 | False | False | True |
| A+S+E_RERANK+T | prototype | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False | False |
| A+S+E_RERANK+T | knn3 | 0.50 | 2 | 0, 1, 0, 1, 0 | 0.78 | 0.99 | False | True | True |
| A+S+E_RERANK+T | logreg | 0.33 | 0 | 0, 0, 0, 0, 0 | 0.58 | 0.99 | True | True | True |
| A+S+E_RERANK+T | tree | 0.50 | 4 | 0, 1, 0, 3, 0 | 0.83 | 0.86 | False | False | True |

## Without the gate

| representation | model | accuracy | recall CAPTURE_PERSON | predicted CAPTURE_PERSON on: negation, temporal, past_question, object_change, inspection_only |
|---|---|---|---|---|
| A+S | prototype | 0.64 | 0.85 | 3, 9, 4, 5, 0 |
| A+S | knn3 | 0.75 | 0.91 | 1, 7, 5, 5, 1 |
| A+S | logreg | 0.81 | 0.83 | 0, 4, 0, 2, 0 |
| A+S | tree | 0.65 | 0.59 | 4, 8, 4, 4, 2 |
| A+S+T | prototype | 0.67 | 0.87 | 0, 1, 0, 6, 1 |
| A+S+T | knn3 | 0.81 | 0.93 | 0, 1, 0, 8, 2 |
| A+S+T | logreg | 0.89 | 0.91 | 0, 1, 0, 2, 0 |
| A+S+T | tree | 0.72 | 0.76 | 2, 1, 0, 4, 1 |
| E_NLI | prototype | 0.45 | 0.11 | 1, 5, 2, 2, 1 |
| E_NLI | knn3 | 0.61 | 0.72 | 1, 8, 4, 9, 0 |
| E_NLI | logreg | 0.58 | 0.37 | 0, 6, 0, 2, 0 |
| E_NLI | tree | 0.71 | 0.63 | 0, 6, 4, 3, 0 |
| A+E_NLI | prototype | 0.51 | 0.72 | 0, 6, 4, 6, 2 |
| A+E_NLI | knn3 | 0.60 | 0.78 | 1, 11, 8, 8, 1 |
| A+E_NLI | logreg | 0.66 | 0.61 | 0, 3, 1, 2, 1 |
| A+E_NLI | tree | 0.72 | 0.76 | 0, 6, 3, 2, 2 |
| S+E_NLI | prototype | 0.62 | 0.85 | 0, 6, 3, 1, 0 |
| S+E_NLI | knn3 | 0.82 | 0.93 | 0, 7, 0, 1, 0 |
| S+E_NLI | logreg | 0.82 | 0.83 | 0, 4, 0, 2, 0 |
| S+E_NLI | tree | 0.67 | 0.52 | 2, 5, 1, 4, 2 |
| A+S+E_NLI+T | prototype | 0.62 | 0.83 | 0, 1, 0, 6, 0 |
| A+S+E_NLI+T | knn3 | 0.83 | 0.93 | 0, 2, 0, 6, 0 |
| A+S+E_NLI+T | logreg | 0.88 | 0.93 | 0, 1, 0, 2, 0 |
| A+S+E_NLI+T | tree | 0.76 | 0.76 | 0, 2, 0, 3, 3 |
| E_RERANK | prototype | 0.49 | 0.67 | 9, 9, 8, 2, 1 |
| E_RERANK | knn3 | 0.62 | 0.63 | 7, 3, 5, 2, 1 |
| E_RERANK | logreg | 0.65 | 0.59 | 1, 4, 2, 0, 0 |
| E_RERANK | tree | 0.62 | 0.67 | 1, 7, 3, 2, 0 |
| A+E_RERANK | prototype | 0.64 | 0.80 | 4, 7, 6, 1, 0 |
| A+E_RERANK | knn3 | 0.72 | 0.85 | 3, 6, 4, 4, 0 |
| A+E_RERANK | logreg | 0.71 | 0.74 | 1, 1, 2, 0, 0 |
| A+E_RERANK | tree | 0.65 | 0.67 | 3, 4, 2, 1, 0 |
| S+E_RERANK | prototype | 0.58 | 0.76 | 7, 9, 7, 1, 1 |
| S+E_RERANK | knn3 | 0.81 | 0.85 | 1, 6, 2, 1, 1 |
| S+E_RERANK | logreg | 0.84 | 0.83 | 0, 5, 0, 3, 0 |
| S+E_RERANK | tree | 0.72 | 0.76 | 2, 3, 2, 3, 1 |
| A+S+E_RERANK+T | prototype | 0.71 | 0.85 | 0, 2, 0, 1, 0 |
| A+S+E_RERANK+T | knn3 | 0.90 | 1.00 | 0, 1, 0, 2, 1 |
| A+S+E_RERANK+T | logreg | 0.90 | 0.96 | 0, 1, 0, 1, 0 |
| A+S+E_RERANK+T | tree | 0.79 | 0.76 | 0, 2, 0, 3, 0 |

## H2, the C5 regions with the fused k-NN

| representation | region | size | coverage under gate | sel. acc. under gate | FFP hard | positive recall | feasible | certifiable |
|---|---|---|---|---|---|---|---|---|
| A+S+E_NLI+T | R1 | 176 | 0.32 | 0.95 | 2 | 0.43 | False | False |
| A+S+E_NLI+T | R2 | 88 | 0.49 | 0.95 | 1 | 0.33 | False | False |
| A+S+E_NLI+T | R3_p90 | 161 | 0.35 | 0.95 | 2 | 0.43 | False | False |
| A+S+E_NLI+T | R4_p90 | 83 | 0.52 | 0.95 | 1 | 0.33 | False | False |
| A+S+E_NLI+T | R3_p95 | 166 | 0.34 | 0.95 | 2 | 0.43 | False | False |
| A+S+E_NLI+T | R4_p95 | 84 | 0.51 | 0.95 | 1 | 0.33 | False | False |
| A+S+E_NLI+T | R3_p99 | 175 | 0.32 | 0.95 | 2 | 0.43 | False | False |
| A+S+E_NLI+T | R4_p99 | 88 | 0.49 | 0.95 | 1 | 0.33 | False | False |
| A+S+E_RERANK+T | R1 | 176 | 0.36 | 0.97 | 2 | 0.50 | False | False |
| A+S+E_RERANK+T | R2 | 88 | 0.49 | 0.98 | 1 | 0.35 | False | False |
| A+S+E_RERANK+T | R3_p90 | 154 | 0.41 | 0.97 | 2 | 0.50 | False | False |
| A+S+E_RERANK+T | R4_p90 | 81 | 0.53 | 0.98 | 1 | 0.35 | False | False |
| A+S+E_RERANK+T | R3_p95 | 166 | 0.38 | 0.97 | 2 | 0.50 | False | False |
| A+S+E_RERANK+T | R4_p95 | 86 | 0.50 | 0.98 | 1 | 0.35 | False | False |
| A+S+E_RERANK+T | R3_p99 | 173 | 0.36 | 0.97 | 2 | 0.50 | False | False |
| A+S+E_RERANK+T | R4_p99 | 86 | 0.50 | 0.98 | 1 | 0.35 | False | False |
| A+S+T | R1 | 176 | 0.32 | 0.96 | 2 | 0.46 | False | False |
| A+S+T | R2 | 88 | 0.49 | 0.98 | 1 | 0.33 | False | False |
| A+S+T | R3_p90 | 158 | 0.36 | 0.96 | 2 | 0.46 | False | False |
| A+S+T | R4_p90 | 82 | 0.52 | 0.98 | 1 | 0.33 | False | False |
| A+S+T | R3_p95 | 163 | 0.35 | 0.96 | 2 | 0.46 | False | False |
| A+S+T | R4_p95 | 85 | 0.51 | 0.98 | 1 | 0.33 | False | False |
| A+S+T | R3_p99 | 172 | 0.33 | 0.96 | 2 | 0.46 | False | False |
| A+S+T | R4_p99 | 88 | 0.49 | 0.98 | 1 | 0.33 | False | False |
