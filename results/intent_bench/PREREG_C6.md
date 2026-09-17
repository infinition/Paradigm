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
