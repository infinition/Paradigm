# Intent generalization benchmark, results v1

Metric correction, recorded: the first run of this script counted hard-negative-role sentences whose class is CAPTURE_PERSON (an object_change that turns the request back into a capture) as false fast paths when predicted CAPTURE_PERSON. That was a counting bug, fixed before any interpretation; the protocol, the dataset and the models are unchanged. Hard negatives below are hard-negative-role sentences whose class is not CAPTURE_PERSON.

Dataset `phrases.jsonl` sha256 `b5ce90ed8b40ee79dc61012363dc0207d683829397a196c46b27b252c40b055b`, 320 sentences, 39 groups, leave-one-group-out. Encoders: B nomic (LaRuche memory) 768 dims, median 8.1 ms; S paraphrase-multilingual-MiniLM-L12-v2 384 dims, median 8.7 ms on CPU, about 734 MB added resident memory in this process.

## Under Paradigm's gate (what a reflex would act on): the pre-registered criterion

| representation | model | unseen positive recall under gate | same, excluding leaked twins | false fast paths (all / hard neg. / hard neg. excl. leaks / out of domain) | FFP per transformation: negation, temporal, past_question, object_change, inspection_only | hard-negative rejection | gate acc. pos / hard neg | coverage | sel. acc. (selector) | selector feasible | sel. acc. under gate | ECE | criterion vs lexical same model | criterion vs best lexical |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_lexical | prototype | 0.00 | 0.00 | 0 / 0 / 0 / 0 | 0, 0, 0, 0, 0 | 1.00 | 1.00 / 0.99 | 0.00 | 0.00 | False | 0.00 | 0.24 | False | False |
| A_lexical | knn3 | 0.26 | 0.26 | 4 / 4 / 4 / 0 | 1, 2, 1, 0, 0 | 0.98 | 1.00 / 0.99 | 0.22 | 0.76 | False | 0.76 | 0.13 | False | False |
| A_lexical | logreg | 0.00 | 0.00 | 0 / 0 / 0 / 0 | 0, 0, 0, 0, 0 | 1.00 | 1.00 / 0.99 | 0.00 | 1.00 | False | 1.00 | 0.10 | False | False |
| A_lexical | tree | 0.07 | 0.07 | 2 / 1 / 1 / 1 | 0, 1, 0, 0, 0 | 0.99 | 1.00 / 0.99 | 0.17 | 0.74 | False | 0.73 | 0.20 | False | False |
| B_nomic_laruche | prototype | 0.00 | 0.00 | 0 / 0 / 0 / 0 | 0, 0, 0, 0, 0 | 1.00 | 0.26 / 0.16 | 0.00 | 1.00 | False | n/a | 0.17 | False | False |
| B_nomic_laruche | knn3 | 0.09 | 0.09 | 1 / 1 / 1 / 0 | 0, 0, 0, 1, 0 | 0.99 | 0.26 / 0.16 | 0.30 | 0.89 | False | 0.94 | 0.09 | False | False |
| B_nomic_laruche | logreg | 0.00 | 0.00 | 0 / 0 / 0 / 0 | 0, 0, 0, 0, 0 | 1.00 | 0.26 / 0.16 | 0.00 | 1.00 | False | n/a | 0.10 | False | False |
| B_nomic_laruche | tree | 0.13 | 0.13 | 4 / 4 / 4 / 0 | 1, 0, 0, 1, 2 | 0.98 | 0.26 / 0.16 | 0.70 | 0.62 | False | 0.65 | 0.31 | False | False |
| S_paraphrase_minilm | prototype | 0.00 | 0.00 | 0 / 0 / 0 / 0 | 0, 0, 0, 0, 0 | 1.00 | 0.89 / 0.69 | 0.00 | 1.00 | False | 1.00 | 0.17 | False | False |
| S_paraphrase_minilm | knn3 | 0.52 | 0.52 | 5 / 5 / 5 / 0 | 0, 3, 0, 2, 0 | 0.97 | 0.89 / 0.69 | 0.62 | 0.93 | False | 0.94 | 0.04 | False | False |
| S_paraphrase_minilm | logreg | 0.00 | 0.00 | 0 / 0 / 0 / 0 | 0, 0, 0, 0, 0 | 1.00 | 0.89 / 0.69 | 0.00 | 1.00 | False | n/a | 0.22 | False | False |
| S_paraphrase_minilm | tree | 0.46 | 0.46 | 13 / 10 / 10 / 0 | 1, 4, 2, 2, 1 | 0.94 | 0.89 / 0.69 | 0.71 | 0.77 | False | 0.81 | 0.24 | False | False |
| A+B | prototype | 0.00 | 0.00 | 0 / 0 / 0 / 0 | 0, 0, 0, 0, 0 | 1.00 | 0.20 / 0.12 | 0.00 | 0.00 | False | n/a | 0.28 | False | False |
| A+B | knn3 | 0.04 | 0.04 | 0 / 0 / 0 / 0 | 0, 0, 0, 0, 0 | 1.00 | 0.20 / 0.12 | 0.29 | 0.86 | False | 1.00 | 0.09 | False | False |
| A+B | logreg | 0.00 | 0.00 | 0 / 0 / 0 / 0 | 0, 0, 0, 0, 0 | 1.00 | 0.20 / 0.12 | 0.00 | 1.00 | False | n/a | 0.13 | False | False |
| A+B | tree | 0.13 | 0.13 | 2 / 2 / 2 / 0 | 1, 0, 0, 1, 0 | 0.99 | 0.20 / 0.12 | 0.71 | 0.64 | False | 0.79 | 0.31 | False | False |
| A+S | prototype | 0.02 | 0.02 | 0 / 0 / 0 / 0 | 0, 0, 0, 0, 0 | 1.00 | 0.80 / 0.58 | 0.00 | 1.00 | False | 1.00 | 0.35 | True | False |
| A+S | knn3 | 0.37 | 0.37 | 4 / 4 / 4 / 0 | 0, 3, 1, 0, 0 | 0.98 | 0.80 / 0.58 | 0.43 | 0.93 | False | 0.93 | 0.05 | True | True |
| A+S | logreg | 0.00 | 0.00 | 0 / 0 / 0 / 0 | 0, 0, 0, 0, 0 | 1.00 | 0.80 / 0.58 | 0.00 | 1.00 | False | n/a | 0.16 | False | False |
| A+S | tree | 0.43 | 0.43 | 9 / 8 / 8 / 0 | 1, 2, 2, 2, 1 | 0.95 | 0.80 / 0.58 | 0.72 | 0.76 | False | 0.82 | 0.25 | False | False |

