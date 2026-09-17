# Attempt `d1-pilot-a1`: invalid, harness fault

Stopped by hand during mission 10 of the code block, after the fault below was identified. Kept whole and never merged with any later attempt, under the rule fixed in `pilot_prereg.md` before the first provider call.

## Fault

`pytest` is not importable by the `python3` on this machine's PATH:

```text
/opt/homebrew/opt/python@3.14/bin/python3.14: No module named pytest
```

Two consequences, both fatal to the attempt:

1. The harness verifies a code mission with `python3 -m pytest -q -p no:cacheprovider` and scores SUCCESS from its exit status. With no pytest module the command always fails, so **every code mission was scored FAILURE whatever the model did**. The outcome contract could not be satisfied by any trajectory.
2. The missions instruct the model to run `python -m pytest -q` itself. It hit the same missing module, and spent its budget searching for a way around it. The recorded cost is therefore the cost of an agent fighting a broken environment, not the cost of the pre-registered task.

This is the same class of fault as run C1's attempts 1 to 3: the harness, not Paradigm, not the missions, not the model.

## What was recorded before the stop

```text
episodes closed         9 of 12 code missions, all FAILURE
steps observed          160
step outcomes           22 success, 138 unknown, 0 failure
model calls             132 (telemetry), 110 carrying usage in the trace
tokens                  1 696 578
per mission             about 14 calls and 188k tokens
```

For comparison, run 11 spent 5.9 calls and 56.4k tokens per mission on the same template A prompt and the same three bug variants. The inflation is the fault, not a property of the task.

None of these numbers is pilot evidence. They are not cost extrapolation, they do not count toward the diversity criterion, and they are not part of D1.

The trace itself is well formed and was not the problem: 160 step rows carrying `goal_raw`, the full `state_raw`, the teacher action, the verified outcome and the token split, plus 9 episode rows, all under `attempt_id: d1-pilot-a1`. The sink behaved as specified, including keeping all 9 FAILURE episodes that the compiler discarded.

## Cause corrected before the restart

The mission process gets a PATH whose first entry provides both `python` and `python3` with pytest available, so that the harness's verification and the model's own test command resolve to the same working interpreter. Checked before relaunching: the corrected interpreter reports `1 passed` on a corrected `calc.py` and `1 failed` on the injected bug, so the verification discriminates again.

Nothing else changes. Missions, prompts, order, outcome contracts, ceilings, the circuit breaker, the diversity criterion and the certification parameters are untouched, and the restart begins at mission 1 with a fresh Paradigm state and a new `attempt_id`.

## Note on the ceiling, recorded but not acted on

At the moment of the stop the attempt stood at 132 model calls and 1.70M tokens for 9 missions, so the pre-registered breaker (200 calls, 2M tokens) would have fired during the code block. Under a working environment the expected cost is run 11's, about 6 calls and 56k tokens per mission, which leaves the 24 missions inside the ceiling. The ceiling was not changed on the strength of an invalid attempt.
