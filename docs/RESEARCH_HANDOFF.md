# Research handoff

Written at the close of the session that ran the LaRuche integration line (runs 11 to 12b, C1) and the intent benchmark line (C2 to C7, C4b), and extended at the close of the session that opened the D1 branch. It lets a new agent resume without rereading the history. Everything below is on `main`, after the frozen release `v0.2.0`; the pre-registration files under `results/` carry each outcome, including the ones that did not hold.

## Current status

- Paradigm is a working research prototype. The procedural reflex works in a real agent with a real provider: validated deliberative experience is compiled, certified per family, promoted atomically, and replayed only inside the trusted region, with fallback to the model everywhere else.
- The natural-language line C1 to C4b is finished. No further tuning of the camera or intent benchmarks is to be launched.
- The D1 branch is open: validated-experience collection for a procedural representation conditioned on the action. The cost and diversity pilot is pre-registered and has not yet produced a valid attempt; two attempts were invalidated by faults outside the experiment, one environmental and one hardware. Section "D1 state" has everything needed to resume.
- B1, the learned representation itself, has not been started and must not start before D1 is finished and frozen.

## Frozen release

`v0.2.0`, commit `6e611a2`. Do not modify or retag. `p2.4-type-b-baseline` (`78e0a25`) and `laruche-family-scoped-run11` (`59a46a5`) are milestones, not to be moved. All research described here is post-`v0.2.0` on `main`, without a new tag.

## Important post-v0.2.0 results (numbers as recorded, no reinterpretation)

Run 11 (`results/integration_laruche/run11_family_scoped.md`): 24 of 24 missions verified; first family-scoped activation at mission 16 (`start`, `file_edit:success`); 15 reflex decisions, 15 model calls avoided, 0 false fast paths, 0 unsafe actions; candidate at 20 rejected because an active family regressed on its probes (15 of 16).

Probe re-certification (`probe_recertification_prereg.md`): unsupported as pre-registered; a single fresh held-out trace still dominated an otherwise passing probe set.

Sparse held-out sensitivity (`sparse_heldout_prereg.md`): one fresh observation is insufficient evidence; no minimum fresh support above 1 was identified (every `m` in {2, 3, 5, 8} gave the same candidate decisions on the records).

Run 12, shadow sampling (`shadow_sampling_prereg.md`, `run12_shadow_report.md`, `run12_shadow_ledger.md`): 36 of 36 verified; fresh evidence restored (2 to 7 fresh traces per active family); 53 shadow-sample calls against 17 reflex decisions, net negative economics as scheduled; no preferred `min_fresh_support`; the pre-registered veto conflated teacher disagreement with regression.

Triadic veto (`triadic_veto_prereg.md`): distinguished a candidate regression (point 25) from an alternative valid trajectory (point 33); did not fix the held-out branch, where literal equality with the teacher still scores the alternative as an error.

Behavioral equivalence (`behavioral_equivalence_prereg.md`): contract `laruche-equivalence-1`, one class (TEST_EXECUTION); point 33 literal agreement 0.857 to behavioral 1.000; point 25 (a true regression) stayed rejected; runs 9 and 11 replayed identically at the decision level.

Run 12b (`live_equivalence_prereg.md`, `run12b_equivalence_report.md`): attempt 1 invalidated by a persistence fault (non-picklable callback), preserved as `run12b_attempt1_*`; retry 24 of 24 verified; the version 2 promotion's authorized family set depended on the contract (`file_edit` activated with it, not without); no live discrimination of a true regression under the same contract was observed; historical probe semantics are frozen (a probe set is scored under the contract it was frozen with).

Camera C1 (`camera_prereg.md`, `runC1_camera_report.md`): phase 1, 47 of 48 correct under the contract, 1 teacher failure; the learned sub-procedure is `camera list` then `camera capture index 0` (not the first decision from language, which stayed deliberative); 2 verified reflex captures; 0 false fast paths after activation (N2, N3, N4 rejected by the OOD gate, not by the tree, since finishing calls are never observed); phase 2, 8 of 8 missions with no camera execution and no blind replay after the tool was removed. Three harness attempts failed before the valid one and are preserved as faults (unanswered approvals, a home-directory scan, a personal-directory listing by a read tool the approval gate never saw).

Intent benchmark line (`results/intent_bench/`, one `PREREG_*.md` per experiment with its outcome, `SYNTHESIS.md` for the whole):

