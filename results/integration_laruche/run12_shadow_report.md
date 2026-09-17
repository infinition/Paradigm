# Run 12 report: shadow sampling

Live rule reproduced by the `recorded` replay: yes. Compile points from the first promotion, labeled by stream episode: [16, 20, 25, 29, 33] (buffer sizes [16, 20, 24, 28, 32]).

## Economy

| natural model calls | shadow-sample model calls | reflex decisions | model calls avoided | net after sampling overhead |
|---|---|---|---|---|
| 139 | 53 | 17 | 17 | -36 |

Shadow-sample outcomes: {'unknown': 15, 'success': 24, 'None': 14}. Reflex outcomes: {'success': 11, 'unknown': 6}.

## Per compile point and active family

| point | family | fresh | fresh gate-accepted | fresh covered | fresh disagreements | probes | probe agreement | probe coverage | probe gate acc. | hard veto | recorded (family / candidate) | m=1 (family / candidate) | m=2 (family / candidate) | m=3 (family / candidate) | m=5 (family / candidate) | m=8 (family / candidate) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | `file_edit:success:other` | 2 | 2 | 2 | 0 | 14 | 0.929 | 1.000 | 1.000 | no | rejected (retention) / rejected | rejected (retention) / rejected | rejected (retention) / rejected | rejected (retention) / rejected | rejected (retention) / rejected | rejected (retention) / rejected |
| 20 | `file_read:success:other` | 1 | 1 | 1 | 0 | 6 | 1.000 | 1.000 | 1.000 | no | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected |
| 20 | `shell_exec:success:tests_passed` | 1 | 1 | 1 | 0 | 6 | 1.000 | 1.000 | 1.000 | no | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected |
| 20 | `start:none:none` | 2 | 2 | 2 | 0 | 8 | 1.000 | 1.000 | 1.000 | no | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected |
| 25 | `file_edit:success:other` | 3 | 3 | 3 | 1 | 14 | 0.929 | 1.000 | 1.000 | yes | rejected (calibration) / rejected | rejected (calibration) / rejected | rejected (calibration) / rejected | rejected (calibration) / rejected | rejected (fresh_disagreement,retention) / rejected | rejected (fresh_disagreement,retention) / rejected |
| 25 | `file_read:success:other` | 0 | n/a | n/a | n/a | 6 | 1.000 | 1.000 | 1.000 | no | insufficient (no_held_out_evidence) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected |
| 25 | `shell_exec:success:tests_passed` | 4 | 3 | 3 | 0 | 6 | 1.000 | 1.000 | 1.000 | no | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected |
| 25 | `start:none:none` | 1 | 1 | 1 | 0 | 8 | 1.000 | 1.000 | 1.000 | no | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected |
| 29 | `file_edit:success:other` | 6 | 6 | 6 | 0 | 14 | 1.000 | 1.000 | 1.000 | no | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (probe_recertified) / rejected |
| 29 | `file_read:success:other` | 1 | 1 | 1 | 0 | 6 | 1.000 | 1.000 | 1.000 | no | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected |
| 29 | `shell_exec:success:tests_passed` | 4 | 3 | 3 | 0 | 6 | 1.000 | 1.000 | 1.000 | no | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected |
| 29 | `start:none:none` | 1 | 1 | 1 | 0 | 8 | 1.000 | 1.000 | 1.000 | no | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected |
| 33 | `file_edit:success:other` | 7 | 7 | 7 | 1 | 14 | 1.000 | 1.000 | 1.000 | yes | rejected (quality,calibration) / rejected | rejected (quality,calibration) / rejected | rejected (quality,calibration) / rejected | rejected (quality,calibration) / rejected | rejected (quality,calibration) / rejected | rejected (fresh_disagreement) / rejected |
| 33 | `file_read:success:other` | 4 | 3 | 3 | 0 | 6 | 1.000 | 1.000 | 1.000 | no | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected |
| 33 | `shell_exec:success:tests_passed` | 1 | 1 | 1 | 0 | 6 | 1.000 | 1.000 | 1.000 | no | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected |
| 33 | `start:none:none` | 2 | 2 | 2 | 0 | 8 | 1.000 | 1.000 | 1.000 | no | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (quality_trust_retention_pass) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected | active (probe_recertified) / rejected |

## Three levels of change relative to the recorded rule

| variant | evidence path changed (family-points) | family verdict changed | candidate adoption decision changed |
|---|---|---|---|
| recorded | 0 | 0 | 0 |
| m=1 | 1 | 1 | 0 |
| m=2 | 7 | 1 | 0 |
| m=3 | 10 | 1 | 0 |
| m=5 | 14 | 1 | 0 |
| m=8 | 16 | 1 | 0 |

## Candidate verdicts per variant

| variant | 16 | 20 | 25 | 29 | 33 | final version | final active families |
|---|---|---|---|---|---|---|---|
| recorded | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 | `file_edit:success:other`, `file_read:success:other`, `shell_exec:success:tests_passed`, `start:none:none` |
| m=1 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 | `file_edit:success:other`, `file_read:success:other`, `shell_exec:success:tests_passed`, `start:none:none` |
| m=2 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 | `file_edit:success:other`, `file_read:success:other`, `shell_exec:success:tests_passed`, `start:none:none` |
| m=3 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 | `file_edit:success:other`, `file_read:success:other`, `shell_exec:success:tests_passed`, `start:none:none` |
| m=5 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 | `file_edit:success:other`, `file_read:success:other`, `shell_exec:success:tests_passed`, `start:none:none` |
| m=8 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 | `file_edit:success:other`, `file_read:success:other`, `shell_exec:success:tests_passed`, `start:none:none` |
