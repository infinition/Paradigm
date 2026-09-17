# Behavioral equivalence audit (offline, frozen records)

Contract `laruche-equivalence-1`, digest `d7d6df94a13503f9bc4b5cc034438334c6d9025d5c8592318477f883353416ca` on the run 12 keys; classes other than identity: `shell_exec#5fa23c7577e0` -> TEST_EXECUTION, `shell_exec#a4e317297fb3` -> TEST_EXECUTION.

## Pre-registered checks

- run12_recorded_without_contract_reproduces_live: pass
- 25_rejected_every_variant_with_contract: pass
- 33_held_out_passes_with_contract: pass
- 33_held_out_selective_accuracy: 1.0
- 33_held_out_ece: 0.0
- 33_literal_agreement: 0.8571428571428571
- 33_equivalent_agreement: 1.0
- 33_candidate_no_new_family_every_variant: pass
- run11_identical: pass
- run9_identical: pass
- run12_earlier_points_identical: pass
- contract_digest_run12: d7d6df94a13503f9bc4b5cc034438334c6d9025d5c8592318477f883353416ca
- contract_version: laruche-equivalence-1

## Run 12, `file_edit:success:other` at 25 and 33, without and with the contract

| variant | 25 without | 25 with | 33 without | 33 with | 33 sel. acc. with | 33 ECE with | 33 literal / equivalent agreement |
|---|---|---|---|---|---|---|---|
| recorded | rejected (calibration) | rejected (calibration) | rejected (quality,calibration) | active (quality_trust_retention_pass) | 1.000 | 0.000 | 0.857 / 1.000 |
| triadic m=1 | rejected (calibration) | rejected (calibration) | rejected (quality,calibration) | active (quality_trust_retention_pass) | 1.000 | 0.000 | 0.857 / 1.000 |
| triadic m=2 | rejected (calibration) | rejected (calibration) | rejected (quality,calibration) | active (quality_trust_retention_pass) | 1.000 | 0.000 | 0.857 / 1.000 |
| triadic m=3 | rejected (calibration) | rejected (calibration) | rejected (quality,calibration) | active (quality_trust_retention_pass) | 1.000 | 0.000 | 0.857 / 1.000 |
| triadic m=5 | rejected (candidate_regression,retention) | rejected (candidate_regression,retention) | rejected (quality,calibration) | active (quality_trust_retention_pass) | 1.000 | 0.000 | 0.857 / 1.000 |
| triadic m=8 | rejected (candidate_regression,retention) | rejected (candidate_regression,retention) | active (probe_recertified) | active (probe_recertified) | 1.000 | 0.000 | n/a / n/a |
| naive m=8 | rejected (fresh_disagreement,retention) | rejected (fresh_disagreement,retention) | rejected (fresh_disagreement) | active (probe_recertified) | 1.000 | 0.000 | n/a / n/a |

## run12: candidate decisions without and with the contract

| variant | 16 | 20 | 25 | 29 | 33 | identical |
|---|---|---|---|---|---|---|
| recorded | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) / rejected (no_new_family) | yes |
| triadic m=1 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) / rejected (no_new_family) | yes |
| triadic m=2 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) / rejected (no_new_family) | yes |
| triadic m=3 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) / rejected (no_new_family) | yes |
| triadic m=5 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) / rejected (no_new_family) | yes |
| triadic m=8 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (no_new_family) | yes |
| naive m=8 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | rejected (no_new_family) | rejected (active_family_regressed) / rejected (no_new_family) | yes |

## run11: candidate decisions without and with the contract

| variant | 16 | 20 | 24 | identical |
|---|---|---|---|---|
| recorded | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | yes |
| triadic m=1 | promoted (families_activated) | rejected (active_family_regressed) | rejected (active_family_regressed) | yes |
| triadic m=2 | promoted (families_activated) | rejected (active_family_regressed) | promoted (families_activated) | yes |
| triadic m=3 | promoted (families_activated) | rejected (active_family_regressed) | promoted (families_activated) | yes |
| triadic m=5 | promoted (families_activated) | rejected (active_family_regressed) | promoted (families_activated) | yes |
| triadic m=8 | promoted (families_activated) | rejected (active_family_regressed) | promoted (families_activated) | yes |
| naive m=8 | promoted (families_activated) | rejected (active_family_regressed) | promoted (families_activated) | yes |

## run9: candidate decisions without and with the contract

| variant | 20 | 24 | 28 | 32 | identical |
|---|---|---|---|---|---|
| recorded | promoted (families_activated) | rejected (active_family_regressed) / rejected (no_new_family) | rejected (active_family_regressed) | rejected (active_family_regressed) | yes |
| triadic m=1 | promoted (families_activated) | rejected (active_family_regressed) / rejected (no_new_family) | rejected (active_family_regressed) | rejected (active_family_regressed) | yes |
| triadic m=2 | promoted (families_activated) | rejected (active_family_regressed) / rejected (no_new_family) | rejected (active_family_regressed) | rejected (active_family_regressed) | yes |
| triadic m=3 | promoted (families_activated) | rejected (active_family_regressed) / rejected (no_new_family) | rejected (active_family_regressed) | rejected (active_family_regressed) | yes |
| triadic m=5 | promoted (families_activated) | rejected (active_family_regressed) / rejected (no_new_family) | rejected (active_family_regressed) | rejected (active_family_regressed) | yes |
| triadic m=8 | promoted (families_activated) | rejected (active_family_regressed) / rejected (no_new_family) | rejected (active_family_regressed) / rejected (no_new_family) | rejected (active_family_regressed) / rejected (no_new_family) | yes |
| naive m=8 | promoted (families_activated) | rejected (active_family_regressed) / rejected (no_new_family) | rejected (active_family_regressed) / rejected (no_new_family) | rejected (active_family_regressed) | yes |
