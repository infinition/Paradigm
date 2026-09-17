# Offline counterfactual audit: probe-based re-certification

Source of truth: `engine_state_family_scoped_after_24.pkl` (tag `laruche-family-scoped-run11`). Frozen probes: `laruche:file_edit:success:other` 16, `laruche:start:none:none` 5. No threshold, split, family definition, probe set or historical artifact was modified; the replay works on deep copies.

## Compile point 20

Recorded verdict: rejected (active_family_regressed:laruche:file_edit:success:other,laruche:start:none:none). Replay with the rule off: rejected (active_family_regressed:laruche:file_edit:success:other,laruche:start:none:none). Reproduced exactly: yes.

Replay with the rule on: **rejected** (active_family_regressed:laruche:file_edit:success:other); version after: 1; active families after: `laruche:file_edit:success:other`, `laruche:start:none:none`.

| family | evidence | train / held-out | probes | coverage | agreement or sel. acc. | ECE | gate acc. | verdict | reason |
|---|---|---|---|---|---|---|---|---|---|
| `laruche:file_edit:success:other` | held-out | 15 / 1 | 16 | 1.000 | 1.000 | 0.000 | 1.000 | rejected | retention |
| `laruche:file_list:success:other` | none | 1 / 0 |  | n/a | n/a | n/a | n/a | insufficient | no_held_out_evidence |
| `laruche:file_read:success:other` | held-out | 4 / 1 |  | 1.000 | 1.000 | 0.500 | 1.000 | rejected | calibration |
| `laruche:shell_exec:failure:other` | held-out | 3 / 4 |  | 1.000 | 0.750 | 0.000 | 1.000 | rejected | quality |
| `laruche:shell_exec:success:other` | none | 1 / 0 |  | n/a | n/a | n/a | n/a | insufficient | no_held_out_evidence |
| `laruche:shell_exec:success:tests_failed` | held-out | 4 / 4 |  | 1.000 | 1.000 | 0.000 | 1.000 | active | quality_trust_retention_pass |
| `laruche:shell_exec:success:tests_passed` | held-out | 7 / 1 |  | 1.000 | 1.000 | 0.167 | 1.000 | rejected | calibration |
| `laruche:start:none:none` | probes_only | 5 / 0 | 5 | 1.000 | 1.000 | 0.000 | 1.000 | active | probe_recertified |

## Compile point 24

Recorded verdict: rejected (active_family_regressed:laruche:file_edit:success:other,laruche:start:none:none). Replay with the rule off: rejected (active_family_regressed:laruche:file_edit:success:other,laruche:start:none:none). Reproduced exactly: yes.

Replay with the rule on: **rejected** (active_family_regressed:laruche:file_edit:success:other); version after: 1; active families after: `laruche:file_edit:success:other`, `laruche:start:none:none`.

| family | evidence | train / held-out | probes | coverage | agreement or sel. acc. | ECE | gate acc. | verdict | reason |
|---|---|---|---|---|---|---|---|---|---|
| `laruche:file_edit:success:other` | held-out | 16 / 1 | 16 | 1.000 | 1.000 | 0.000 | 0.000 | rejected | trust |
| `laruche:file_list:success:other` | none | 1 / 0 |  | n/a | n/a | n/a | n/a | insufficient | no_held_out_evidence |
| `laruche:file_read:success:other` | held-out | 5 / 2 |  | 1.000 | 0.000 | 1.000 | 0.500 | rejected | quality,calibration,trust |
| `laruche:shell_exec:failure:other` | held-out | 6 / 6 |  | 1.000 | 0.667 | 0.167 | 0.833 | rejected | quality,calibration |
| `laruche:shell_exec:success:other` | none | 1 / 0 |  | n/a | n/a | n/a | n/a | insufficient | no_held_out_evidence |
| `laruche:shell_exec:success:tests_failed` | held-out | 6 / 3 |  | 1.000 | 0.667 | 0.333 | 1.000 | rejected | quality,calibration |
| `laruche:shell_exec:success:tests_passed` | held-out | 8 / 3 |  | 1.000 | 1.000 | 0.095 | 0.667 | active | quality_trust_retention_pass |
| `laruche:start:none:none` | probes_only | 5 / 0 | 5 | 1.000 | 1.000 | 0.000 | 1.000 | active | probe_recertified |

## Negative control at 24, rule on

Every training trace of `laruche:file_edit:success:other` relabeled with another family's most frequent action; probes untouched. Verdict: **rejected** (active_family_regressed:laruche:file_edit:success:other).

| family | evidence | train / held-out | probes | coverage | agreement or sel. acc. | ECE | gate acc. | verdict | reason |
|---|---|---|---|---|---|---|---|---|---|
| `laruche:file_edit:success:other` | held-out | 16 / 1 | 16 | 1.000 | 0.000 | 0.750 | 0.000 | rejected | quality,calibration,trust,retention |
| `laruche:start:none:none` | probes_only | 5 / 0 | 5 | 1.000 | 1.000 | 0.000 | 1.000 | active | probe_recertified |

## Checks

- 20_reproduced: pass
- 24_reproduced: pass
- 20_still_rejected: pass
- 24_promoted: FAIL
- 24_start_on_probes: pass
- 24_file_edit_active: FAIL
- 24_tests_passed_activated: FAIL
- 24_active_families_kept: pass
- poison_rejected: pass
- discriminative: FAIL

## Conclusion: unsupported
