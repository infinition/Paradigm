# Pre-registration: D1-language, a collection designed to test whether language carries procedural intent

Written before a single formulation exists, and before either generator has produced anything. The crossing plan, the splits, the arms, the reporting and the verdict are fixed here so that none of them can be chosen after seeing a phrase or a number.

The D1 pilot is closed and established what this collection exists to repair: the code domain gives state depth and enough transitions per mission to learn a procedural policy, and its frozen missions carry two goal formulations, so the pilot could show that the state carries the procedure and could say nothing about language. The camera domain, which had twelve formulations, yields about one decision per mission and cannot carry the question either.

## What is reused unchanged

The code domain machinery of `laruche-essaim/examples/paradigm_demo.rs` and the D1 harness: `calc.py` and `test_calc.py` in a per-mission workspace, the guard hook, the 30-iteration ceiling, the episode closed from the harness's own `pytest` run and never from the model's claim, `deepseek-v4-flash`, Paradigm observe-only at `--shadow-schedule 1-80:1.0` so nothing is replayed and no promotion has behavioral effect, the trace sink with its attempt id, and the block-level invalidation rule with its mandatory preflight for physical devices. No change to the engine, the adapter, the reflex policy, the contracts or the thresholds.

Circuit breaker, unchanged in kind and rescaled to the block: 800 deliberative decisions or 8,000,000 tokens, which are the 80% margins of the D1 ceilings.

**Raised during the run, at mission 12, on cost alone.** The measured rate was 9.4 deliberative decisions and 103k tokens per mission against the 6.2 and 56k estimated from the pilot, which projects about 753 decisions and 8.3M tokens over the eighty missions, so the token breaker would have fired around mission 77 and, under the rule, invalidated a block of seventy-seven clean missions for an overshoot of three. The ceiling is raised to 1,200 deliberative decisions and 12,000,000 tokens for this block.

What this decision was and was not based on: the only quantity inspected was the running cost, mission verdicts and counters; no arm, no split, no comparison and no scored result existed or was looked at, and none could, since the evaluation runs after the collection. The device is a guard against a runaway harness and was declared from the start not to be a scientific criterion and never a target to consume; nothing is looping here, the missions simply cost more than an estimate drawn from a prompt that dictated the procedure step by step. That underestimation is itself one of this collection's results and is reported as such.

The raise applies to this block only and does not touch the D1 ceilings, the 80% sizing rule for a planned campaign, or the invalidation rules.

## Outcome contract, corrected before the first provider call

The pilot's contract, "SUCCESS when the harness's own pytest run passes", is inherited for the intentions that ask for a repair and is wrong for the two that do not. Under it, a mission that correctly diagnoses without fixing leaves the suite red and would be scored FAILURE for having done exactly what was asked, and its steps would then be dropped from the learnable set, removing the very intentions that separate diagnosing from repairing. The contract is therefore intention-aware, and the correction is recorded here rather than applied silently. Nothing about the missions, the formulations, the crossing plan or the splits changes.

```text
I1, I4, I5   SUCCESS iff the harness's own final pytest run passes
             and no guarded action ran
I2, I3       SUCCESS iff every workspace file is byte-identical to what the
             harness wrote before the mission, and no guarded action ran;
             the state of the test suite is irrelevant to the verdict
```

Both branches are verified by the harness from the workspace itself, never from the model's claim. The limit of the second branch is stated plainly: it verifies the procedural postcondition of "diagnose only" and "check only", that nothing was modified, and it does not verify that the diagnosis is correct. Judging the content of a natural-language diagnosis automatically is out of scope here, so no verdict about diagnosis quality is recorded and none may be read into these missions.

For I4 in the state with no bug, where the defect is claimed but absent, the fix branch applies: a mission that checks and changes nothing leaves a green suite and passes, and one that edits and breaks the suite fails.

## The four axes

Five procedural intentions, distinct by the procedure they call for and not by vocabulary:

```text
I1  fix and verify              the full procedure
I2  diagnose only               no write expected
I3  check the project state     neither deep reading nor writing expected
I4  fix, bug already named      entry point past the diagnosis
I5  fix under a constraint      without touching the tests, without regressing
```

Four initial-state families, which change the trajectory and not only the decor:

```text
S1  one bug          the three existing variants, rotated
S2  no bug           the structural negative for writing
S3  two bugs         two edits, a longer trajectory
S4  bug in a second module   forces exploration through file_list and file_read
```