- C2: the LaRuche memory embedding `nomic-embed-text-v1.5` groups by topic more than by procedural intent; unsupported.
- C3: lexical + MiniLM paraphrase helps; best pre-registered improvement 0.26 to 0.37 unseen-positive recall under the gate at the same 4 hard false fast paths; partially supported.
- C4: explicit temporality and actionability features (7 deterministic dimensions); supported; k-NN recall 0.37 to 0.46, false fast paths 4 to 2, selective accuracy 0.93 to 0.96.
- C5: trusted sub-regions; unsupported under the existing criterion; R2/R4 reached 0.98 and kept one hard false fast path.
- C6: action-contract scoring; the zero-shot NLI failed for this task; the reranker is useful only in combination; `A+S+E_RERANK+T` improved the signal; H1 partially supported, H2 unsupported.
- C6R: prospective replication of the one selector-feasible configuration; NOT REPLICATED; PRIMARY precision 0.89, 0 hard false fast paths, coverage 0.08 against 0.15 required; the failure is the gate under distribution shift.
- C7: exploratory gate comparison; no gate selected for C7R; G1 (class-conditional Mahalanobis) meets the grid on v1 out of fold and collapses on v2; permissive gates restore coverage and expose classifier errors; none satisfies safety and coverage on both distributions.
- C4b: subordinate temporal clauses handled from grammar, not from the dataset; 0 hard temporal false fast paths on v2; neutral on the C4 protocol; did not solve transport; the line is CLOSED.

## Architectural conclusions to preserve

```text
semantic similarity != procedural intent != immediate executability != authorization
capability != trust != authorization != availability
teacher disagreement != reflex invalidity != mission failure
literal action identity != behavioral correctness
freshness != evidential sufficiency
```

Structural limits of the evidence, recorded: control calls (finishing) are never observed, so a family that ends there has no negative examples; a benchmark repeats identical requests while a product sees each phrasing once, so the gate's behavior under distribution shift is the quantity that matters.

## What not to do next

- Do not keep tuning the camera or intent benchmarks v1/v2.
- Do not lower the certification threshold because an observed precision is close to it.
- Do not replace Paradigm's gate globally on the strength of a language result; test any gate change separately on runs 11, 12 and C1.
- Do not treat intent v1/v2 as validated experience for training the next branch; they are benchmarks.
- Do not fine-tune on test sets; do not reuse v2 as a prospective set (it was scored once by C6R and is no longer virgin).
- Do not rewrite historical probe semantics; a probe set keeps the contract it was frozen with.
- Do not merge the LaRuche branch `paradigm-integration` unless explicitly requested.
- Do not tag a new release unless explicitly requested.
- Do not revive any part of an attempt declared invalid, `a2`'s clean code block included; an amendment never applies retroactively.
- Do not start a run that depends on the camera without `camera_preflight` passing first.
- Do not merge the two call counters under one term; deliberative decisions and actual model responses are different quantities.
- Do not start B1 before D1 is finished and frozen.

## Next research branch

Question, verbatim:

> Paradigm can learn from validated experience a procedural representation conditioned on the action that generalizes to new formulations, distinguishing relevance, immediate executability, and authorization, without stacking domain-specific linguistic rules?

The longer form and the requirements are in `results/intent_bench/SYNTHESIS.md`, section 5. Sequence:

```text
D1 = validated-experience collection      (opened; cost and diversity pilot in progress, not finished)
B1 = learned procedural representation    (not started; candidate methods only: contrastive learning, SetFit, a small Paradigm-specific model; the branch is not "use SetFit")
```

D1, source: real LaRuche + DeepSeek missions; Paradigm observes only, no training or promotion during collection; the existing outcome contract stays authoritative; only verified successful experience can become positive evidence; capture per step `goal, state, candidate action, teacher decision, verified action outcome, episode outcome`. Fix the D1 size only after the cost and diversity pilot. B1's baseline is the current stack (`A+S+E+T`, current classifier and gate) under the same certification protocol, then a prospective replication on a new distribution before any claim of generalization. No B1 work of any kind before D1 is finished and frozen.

## D1 state (everything is in `results/d1_experience/`)

The pilot is pre-registered in `pilot_prereg.md`, with its outcome sections; the 24 missions, their order and their verbatim prompts are frozen in `missions.json` (sha256 in `MANIFEST.md`) and read by the harness so it cannot drift from the pre-registration. 12 code missions (three request templates over the three bug variants of `paradigm_demo`), then 12 camera missions (capture, list only, preview, negation, future, past, conditional, screenshot, unrelated).

Two attempts have run, both invalid, both archived whole with their incident record, neither merged with anything:

