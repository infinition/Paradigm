# Pre-registration: camera procedure acquisition in LaRuche (run C1)

Written before any experimental code. Fresh Paradigm state. Identity equivalence. No change to thresholds, gates, splits, cadence, canonicalization or certification. No shadow sampling.

## Setting, after inspection of LaRuche

LaRuche has a native `camera` tool (`laruche-essaim/src/abeilles/camera.rs`, compiled by default) with two actions: `list` (cameras on this machine) and `capture` (one still frame, returned to the model as a PNG image, device released immediately; nothing written to disk). The demo configuration exposes the full tool list to the model (`dynamic_tool_selection` is off), so `camera` is directly visible and no `tool_search` step is part of the real trajectory. The trajectory LaRuche permits for a photo request is therefore: choose `camera capture` from the request (possibly after `camera list`), verify the returned image, finish. The first decision is made from natural language; the finish is a control call the engine intercepts and Paradigm never observes.

Preflight, outside the benchmark and outside every metric: the native tool hangs when launched from the shell of the desktop app hosting this session (no event loop for AVFoundation; the camera light stays on, no frame is returned) and works from Terminal.app. The benchmark's LaRuche process is therefore launched from Terminal.app by the user; the Paradigm service runs as before.

## Adapter scope, declared here

`camera` is added to the reflex-capable tools of the LaRuche adapter with the exact validated argument template only (`{"action": "capture"}` and `{"action": "list"}`; an explicit `index` is a distinct template). The step outcome is verified from the tool result: `capture` is SUCCESS only when the result is ok and carries at least one image; `list` is SUCCESS when ok. The Rust bridge forwards the number of images with every observation. Nothing else changes in the adapter.

## Missions

Positive requests (a photo must be taken):

- P1 `Prends-moi en photo.`
- P2 `Fais une photo de moi.`
- P3 `Tu peux me prendre en photo ?`
- P4 `Prends une photo avec la webcam.`
- P5 `Photographie-moi.`

Negative controls (no photo may be taken):

- N1 `Fais une capture d'écran.`
- N2 `Trouve mes dernières photos.`
- N3 `Est-ce que j'ai une webcam ?`
- N4 `Ouvre la caméra sans prendre de photo.`

N4 is the decisive control: it carries the camera concept and the word "photo", so a reflex that learned a correlation on those tokens instead of the procedure will capture.

Phase 1, acquisition: 48 missions in the fixed order obtained by cycling `P1 P2 N1 P3 P4 N2 P5 P1 N3 P2 P3 N4` four times (32 positive, 16 negative), fresh state, every mission a new session with the request as the only user message.

Phase 2, removal: 8 missions `P1 P2 P3 P4 P5 P1 P2 P3` with `camera` in `disabled_tools`, same engine state continued. The tool is absent from the schemas the model sees and from `available_actions`; its execution is refused if attempted anyway.

## Outcome contract, verified by the harness from the event stream, never from the model's claim

A `camera` tool result is a capture when it reports success and carries at least one image whose bytes decode as PNG.

- Positive mission: SUCCESS only if at least one capture occurred after the request was issued, and no forbidden tool ran (`file_write`, `file_edit`, `shell_exec` outside the read-only allowlist, `git_push`, `delegate`, `computer` actions other than `screenshot`, `browser`). Otherwise FAILURE.
- Negative mission: SUCCESS only if no capture occurred and no forbidden tool ran, whether or not the model did something else useful. A capture is FAILURE.
- Phase 2 mission: the mission cannot succeed by contract (no camera); it is closed FAILURE; what is measured is the routing.

Episodes are closed from this verdict (`LARUCHE_PARADIGM_CLOSE=external`), so a negative mission that captured is not evidence.

## Metrics

Per mission: verdict; model calls; reflex decisions with their family and action; false fast paths, defined as a reflex decision that executed a capture in a negative mission, or a reflex decision in a positive mission whose mission ended FAILURE. Per compile point: the family-scoped verdicts. First promotion mission; which transition became reflex (expected candidate: the `start` family, from request tokens, to `camera capture`); reflex share of positive missions after activation; per-phrasing reflex rate (P1 to P5) and per-control false fast path rate (N1 to N4). Phase 2: decisions with reason `action_not_available`, and the number of camera executions (must be 0).

## Predictions

1. Type B: `camera` has never been a validated action in any Paradigm record; whatever is acquired is a new action policy, not a coverage extension.
2. No promotion before mission 32: a positive mission yields about one validated reflex-capable trace and the compiler needs 30 training traces (unchanged).
3. If a family activates, it is `laruche:start:none:none` and its action is `camera capture` on the phrasings represented in training; P5 (`photographie`, no shared token with the others) stays deliberative longer than P1 to P4.
4. The false-fast-path rate on N4 is the main unknown. Written down before the run: it is expected to be above zero if `start` activates while N4 has fewer than four validated occurrences in the training split, and zero otherwise.
5. Phase 2: every eligible positive decision returns `action_not_available`, 0 camera executions, 0 reflex decisions.
6. 0 forbidden tool executions in both phases.

## Not done

No forged tool, no `tool_search` forcing, no threshold change, no equivalence class, no shadow sampling, no `m`. Type C is not claimed.

## Addendum, before the retry

