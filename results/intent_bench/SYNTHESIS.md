# From the camera run to the intent benchmark: what C1 to C4b established, and the question they leave

Every experiment below was pre-registered before it ran; the pre-registration files carry their outcomes, including the ones that did not hold. Numbers are those of the frozen records under `results/integration_laruche/` and `results/intent_bench/`.

## 1. Established

- A procedure on a physical tool is acquired from validated experience in a real agent (C1: LaRuche, DeepSeek, native `camera`). What activated was not the decision from language but the transition after a `camera list`: `capture`, 6 training and 3 held-out traces, 3 of 3, two reflexes executed and verified, 48 of 48 missions with a correct contract verdict but one teacher failure. With the camera removed, 8 of 8 missions fell back to the model with 0 camera executions.
- After activation the three negative controls that carry the camera concept (N2, N3, N4) put Paradigm in exactly the active family's state; the gate rejected all three. The protection came from the OOD gate on the request tokens, not from the tree: the family had no negative example, because a mission that ends after `list` ends with a control call Paradigm never observes.
- The lexical goal representation does not generalize beyond shared word stems (C3: recall of unseen positives under the gate at most 0.26, with false fast paths spread over negation, temporal and past).
- The memory embedding LaRuche already runs (`nomic-embed-text-v1.5`) groups by topic: "Ouvre la caméra sans prendre de photo" sits at 0.81 to 0.86 cosine from every positive, inside the model's own paraphrase band (C2), and under Paradigm's gate it is worse than lexical (C3: the gate fitted in nomic space accepts 26% of unseen positives).
- A specialized paraphrase encoder (`paraphrase-multilingual-MiniLM-L12-v2`) helps and does not suffice: alone, recall 0.52 with one more false fast path than lexical; concatenated with lexical, the only configuration of C3 meeting the pre-registered criterion (0.26 to 0.37, false fast paths 4 to 4). It separates negation, past questions and inspection-only; its failure is temporal deferral, which a paraphrase model treats as the same meaning.
- Seven deterministic dimensions of temporality and actionability (C4) raise recall and lower false fast paths at once (k-NN 0.37 to 0.46, 4 to 2; tree 0.43 to 0.59, 8 to 3). Immediate executability is a property the encoders do not carry and that costs nothing to represent explicitly.
- The relation between the goal and a candidate action (C6) adds signal in combination (A+S+E+T with k-NN, 0.46 to 0.50 at constant false fast paths; with logistic regression, from 0.00 to 0.33 at 0) and not alone; the zero-shot NLI is unusable for the contracts as written, and the instruction-aware reranker follows the topic (0.98 on "Ne me prends pas en photo", 0.98 on a deferral).
- A class-conditional Mahalanobis gate (C7, G1) is the first gate of the line meeting Paradigm's reading grid out of sample on version 1: selective accuracy 1.00, 0 false fast paths, coverage 0.79 (0.81 with the version 2 extractor).

## 2. Closed

- Probe-only re-certification as pre-registered: a single fresh held-out trace still dominated an otherwise passing probe set (run 11 point 24). The subsequent sensitivity study changed evidence routing across `m` in {1, 2, 3, 5, 8} and no candidate-level decision.
- The grammar of deferrals: with subordinate temporal clauses covered by a rule written from grammar (C4b), deferrals produce no false fast path on either dataset. The correction is neutral on the C4 protocol, since it also removes a false protection (indirect questions wrongly tagged conditional).
- Trusted sub-regions defined by agreement or density (C5): they raise selective accuracy to 0.98 and none is certifiable; the single blocker was the deferral sentence C4b now covers.
- Language-aware gates on this benchmark (C7, C4b): no gate satisfies safety and coverage together on both dataset versions; C7R was not opened on a gate.

## 3. Not replicated, and why

The one configuration whose selector was feasible on version 1 (A+S+E_RERANK+T, logistic regression, C6) did not replicate prospectively on version 2 (C6R): coverage 0.08 against 0.15 required, selective accuracy 0.89 against 0.99, false fast paths 0. The safety of the CAPTURE action transferred better than the coverage and than the general classification (0.81 without the gate). The gate fitted on 320 sentences accepted 14% of the new ones; the classifier covered 78%. The failure is the modeling of the language distribution by the gate under a shift of generators and phrasing length, the same behavior as in C1 and C2 at a larger scale: what Paradigm does for tool states, where variability is bounded, does not transpose as such to language, where it is not.

## 4. What the line makes explicit

Three properties were conflated at the start and are now measured separately:

```text
semantic similarity        what the encoders carry; groups by topic
procedural intent          the class of action the request calls for; what the classifier learns
immediate executability    now or not now; what T represents and what no encoder or scorer carried on its own
```

and a fourth sits above them, unchanged since run 11: authorization, which Paradigm grants per family from verified evidence, never from capability.

Two structural limits of the evidence are recorded: control calls (finishing a mission) are never observed, so a family that ends there has no negative examples; and identical requests recur in a benchmark while a product sees each phrasing once, which is why the gate's behavior under distribution shift is the quantity that matters.

## 5. The question that opens the next branch

The line is stopped here, not for lack of gains but because each further correction explains the same failure from another angle, and continuing would optimize one dataset. The next question is general to Paradigm:

> Can Paradigm learn, from validated experience, a procedural representation conditioned on the action, that generalizes to new phrasings while separating "relevant action", "action executable now" and "authorized action", without domain-specific linguistic rules?

```text
validated experience
(goal, state, candidate action, verified outcome)
              |
learned procedural representation
              |
does this action apply here, now?
              |
trusted reflex / fallback
```

Requirements fixed for that branch: learning from Paradigm's validated traces, not from annotations invented for a benchmark; procedural hard negatives (same topic with negation, future, past, another object, inspection only); no hand-written French grammar in the final solution; prospective replication on unknown phrasings and generators before any claim of generalization. Success is not accuracy: it is, together, sufficient coverage of new positive phrasings, rejection of the hard negatives, a coverage that does not collapse under distribution shift, and zero false fast paths under Paradigm's unchanged criterion.

Contrastive learning of a goal-by-action embedding from validated traces (SetFit or similar) is one candidate method for that question, compared against the present stack (A+S+E+T with the current classifier and gate) under the same certification protocol; it is not the definition of the branch.