Forty formulations, eight per intention, from two generators, four per intention per generator:

```text
gen_a   20 formulations, written by the assistant of this session
gen_b   20 formulations, written by a second language model
```

Both are synthetic. No human-written slice is claimed. The two batches are written independently and neither generator sees the other's batch before writing its own; `gen_a` is committed first and is not shown in the conversation, so that the second batch is not anchored on it.

## Shared specification both generators must follow, fixed before either writes

**Language.** Every formulation is in French, for both generators. The whole intent line was French and mixing languages across generators would confound the transfer test with a translation effect. The English scaffold of the pilot's prompt is dropped.

**Constant constraint suffix.** Each mission prompt is one formulation followed by the same suffix, identical in all 80 missions: the workspace path, and the instructions not to install anything, not to touch anything outside it, and never to modify the test file. Being identical everywhere it carries no discriminative signal, and the path is stripped before encoding. A formulation therefore does not need to restate the constraints, and must not.

**The `{bug}` slot of intention I4.** I4 names the defect, which is what moves its entry point past the diagnosis, so its formulations cannot name a fixed defect while the injected bug rotates. An I4 formulation contains the slot `{bug}`, filled by the harness with the description of the bug actually injected in that mission: a wrong constant, a missing import, an off-by-one bound. In the `S2` state, where no bug is injected, the slot is filled with a rotated plausible defect, which makes those missions the case of a defect claimed but absent, where the procedure is to check and report rather than to edit. No other intention uses a slot.

## Crossing plan, fixed before any formulation exists

Each formulation appears in exactly two of the four state families, by systematic rotation on its index `j` inside its intention:

```text
j mod 4 == 0  ->  S1, S3
j mod 4 == 1  ->  S2, S4
j mod 4 == 2  ->  S1, S4
j mod 4 == 3  ->  S2, S3
```

with `j = 0..3` for the intention's `gen_a` formulations and `j = 4..7` for its `gen_b` formulations, so each generator covers all four patterns inside every intention. Per intention this gives four missions in each state family, and twenty per family overall.

```text
40 formulations x 2 states = 80 missions
```

Two properties this buys, and they are the point of the plan. A formulation never meets all four states, so a phrase held out at the mission level can be tested in a state it never occupied, which separates "learned the procedure" from "memorised a phrase to trajectory association". And the same state family is met by many different phrasings across intentions, so the goal cannot serve as a proxy for the state.

Bug kinds inside S1, S3 and S4 rotate deterministically over `wrong_constant`, `off_by_one`, `missing_import` by mission index, so no formulation is tied to one kind.

## Two properties of the two batches, measured before the run and not corrected

Both batches are frozen and hashed. Neither is edited, and these notes exist so that the transfer result is read correctly rather than adjusted afterwards.

**Surface form separates the sources perfectly.** Every `gen_a` formulation starts with a capital and ends with a period or a question mark; no `gen_b` formulation does either. Mean length 70 characters against 84.

```text
                              gen_a   gen_b
starts with a capital         20/20    0/20
ends with . or ?              20/20    0/20
```

A leave-source-out result therefore measures resistance to a style change that includes a trivial typographic marker, not only to a change of phrasing. The mitigation is reporting, not editing: the transfer evaluation is run twice, once on the frozen text and once with case and final punctuation normalized, and both numbers are reported. If they differ, the difference is the part of the transfer gap that is typographic rather than linguistic.

**The two batches take different stances inside intention I4.** The `gen_a` formulations assert the named defect ("inutile de chercher longtemps, c'est {bug}"), while every `gen_b` one hedges and asks for a check before the fix ("vérifie ce point et corrige-le si c'est bien le problème", "confirme d'abord puis corrige si c'est avéré"). That is not only style: an asserted defect invites going straight to the edit, a hedged one invites verifying first, so the expected procedure differs. Transfer on I4 may therefore reflect a procedural difference and not a stylistic one, and I4 is reported separately from the other intentions in the leave-source-out analysis for that reason.

Neither property is a defect of the batches. They are what two independent generators actually produce, which is the situation the collection is meant to face.

## Splits, and what each one answers

