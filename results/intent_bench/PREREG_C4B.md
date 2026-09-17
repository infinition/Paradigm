# Pre-registration C4b: subordinate temporal clauses and indirect questions in the extractor (final experiment of this benchmark line)

Written before the version 2 extractor is applied to any dataset. Offline only. Datasets version 1 and 2 unchanged. The version 1 extractor (`intent_temporal_fr.py`, `4b6b623`) stays as it is; version 2 is a separate module. No classifier, gate or threshold change beyond what the protocol below states. This is the last experiment on this benchmark line whatever its result; a synthesis of C1 to C7 and C4b follows, and the next work is a new architectural branch, not a further correction of this dataset.

## Motivation, stated plainly

The motivation is the errors already observed: in C4 the frozen rule missed "quand je te le dirai" and "quand j'aurai fini"; in C5 that miss was the single sentence keeping the agreement region below the criterion; in C7 the false fast paths that survive a permissive gate on version 2 are "quand je te dis go tu prends la photo" and "fait la photo une fois que j'ai fini". The rule below is nevertheless defined from French grammar, not from those sentences: it is written to cover the grammatical construction (a temporal subordinate that defers the main clause), and the sentences above are checked afterwards like any other.

## Extractor version 2, the changes and nothing else

1. FUTURE by temporal subordinate clause. A request whose main clause is deferred by a temporal subordinate is a deferral whatever the tense inside the subordinate: `quand`, `lorsque`, `dès que`, `une fois que`, `après que`, `aussitôt que`, `sitôt que`, `au moment où`, `le jour où` followed by a clause (subject and verb), in any tense, including the present ("quand je te dis go") and the compound past used prospectively ("une fois que j'ai fini"); `attends que`, `attends de`, `attends d'`, `attends avant de`, `avant de` followed by an infinitive in an imperative context ("attends avant de prendre la photo"); `après` followed by a clause or an infinitive ("après que j'aurai terminé", "après avoir fini"). Exception, from grammar: `quand` in an interrogative ("quand est-ce que", "c'est quand") is a question about time, not a deferral, and is left to the other rules. The version 1 FUTURE markers stay.
2. CONDITIONAL only for real conditions. `si` introduces an indirect question, not a condition, when it directly follows a verb of perception, verification or saying (`regarde si`, `vérifie si`, `dis-moi si`, `indique-moi si`, `check si`, `sais si`, `voir si`, `savoir si`, `test si`, `teste si`, `tu peux voir si`, `est-ce que` before `si` is not affected). Those are not CONDITIONAL; `si` at the start of the sentence or after a comma, and `si jamais`, remain CONDITIONAL.
3. Everything else is version 1, verbatim: PAST_REFERENCE, NOW, negation, `actionable_now`, the 7-dimensional block.

The module is implemented from this text, unit-tested on grammar sentences that appear in neither dataset, committed, and only then applied to versions 1 and 2. Its outputs are reported first (category counts per transformation, and the differences with version 1 sentence by sentence).

## What is run, in order

1. The C4 protocol on version 1: `A+S+T_v1` against `A+S+T_v2`, same four models, same folds, same gate and selector, same criterion (hard-negative false fast paths fall, unseen positive recall does not fall, per model).
2. The C7 gate grid, exploratory, with `A+S+E_RERANK+T_v2`: the classifier of the C6R configuration refitted (leave-one-group-out on version 1 for the version 1 numbers, all of version 1 for the version 2 numbers), threshold by the same rule, gates G0, G1, G2, G3-exp, G4 as in C7. This is not the frozen C6R model, since T changed; it is labeled a refit throughout.
3. Stop.

## Predictions

1. On version 1, the temporal false fast path of `A+S+T` with k-NN (1) disappears and the C5 blocker sentence leaves `actionable_now`; the inspection_only sentences tagged CONDITIONAL (16) become UNSPECIFIED.
2. On version 2 under G2 and G3-exp, the two temporal false fast paths disappear; the CHECK_CAMERA sentence read as a capture request remains, so the selective accuracy under a permissive gate rises but stays below 0.99.
3. No gate meets the grid on both versions; the reason is no longer the extractor but the refit classifier's accuracy on version 2 and the gates' behavior under distribution shift. This is written as the expected closing result of the line.

## Not done

No live run, no dataset change, no gate or threshold change, no further correction after this experiment.

## Outcome (`RESULTS_C4B.md`, `results_c4b.json`); the line stops here

Extractor version 2 on the datasets, reported first. Version 1: temporal negatives 37 of 37 FUTURE (35 before), the 16 inspection_only sentences tagged CONDITIONAL by the indirect-question misfire are now UNSPECIFIED, the C5 blocker sentence leaves `actionable_now`; 23 sentences change, all in those two directions. Version 2: temporal negatives 26 of 30 FUTURE (19 before), including the two C7 false fast paths and "attends avant de prendre la photo"; conditional 13 of 17 CONDITIONAL (11 before); 14 sentences change. The four temporal negatives still not FUTURE on version 2 are deferrals without a subordinate marker ("Attends que je sois revenu" is now covered; the remaining ones use other constructions), left as they are.

Prediction 1 held. Prediction 2 held: on version 2 under every gate the hard-negative false fast paths are 0, the temporal ones included; the CHECK_CAMERA sentence read as a capture remains the single false fast path, and selective accuracy under the permissive gates rises from 0.85 to 0.87 to 0.88 to 0.90, below 0.99. Prediction 3 held: no gate meets the grid on both versions.

The C4 protocol on version 1 does not credit version 2 of the extractor: with k-NN the temporal false fast path disappears (1 to 0) but an inspection_only one appears (0 to 1), because the inspection sentences the misfire kept out of `actionable_now` are now inside it and the classifier fires on one of them; hard-negative false fast paths 2 to 2, recall 0.46 to 0.46, criterion not met for any model. The correction is right on the grammar and neutral on this protocol: it removes a false protection (the misfire) as well as a real error.

On version 1 out of fold, the class-conditional gate G1 meets the grid with the refit classifier and version 2 features: selective accuracy 1.00, 0 false fast paths of any kind, coverage 0.81, positive reflex coverage 0.83 (0.76 in C7). On version 2 the picture of C7 is unchanged in structure: G1 accepts nothing, the permissive gates transport 0.70 of the positives at 0.88 to 0.90 selective accuracy, and the residual error is no longer temporal.

Closing reading of the line. The grammatical hypothesis is closed: with the subordinate clauses covered, deferrals no longer produce false fast paths on either dataset. What remains is not a rule: a classifier at 0.81 to 0.90 accuracy on phrasings written by other generators, and a gate that either refuses them or admits its errors. No further correction of this dataset is made.
