# Pre-registration C6R: prospective replication of the one selector-feasible configuration (offline)

Written before any sentence of dataset version 2 exists. Offline only, no live run, no fine-tuning, no threshold or gate change.

## The frozen configuration

Trained once on the whole of dataset version 1 (320 sentences, `DATASET_SHA256.txt`), then frozen and hashed, before version 2 is written:

```text
representation = A (lexical, GenericStateEncoder) + S (paraphrase-multilingual-MiniLM-L12-v2) + E_RERANK (Qwen3-Reranker-0.6B, the five frozen contracts and instruction of C6) + T (C4 extractor, weight 1)
classifier     = logistic regression (max_iter 3000, C 1.0), fitted on all 320 sentences
threshold      = Paradigm's selector rule applied to the classifier's probabilities on the 320 training sentences (tolerance 0.01, minimum coverage 0.55); the rule is pre-registered, its value is recorded in the frozen artifact, whatever it is
gate           = Mahalanobis, quantile 0.997, fitted on the 320 training feature vectors
```

Artifact: `c6r_frozen_model.pkl` with `c6r_frozen_model.sha256`, committed before `phrases_v2.jsonl`. Version 2 is used for nothing but one scoring pass: no training, no calibration, no second attempt with another threshold, no model selection.

## Dataset version 2

Same six classes, roles and five transformations as version 1, plus: `conditional` (unambiguous), `long` (sentences of 15 words or more), `oral` (typos, abbreviations, spoken turns), and `ambiguous` (a sentence that admits more than one reading, given an assigned class anyway). Three sources, provenance in `MANIFEST_v2.md` with the same honesty as version 1. Written after this file and after the frozen artifact, by people or models that have seen no score of the frozen model on any of their sentences. Frozen and hashed (`DATASET_v2_SHA256.txt`) before the reranker scores are computed on it.

Two pre-declared slices:

```text
PRIMARY     immediate positives, negation, future or deferral, past, unambiguous conditional, inspection only, object change, long, oral
DIAGNOSTIC  ambiguous
```

## The single question, and its criterion

On the PRIMARY slice of version 2, among the sentences the frozen classifier covers at the frozen threshold and the frozen gate accepts:

```text
selective accuracy >= 0.99
hard-negative false fast paths = 0     (hard negatives: hard-negative-role sentences whose class is not CAPTURE_PERSON)
coverage of the slice >= 0.15
```

All three hold: REPLICATED. Any one fails: NOT REPLICATED. No second run.

Reported alongside, not as criteria: the positive reflex coverage (how many CAPTURE_PERSON requests of the slice fire correctly, and how many fire wrongly), per transformation and per source; the same numbers on the DIAGNOSTIC slice; the version 1 reference values of the frozen model under the same gate (recorded in the artifact); and the raw reranker scores on version 2 by sentence type.

## Predictions

1. Coverage of the PRIMARY slice between 0.15 and 0.35 (version 1 under the gate: about 0.28).
2. Selective accuracy at or above 0.99 on the covered PRIMARY sentences, 0 hard-negative false fast paths.
3. The weakest transformation is future or deferral by subordinate clause; if a false fast path appears, it is there.
4. Positive reflex coverage between a fifth and a half of the immediate positives.

## Not done

No live run, no training on version 2, no threshold, gate or contract change, no model selection.
