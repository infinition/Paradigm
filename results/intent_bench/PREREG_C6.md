# Pre-registration C6: the relation between the goal and a candidate action (offline)

Written before any score. Offline only, no live run, no fine-tuning, no threshold or gate change, dataset version 1 unchanged, extractor of C4 unchanged. Same leave-one-group-out folds, models, gate and selector as C3 to C5.

## Hypothesis

Paradigm should not only represent what a sentence means; it should measure the relation between the sentence and a candidate action. Two levels of result, pre-declared:

- H1, representation: `goal x action` improves the recall of unseen positives under the gate without raising the hard-negative false fast paths, against goal-only representations (A+S and A+S+T).
- H2, certification: with `goal x action`, a pre-defined region of C5 (R1 to R4, unchanged) satisfies Paradigm's existing criterion.

H1 may hold while H2 does not; both are reported.

## Action contracts, frozen here, in French like the premises

```text
camera.capture   "L'utilisateur demande qu'une photo de lui soit prise maintenant."
camera.list      "L'utilisateur demande de vérifier la présence, la disponibilité ou le fonctionnement d'une caméra, sans prendre de photo."
camera.preview   "L'utilisateur demande de montrer l'image d'une caméra maintenant, sans enregistrer de photo."
photos.find      "L'utilisateur demande de retrouver des photos déjà existantes."
screen.capture   "L'utilisateur demande une capture de l'écran ou d'une fenêtre maintenant."
```

`OTHER` is the absence of any entailed contract; it has no contract of its own.

## Scorers, named and fixed here; both frozen

- `E_NLI`: `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`, zero-shot NLI. For each sentence (premise) and each contract (hypothesis): `P(entailment)` and `P(contradiction)` from the softmax over the three labels; `neutral` stays implicit. 10 dimensions.
- `E_RERANK`: `Qwen/Qwen3-Reranker-0.6B`, one score per contract, obtained by the model's documented procedure: the instruction below, the sentence as query, the contract as document, and the score is the probability of the "yes" token against "no" at the last position, as in the model card. 5 dimensions. Instruction, fixed: "Indique si l'action candidate doit être exécutée maintenant d'après la demande de l'utilisateur. Une demande au futur, une question sur le passé, une négation ou une simple demande d'observation n'autorisent pas l'exécution." No prompt or parsing change after the first results.

Both run locally on CPU (or on the RTX box through Ollama-free transformers if it is reachable; same weights either way). Latency and resident memory reported.

## Representations

`E_NLI`, `E_RERANK`, `A+E_NLI`, `S+E_NLI`, `A+S+E_NLI+T`, and the same three combinations with `E_RERANK`. `E` alone is kept deliberately, to know whether the relation can replace part of the feature stack, not only complement it. Baselines: `A+S` and `A+S+T` from C4, recomputed in the same run.

## Evaluation

As in C3 and C4: k-NN (3), logistic regression, tree, prototype; the Mahalanobis gate refitted on the training fold for each representation; the selector unchanged; no calibration specific to C6. H1 criterion, verbatim: unseen positive recall under the gate rises and hard-negative false fast paths do not rise, against `A+S+T` with the same model, and against `A+S` with the same model; both reported. H2: the C5 regions R1 to R4 (density at p90, p95, p99) evaluated with the fused k-NN on `A+S+E+T` for each scorer, same criterion as C5, unchanged.

Also reported: the raw scores of the two scorers on the four decisive sentence types, before any classifier: "Prends-moi en photo." (entailment expected), "Ne me prends pas en photo." (non-entailment expected), "Tu m'as pris en photo tout à l'heure ?" (non-entailment expected), and "Fais une photo de moi avec la webcam quand je te le dirai." (non-entailment expected: the entailment of `camera.capture` must fall enough not to authorize the action; contradiction or neutral are both acceptable). This last sentence is the one C4 and C5 fail on, without any grammatical rule dedicated to it.

## Predictions

1. On negation and past questions, `E` alone matches or exceeds `S+T`.
2. On the subordinate deferral above, both scorers give non-entailment of `camera.capture` where the frozen extractor fails.
3. On inspection_only and object_change, open question, written as such.
4. H2: open; if any region becomes certifiable it is R2 or R4 with `A+S+E+T`.

## Not done

No live run, no fine-tuning, no gate or threshold change, no contract or instruction change after the first scores, no extractor revision.

## Outcome (written after the run, `RESULTS_C6.md`, `results_c6.json`, scores cached in `results_c6_scores.json`)

Raw scores first, as pre-registered. The zero-shot NLI does not do what the contracts ask: `camera.capture` entailment averages 0.18 on the positives (17% above 0.5) and 0.31 on past questions, higher than on the positives; on "Prends-moi en photo." it is 0.00 (neutral). The reranker follows the topic: 0.98 on the positives, and 0.47 to 0.62 on every hard-negative type, including 0.82 on "Ne me prends pas en photo.", 0.98 on the past question and 0.98 on "Fais une photo de moi avec la webcam quand je te le dirai." Prediction 2 did not hold: neither frozen scorer refuses the deferral on its own; prediction 1 did not hold for the NLI. As relation scorers, both measure relevance, not executability, under the frozen contracts and instruction.

H1, representation: SUPPORTED for the full stack with the reranker, not for the relation alone. `E` alone is below `A+S+T` for both scorers. `A+S+E_RERANK+T` with k-NN: unseen positive recall 0.50 against 0.46, hard-negative false fast paths 2 against 2 (criterion met against `A+S+T` and against `A+S`); with logistic regression: recall 0.33 against 0.00, 0 false fast paths. The NLI block adds nothing to `A+S+T` (k-NN 0.46 / 2, unchanged).

H2, certification, as pre-registered (the C5 regions with the fused k-NN): UNSUPPORTED. No region is certifiable for either scorer; the agreement regions reach 0.98 with one hard-negative false fast path, the same subordinate deferral as in C5.

An observation outside the pre-registered H2, reported as such and not claimed: with `A+S+E_RERANK+T` and logistic regression, Paradigm's whole-family selector is feasible for the first time in this benchmark line: selective accuracy 0.995 at coverage 0.58 of the sentences (six classes; the OTHER class, 48% of the dataset, is the easy part of that coverage), and under the gate 28% of the sentences fire with selective accuracy 1.00 and 0 false fast paths, 15 of 46 positives among them (7 Claude, 4 ChatGPT, 4 user-style). The deferral sentence is predicted CAPTURE_PERSON with confidence 0.75 against a selector threshold of 0.785: it is excluded by a margin of 0.035, not by understanding; a small change of the training folds could move it. This feasibility is therefore a candidate result for a confirmation on new sentences written after this run, pre-registered on its own, not a result of C6.

Costs, for the record: NLI 837 ms and reranker 1085 ms per sentence for five contracts on CPU; about 0.9 GB and 3.6 GB resident respectively. Nothing in these numbers is compatible with a per-decision call in the product on this machine; the RTX would change the latency, not the conclusion on what the scorers measure.

Not done: no fine-tuning, no contract or instruction change, no threshold change, no live run.
