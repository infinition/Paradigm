# Pre-registration: intent generalization benchmark (offline)

Written before any embedding is computed. Offline only, no model call to any provider, no live run, no fine-tuning, no change to Paradigm's gate, thresholds or certification.

## Question

Does a semantic encoder let Paradigm generalize from natural language at the first decision, in the sense Paradigm needs: the gate accepts unseen positive phrasings while keeping semantically close hard negatives out?

## Classes

`CAPTURE_PERSON`, `CHECK_CAMERA`, `OPEN_CAMERA_NO_CAPTURE`, `FIND_EXISTING_PHOTOS`, `SCREENSHOT`, `OTHER`. `OTHER` holds deferred, negated or past-tense requests that call for no action now, and genuinely out-of-domain sentences (no image, no camera), which calibrate every encoder's noise floor.

## Dataset

`phrases.jsonl`, one sentence per line: `id`, `group`, `source`, `role`, `transformation`, `intent`, `text`. Three sources of roughly equal size, each written blind to every score: `gen_a`, `gen_b`, `user`. A group is one base sentence, its variants (same intent, rewordings), and its hard negatives obtained by minimal transformation of the base: `negation`, `temporal` (future or deferred), `past_question` (question about an action already done), `object_change` (same verb, another object), `inspection_only` (look or check without acting). Every hard negative carries the class it actually belongs to. Each group is written by one source. Once the three parts are in, the file is frozen: SHA-256 recorded in `DATASET_SHA256.txt` and committed before the first embedding is computed. Nothing is added, edited or removed afterwards; a later correction is a new version with a new hash and its own results.

## Split

By group, never by sentence: every sentence of a group is train or held-out together. Leave-one-group-out over all groups, so every group is held-out once and all its variants and hard negatives are unseen at the same time. Out-of-domain `OTHER` sentences form their own groups.

## Representations, named now

- A. lexical, as `GenericStateEncoder` hashes goal words today;
- B. `nomic-embed-text-v1.5` as LaRuche's memory calls it (raw, no task prefix), through the integrated `llama-server`;
- S. a specialized sentence encoder chosen here and not changed: `paraphrase-multilingual-MiniLM-L12-v2` (trained on paraphrase and NLI, multilingual including French), run locally with `sentence-transformers` on CPU; it is the smallest widely used paraphrase model, and paraphrase supervision is the closest available proxy for intent equivalence without fine-tuning;
- A+B and A+S, concatenations.

All encoders frozen. Latency and resident memory measured for B and S.

## Models

Nearest prototype (cosine), k-NN (3), logistic regression, Paradigm's decision tree (depth 8, min leaf 4). No MLP.

## Evaluation, per representation and model

Without the gate: accuracy, per-class recall, confusion between `CAPTURE_PERSON` and each hard-negative class. With the gate: the Mahalanobis gate as Paradigm fits it (quantile 0.997) on the training features; coverage and selective accuracy at the threshold Paradigm's selector picks (tolerance 0.01, minimum coverage 0.55); ECE; false fast paths (a covered, gate-accepted `CAPTURE_PERSON` prediction on a sentence of another class); recall of unseen positives (held-out `CAPTURE_PERSON` sentences that are covered, gate-accepted and correct); rejection of unseen hard negatives (held-out hard negatives not covered or not gate-accepted); the same per transformation type.

## Criterion

A representation is better than A only if the recall of unseen positive intents under the gate rises without any rise in false fast paths on hard negatives. The winner is not chosen on overall accuracy. If no encoder lets the gate accept unseen positives without admitting hard negatives, the conclusion is UNSUPPORTED, and the gate and its thresholds are not modified in this experiment.

## Predictions, written before the data

1. Without the gate, B groups by topic: its confusions concentrate on `inspection_only` and `object_change` negatives.
2. S separates `negation` and `past_question` better than B, and still confuses `inspection_only`.
3. Under the gate, every representation loses most unseen positives at 9-sentence scale (C2); with an order of magnitude more sentences, the gate accepts a non-zero fraction of unseen positives for S and B, and the question is whether hard negatives come in with them.
4. A does not generalize beyond shared word stems.

## Not done

No live run, no fine-tuning, no contrastive adaptation, no gate change.

## Addendum, before the first embedding

The three parts are three generators with distinct styles, not two models and a person: `gen_a-*` by generator A, `g*` by generator B, `u*` by generator B simulating the user's writing style (synthetic). No human-written sentence is in version 1; see `MANIFEST.md`. Four sentence texts occur in two groups of different sources; the dataset is frozen with them, and a leave-one-group-out fold can therefore contain a held-out text that also exists in training (4 of 320); this is reported, not corrected. The RTX box was unreachable from this Mac, so the specialized encoder runs locally on CPU with `sentence-transformers`, as the pre-registration allows.

## Outcome (written after the run, `RESULTS_v1.md`, `results_v1.json`)

Metric correction, before interpretation: the first execution counted hard-negative-role sentences whose class is CAPTURE_PERSON as false fast paths when predicted CAPTURE_PERSON; a counting bug, fixed, recorded in the results file. Protocol, dataset and models unchanged. Leakage: 8 of 320 sentences have an identical twin in another group (the four duplicate texts); excluding them from the test side changes no criterion metric.

Verdict under the pre-registered criterion: PARTIALLY SUPPORTED.

- Lexical baseline (A), best configuration: k-NN, unseen positive recall under the gate 0.26, 4 false fast paths on hard negatives.
- The specialized paraphrase encoder alone (S, k-NN) doubles the recall to 0.52 but adds one hard-negative false fast path (5): it fails the criterion as written, by one sentence.
- Lexical concatenated with the specialized encoder (A+S, k-NN) is the only configuration that satisfies the criterion: recall 0.37 against 0.26, hard-negative false fast paths 4 against 4, both against the same-model lexical baseline and against the best lexical one.
- The LaRuche memory embedding (B, and A+B) is worse than lexical under the gate: the Mahalanobis gate fitted on nomic vectors accepts only 26% of unseen positives (11% to 16% of hard negatives), so recall stays at or below 0.13. C2's conclusion stands, for an additional reason.

Where the errors are (false fast paths per transformation under the gate, S with k-NN: negation 0, temporal 3, past_question 0, object_change 2, inspection_only 0; without the gate S predicts CAPTURE_PERSON on 0 negations, 7 temporal, 1 past question, 2 object changes, 1 inspection). Prediction 1 held: nomic's confusions concentrate on inspection_only (8 with k-NN) and object_change. Prediction 2 held for negation and past_question and did not hold for inspection_only, which the paraphrase encoder handles; its remaining failure is temporal deferral ("prends-moi en photo demain"), which a paraphrase model treats as the same meaning. Prediction 3 held: with 320 sentences the gate accepts most unseen positives in lexical (1.00) and paraphrase (0.89) space, so the protection C1 got from the gate was a small-sample effect; in nomic space the gate stays closed (0.26). Prediction 4 held: lexical recall under the gate never exceeds 0.26 and its false fast paths spread over negation, temporal and past_question.

What none of this changes: Paradigm's own certification rule (selective accuracy within 0.01 of the teacher at coverage at least 0.55) is infeasible for every representation and model on this dataset; no configuration would be promoted as a first-decision reflex as it stands. A+S with k-NN reaches selective accuracy 0.93 at coverage 0.43.

Not done, as pre-registered: no gate or threshold change, no fine-tuning, no live run. The next question is not another encoder but the temporal transformation, and whether a certification rule can accept a first-decision family at 0.93 selective accuracy; both are separate pre-registrations.
