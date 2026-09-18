# Pre-registration: `a3-code-1`, a valid code block, and the B0 feasibility test it feeds

Written before the block runs and before any B0 code exists. It replaces the plan of testing B0 on the intent benchmarks, which was abandoned for the reason recorded below. Nothing here changes the D1 pilot's frozen protocol: the missions, prompts, order, outcome contracts, ceilings and diversity criterion of `pilot_prereg.md` are reused unmodified, under the amendment that makes invalidation block-level from `a3` on.

## Why B0 is not run on the intent benchmarks

The plan was to compare `goal only` against `goal + candidate_action` on intent v1 and v2. Inspection of the data before writing any code shows the comparison could not mean what it claims:

```text
v1: 320 phrases, 39 groups, 6 intent classes
fields: id, group, source, role, transformation, intent, text
transformation: negation 37, temporal 37, past_question 37, object_change 37, inspection_only 37, none 135
no state, no action
```

The label is a function of the goal alone: "Ne me prends pas en photo" carries `intent: OTHER` directly. Building pairs `(goal, candidate_action) -> applicable` therefore requires deriving the label as `candidate_action == action_of(intent(goal))`, which makes the candidate action a mirror of the label rather than an independent variable. A goal-only binary model then sees one goal with several actions and contradictory labels and cannot exceed the base rate, so the action-conditioned model wins by construction, whatever the encoder. The experiment would measure the dataset's construction, not the architecture.

Action conditioning can only pay where **the same goal leads to different correct actions depending on the state**. That variation is absent from v1 and v2 by construction, and present in D1 traces. Hence this block.

## The distinction this branch rests on, documented before collection

```text
learnable_for_representation   !=   replayable_as_reflex
```

A step may be legitimate evidence for learning a procedural representation without ever being authorized for automatic replay. The two properties answer different questions: one asks whether an observation carries information about the procedure, the other whether Paradigm may execute the action on its own.

Concretely, `file_edit` and `file_write` are marked `not_reflex_capable` by the adapter, so they never become exploitable positive transitions for certification, and they will keep that status. Nothing about the engine, the adapter, the reflex policy or their authorization changes. But they are observed steps with a verified episode outcome, and for B0 they are kept in the dataset as learnable transitions. The reason is the one the pilot already exposed: of the 28 exploitable validated transitions the previous code block produced, not one was a write, so a representation built from certification-eligible steps alone would learn to read and to test and never to change the environment, which is the part of a procedure that matters most.

The rule for the B0 dataset, fixed here:

```text
kept as learnable      a step observed in an episode that closed SUCCESS,
                       whatever its reflex capability
never positive         a step in an episode that closed FAILURE or UNKNOWN
never replayable       anything the adapter marks not_reflex_capable stays
                       unauthorized for reflex, in the engine, unchanged
```

Each row carries both flags, so any later analysis can separate the two populations rather than conflate them.

## Block `a3-code-1`

Twelve code missions, identical to the pilot's: the frozen `missions.json` (sha256 in `MANIFEST.md`), templates A, B and C over the three bug variants, same order, same outcome contract verified by the harness's own `pytest` run, same guard hook, same 30-iteration ceiling, same model `deepseek-v4-flash`. Fresh Paradigm state, `--shadow-schedule 1-24:1.0` so nothing is replayed and no promotion has behavioral effect, trace sink on with `--attempt-id a3-code-1`.

The camera preflight does not gate this block: it depends on no physical device. The camera block stays out of `a3` until its preflight passes, and will run later as `a3-camera-1` under the block-level rule.

Circuit breaker unchanged, 200 deliberative decisions or 2,000,000 tokens. Expected cost, from the previous code block, about 72 decisions and 590k tokens.

The interpreter correction of `a1` applies: a venv providing `python` and `python3` with pytest is first on the harness PATH, for the harness verification and for the model's own commands alike.

If the block closes without incident, its trace is frozen and hashed, and becomes the B0 dataset. If any harness incident occurs, only this block is invalidated, archived under its id, and restarted as `a3-code-2` from mission 1.

## B0, pre-registered now, before the data exists

Question, and the only one: does conditioning on the state and on the candidate action carry real signal on observed transitions? Not whether it generalizes, not whether it is ready for anything.

Task: for a step, predict whether the candidate action is the one the teacher took in that state, a binary applicability judgement built from the trace and never from a hand-written rule. Negatives are drawn from the actions actually available in that state (`available_actions`), so a negative means "not the action taken here", never "invalid action". Rows from episodes that closed FAILURE or UNKNOWN are excluded from the positive class entirely.

