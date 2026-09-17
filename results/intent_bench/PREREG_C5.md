# Pre-registration C5: is a pre-defined sub-region of `start` certifiable? (offline)

Written before any region is scored. Offline only, dataset version 1 unchanged, extractor of C4 unchanged (`4b6b623`), same leave-one-group-out folds, same gate (Mahalanobis, quantile 0.997, fitted on the training fold), same selector rule and same certification thresholds as Paradigm. Representation: `A+S+T` with T at weight 1, k-NN (3) for the fused prediction, as in C4. No live run.

## Question

A family that is not certifiable as a whole may contain a region, defined independently of the classifier's confidence and before any score is seen, that satisfies Paradigm's existing criterion. Does one of the four regions below?

## Regions, fixed here

```text
R1 = actionable_now
R2 = actionable_now AND pred_A == pred_S
R3 = actionable_now AND density_pass
R4 = actionable_now AND pred_A == pred_S AND density_pass
```

- `actionable_now` is the C4 feature (temporal NOW or UNSPECIFIED, not negated, not a past reference), computed on the sentence itself.
- `pred_A` is the prediction of a k-NN (3) trained on the lexical representation A alone; `pred_S` the prediction of a k-NN (3) trained on the paraphrase representation S alone; both trained on the training fold, computed independently of the fused model, never from it.
- `density_pass`: the mean Euclidean distance from the sentence to its 3 nearest training sentences in `A+S+T` is at most the p-th percentile of the same quantity computed over the training fold (each training sentence against its 3 nearest other training sentences). p is pre-declared as 90, 95 and 99; all three are reported, none is selected afterwards.

Every sentence is scored in the fold where its group is held out, so region membership and the fused prediction are both out of sample.

## Criterion, verbatim, unchanged

A region is certifiable if, restricted to its members and under the gate:

```text
selective accuracy at the selector's threshold >= teacher - 0.01   (the selector rule, minimum coverage 0.55 inside the region)
AND hard-negative false fast paths = 0
AND coverage > 0
```

with the selector applied to the region's members only (threshold chosen inside the region, same rule, same tolerance), the gate as fitted on the training fold, and hard negatives as in C3 (hard-negative-role sentences whose class is not CAPTURE_PERSON). If several regions satisfy it, none is declared better: coverage, selective accuracy, false fast paths and size are reported for each. If none does, C5 is UNSUPPORTED and the certification thresholds are not touched.

Also reported per region: size (share of all sentences, of positives, of hard negatives that fall in the region), the fused model's accuracy inside and outside the region, and the same numbers without the gate.

## Predictions

1. R1 removes the temporal and past-reference negatives from the region almost entirely (C4's extractor) but keeps the inspection_only and object_change ones, so R1 alone is not certifiable.
2. Agreement (R2) raises selective accuracy above 0.96 at a cost in coverage; whether it reaches the criterion is the open question.
3. Density alone (R3) mostly removes out-of-domain sentences that the gate already rejects and changes little.
4. If any region is certifiable, it is R4 at p90 or p95, with a coverage well below 0.5 of the positives.

## Not done

No threshold change, no region added after the fact, no live run.
