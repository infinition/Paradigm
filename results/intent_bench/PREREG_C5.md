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

## Outcome (written after the run, `RESULTS_C5.md`, `results_c5.json`)

Verdict under the pre-registered criterion: UNSUPPORTED. No region is certifiable; the certification thresholds are not touched.

Per region, under the gate, out of sample: R1 (actionable_now, 176 sentences, 98% of positives, 26% of hard negatives) selective accuracy 0.96, 2 hard-negative false fast paths. R2 (plus lexical and semantic agreement, 88 sentences, 61% of positives, 10% of hard negatives) 0.98, 1 false fast path, coverage 0.49 of the region, ECE 0.02. R3 (density) changes R1 by a few sentences at every percentile and leaves its verdict unchanged. R4 (agreement and density) equals R2 within a few sentences at every percentile: 0.98, 1 false fast path. The selector is infeasible in every region (best selective accuracy 0.98 against the 0.99 required).

Prediction 1 held (R1 keeps 26% of the hard negatives, mostly inspection_only and object_change, and is not certifiable). Prediction 2 held in direction (agreement raises selective accuracy from 0.96 to 0.98 at the cost of coverage, from 98% to 61% of the positives) and the criterion is not reached. Prediction 3 held (density changes almost nothing). Prediction 4 did not hold: no region is certifiable, R4 included.

What keeps R2 and R4 below the criterion is a single sentence: "Fais une photo de moi avec la webcam quand je te le dirai." (temporal hard negative, class OTHER), the only covered error inside the region and its only false fast path. It is one of the two `quand + future` clauses the frozen C4 extractor does not tag as FUTURE, so it enters `actionable_now`, both k-NNs agree it is a capture, and the fused model is unanimous. The region logic did what it was designed to do on everything else: inside R2 every other covered sentence is correct.

This is not turned into a correction here. A version 2 of the extractor that handles subordinate temporal clauses is a separate pre-registration, and its motivation is this observation, which the pre-registration will say. Whether such a version makes R2 certifiable is then a prediction to write before running, not a result to claim now.

Not done: no threshold change, no extractor change, no region added, no live run.