Four arms, same encoder, same splits, same seeds:

```text
B0-A   goal                    multi-class over the candidate actions
B0-B   goal + state            multi-class over the candidate actions
B0-C   goal + action           scores one candidate, ranked over the same set
B0-D   goal + state + action   scores one candidate, ranked over the same set
```

Correction made before any B0 number exists, and recorded rather than silently applied. The first formulation asked every arm the binary question "is this candidate the action taken here", which makes the arms without the action structurally blind: one `(goal, state)` appears with every available candidate and different labels, so they could not exceed the base rate and the action-conditioned arms would have won by construction. That is the same flaw that disqualified the benchmark plan, reproduced in this file. All four arms now decide the same thing on the same candidate set: which of the 36 available actions was taken. Arms without the action emit a distribution over the 36; arms with the action score each candidate and take the argmax. The metric is top-1 accuracy for everyone, so no arm is handed an advantage by its formulation.

`goal` is the raw mission text; `state` is the structured state the sink recorded (phase, last action, last outcome, output kind, recent actions, step index, consecutive failures); `action` is the candidate tool.

Encoder: `paraphrase-multilingual-MiniLM-L12-v2`, frozen, already used in C3 and cached locally, on CPU. Structured fields are encoded as categorical vectors, not as sentences. Head: one small MLP. No fine-tuning of the encoder, no RL, no multi-head, no calibration, no gate, no wiring, no change to the engine.

Split: leave one mission out, twelve folds, so no step of a mission appears on both sides. Five seeds, mean and standard deviation for every metric; an arm that beats another by less than the spread of the seeds is reported as indistinguishable, not as a winner.

Metric: top-1 accuracy over the candidate set, with the majority-action rate reported as the trivial baseline.

## What this block can and cannot answer

The code block carries **two distinct goal texts** for its 69 steps, because templates B and C share their wording by design and the workspace path is identical across missions. All the variation is in the state. This is the mirror image of the benchmark's defect, where all the variation was in the goal and there was no state.

So the verdict from this block is narrow and is stated as such: **does the state carry the procedure, that is, is the next action predictable from the state**. It says nothing about generalization to new phrasings, which needs goal variation and therefore the camera block. The informative comparison here is `goal` against `goal + state`; the arms carrying the action are reported for completeness, not as an answer about language.

Verdict, fixed now, on that narrow question:

```text
SIGNAL CLAIR    goal + state beats goal only beyond the spread of the five
                seeds, and beats the majority-action baseline
SIGNAL FAIBLE   a gain inside or near the seed spread
PAS DE SIGNAL   the state adds nothing, or costs accuracy
```

The frozen missions are not modified to manufacture goal variation. Stop after this verdict, then wait for `a3-camera-1` for the full question.

## Outcome, collection

Block `a3-code-1` ran clean: 12 of 12 missions verified, no circuit breaker, no incident.

```text
missions              SUCCESS 12   FAILURE 0   UNKNOWN 0
deliberative decisions    65       actual model responses  48
tokens                584193       (input 572934, output 11259)
per mission              5.4 decisions, 48.7k tokens
steps observed            69       of which 9 file_edit
exploitable validated     33       over shell_exec, file_read, file_list
families                   8
distinct goal texts        2
```

Trace frozen, sha256 in `TRACE_SHA256.txt`. It is the B0 dataset: 69 learnable steps, every one of them from an episode that closed SUCCESS, writes included under the distinction recorded above.

## Outcome, B0

```text
trivial baseline, always shell_exec        0.420
B0-A  goal                    top-1  0.362 +/- 0.013
B0-B  goal + state            top-1  0.754 +/- 0.018
B0-C  goal + action           top-1  0.339 +/- 0.012
B0-D  goal + state + action   top-1  0.652 +/- 0.022
```

SIGNAL CLAIR on the narrow question: `goal + state` beats `goal only` by 0.39, about twenty times the seed spread, and the trivial baseline by 0.33. The state carries the procedure.

Two qualifications belong to the result. The block has two distinct goal texts, so `goal only` sits near the trivial baseline by construction and nothing here speaks about language or about generalization to new phrasings. And the action-conditioned scoring arm does not win: `goal + state + action` reaches 0.652 against 0.754 for the plain multi-class arm on the same features, outside the seed spread, so on this data framing the decision as per-candidate scoring costs accuracy instead of adding signal. The two families do not see the same loss, 36 independent binary problems per decision against one softmax over the classes, so this judges the formulation and not the architecture; a listwise loss over the candidates would be the fair test. Full numbers and their reading in `experiments/decision_model_v0/RESULTS.md`.
