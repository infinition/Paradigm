# C4 results: explicit temporality and actionability features

Dataset sha256 `b5ce90ed8b40ee79dc61012363dc0207d683829397a196c46b27b252c40b055b`. Extractor `intent_temporal_fr` frozen before this run.

## Extractor outputs on the dataset (before any classifier)

| sentences | n | temporal categories | negated | actionable_now |
|---|---|---|---|---|
| base_or_variant | 135 | CONDITIONAL 6, FUTURE 1, NOW 8, PAST_REFERENCE 3, UNSPECIFIED 117 | 7 | 118 |
| negation | 37 | NOW 1, UNSPECIFIED 36 | 35 | 2 |
| temporal | 37 | FUTURE 35, UNSPECIFIED 2 | 0 | 2 |
| past_question | 37 | PAST_REFERENCE 37 | 0 | 0 |
| object_change | 37 | NOW 5, PAST_REFERENCE 1, UNSPECIFIED 31 | 2 | 34 |
| inspection_only | 37 | CONDITIONAL 16, UNSPECIFIED 21 | 2 | 20 |
| CAPTURE_PERSON sentences | 46 | | | 45 |

## Under the gate: A+S against A+S+T

| representation | model | unseen positive recall | FFP hard neg. | FFP per transformation: negation, temporal, past_question, object_change, inspection_only | coverage | sel. acc. | selector feasible | ECE | criterion C4 | temporal FFP fell |
|---|---|---|---|---|---|---|---|---|---|---|
| A+S | prototype | 0.02 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | 0.35 |  |  |
| A+S | knn3 | 0.37 | 4 | 0, 3, 1, 0, 0 | 0.43 | 0.93 | False | 0.05 |  |  |
| A+S | logreg | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | 0.16 |  |  |
| A+S | tree | 0.43 | 8 | 1, 2, 2, 2, 1 | 0.72 | 0.76 | False | 0.25 |  |  |
| A+S+T | prototype | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | 0.29 | False | False |
| A+S+T | knn3 | 0.46 | 2 | 0, 1, 0, 1, 0 | 0.66 | 0.96 | False | 0.06 | True | True |
| A+S+T | logreg | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | 0.16 | False | False |
| A+S+T | tree | 0.59 | 3 | 0, 1, 0, 1, 1 | 0.81 | 0.83 | False | 0.20 | True | True |
| A+S+T(x4) | prototype | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | 0.13 | False | False |
| A+S+T(x4) | knn3 | 0.46 | 2 | 0, 1, 0, 1, 0 | 0.66 | 0.96 | False | 0.06 | True | True |
| A+S+T(x4) | logreg | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | 0.15 | False | False |
| A+S+T(x4) | tree | 0.59 | 3 | 0, 1, 0, 1, 1 | 0.81 | 0.83 | False | 0.20 | True | True |

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
| A+S+T(x4) | prototype | 0.47 | 0.48 | 0, 0, 0, 2, 0 |
| A+S+T(x4) | knn3 | 0.81 | 0.93 | 0, 1, 0, 8, 2 |
| A+S+T(x4) | logreg | 0.89 | 0.91 | 0, 1, 0, 2, 0 |
| A+S+T(x4) | tree | 0.72 | 0.76 | 2, 1, 0, 4, 1 |
