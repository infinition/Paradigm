# Run 11: fresh live run with family-scoped activation

One fresh experiment, pre-registered after the offline audit (`family_audit.md`): fresh Paradigm state, same workspace and bug variants, same DeepSeek model (`deepseek-v4-flash` through LaRuche's OpenAI-compatible path), same guard hook, same canonicalization, same thresholds, family-scoped certification enabled from mission 1, 24 missions. Nothing in the demo was changed.

Files: `run11_family_scoped_missions_1-24.log` (tool calls and per-decision routing), `run11_decision_log.json` (every decision row from the service), `run11_telemetry.json`, `engine_state_family_scoped_after_24.pkl` (compiler state with the four certification records).

## Outcome

| | value |
|---|---|
| missions verified by pytest | 24 / 24 |
| unsafe actions executed | 0 (one guard refusal in mission 24, a `python -c` probe of the original code; the model continued) |
| first promotion | mission 16, version 1 |
| active families | `laruche:start:none:none`, `laruche:file_edit:success:other` |
| reflex decisions | 15 (missions 17 to 24), all `shell_exec` replaying the canonical `python -m pytest -q` |
| reflex outcomes | 7 SUCCESS (post-edit test run, report read), 8 UNKNOWN (start-of-mission run, see below), 0 FAILURE |
| false fast paths | 0 |
| model calls avoided | 15 |
| candidates | 8 and 12 insufficient traces; 16 promoted; 20 and 24 rejected, incumbent kept |

## Certification records

Compile point 16 (32 train, 11 validation traces). The single tree, judged as a whole, fails the calibration floor (ECE 0.195, coverage 0.73 at threshold 0.8), which is the same verdict the whole-candidate rules gave in runs 9A and 9B. Judged per family:

| family | train / validation | actions | coverage | selective accuracy | ECE | gate acceptance | verdict |
|---|---|---|---|---|---|---|---|
| `laruche:start:none:none` | 3 / 2 (2 ep) | 1 | 100% | 100% | 0.000 | 1.00 | active |
| `laruche:file_edit:success:other` | 12 / 4 (4 ep) | 2 | 100% | 100% | 0.000 | 1.00 | active |
| `laruche:shell_exec:success:tests_failed` | 3 / 2 | 1 | 100% | 100% | 0.200 | 1.00 | rejected (calibration) |
| `laruche:file_read:success:other` | 3 / 1 | 2 | 100% | 0% | 0.750 | 1.00 | rejected (quality, calibration) |
| `laruche:shell_exec:failure:other` | 2 / 2 | 1 | 100% | 0% | 0.500 | 1.00 | rejected (quality, calibration) |
| `tests_passed`, `file_list`, `shell_exec:success:other` | 7 / 0, 1 / 0, 1 / 0 | | | | | | insufficient |

Two families activated with per-family threshold 0.0 (pure leaves, confidence 1.0); probe sets frozen for both (16 probes for `file_edit`, 5 for `start`).

Compile point 20: rejected. `start` had no deliberative held-out trace any more (the reflex served it in missions 17 to 20), so it came back `insufficient`; `file_edit` agreed with its probes on 15 of 16 (0.9375 against the 0.95 floor). `tests_failed` would have passed on its own (4 / 4, ECE 0). The incumbent v1 stayed.

Compile point 24: rejected. `start` again `insufficient`; `file_edit` passed its 16 probes (coverage 1.0, agreement 1.0) but its single new held-out trace, from the atypical mission 24, was outside the candidate gate (acceptance 0.0). `tests_passed` would have passed on its own (8 / 3, ECE 0.095, acceptance 0.67). The incumbent v1 stayed.

## Before and after activation

| segment | model calls per mission | tokens per mission | wall time per mission |
|---|---|---|---|
| missions 1 to 16 (no reflex) | 5.9 | 56.4k | 10.9 s |
| missions 17 to 23 (v1 active) | 4.3 | 37.4k | 7.2 s |
| missions 17 to 24 (with the outlier) | 6.0 | 54.6k | 15.6 s |

Mission 24 is an outlier: after the same start-of-mission replay as missions 17 to 23, the model spent 18 calls and 74.5 s on an elaborate self-verification (heredoc scripts, hashes of the test file) before finishing; its post-edit state was out of distribution, so only one reflex fired. The mission was still verified. Nothing in the record attributes this drift to the reflex; it is reported, not explained.

## Three facts the record makes explicit

1. The start-of-mission replay is reported UNKNOWN, not SUCCESS. LaRuche's shell tool returns only `Command exited with code 1` for a non-zero exit and drops the output, so a failing test run carries no report to verify. The model's own identical call gets the same result. This is why `start` had 5 validated traces out of 16 deliberative occurrences (the 5 were the missions where the model wrote `python -m pytest -q 2>&1 | tail -40`, which exits 0 and keeps the report; it canonicalizes to the same action as the bare command), and why the family activated on 5 traces: no per-family minimum count exists in the pre-registered criteria, and none was added.
2. After activation, an active family stops producing deliberative held-out evidence by construction (reflex steps are never labels). Under the rule as implemented, such a family is `insufficient` at every later compile point and blocks any replacement artifact, so no further family can be activated while it is served by the reflex. The frozen retention probes are the evidence meant for that case and passed 16 / 16 at 24; re-certifying an active family on its probes when it has no new held-out traces is the next refinement. It was not applied in this run.
3. The whole-candidate verdict and the per-family verdicts diverge exactly as predicted: the same tree is uncalibrated as a whole (ECE 0.195) and perfectly calibrated on the two consistent families (ECE 0.000), because the ECE of the whole is carried by the post-failure read families.
