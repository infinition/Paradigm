# Pre-registration: C2, the memory embedding of LaRuche as goal representation (offline)

Written before any classifier is trained. Offline only, on the frozen run C1 record and on pre-declared unseen phrasings. No live run. No new model, no fine-tuning: the encoder is the one LaRuche already runs for its memory, frozen. No change to thresholds, gates, certification, outcome contract or the C1 data.

## The encoder LaRuche already has, as inspected

`nomic-embed-text-v1.5` (Q8_0 GGUF, 146 MB, from the LaRuche profile), served by the integrated `llama-server` (`laruche-local`, role `embeddings`; the Homebrew build is the one detected here), 768 dimensions, L2-normalized output, `/v1/embeddings` OpenAI-compatible route, the same `HttpEmbedder` the memory uses. LaRuche adds no nomic task prefix. Resident whenever the node runs (started at boot when the memory uses the local engine); not resident in the headless demo. Measured here: 219 MB RSS for the server, median 19 ms per sentence, 194 ms on the first call. The memory's own calibration of this model: unrelated 0.413, paraphrase 0.878 cosine. Additional memory for Paradigm when the node runs: zero; when it does not: the server above.

Measured before any training, raw cosine on the C1 phrasings plus "Fais-moi un portrait": positives among themselves 0.81 on average; N4 ("Ouvre la caméra sans prendre de photo") sits at 0.81 to 0.86 from every positive; for P4 the nearest sentence is N3 (0.89), closer than any positive. The retrieval embedding groups by topic.

## Hypothesis

The gap observed in C1 at the first decision may come from the lexical representation of the goal. The semantic representation LaRuche already computes may give Paradigm enough to generalize across natural phrasings without adding a model, or it may group by topic and fail on hard negatives. C2 decides which.

## Representations

- A. lexical, as `GenericStateEncoder` hashes goal words today;
- B. embedding: the LaRuche encoder, raw, as the memory calls it;
- B'. the same encoder with nomic's documented `classification:` task prefix (a zero-cost variant, no new model, not what the memory does; reported separately);
- C. A concatenated with B.

## Models behind each representation

Nearest prototype by cosine, k-NN (k = 3), logistic regression, and the decision tree Paradigm uses. No MLP unless the simple models manifestly cannot use the features. Encoder frozen.

## Data

The 48 phase-1 missions of run C1 (mission id, request text, teacher's first action at `start` from the buffer). Two targets, both reported: T1, the teacher's literal first action (what certification scores today: `capture`, `capture index 0`, `list`, other); T2, the mission's intent under the outcome contract (capture required or forbidden), which is what a false fast path is defined against.

Unseen phrasings, never in C1, fixed here: positives "Fais-moi un portrait.", "Capture une image de moi avec la caméra.", "Je veux une photo de moi maintenant."; hard negatives "Allume la caméra sans capturer.", "Liste les caméras disponibles.", "Combien de photos ai-je prises hier ?", "Vérifie que la webcam fonctionne, sans photo.". Their labels are T2 only (no teacher ran them).

## Evaluation

Seen wording: leave-one-mission-out over the 48 missions (identical strings recur, so this measures little more than memorization; reported for completeness). Unseen wording: leave-one-phrasing-out over the 9 C1 phrasings, plus the 7 unseen phrasings above scored by models trained on all 48 missions. Split into positive seen, positive unseen, negative seen, negative unseen (hard).

Metrics: coverage and selective accuracy at the threshold Paradigm's selector would pick (same rule, same floors), ECE, false fast paths (a confident capture prediction on a negative), recall on unseen positives, OOD fallback on unseen negatives with the Mahalanobis gate as Paradigm fits it, encoding latency, additional memory.

## Criterion

B, B' or C is better than A only if coverage rises on unseen positive phrasings without any increase in false fast paths on the semantically close negatives. If the memory embedding fails the hard negatives, it is not replaced here; the result is documented and a specialized sentence or intent encoder is a separate experiment.

## Not done

No live run. No change to the encoder in the product. No fine-tuning. No threshold change.
