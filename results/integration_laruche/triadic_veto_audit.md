# Triadic veto audit on frozen run 12

Live rule reproduced by the `recorded` replay: yes. Compile points (stream episodes): [16, 20, 25, 29, 33].

## Covered fresh disagreements by class, per compile point and active family (triadic m=8 replay, probe branch with the fresh report)

| point | family | fresh | covered | disagreements | candidate regression | alternative trajectory | ambiguous |
|---|---|---|---|---|---|---|---|
| 20 | `file_edit:success:other` | 2 | 2 | 0 | 0 | 0 | 0 |
| 20 | `file_read:success:other` | 1 | 1 | 0 | 0 | 0 | 0 |
| 20 | `shell_exec:success:tests_passed` | 1 | 1 | 0 | 0 | 0 | 0 |
| 20 | `start:none:none` | 2 | 2 | 0 | 0 | 0 | 0 |
| 25 | `file_edit:success:other` | 3 | 3 | 1 | 1 | 0 | 0 |
| 25 | `file_read:success:other` | 0 | n/a | n/a | n/a | n/a | n/a |
| 25 | `shell_exec:success:tests_passed` | 4 | 3 | 0 | 0 | 0 | 0 |
| 25 | `start:none:none` | 1 | 1 | 0 | 0 | 0 | 0 |
| 29 | `file_edit:success:other` | 6 | 6 | 0 | 0 | 0 | 0 |
| 29 | `file_read:success:other` | 1 | 1 | 0 | 0 | 0 | 0 |
| 29 | `shell_exec:success:tests_passed` | 4 | 3 | 0 | 0 | 0 | 0 |
| 29 | `start:none:none` | 1 | 1 | 0 | 0 | 0 | 0 |
| 33 | `file_edit:success:other` | 7 | 7 | 1 | 0 | 1 | 0 |
| 33 | `file_read:success:other` | 4 | 3 | 0 | 0 | 0 | 0 |
| 33 | `shell_exec:success:tests_passed` | 1 | 1 | 0 | 0 | 0 | 0 |
| 33 | `start:none:none` | 2 | 2 | 0 | 0 | 0 | 0 |

## `file_edit:success:other` at points 25 and 33 under every variant

| variant | 25: verdict (reason) | 25: evidence | 33: verdict (reason) | 33: evidence | 33: sel. acc. | 33: ECE |
|---|---|---|---|---|---|---|
| recorded | rejected (calibration) | held-out | rejected (quality,calibration) | held-out | 0.857 | 0.143 |
| naive m=1 | rejected (calibration) | held-out | rejected (quality,calibration) | held-out | 0.857 | 0.143 |
| naive m=2 | rejected (calibration) | held-out | rejected (quality,calibration) | held-out | 0.857 | 0.143 |
| naive m=3 | rejected (calibration) | held-out | rejected (quality,calibration) | held-out | 0.857 | 0.143 |
| naive m=5 | rejected (fresh_disagreement,retention) | probes_only | rejected (quality,calibration) | held-out | 0.857 | 0.143 |
| naive m=8 | rejected (fresh_disagreement,retention) | probes_only | rejected (fresh_disagreement) | probes_only | 1.000 | 0.000 |
| triadic m=1 | rejected (calibration) | held-out | rejected (quality,calibration) | held-out | 0.857 | 0.143 |
| triadic m=2 | rejected (calibration) | held-out | rejected (quality,calibration) | held-out | 0.857 | 0.143 |
| triadic m=3 | rejected (calibration) | held-out | rejected (quality,calibration) | held-out | 0.857 | 0.143 |
| triadic m=5 | rejected (candidate_regression,retention) | probes_only | rejected (quality,calibration) | held-out | 0.857 | 0.143 |
| triadic m=8 | rejected (candidate_regression,retention) | probes_only | active (probe_recertified) | probes_only | 1.000 | 0.000 |

## Candidate decisions per variant

| variant | 16 | 20 | 25 | 29 | 33 | final version |
|---|---|---|---|---|---|---|
| recorded | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 |
| naive m=1 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 |
| naive m=2 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 |
| naive m=3 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 |
| naive m=5 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 |
| naive m=8 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 |
| triadic m=1 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 |
| triadic m=2 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 |
| triadic m=3 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 |
| triadic m=5 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) | v1 |
| triadic m=8 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (no_new_family) | v1 |

## Pre-registered checks

- reproduced: pass
- 25_classified_candidate_regression: pass
- 25_rejected_under_every_variant: pass
- 25_triadic_veto_fires_in_probe_branch: pass
- 33_classified_alternative_trajectory: pass
- 33_naive_veto_fires_m8: pass
- 33_triadic_no_veto_m8: pass
- 33_held_out_still_rejected: pass
- 33_held_out_reasons: ['quality,calibration']
- 33_held_out_selective_accuracy: 0.8571428571428571
- 33_held_out_ece: 0.1428571428571429
