# Pre-registration: D1 cost and diversity pilot (proposal, nothing run yet)

Written before any experimental code or launch, as the opening move of the D1 branch (`docs/RESEARCH_HANDOFF.md`, "Next research branch"; `results/intent_bench/SYNTHESIS.md`, section 5). D1 is validated-experience collection for a procedural representation conditioned on the action; B1, the learned representation itself, does not start before D1 is finished and frozen, and is out of scope here. This document proposes only the small cost pilot that the handoff requires before the real D1 mission count is fixed. Nothing below is an outcome; the Outcome section is left for after the run, once this protocol is confirmed.

## Purpose, and what it is not

The pilot answers one question first: do real LaRuche traces, verified by the existing outcome contract, produce enough diversity of `(goal, state, action, outcome)` across more than one tool to be worth scaling into a full D1 collection at all. Cost (calls, tokens, latency) and success rate are measured at the same time, but sizing the real dataset from cost alone, without checking that the diversity is there, would repeat the mistake the intent-benchmark line already recorded: a benchmark can look sufficient by one axis and still fail to transport. The pilot is not a training set. It is not scored for B1. Its own traces may later be folded into the frozen D1 set only if they were collected under the exact protocol below, and only as part of the same decision that fixes D1's size, not before.

## Non-negotiable constraints, carried from the handoff and from this session's instructions

- Paradigm observes only during the pilot. No family is ever replayed as a reflex, whatever the compiler's internal bookkeeping concludes. No promotion has behavioral effect.
- The existing outcome contract stays authoritative in both domains; nothing here redefines SUCCESS, FAILURE or UNKNOWN.
- Only a verified SUCCESS step or episode can become positive evidence. UNKNOWN and FAILURE are recorded, never treated as positive.
- No B1 work, no representation training, no embedding fit, before D1 is finished and frozen.
- The real D1 mission count is not fixed by this document. It is fixed after the pilot, from the pilot's own numbers, under the decision rule declared below.
- No new certification rule, no threshold change, no tag, no merge of `paradigm-integration`.

## Mechanism for "observe only"

Reuse of run 12's shadow-sampling path, not new code: `paradigm serve` started fresh, `--shadow-schedule` covering the pilot's whole episode range at rate 1.0, so every reflex-eligible decision in both domains is routed to the teacher and logged with reason `shadow_sample`, never replayed. The compiler still computes candidates and may mark families active internally; that bookkeeping has no effect on any executed action, since a rate of 1.0 forces the teacher on every eligible step. This is the default proposed here because it needs no new engineering and its behavior is already validated (run 12). A stricter alternative, a new flag that disables candidate compilation entirely for the pilot, would be a small code change and is not proposed for this first pilot; flagged here in case the internal bookkeeping is judged not clean enough to accept.

One fresh Paradigm state, one `paradigm serve` process, for the whole pilot, both domains against the same server. This lets the family-scoped store hold heterogeneous tool families (`camera:*`, `laruche:*` from the code domain) at once, which is closer to eventual real use than two isolated states, and lets the pilot also surface, incidentally, whether the store behaves sanely with two unrelated tool vocabularies present together; that is a diagnostic side effect, not a criterion this pilot is scored on.

## Setting, both domains reused unmodified

Camera domain: exactly the adapter scope declared in `camera_prereg.md` (`camera` reflex-capable with the exact validated argument templates for `list` and `capture`; a capture verified only when the tool result is ok and carries at least one image whose bytes decode as PNG), the same containment fixes (every path confined to the mission workspace, the `pre_tool` hook covering every tool, not `shell_exec` alone, 30-iteration ceiling), the camera process launched from Terminal.app as required there.

Code domain: exactly the workspace and bug-variant machinery of `laruche-essaim/examples/paradigm_demo.rs`, unmodified where reused (`variant(i)` cycling `wrong_constant`, `off_by_one`, `missing_import`; the guard hook refusing install, link, copy, move, delete, `sudo`, network fetch, or writes outside the workspace; episodes closed from the harness's own `pytest` verification, never from the model's claim).

Model: `deepseek-v4-flash` through LaRuche's OpenAI-compatible path in both domains, as in every run since run 9, for cost comparability.

## Missions, 24 total (12 camera, 12 code), fixed order within each domain, code domain run first

The four camera classes and the three code sequences below are the categories the resulting trajectories are tagged into afterward, from the verified event stream. No mission text forces a tool order; the teacher chooses it, as in every prior run (C1 found about half of direct capture requests opened with `list` and half did not; run 11 found about a third of missions opened with a redirected pytest call and the rest did not). Fixing an order in the mission text would not be measuring what a product sees.