```text
a1         invalid    pytest not importable by the python3 on PATH, so every code
                      mission scored FAILURE whatever the model did
a2         invalid    camera enumerates devices and delivers no frame to any process
a3-code-1  valid      12 of 12 verified, 65 deliberative decisions, 48 model
                      responses, 584k tokens, 69 steps, 33 exploitable transitions
a3-camera-1  not run  external capture-system failure, not a scientific failure
```

The pilot is closed with the code domain completed and valid and the camera domain not run. The camera's capture path is broken on the machine, outside Paradigm and LaRuche: the native tool and `ffmpeg` both start a session, light the indicator and receive no frame, on the built-in and Continuity cameras alike, from two launch contexts, with permissions granted, surviving a reboot, with no third-party CoreMediaIO plugin installed. `a3-camera-1` stays available unchanged and can run later under the block-level rule.

The feasibility test on the frozen `a3-code-1` trace (`experiments/decision_model_v0/`) gave a clear signal on a narrow question: `goal + state` reaches 0.754 top-1 against 0.362 for `goal only` and a trivial baseline of 0.420, over 69 decisions, 12 missions, leave one mission out, five seeds. The state carries the procedure. The arm that scores each candidate action lands at 0.652, below the plain multi-class arm on the same features, but the two families do not share a loss, so that judges the formulation and not the architecture; a listwise loss over the candidates would be the fair test. The block carries two distinct goal texts, so nothing there speaks about language.

`a2`'s code block was clean (12 of 12 verified, 72 deliberative decisions, 46 actual model responses, 587k tokens, 28 exploitable validated transitions over `shell_exec`, `file_read`, `file_list`) and is invalid all the same, because the rule in force when the camera fault occurred invalidated the whole attempt. It is not revived by the later amendment.

Instrumentation added for D1, and the reason it exists: the engine's buffer keeps encoded features and ingests SUCCESS episodes only, so the goal text and every step of a FAILURE or UNKNOWN episode were lost at close, and training B1 on those features would be circular. `paradigm serve --trace-file <path> --attempt-id <id>` (off by default) writes a JSONL row per observed step and per closed episode, FAILURE and UNKNOWN included, with the raw goal and the full structured state. It is written to and never read by the engine; a run with it produces the same decision log, counters, trust manifest and reflex version as a run without it. No image payload is ever written.

Two protocol amendments, both decided before knowing what the next attempt would give, both prospective and never retroactive: a fault demonstrated to be confined to one domain invalidates only its block, under five conditions, with two-level attempt ids (`a3-code-1`, `a3-camera-1`); and no attempt that depends on physical hardware starts until a preflight proves the device works at no provider cost.

Findings already worth carrying, from invalid attempts but independent of their faults:

- The code domain costs about 6 deliberative decisions and 49k tokens per mission, run 11's range, and yields about 2.3 exploitable validated transitions per mission over 3 action keys.
- Write actions (`file_edit`, `file_write`) are marked `not_reflex_capable` by the adapter, so **a write never becomes an exploitable positive transition**. A representation conditioned on the action that never learns on the actions that change the environment is cut off from a part of the procedures that matters. This is the question most likely to change the design of the full collection, and it is open.
- The two call counters, deliberative decisions and actual model responses carrying usage, measure different things and are never merged: a model response carrying several tool calls yields one teacher decision and several observed steps.
- An action key, for the diversity criterion, is the tool or action type, not the templated `tool#args_hash`; templated keys are an intra-tool diagnostic only.

To resume: reboot or restart the camera services, run `camera_preflight` alone, and start `a3` from mission 1 only on `PREFLIGHT OK` with real PNG dimensions. The harness is `laruche-essaim/examples/paradigm_d1_pilot.rs` on the LaRuche branch `paradigm-integration`, run once per domain against one service and one fresh state; the camera block must be launched from Terminal.app. `results/d1_experience/summarize_pilot.py` reads an attempt's trace and prints the raw numbers before any interpretation.

## Dataset provenance

