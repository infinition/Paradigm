# Pre-registration C4: explicit temporality and actionability features (offline)

Written before the extractor is applied to the dataset. Offline only, no live run, no fine-tuning, dataset version 1 unchanged (`DATASET_SHA256.txt`), same models, same gate, same thresholds, same leave-one-group-out protocol as C3.

## Hypothesis

Adding an explicit representation of temporality and actionability to the goal improves the rejection of deferred requests without reducing semantic generalization on immediate requests.

## Comparison, and nothing else

`A+S` (lexical + `paraphrase-multilingual-MiniLM-L12-v2`, as in C3) against `A+S+T`, where T is the feature block below. Two pre-declared weightings of T in the concatenation, since k-NN distances are dominated by the 384 dimensions of S: T as is (values 0 or 1), and T scaled by 4. Both are reported; neither is chosen afterwards.

## The extractor, defined from French grammar, not from the dataset

Deterministic rules on the lowercased sentence with accents kept or stripped alike. Categories, in priority order when several markers occur:

1. `PAST_REFERENCE` if the sentence contains a compound past or pluperfect of the second or first person (`tu as`, `t'as`, `ta` before a past participle in `-é`, `-i`, `-u`, `-is`, `-it`; `tu avais`, `t'avais`, `j'avais`, `tu m'as`, `tu m'avais`, `tu l'avais`), an imperfect of a state verb (`marchait`, `était`, `fonctionnait`, `yavait`, `y avait`), or the adverbs `hier`, `déjà`, `avant` used as a final adverb or before `?`. The phrase `tout à l'heure` / `tout a l'heure` is resolved by the tense of the verb: past when a marker above is present, future otherwise.
2. `CONDITIONAL` if the sentence contains `si ` followed by a clause with a verb of the request, `au cas où`, or `quand tu pourras`.
3. `FUTURE` if the sentence contains a future simple of the second person (`-ras`, `-eras`, `-iras`, `-dras` verb endings, including misspelled `-ra` after `tu`), an adverb of deferral (`demain`, `ce soir`, `ce matin` when combined with `demain`, `plus tard`, `après` as a final adverb or before punctuation, `ensuite`, `pas maintenant`, `tout à l'heure` without a past marker), `dans` followed by a duration (`dans cinq minutes`, `dans 10 min`, `dans une heure`), or `quand` followed by a future or a future perfect (`quand je te le dirai`, `quand j'aurai fini`, `quand elle sera chargée`).
4. `NOW` if the sentence contains `maintenant`, `tout de suite`, `là` as an adverb (`là maintenant`, sentence-final `là`), `vite fait`, `immédiatement`, `direct`.
5. `UNSPECIFIED` otherwise.

`negated`: the sentence contains `ne ... pas`, `n'... pas`, `pas de`, `pas d'`, `surtout pas`, `jamais`, `aucun`, `aucune`, or an imperative negation without `ne` (`prends pas`, `fait pas`, `fais pas`, `cherche pas`, `touche pas`, `regarde pas`, `montre pas`, `ouvre pas`, `test pas`, `teste pas`, `capture pas`, `utilise pas`, `va pas`). `sans` is not a negation marker: "sans prendre de photo" is a scope the semantic encoder already separates.

`actionable_now` = temporal is `NOW` or `UNSPECIFIED`, and not `negated`, and not `PAST_REFERENCE`.

Feature block T: one-hot of the five temporal categories, `negated`, `actionable_now`; 7 dimensions.

The extractor is implemented exactly as written here, unit-tested on grammar examples that are not dataset sentences, committed, and only then applied to `phrases.jsonl`. Its outputs on the dataset are reported in full (category counts per transformation) before the classifier results.

## Metrics and criterion

Same as C3, under the gate: unseen positive recall, false fast paths on hard negatives (class not `CAPTURE_PERSON`), per transformation, selector feasibility, and without the gate. Pre-registered prediction: with T, the false fast paths on `temporal` and `past_question` negatives fall, and the unseen positive recall on immediate positives does not fall. The criterion, verbatim: `A+S+T` is better than `A+S` only if the hard-negative false fast paths fall and the unseen positive recall does not fall, for the same model. If no model satisfies it, UNSUPPORTED.

## Not done

No gate or threshold change, no live run, no change to the dataset, no selection of a weighting after the fact.

## Outcome (written after the run, `RESULTS_C4.md`, `results_c4.json`)

Verdict under the pre-registered criterion: SUPPORTED, for k-NN and for the tree; not for the prototype and logistic regression, whose recall under the gate is zero with or without T (the selector's threshold sits above every confidence they produce).

Extractor on the dataset, reported before the classifiers: 35 of 37 temporal negatives tagged FUTURE (the two misses are `quand + future` clauses the `quand` rule did not match: "quand je te le dirai", "quand j'aurai fini"); 37 of 37 past questions tagged PAST_REFERENCE; 35 of 37 negation negatives tagged negated (the two misses are the two "negation" hard negatives whose class is CAPTURE_PERSON, that is, sentences that remove the "sans photo" restriction and are not negations); 45 of 46 positives actionable_now (the miss is "cherche pas les anciennes prends moi en photo maintenant", where the imperative-negation rule fires on "cherche pas"). One misfire to record: 16 of 37 inspection_only sentences are tagged CONDITIONAL because the `si ` rule matches the indirect question ("regarde si la caméra marche"), which is not a conditional; the rule was frozen and is left as is, and the effect is visible in the results (inspection_only false fast paths do not fall).

Under the gate, k-NN: unseen positive recall 0.37 to 0.46, hard-negative false fast paths 4 to 2, temporal 3 to 1, past_question 1 to 0, object_change 0 to 1, coverage 0.43 to 0.66, selective accuracy 0.93 to 0.96, ECE 0.05 to 0.06. Tree: recall 0.43 to 0.59, false fast paths 8 to 3, temporal 2 to 1. Without the gate, logistic regression: accuracy 0.81 to 0.89, CAPTURE_PERSON predicted on 4 temporal negatives to 1 and on 0 past questions. The weighting of T (1 or 4) makes no difference for k-NN and the tree and degrades the prototype; nothing is chosen.

Prediction held: the temporal and past-reference false fast paths fell and the recall on immediate positives rose rather than fell. The remaining temporal false fast path under k-NN and the two `quand` misses are the same phenomenon: a deferral expressed by a subordinate clause, which the frozen rule covers only partially.

What does not change: Paradigm's selector remains infeasible for every configuration (best: selective accuracy 0.96 at coverage 0.66 with k-NN). No first-decision family would be certified as it stands. This is the input of C5: whether a region of `start` defined independently of the confidence becomes certifiable with these features available.

Not done: no gate or threshold change, no dataset change, no live run, no extractor revision after seeing the misses.