### Code domain (12 missions, 4 per template, cycling the 3 bug variants once per template)

Template A, unmodified existing prompt (targets `tests_failed -> file_edit -> tests`): "You are working in the directory `{d}` which contains `calc.py` and `test_calc.py`. The test suite fails. python and pytest are already installed; do not install anything and do not touch anything outside `{d}`. Run `python -m pytest -q` with shell_exec, read calc.py, fix the bug in calc.py only (never modify the test), run `python -m pytest -q` again, and finish once the tests pass." Applied to the 3 bug variants, then repeated once more (6 missions), matching the cadence used in runs 9, 11, 12 and 12b.

Template B, read-first phrasing, bug present (targets `file_read -> file_edit -> tests`): "You are working in the directory `{d}` which contains `calc.py` and `test_calc.py`. Please review calc.py for correctness against test_calc.py, fix any bug you find in calc.py only (never modify the test), then confirm with `python -m pytest -q` via shell_exec that the suite passes. Do not install anything and do not touch anything outside `{d}`." Applied once per bug variant (3 missions).

Template C, inspection only, no bug injected (targets `file_read -> tests`, no edit; the structural hard negative for `file_edit`, same topic, nothing to fix): same phrasing as template B, `calc.py` set to the corrected version of each of the 3 variant families instead of the buggy one (3 missions).

Outcome contract, unchanged: SUCCESS iff the harness's own final `pytest` run passes and no guarded action ran. For template C only, an additional diagnostic tag (not a pass/fail criterion) records whether `file_edit` occurred at all, since the intended positive path there has none.

### Camera domain (12 missions)

List then capture, positive (3): `Prends-moi en photo.` / `Peux-tu prendre une photo avec la webcam ?` / `Fais une photo de moi maintenant.`

Immediate capture, positive, low token overlap with the above (1): `Photographie-moi.`

List only, no capture (1, new class, not in C1): `Combien de caméras sont connectées sur cet ordinateur ?`

Preview, no capture (1, reused from C1 N4): `Ouvre la caméra sans prendre de photo.`

Negation (1): `Ne me prends pas en photo.`

Future, deferred (1): `Tu pourras me prendre en photo tout à l'heure ?`

Past, references existing photos, reused from C1 N2 (1): `Trouve mes dernières photos.`

Conditional, unmet condition (1): `Si la lumière est meilleure, prends une photo.`

Different tool entirely, reused from C1 N1 (1): `Fais une capture d'écran.`

Unrelated, outside the camera topic altogether (1): `Quelle heure est-il ?`

Outcome contract, unchanged from `camera_prereg.md`: the 4 positive missions are SUCCESS iff at least one verified capture occurred and no forbidden tool ran; every other mission is SUCCESS iff no capture occurred and no forbidden tool ran. Whether `camera list` occurred is logged as a diagnostic tag on every mission, not a pass/fail criterion.

The exact order of the 24 missions and their verbatim prompts are frozen in `missions.json` (hash in `MANIFEST.md`), which the harness reads; it is the authority, so the harness cannot drift from this document. An earlier draft of this section listed a second list-only phrasing, which made the camera block 13 missions against the 12 stated here; it was removed before anything ran, and is recorded here rather than silently corrected.

## Per-step capture, both domains

`goal` (the mission's user request, verbatim), `state` (Paradigm's own encoded state at decision time, as already logged), `candidate action` (the shadow decision, logged even though never executed), `teacher decision` (the actual tool call), `verified action outcome` (from the domain's outcome contract above, never from the model's claim), `episode outcome` (the mission verdict). Provenance tag on every row: `pilot`, domain (`camera` or `code`), mission id and template, so that if these traces are later folded into frozen D1 they remain traceable, in the same way v1 and v2 tag `gen_a`, `gen_b`, `synthetic_user_style`.

## Metrics reported after the run

Per domain and per mission: model calls, tokens, wall time, episode verdict. Per action key: count of verified SUCCESS steps (the quantity the handoff calls exploitable validated transitions), count of UNKNOWN, count of FAILURE. Diversity, read directly off the above: number of distinct verified action keys across both domains; number of missions per class (the four camera classes, the three code templates) that produced a verified trace distinguishable in encoded state from the others of its domain; count of verified hard-negative traces per domain (camera: list-only, preview, negation, future, past, conditional, unrelated, each checked for zero capture; code: template C, checked for zero edit).

