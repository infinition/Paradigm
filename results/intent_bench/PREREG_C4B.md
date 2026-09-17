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
