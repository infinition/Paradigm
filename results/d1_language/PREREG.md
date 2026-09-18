# Pre-registration: D1-language, a collection designed to test whether language carries procedural intent

Written before a single formulation exists, and before either generator has produced anything. The crossing plan, the splits, the arms, the reporting and the verdict are fixed here so that none of them can be chosen after seeing a phrase or a number.

The D1 pilot is closed and established what this collection exists to repair: the code domain gives state depth and enough transitions per mission to learn a procedural policy, and its frozen missions carry two goal formulations, so the pilot could show that the state carries the procedure and could say nothing about language. The camera domain, which had twelve formulations, yields about one decision per mission and cannot carry the question either.

## What is reused unchanged

The code domain machinery of `laruche-essaim/examples/paradigm_demo.rs` and the D1 harness: `calc.py` and `test_calc.py` in a per-mission workspace, the guard hook, the 30-iteration ceiling, the episode closed from the harness's own `pytest` run and never from the model's claim, `deepseek-v4-flash`, Paradigm observe-only at `--shadow-schedule 1-80:1.0` so nothing is replayed and no promotion has behavioral effect, the trace sink with its attempt id, and the block-level invalidation rule with its mandatory preflight for physical devices. No change to the engine, the adapter, the reflex policy, the contracts or the thresholds.

Circuit breaker, unchanged in kind and rescaled to the block: 800 deliberative decisions or 8,000,000 tokens, which are the 80% margins of the D1 ceilings.

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

## Splits, and what each one answers

```text
primary    leave-formulation-out    10 of the 40 formulations, with both of their
                                    missions, held out. No test phrase is seen in
                                    training. Answers: does it generalize to a new
                                    formulation.
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
