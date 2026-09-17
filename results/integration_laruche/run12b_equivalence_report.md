# Run 12b report: live run with `laruche-equivalence-1`

Live certification reproduced by the replay with the contract: yes. Compile points (stream episodes): [16, 20, 24]. Contract in telemetry: `laruche-equivalence-1` digest `e00115ab2921714c16aa6468274960077b05e479a2a4970e82a0b5146c13523b`; probe sets frozen under: `start:none:none` 76dcf5c1b074, `file_edit:success:other` 5f55584fd34f, `shell_exec:success:tests_failed` 3ff9cb86d7ea.

Families containing a TEST_EXECUTION action: `file_edit:success:other`, `file_read:success:other`, `file_write:success:other`, `mission_criteria:none:none`, `shell_exec:failure:other`, `start:none:none`.

## Economy

natural model calls 129, shadow-sample model calls 3, reflex decisions 1, reflex outcomes {'unknown': 1}.

## Per compile point and family: literal versus behavioral agreement, verdict with and without the contract

| point | family | test action in family | literal | behavioral | verdict with (reason) | verdict without (reason) |
|---|---|---|---|---|---|---|
| 20 | `file_edit:success:other` | yes | 1.000 | 1.000 | rejected (calibration) | rejected (calibration) |
| 20 | `file_read:success:other` | yes | 1.000 | 1.000 | rejected (calibration,trust) | rejected (calibration,trust) |
| 20 | `file_write:success:other` | yes | n/a | n/a | insufficient (no_held_out_evidence) | insufficient (no_held_out_evidence) |
| 20 | `mission_criteria:none:none` | yes | 1.000 | 1.000 | rejected (trust) | rejected (trust) |
| 20 | `shell_exec:failure:other` | yes | 1.000 | 1.000 | rejected (calibration) | rejected (calibration) |
| 20 | `shell_exec:success:other` | no | n/a | n/a | insufficient (no_held_out_evidence) | insufficient (no_held_out_evidence) |
| 20 | `shell_exec:success:tests_failed` | no | 1.000 | 1.000 | rejected (calibration) | rejected (calibration) |
| 20 | `shell_exec:success:tests_passed` | no | 0.667 | 0.667 | rejected (quality,calibration) | rejected (quality,calibration) |
| 20 | `start:none:none` | yes | 1.000 | 1.000 | active (quality_trust_retention_pass) | active (quality_trust_retention_pass) |
| 24 | `file_edit:success:other` | yes | 0.800 | 1.000 | active (quality_trust_retention_pass) | rejected (quality,calibration) |
| 24 | `file_read:success:other` | yes | 1.000 | 1.000 | rejected (calibration) | rejected (calibration) |
| 24 | `file_write:success:other` | yes | 1.000 | 1.000 | rejected (trust) | rejected (trust) |
| 24 | `mission_criteria:none:none` | yes | n/a | n/a | insufficient (no_held_out_evidence) | insufficient (no_held_out_evidence) |
| 24 | `shell_exec:failure:other` | yes | 0.750 | 1.000 | rejected (calibration) | rejected (quality) |
| 24 | `shell_exec:success:other` | no | n/a | n/a | insufficient (no_held_out_evidence) | insufficient (no_held_out_evidence) |
| 24 | `shell_exec:success:tests_failed` | no | 1.000 | 1.000 | active (quality_trust_retention_pass) | active (quality_trust_retention_pass) |
| 24 | `shell_exec:success:tests_passed` | no | 0.500 | 0.500 | rejected (quality) | rejected (quality) |
| 24 | `start:none:none` | yes | 1.000 | 1.000 | active (quality_trust_retention_pass) | active (quality_trust_retention_pass) |

## Adoption decisions with and without the contract (outcome, version, active families after)

| point | with | without |
|---|---|---|
| 16 |  (insufficient_validated_traces), v0:  |  (insufficient_validated_traces), v0:  |
| 20 | promoted (families_activated), v1: `start:none:none` | promoted (families_activated), v1: `start:none:none` |
| 24 | promoted (families_activated), v2: `file_edit:success:other`, `shell_exec:success:tests_failed`, `start:none:none` | promoted (families_activated), v2: `shell_exec:success:tests_failed`, `start:none:none` |

Family verdicts changed by equivalence: 1; adoption decisions changed: 1; changes in families without a TEST_EXECUTION action: 0.

## Divergence from run 12 at the common compile points (family verdicts of the live records)

| point | family | run 12 | run 12b |
|---|---|---|---|
| 16 | `file_edit:success:other` | active | absent |
| 16 | `file_read:success:other` | active | absent |
| 16 | `file_write:success:other` | insufficient | absent |
| 16 | `shell_exec:failure:other` | rejected | absent |
| 16 | `shell_exec:success:tests_failed` | insufficient | absent |
| 16 | `shell_exec:success:tests_passed` | active | absent |
| 16 | `start:none:none` | active | absent |
| 20 | `file_edit:success:other` | rejected | rejected |
| 20 | `file_read:success:other` | active | rejected |
| 20 | `file_write:success:other` | insufficient | insufficient |
| 20 | `mission_criteria:none:none` | absent | rejected |
| 20 | `shell_exec:failure:other` | active | rejected |
| 20 | `shell_exec:success:other` | absent | insufficient |
| 20 | `shell_exec:success:tests_failed` | rejected | rejected |
| 20 | `shell_exec:success:tests_passed` | active | rejected |
| 20 | `start:none:none` | active | active |
