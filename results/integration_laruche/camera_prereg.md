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
