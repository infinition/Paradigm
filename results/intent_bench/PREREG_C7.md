# Pre-registration C7: language-aware trust gating (exploratory, v1 and v2 known)

Written before any gate other than the current one is scored. Offline only. Exploratory by construction: version 2 has been scored once by the frozen C6R model, so nothing found here is confirmed; C7 ends with at most one gate named and frozen for C7R, which is a separate pre-registration on a version 3 written afterwards.

## What is fixed

The decision model is the frozen C6R model (`c6r_frozen_model.sha256`): the same logistic regression on `A+S+E_RERANK+T`, the same threshold 0.6179 by the same rule. Only the acceptance gate changes. Every difference between gates is therefore attributable to the gate. No threshold, selector or training change.

## Gates

Three questions, kept distinct:

```text
G0, G1, G2   "does this state resemble a known region?"           (geometry)
G3           "is the uncertainty of this decision calibrated?"    (predictive uncertainty)
G4           "known region AND procedurally allowed now?"         (geometry and actionability)
```

- G0: the current gate, Mahalanobis with Ledoit-Wolf shrinkage on standardized features, quantile 0.997 of the training scores, fitted on the fused features of the 320 version 1 sentences. Baseline.
- G1: class-conditional Mahalanobis. One gate per class, fitted on the version 1 sentences of that class with exactly the same standardization, shrinkage and quantile as G0; a sentence is accepted if it passes the gate of the class the frozen model predicts. Rule fixed now for small classes: a class with fewer than 20 version 1 sentences has no gate and its predictions are never accepted (all six classes have at least 24 in version 1, so the rule is written for completeness and for version 3).
- G2: local density in S alone. Mean Euclidean distance to the k = 3 nearest version 1 sentences in the paraphrase embedding; accepted if at most the p-th percentile of the same quantity over version 1 (each sentence against its 3 nearest others), p in {90, 95, 99}, all three reported, none selected here.
- G3-exp: predictive-uncertainty gate, exploratory only. Nonconformity score 1 minus the probability of the predicted class. Because the frozen model has seen all of version 1, no calibration on version 1 is independent; G3-exp therefore uses the out-of-fold probabilities of the same configuration from C6 (leave-one-group-out, a model that is not the frozen one) to set the acceptance threshold at the 1 minus alpha quantile of out-of-fold nonconformity, alpha in {0.05, 0.10}, both reported, and applies that threshold to the frozen model's probabilities on version 2. This is explicitly not a conformal guarantee; it is a transported uncertainty threshold, and it is labeled as such everywhere.
- G4: G1 and `actionable_now` (the C4 feature).

## Measured, on version 1 out of sample (with the C6 out-of-fold predictions) and on version 2 (with the frozen model)

Per gate: acceptance of positives, acceptance of hard negatives, coverage under the gate, selective accuracy under the gate, hard-negative false fast paths, positive reflex coverage, by source and by transformation. Paradigm's criterion (selective accuracy at or above 0.99, 0 hard false fast paths, coverage) is the reading grid, not an optimization target: no gate parameter is tuned on version 2.

## What C7 may and may not conclude

C7 may say which question (geometry, uncertainty, or geometry and actionability) transports better from version 1 to version 2 and why. It may name at most one gate, with its parameters fixed, for C7R. It may not declare any gate confirmed, since version 2 is not new.

## Provisions for C7R, written now

If G3 is the gate named for C7R, a calibration set distinct from versions 1, 2 and 3 must exist before version 3 is scored (or version 3 is split into calibration and test before any score is seen), so that the calibration is independent of the training data; otherwise "conformal" would mean a threshold on in-sample confidence. If a geometric gate is named, its parameters are those reported here, unchanged.

## Scope note, explicit

A gate that wins on language is not automatically a candidate to replace Paradigm's global gate. Its effect on tool states and on the historical certifications must be tested separately on run 11, run 12 and C1 before any change to the engine. Nothing in C7 or C7R modifies the engine.

## Predictions

1. G0 on version 2: acceptance of positives 0.14 (C6R), the baseline to beat.
2. G1 raises acceptance of positives on version 2 above G0 without raising hard-negative false fast paths above 0, because the CAPTURE_PERSON region of version 1 is tighter than the global one.
3. G2 in S alone accepts more of version 2 than G0 at p95 and p99, and lets in more hard negatives without the gate on T; G4 is the combination that keeps them out.
4. G3-exp transports coverage better than the geometric gates at alpha 0.10 and worse at 0.05; whether it keeps false fast paths at 0 is the open question.