## Diversity criterion, fixed now, not after seeing the numbers, confirmed by the user

The pilot supports moving to a sized D1 collection only if all of the following hold on this run:

- at least 5 distinct verified action keys across the two domains combined, with at least 2 in each domain, so that no single domain can carry the whole count;
- at least one verified structural-negative trace in each domain, distinguishable from that domain's positive traces by encoded state, not merely by mission id (camera: a list-only, preview, negation, future, past, conditional or unrelated mission with zero capture in a state that differs from the capture-positive states; code: a template C mission with zero edit in a state that differs from the template A and B post-fix states);
- no single action key accounts for more than 70% of all verified steps.

These three numbers are deliberately not tightened further for a 24-mission pilot. The pilot asks whether D1 is worth collecting at scale, not whether it already meets a bar sufficient for B1. They are fixed before the pilot runs so they cannot be adjusted to fit the result, and are open to revision with the user only before launch, never after.

## Decision after the pilot

If the diversity criterion holds and cost is judged acceptable: fix the real D1 mission count from `N_real = ceil(target_min_verified_traces_per_cell / observed_verified_traces_per_cell_per_mission)`, `target_min_verified_traces_per_cell` defaulting to 30 (the compiler's own established minimum, `camera_prereg.md`: "the compiler needs 30 training traces"), computed on the pilot's sparsest class.

`N_real` is then capped by absolute ceilings on the real D1 collection, confirmed by the user: `max_model_calls = 1000`, `max_tokens = 10_000_000`, consistent with the per-mission cost already observed on LaRuche (a few calls and some tens of thousands of tokens per mission), which leaves room for roughly 100 to 150 missions without letting the collection drift. The additional rule: `estimated_cost(D1)` (extrapolated from the pilot's own per-mission calls and tokens) must stay at or under 80% of both ceilings before `N_real` is accepted, so the real collection is never deliberately planned against the ceiling itself; the 20% margin is kept for variance and for missions that run longer than the pilot's own. If the extrapolation from the pilot exceeds 80% of either ceiling at the size the diversity target would otherwise call for, `N_real` is reduced to the largest size that respects the 80% margin, and that reduction is recorded as a limitation of the resulting D1 set, not silently absorbed.

If the diversity criterion does not hold: D1's design is revised, more domains, different modifiers, or a third tool, before any mission count is fixed. This is a possible outcome of the pilot, not a failure of it.

If cost per mission is judged prohibitive relative to the observed yield even within the ceilings above: scope is reconsidered (fewer domains, a cheaper model, a lower per-cell target) before fixing a count.

None of `max_model_calls`, `max_tokens`, or the 80% margin is a target to consume; they are ceilings on the real D1 run, not goals for it.

## Amendment, in force from attempt `a3`: invalidation by block

Written after attempts `a1` and `a2` were both invalidated whole, and **not applied retroactively to either of them**. `a1` stays invalid in its entirety. `a2` stays invalid in its entirety, its clean 12 of 12 code block included: that block was declared invalid under the rule in force when the fault occurred, and reviving it now, because a later amendment would have spared it, is precisely the post-hoc move this project does not make. The amendment changes what happens next, never what already happened.

From `a3` on, a hardware, environment or harness fault demonstrated to be confined to one domain invalidates only the block it occurred in, provided all of the following hold:

- the preceding block is already closed;
- no learning, promotion or policy update took place between the blocks;
- the fault did not alter the data or the state used by the other domain;
- the incident was diagnosed independently of the scientific result;
- the faulty block restarts from its own mission 1 under a new block attempt id.

Identifiers become two-level, a pilot attempt and one attempt id per block:

```text
pilot_attempt_id      = d1-pilot-a3
code_block_attempt    = a3-code-1
camera_block_attempt  = a3-camera-1
```

so that a second camera fault reads:

```text
a3-code-1     stays valid
a3-camera-1   invalid, archived
a3-camera-2   restarts at camera mission 1
```

The justification is the experimental reality and not convenience: the two domains are separate, Paradigm runs observe-only at shadow rate 1.0, so nothing learned in one block conditions the other, and a camera fault has no path by which it could have changed what the code block recorded. The third condition is the one that does the work: if a fault ever touched shared state, the whole attempt falls again.

## Mandatory preflight for any run on physical hardware, in force from `a3`

No scientific attempt begins until the device it depends on is proven to work, by a check that costs nothing and calls no provider.

```text
camera preflight FAIL  ->  no attempt starts
```

For the camera that check is `camera_preflight`, run under Terminal.app immediately before the block. It must show `list` succeeding **and** `capture` returning an image that actually decodes as a PNG with plausible dimensions, not merely a call that returns. `a2` failed for want of ten seconds of this: the tool was available, the device was listed, and capture never returned, which three positive missions at about 305 seconds each discovered the expensive way.

## What the pilot has established about the design of the real D1

Recorded while the camera block is still pending, because it does not depend on that block's results and it is the question the pilot exists to answer: does real experience, collected this way, carry the diversity the next branch needs.

```text
code domain      69 decisions over 12 missions,  2 distinct goal formulations
camera domain   about 11 decisions over 12 missions, 12 distinct formulations
```

The code figure is measured on the valid block `a3-code-1`. The camera figure is a structural property of the domain, not a result: a camera mission is a single shot, the teacher calls one tool or none and finishes, and the finishing call is never observed, so a request like "do I have a webcam" yields zero or one observed decision. The per mission step counts that show this come from the invalidated attempt `a2` and are used here as an engineering fact about mission shape, never as evidence.

The consequence is that neither domain, as frozen, can carry the language question. The code domain has the state depth and two formulations; the camera domain has twelve formulations and too few decisions to fit anything. For learning whether a procedural representation generalizes to new phrasings, the unit that matters is the distinct formulation, not the step, so repeating twelve phrases more often adds decisions and no linguistic variation at all.

What a collection designed for that question needs, fixed here before it is designed:

```text
many distinct formulations per intention, not repetitions of a few
several intentions
a domain that yields several decisions per mission, which the code domain does
  and the camera domain does not
the two varying together, so that the same goal can meet different states
```

The camera block is still run, to close the pilot on cost, action diversity and the physical domain working again, and it is not asked to answer the language question. The frozen missions are not modified to manufacture formulations; a collection for the language question is a new pre-registration and a new mission set, and it is the sizing decision the pilot was meant to inform.

## Pilot safety hard stop

Not a scientific criterion, a protection against a looping harness or a teacher trajectory running abnormally long, confirmed by the user: the 24-mission pilot stops immediately if cumulative model calls exceed 200, or cumulative tokens exceed 2,000,000, whichever comes first, counted across both domains from the start of the pilot. A stop under this rule is reported as an incident, exactly like the harness faults recorded in `camera_prereg.md`'s addenda, and does not by itself decide the diversity question.

Counters are read from Paradigm's own telemetry (`deliberative_decisions` and `llm_tokens_spent`), the same instrument every LaRuche run since run 9 reported. A model call that produces no tool call is not observed by the bridge and therefore not counted, so the breaker fires on a lower bound of the true cost. That is acceptable for a safety device and is stated here so the pilot's reported cost is never read as an exact provider bill.

## Attempts, and what may never be mixed

Operational rule fixed before the first provider call, confirmed by the user. Every launch carries an `attempt_id`. If the circuit breaker fires, or any harness incident occurs (a stall, an unanswered approval, a containment fault, a crash), the entire attempt is kept as an invalid attempt and is never merged, partially or wholly, with any later one. A restart means: a new `attempt_id`, a fresh Paradigm state, mission 1 again, the same prompts, the same order, the same protocol, with only the cause of the incident corrected in the harness. The previous attempt stays archived under its own `attempt_id` and is cited in the outcome, as runs C1 attempts 1 to 3 and run 12b attempt 1 are. Partial missions from an invalid attempt are never evidence, never cost extrapolation, and never part of D1.

## Addendum, before the first provider call: required instrumentation found at preflight

The pre-launch check of what a mission actually leaves behind found that the pilot as written could not produce its own dataset, and nothing had run yet. Recorded here rather than silently fixed.

What the engine kept before this addendum: `close_episode` returns before ingestion when an episode closes FAILURE or UNKNOWN, so every step of such an episode was discarded; what a SUCCESS episode ingested was `AgentDecisionRecord(features, action, source, phase, failure_kind, confidence, family, validated)`, an encoded vector without the goal text; and `save` persists the compiler, the templates and the counters, explicitly not the decision log, which carries neither goal nor state. The consequence for D1 is direct: the run would have produced verdicts and cost counters and no `(goal, state, action, outcome)` record. The consequence for B1 is worse than an absence. Training it on the persisted `features` would train it on the output of the current encoder, which is the very thing B1 exists to be compared against; the experiment would have been circular by construction.

What was added, optional and behaviorally neutral: `paradigm serve --trace-file <path> --attempt-id <id>`, off by default. A JSONL sink writes one `step` row per observed step (schema version, attempt, episode, stream episode, step, timestamp, raw goal, the full structured state, available actions, family, phase, teacher action, reflex candidate action, decision source, confidence, verified outcome with its evidence and verifier, failure kind, output kind, model calls, input and output tokens, decision and model latency) and one `episode` row per closed episode (status, verified flag, verifier, step count, family, stream episode). The write points are `observe`, and `close_episode` before the returns that discard FAILURE, UNKNOWN and empty episodes, so those are kept in the raw record. A `proposed_action` field was added to the decision log row so the reflex candidate is recorded next to the teacher's action on a shadow-sampled step, and the LaRuche adapter now passes input and output tokens separately instead of only their sum. No payload bytes are written: an image is recorded as its count and the verdict the adapter derived from it.

The retention rule is unchanged and is what the sink makes auditable: a SUCCESS episode's verified step may become positive evidence; FAILURE and UNKNOWN are kept for audit, hard negatives and analysis, and are never positive.

What was not changed: `decide`, the gate, thresholds, calibration, certification, promotion, trust, the equivalence contract, the outcome contracts, the missions, their order, the diversity criterion, the ceilings. The sink is written to and never read by the engine.

Evidence, in `tests/test_integration.py`: the sink records goal and state for every step; FAILURE and UNKNOWN episodes keep their steps in the trace while the compiler still rejects them; the reflex candidate is recorded on shadow-sampled steps; running 24 episodes with and without the sink produces the same decision log, the same counters, the same trust manifest and the same reflex version; the trace survives save and reload; and no image payload reaches the file. Full suite 88 passed, `ruff check --select E9,F` clean on the changed files. A smoke test drove the real `serve` path over HTTP with no provider, one SUCCESS and one FAILURE episode, and confirmed the FAILURE episode is absent from acquisition and present in the trace.

One incidental finding, recorded because it affects how the dataset is keyed: the engine's episode id is a millisecond clock plus the instance address, so two episodes closing inside the same millisecond share one id. Nothing about it was changed. The trace carries the monotonic `stream_episode` on every row instead, and the dataset key is `(attempt_id, stream_episode, step_id)`.

## Not done in this pilot

No B1 training or embedding fit of any kind. No promotion with behavioral effect. No new certification rule, gate, threshold or veto. No reuse of intent v1 or v2 as training or positive evidence. No fixing of the real D1 mission count before this run's numbers exist. No tag, no merge of `paradigm-integration`.

## Outcome, part 1: the code block of attempt `d1-pilot-a2` (camera block pending)

Attempt `d1-pilot-a1` is invalid and is not part of this outcome: `pytest` was not importable by the `python3` on PATH, so every code mission was scored FAILURE whatever the model did, and the model spent its budget working around the broken environment. It is archived whole with its own incident record and never merged with this attempt, under the rule fixed above. The correction that followed aligned the interpreter available to the harness and to the mission commands with an environment providing the dependency the missions already assume; it is not an aid to the model and not a change to the task.

Attempt `d1-pilot-a2`, fresh Paradigm state, `--shadow-schedule 1-24:1.0`, so no reflex was ever replayed and every decision recorded is the teacher's. Code block, missions 1 to 12, no circuit breaker and no incident.

```text
code missions        SUCCESS 12   FAILURE 0   UNKNOWN 0      (12 / 12)
deliberative decisions   72       the counter the circuit breaker reads
actual model responses   46       the real provider cost
tokens                   587424   (input 575161, output 12263)
per mission              6.0 deliberative decisions, 48.9k tokens
exploitable validated transitions   28   (72 steps: 28 success, 44 unknown, 0 failure)
distinct action keys     3        shell_exec, file_read, file_list
distribution             shell_exec 17, file_read 10, file_list 1
templated keys           7        intra-tool diagnostic only
```

The two call counters are reported separately and are never merged under one term: a model response carrying several tool calls yields one teacher decision and several observed steps, so 72 and 46 measure different things. Run 11's reference on the same template A prompts is 5.9 calls and 56.4k tokens per mission, so the cost is back in range.

Reading of "distinct action key", fixed before the camera block ran: an action key is the tool or action type, not the templated `tool#args_hash`. The code block therefore contributes 3, not 7. The templated keys are kept as an intra-tool diversity diagnostic and do not count toward the threshold of 5, because five argument spellings of one tool would satisfy the letter of the criterion while giving B1 nothing that goes beyond a single tool.

Structural finding, recorded now and acted on only after the full pilot: the code domain produces real write actions, 10 `file_edit` and 1 `file_write` in the raw record, and the adapter marks every one of them `not_reflex_capable`, so **a write never becomes an exploitable positive transition**. The 44 unknown steps break down as 22 `not_reflex_capable`, 19 `batched_call` and 3 `no test report in output`. A representation conditioned on the action that never learns on write actions is cut off from a part of the procedures that matters, which is a real question for the sizing and the design of the full D1 collection. Nothing about the pilot was changed on the strength of it.

The three clauses on the code block alone, with no conclusion drawn about the pilot as a whole: at least 2 keys in this domain, 3, met; at least 1 structural negative in this domain, 3 (the template C missions, closed SUCCESS with no edit), met; no action key above 70% of validated steps, maximum share 46%, met. The clause requiring 5 distinct keys across both domains is pending the camera block.

## Outcome, part 2: the camera block of `d1-pilot-a2`, and the state at the end of the session

The camera block ran and was stopped by hand during mission 21. Its three positive missions (13, 16, 19) each spent about 305 seconds and closed FAILURE, while the five negative controls that closed (list only, negation, preview, future, screenshot) all passed in seconds. The trace holds four verified `camera list` steps, all under one template key, and **not one observed `camera capture`**: a call that blocks until the tool gives up is never executed, so Paradigm never sees it and a positive mission cannot satisfy its contract.

The cause was then isolated at no provider cost, and it is not the launch context that run C1 identified:

```text
permissions   Terminal and the desktop app both authorized, no prompt appears      not TCC
nokhwa        list succeeds, capture blocks, from Terminal.app                     PREFLIGHT FAIL at 30s
ffmpeg        AVFoundation directly, no nokhwa involved: 3 devices enumerated,
              capture blocks                                                       TIMEOUT at 25s
```

Two independent capture paths, launched from two different contexts, fail identically. The machine enumerates its cameras and delivers frames to nothing. The CoreMediaIO services had been up since the boot that followed the system upgrade, the same upgrade that had reset the Xcode license agreement earlier in the session. The fix belongs to the machine, a reboot or a restart of the camera services, and is not an experimental parameter.

Consequently `d1-pilot-a2` is invalid in its entirety under the rule that was in force when the fault occurred, its clean 12 of 12 code block included, and the amendment above does not rescue it.

### State at the end of the session

```text
a1   invalid   pytest missing from the interpreter on PATH        9 missions, 132 decisions, 1.70M tokens
a2   invalid   camera delivers no frames on this machine          20 missions, 93 decisions, 657k tokens
a3   not started, blocked on the mandatory camera preflight
```

Nothing from either attempt is pilot evidence, cost extrapolation, or D1 data. Neither the missions, the prompts, the order, the contracts, the ceilings nor the diversity criterion has been touched since they were frozen; the only protocol changes are the two recorded amendments, both prospective, and both decided before knowing what `a3` would give.

What the two invalid attempts did establish, and what is worth carrying forward:

- The instrumentation works and earns its cost. In `a1` the raw trace showed that the contract could not be satisfied by any trajectory; in `a2` it showed that no capture was ever observed while the `list` calls passed. Neither diagnosis is available from the compiler's buffer, which keeps encoded features and discards FAILURE episodes.
- The code domain runs at run 11's cost, about 6 deliberative decisions and 49k tokens per mission, and yields about 2.3 exploitable validated transitions per mission over 3 action keys.
- Write actions never become exploitable positive transitions, by construction of the adapter. This is the finding most likely to change the design of the full D1 collection, and it is not a defect of the pilot.
- A hardware precondition must be proven before an attempt starts, not discovered by missions. The preflight now bounds the call, decodes the frame and checks its dimensions.

### To resume

1. Reboot the Mac, or restart the camera services, then run `camera_preflight` alone. It costs nothing and calls no provider.
2. Start `a3` only on `PREFLIGHT OK` with real PNG dimensions, from mission 1, code block then camera block, under `a3-code-1` and `a3-camera-1`.
3. Report the raw numbers over the 24 missions before any verdict: missions by status, deliberative decisions and actual model responses kept separate, tokens, exploitable validated transitions, distinct action keys per domain, the maximum share of one action, at least one structural negative per domain, and how many transitions are lost to `not_reflex_capable`.
4. Only then the three diversity clauses, and only then the sizing of the real D1.