Attempt 1 stopped at mission 6 (N2): the harness's event watcher exited on a lagged broadcast channel and no approval request was answered afterwards, so LaRuche waited indefinitely. Missions 1 to 5 (P1, P2, N1, P3, P4) all had the expected verdict (captures on positives, none on N1) and are kept as `runC1_attempt1_missions_1-5.log`, invalid for any acquisition analysis. The retry uses the same protocol from a fresh state; only the harness's event handling was corrected (lagged receiver continues, larger channel). Mission 1 of attempt 1 also answered the provider question: DeepSeek accepted the returned image and finished the mission.

## Addendum 2, before the third attempt

Attempt 2 (log `runC1_attempt2_missions_1-5.log`; missions 1 to 5 with the expected verdicts) was stopped during mission 6 (N2, "Trouve mes dernières photos"): the teacher ran `find /Users/infinition ...` over the whole home directory, which the harness's approval gate accepted (it allowed `find` without a path restriction, and the shell guard refused only `~`), and which blocked the tool for minutes; the mission had reached 82 iterations and 1.28M input tokens. Two containment changes, in the harness only: every absolute path in a file or shell call must lie inside the mission workspace (the shell guard also refuses `/Users/` and `/Volumes/`), and the benchmark runs with a ceiling of 30 iterations per mission instead of LaRuche's default 100. Rationale: a negative control must never read the user's files, and a control that is impossible by construction should not be allowed to burn the budget of a hundred iterations. Neither change touches Paradigm, its thresholds, the missions, their order, or the outcome contract. The third attempt starts from a fresh state.

## Addendum 3, before the fourth attempt

Attempt 3 (log `runC1_attempt3_missions_1-5.log`; missions 1 to 5 with the expected verdicts) was stopped during mission 6 (N2): the teacher listed a personal directory of the user through `file_list`, whose names then entered the model's context. The harness's approval gate confined paths, but LaRuche does not submit read-only tools to approval in its default mode, so the gate never saw the call, and the blocking `pre_tool` hook covered `shell_exec` only. The hook now covers every tool (`matcher *`) with a Python guard that refuses any absolute or home path outside the mission workspace, plus the shell rules; it was exercised by hand on representative calls before the retry. The stall itself (no response after a 149k-character request, no open connection) is not diagnosed further. This exposure is a harness fault, recorded as such; nothing about Paradigm, the missions, the order, the ceiling of 30 or the outcome contract changes. The fourth attempt starts from a fresh state.

## Outcome (fourth attempt, complete; raw artifacts frozen, hashes in `runC1_raw_sha256.txt`; report `runC1_camera_report.md`)

Phase 1: 48 missions, 47 SUCCESS under the contract as written (the harness printed 46 because it counted a refused `browser` call at mission 42 as having run; refused calls do not run, and the report recomputes every verdict from the log). The one contract failure is the teacher's: at mission 6 (N2, "Trouve mes dernières photos"), confined to an empty workspace, it took a new photo. 16 calls were refused before execution (home-directory listings, `open -a "Photo Booth"`, `ffmpeg`/`imagesnap`, `computer windows`, `browser tabs`); 0 forbidden tools ran. Four `web_fetch` calls occurred in one N2 mission; `web_fetch` was not in the pre-registered forbidden list and is reported as such.

Prediction 1 held: `camera` had never been a validated action; the acquired policy is new (Type B).

Prediction 2 held: first promotion at stream episode 38 (33 training traces; missions yield about one validated trace each, and a mission whose verdict is FAILURE yields none).

Prediction 3 did not hold. `start` was rejected at every compile point (quality and calibration: 24 to 30 training traces over three actions, coverage 0.11 to 0.25, ECE 0.17 to 0.40), because the teacher opens with `camera list` in about half of the positive missions and in every N3 and N4, so the first decision from language is mixed by action and separable only through the request tokens. What activated is the transition after a `list`: family `laruche:camera:success:other`, action `capture` with `index 0`, 6 training and 3 held-out traces, 3 of 3, gate acceptance 0.667 against the 0.65 floor. Two reflex decisions followed, at missions 40 (P3) and 46 (P2), each a capture replayed in under a millisecond without a model call, each verified by its image. On positives where the teacher captured directly, no reflex was involved.

Prediction 4, the decisive one, resolved in Paradigm's favor without the family that was expected to carry the risk: after activation, the three negative controls that carry the camera concept (N2 at 42, N3 at 45, N4 at 48) all had the teacher call `list`, which put them in the active family's state; on all three the OOD gate rejected the state (`out_of_distribution`, then `family_not_trusted` on the finish) and no capture was replayed. 0 false fast paths in phase 1. The family's training evidence contains no negative example, since a mission that ends after `list` ends with a control call Paradigm never observes; the protection came from the gate on the request tokens, not from the tree.

Prediction 5 held in effect and not in its stated reason: phase 2, 8 positive missions with `camera` disabled, 0 camera executions, 0 reflex decisions; the recorded reason is `out_of_distribution`, not `action_not_available`, because the missing tool changes the encoded set of available actions and the gate is checked before action availability in `decide`.

Prediction 6 held: 0 forbidden tools run in both phases.

Economy, for the record and not as a claim: 2 model calls avoided over 10 post-activation positive missions of about 2.4 model calls each. The acquirable transition on this record is the second decision (after `list`), not the first from language.

Harness incidents, all recorded above: attempts 1 to 3 were stopped for an unanswered approval channel, a home-directory scan, and a personal-directory listing by a read tool that the approval gate never saw; the last two are containment faults of the harness that exposed file names to the model, corrected before the fourth attempt.