```text
primary    leave-formulation-out    four folds of 10 formulations, with both of
                                    their missions, so every formulation is tested
                                    once and no test phrase is seen in training.
                                    Fold of a formulation, fixed here: for the
                                    intention of index k and fold f, gen_a holds
                                    j = (f+k) mod 4 and gen_b holds
                                    j = 4 + ((f+k+2) mod 4), which puts 2
                                    formulations of every intention and 5 of every
                                    source in each fold and spreads the four state
                                    families across it. Answers: does it generalize
                                    to a new formulation.
transfer   leave-source-out         train on gen_a, test on gen_b, then the reverse.
                                    Answers: does it survive a change of generator
                                    and style, which is exactly what C6R discovered
                                    after the fact and what this design tests on
                                    purpose.
secondary  leave-mission-out        as in B0. Answers: does a phrase seen in one
                                    state transfer to the other state it occupies.
```

## Arms

```text
goal only
state only
goal + state
```

Same encoder, same head, same folds, five seeds, mean and standard deviation; an arm that beats another by less than the seed spread is reported as indistinguishable. The candidate-action arm is deliberately not run here: the pilot showed that the per-candidate scoring formulation loses under an unfair loss, and the fair test needs a listwise loss over the candidates of one decision. It is a separate experiment, opened only if `goal + state` shows there is an exploitable procedural representation.

Encoder `paraphrase-multilingual-MiniLM-L12-v2`, frozen, on CPU. The goal text is normalized before encoding: the absolute workspace path is stripped, so the domain and the mission are not trivially identifiable from the string.

## Reporting

Global, then per intention, then per state family, for every arm and every split. Per intention matters most: the decisive comparison is on the intentions where **the same state allows several procedures**, which is where language must carry information that the state cannot.

## Secondary analyses, specified before the numbers exist

**Trajectory depth against formulation openness.** An open formulation may simply produce longer and more exploratory trajectories than a directive one. If it does, part of any gain of `goal + state` over `state only` could come from the goal predicting how deep the trajectory will go, rather than from it carrying procedural intent. Reported alongside the arms, per intention and per source: steps per mission, share of read and list actions, number of distinct action keys per mission, and the variance of steps per mission. If the arms' gain tracks depth variance rather than intention, that is stated as the more likely reading and the intent claim is withheld.

**What the two non-repair intentions may be claimed to show.** Their contract verifies that nothing was modified and nothing else. A SUCCESS there means the workspace is byte-identical, never that the diagnosis or the check was correct. Any statement about I2 and I3 is therefore about the procedural constraint being respected, and no claim about answer quality is available from this collection.

**Cost of open formulations.** The per-mission cost measured here is compared to the pilot's, whose prompt dictated the procedure step by step. A difference is a result about the goal's form changing the cost of deliberation, not only the trajectory, and is reported as such.

## Order in which the result is read, fixed before it exists

Not a new analysis, an ordering of the ones already specified, so that the conclusion cannot be reached by stopping at the first favourable step.

```text
1  does goal + state actually beat state only
2  does the gain hold at comparable intention
3  does it hold when trajectory depth is controlled
4  does it hold under leave-source-out, including on the normalized text
5  only then may a signal be attributed to procedural intent
```

## Verdict, fixed now

```text
SIGNAL CLAIR    state only beats goal only, confirming the pilot, and
                goal + state beats state only beyond the seed spread on the
                intentions where one state allows several procedures, and that
                gain survives leave-source-out in both directions
SIGNAL FAIBLE   the gain of goal + state appears under leave-formulation-out and
                does not survive leave-source-out, or sits inside the seed spread
PAS DE SIGNAL   goal + state does not beat state only
```

A gain that appears only within one generator is reported as a within-style result and never as generalization. That distinction is the one the previous line paid to learn.

## Expected cost, from the measured code block

From `a3-code-1`, 5.4 deliberative decisions and 48.7k tokens per mission, raised by 30% for the longer S3 and S4 trajectories:

```text
80 missions   about 560 deliberative decisions, 5.1M tokens, 25 minutes
              70% of the decision ceiling, 64% of the token ceiling
```

Expected yield about 480 observed decisions, against 69 in the pilot.

## Order of work, and why it matters

1. This pre-registration is committed before any formulation is written.
2. `gen_a` writes its 20 formulations, which are committed and not shown in the conversation.
3. `gen_b` writes its 20 independently, without having seen `gen_a`.
4. The mission set is assembled by the frozen crossing plan, hashed, and only then run.

## Not done

No candidate-action arm, no listwise loss, no camera, no live wiring, no engine change, no B1, no reuse of intent v1 or v2, no modification of the pilot's frozen missions.

## Outcome

Not run.