Intent v1 (`phrases.jsonl`, sha in `DATASET_SHA256.txt`) and v2 (`phrases_v2.jsonl`, `DATASET_v2_SHA256.txt`) are synthetic benchmark datasets: `gen_a` (assistant of the session, ids `gen_a-*`, groups `c*`), `gen_b` (a second language model, groups `g*`), `synthetic_user_style` (the second model simulating the user's style, groups `u*`). No human-written slice was ultimately used. Both are immutable; a correction is a new version with a new hash. v2 was prospective for C6R and is no longer virgin.

## Experimental discipline

Pre-register before scoring; freeze and hash datasets and models before prospective tests; preserve negative results; label exploratory against confirmatory; require a new distribution for a prospective replication; no post-hoc threshold tuning; report a metric bug as a bug, never as a protocol change.

## LaRuche state

Repository `/Users/infinition/Coding/laruche/laruche`, branch `paradigm-integration`, pushed to `origin` (`https://github.com/infinition/LaRuche`), not merged into `main`; last commit `1575651`. The Paradigm bridge is `laruche-essaim/src/paradigm_pont.rs` (decorators `FournisseurParadigm`, `OutilsParadigm`, wired in `butinage_pont.rs::executer_avec_bilan` when `LARUCHE_PARADIGM_URL` is set; transport errors fail open to the model; `LARUCHE_PARADIGM_CLOSE=external` lets the harness close the episode; the number of images is forwarded with each observation). Examples: `paradigm_demo.rs` (pytest missions), `paradigm_camera_demo.rs` (camera benchmark, native `camera` tool, blocking guard on every tool confining paths to the workspace, 30-iteration ceiling, `preflight` mode), `camera_preflight.rs`, and `paradigm_d1_pilot.rs` (the D1 pilot harness: reads the frozen `missions.json` from the Paradigm repository so it cannot drift from the pre-registration, one invocation per domain, reuses each domain's approval gate and guard hook unchanged, reads the circuit-breaker counters from `/v1/telemetry` after every mission). `camera_preflight.rs` now bounds the capture call, decodes the frame and checks its dimensions, and exits non-zero on anything else, so a blocked capture path is found in seconds instead of by benchmark missions. The camera process must be launched from Terminal.app (AVFoundation needs an event loop the desktop-app shell lacks); launching it through `osascript` with `tell application "Terminal" to do script` works and was used, though it does not fix a camera that delivers no frames at all. Behavioral equivalence is wired live on the Paradigm side (`serve --equivalence laruche`); the persistence faults found in run 12b (non-picklable contract, unsaved episode counter, non-atomic state write) are fixed in Paradigm.

## Operational notes

- Paradigm service: `paradigm serve --port 8765 --state-file <file> --certification family_scoped [--shadow-schedule ...] [--equivalence laruche] [--trace-file <path> --attempt-id <id>]`; always a fresh state file for a new run.
- Observe-only collection, as D1 uses it: `--shadow-schedule 1-<n>:1.0`. At rate 1.0 every reflex-eligible decision is routed to the teacher, so nothing is ever replayed and no promotion has behavioral effect, using the mechanism validated in run 12 rather than new code.
- The DeepSeek key is read from `~/Library/Application Support/LaRuche/provider-profiles.json` (`profiles['Deepseek']['api_key']`) into `LARUCHE_API_KEY` only; never printed, never committed.
- The RTX box (`ssh rtx`) was unreachable from this Mac during the intent line (no route to host while another session could reach it); CPU was used for the encoders.
- Tests: `pytest -q` (88 tests, including the trace sink) on Python 3.14; lint `ruff check --target-version py311 --select E9,F` on the changed files (pre-existing F401/F841 in untouched files are known). Run them with the project venv: the `python3` first on PATH does not have pytest, which is what invalidated D1 attempt `a1`.
- Missions that shell out to `python -m pytest` need an interpreter that provides it. Put a venv with pytest first on the harness PATH, for the harness verification and for the model's own commands alike.
- The camera on this Mac enumerated its devices and delivered no frame to any process at the close of the session, through `nokhwa` and through `ffmpeg` alike, with permissions granted. Reboot or restart the CoreMediaIO services, then run `camera_preflight` before any run that uses the camera.
- In this shell `cc` is an alias, not the C compiler. Use `/usr/bin/cc` when testing whether linking works, otherwise the answer is meaningless.

## Repository state at handoff

Tree clean; `main` in sync with `origin/main`; tags `v0.1.0`, `v0.2.0`, `p2.4-type-b-baseline`, `laruche-family-scoped-run11` unchanged, no new tag. Hygiene checks done: no credentials, no personal file names from the failed camera attempts, no model weights or caches tracked (the 4.4 MB `c6r_frozen_model.pkl` is the frozen C6R artifact and belongs to the record), no forbidden names in commit messages; the one absolute home path in `camera_prereg.md` is the recorded text of a failed attempt's command and is kept as such.

The D1 session added `results/d1_experience/` (pre-registration, frozen mission set and its hash, manifest, summary script, and the two invalid attempts with their traces and incident records), the trace sink `src/paradigm/integration/trace.py` with its tests, and, in the LaRuche repository on `paradigm-integration`, the pilot harness and the hardened camera preflight. The attempt traces contain mission goals, tool names and verdicts, no credentials and no image payload; the workspace paths they carry are temporary directories created per mission.
