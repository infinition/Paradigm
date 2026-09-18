# Attempt `d1lang-1`: invalid, measurement fault in the outcome check

Stopped by hand at mission 30, as soon as the pattern was identified. Kept whole and never merged with any later attempt, under the rule fixed before the first provider call.

## Fault

Every diagnose-only mission closed FAILURE while the model had done exactly what was asked.

```text
I1  16 of 16 SUCCESS      contract: the harness's own pytest run
I2  14 of 14 FAILURE      contract: the workspace byte-identical
```

The trace shows what those episodes actually contained: `file_list`, `file_read` and `shell_exec`, and nothing else. No `file_edit`, no `file_write`, and the harness's own write counter read zero on every one of them. The model diagnosed without modifying, which is the procedure those missions ask for.

The fault is in `workspace_untouched`. It compared the directory entries against the fixture files and treated any entry that was not a fixture as a file the model had added. LaRuche keeps a session store in the working directory, so a `sessions` directory appears in every workspace; it is an artifact of the harness, not an action of the model. The check saw it, found it absent from the fixture map, and returned false. The model itself made the fault visible, in a mission where it listed the workspace with `find . -type f -not -path './sessions/*'`.

`__pycache__` was already excluded by name, which is why the bug did not show in an isolated reproduction outside LaRuche: without a session store, the check passes.

The repair intentions were unaffected, since their contract is the pytest run and never the directory listing.

## Recorded before the stop

```text
episodes closed        30       16 success, 14 failure
steps observed        260
model responses       175
tokens            2539761
writes observed        13       all inside repair missions
```

None of it is evidence. Not the verdicts, which are wrong for half the episodes; not the cost, which belongs to an invalid attempt; not the arms, which were never run.

## Correction, and the test that proves it

Directory entries are skipped, whatever their name, since a fixture is always a file. `__pycache__`, `.pytest_cache` and the session store are then all ignored generically instead of by a name list, and a real change is still caught.

The corrected function was checked against six cases before relaunching, in isolation:

```text
intact                                    true
with __pycache__                          true
with the session store, the d1lang-1 bug  true
with session store, pycache and dotfiles  true
a file added by the model                 false
a file modified by the model              false
```

The protocol is untouched: missions, formulations, crossing plan, splits, contract semantics, arms, reading order and ceilings are all unchanged. Only the implementation of the check was wrong, and only it was corrected.

## Note for the restart

The pattern was visible at mission 17, the first mission of the second intention, and was caught at mission 30 because the run was being watched. It cost 2.54M tokens. A one-mission dry run of each intention against the contract, before committing a block, would have cost about 100k and is the obvious thing to add to the launch sequence, exactly as the camera preflight was added after the pilot's camera block.
