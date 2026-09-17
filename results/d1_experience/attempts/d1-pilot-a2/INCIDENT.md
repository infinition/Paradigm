# Attempt `d1-pilot-a2`: invalid, camera capture never returns on this machine

Stopped by hand during mission 21, after three positive camera missions had failed identically. Kept whole and never merged with any later attempt, under the rule fixed in `pilot_prereg.md` before the first provider call.

## What the code block had produced first

Missions 1 to 12, clean, no breaker, no fault: 12 of 12 verified, 72 deliberative decisions, 46 model responses carrying usage, 587,424 tokens, 28 exploitable validated transitions over 3 distinct action keys (`shell_exec`, `file_read`, `file_list`). Those numbers are in the outcome section of the pre-registration and are not evidence for the pilot, because the attempt they belong to is invalid.

## Fault

`camera capture` never returns on this machine; `camera list` does.

In the camera block the three positive missions (13 `K1`, 16 `K2`, 19 `K3`) each spent about 305 seconds and closed FAILURE, and the trace contains **not one observed `camera capture` step**. What it does contain is four verified `camera list` steps, all SUCCESS, under one template key. A capture that blocks until the tool times out is never executed, so Paradigm never observes it and the positive missions cannot satisfy their contract.

Isolated from the model, from Paradigm and from the pilot with `camera_preflight`, a binary that calls the tool directly and records nothing, launched under Terminal.app:

```text
list:    success=true   1 camera(s): index 0: Caméra MacBook Pro
capture: blocks indefinitely, killed by hand
```

So the fault is the machine's capture path, not the harness, not the adapter, not the missions, and not the launch context that C1 identified: this run was started under Terminal.app precisely to give AVFoundation its event loop, and `list` proves the device is found. Candidate causes, none of them verified here: the camera permission for the hosting application, or a regression in the native capture path after the recent system upgrade, the same upgrade that had also reset the Xcode license agreement earlier in this session.

## Camera block as recorded before the stop

```text
episodes closed        8 of 12 (missions 13 to 20)
  success              5   all negative controls (list only, negation, preview, future, screenshot)
  failure              3   every positive capture mission
observed camera steps  4   all `camera list`, all verified SUCCESS
observed captures      0
```

Attempt totals at the stop: 80 steps, 53 model responses carrying usage, 668,712 tokens.

## Consequence

Under the frozen rule the whole attempt is invalid, the code block included, and no part of it is pilot evidence, cost extrapolation, or D1 data. The restart begins at mission 1 with a fresh state and a new `attempt_id`, once the capture path works, and is verified with `camera_preflight` before any provider call rather than after twelve missions.

## Note for the restart

`camera_preflight` is the cheap check that was available and was not run before the camera block. It costs nothing, uses no provider, and would have caught this in seconds. Running it is added to the launch sequence of the next attempt.