Leaked test sentences (identical text in another group): 8 of 320.

## Without the gate: classification

| representation | model | accuracy | recall CAPTURE_PERSON | predicted CAPTURE_PERSON on: negation, temporal, past_question, object_change, inspection_only |
|---|---|---|---|---|
| A_lexical | prototype | 0.47 | 0.67 | 6, 5, 4, 5, 3 |
| A_lexical | knn3 | 0.54 | 0.72 | 6, 14, 8, 9, 4 |
| A_lexical | logreg | 0.55 | 0.43 | 0, 3, 2, 2, 1 |
| A_lexical | tree | 0.54 | 0.30 | 5, 2, 2, 3, 2 |
| B_nomic_laruche | prototype | 0.57 | 0.76 | 8, 8, 6, 3, 1 |
| B_nomic_laruche | knn3 | 0.66 | 0.78 | 4, 6, 3, 4, 8 |
| B_nomic_laruche | logreg | 0.57 | 0.33 | 0, 1, 0, 1, 1 |
| B_nomic_laruche | tree | 0.57 | 0.52 | 3, 6, 6, 5, 3 |
| S_paraphrase_minilm | prototype | 0.66 | 0.80 | 4, 8, 7, 2, 1 |
| S_paraphrase_minilm | knn3 | 0.82 | 0.89 | 0, 7, 1, 2, 1 |
| S_paraphrase_minilm | logreg | 0.81 | 0.78 | 0, 6, 0, 2, 0 |
| S_paraphrase_minilm | tree | 0.66 | 0.59 | 4, 7, 4, 4, 2 |
| A+B | prototype | 0.53 | 0.67 | 4, 3, 5, 6, 1 |
| A+B | knn3 | 0.63 | 0.76 | 3, 9, 10, 7, 3 |
| A+B | logreg | 0.68 | 0.65 | 0, 2, 0, 2, 0 |
| A+B | tree | 0.57 | 0.57 | 2, 8, 6, 5, 2 |
| A+S | prototype | 0.64 | 0.85 | 3, 9, 4, 5, 0 |
| A+S | knn3 | 0.75 | 0.91 | 1, 7, 5, 5, 1 |
| A+S | logreg | 0.81 | 0.83 | 0, 4, 0, 2, 0 |
| A+S | tree | 0.65 | 0.59 | 4, 8, 4, 4, 2 |

## Per source, unseen positive recall under the gate (logistic regression)

| representation | gen_b | gen_a | synthetic_user_style |
|---|---|---|---|
| A_lexical | 0.00 | 0.00 | 0.00 |
| B_nomic_laruche | 0.00 | 0.00 | 0.00 |
| S_paraphrase_minilm | 0.00 | 0.00 | 0.00 |
| A+B | 0.00 | 0.00 | 0.00 |
| A+S | 0.00 | 0.00 | 0.00 |
