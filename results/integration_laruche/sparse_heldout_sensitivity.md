# Sparse held-out sensitivity study (read-only)

Sources: run 11 state (`engine_state_family_scoped_after_24.pkl`) replayed at 16, 20, 24; runs 9A/9B state (`engine_state_after_32.pkl`, 32 validated episodes recorded without any active reflex) replayed under family-scoped certification at 20, 24, 28, 32, counterfactually. `recorded` is the run 11 rule (no probe re-certification); `m=1` is the rule of the previous pre-registration (probes only when no fresh trace) and the control. Probe sets are frozen inside each replay at its first promotion.

Run 11 reproduced by the `recorded` variant: yes.

`m=1` is behaviorally identical to the recorded rule: every verdict, version and active set is the same. The false accept and false reject counts are retrospective labels defined by the pre-registration; where a variant never evaluated an active family's probes, the label uses the probe numbers of the same candidate from the `m=1` replay (marked `retrospective_probe_label` in the JSON), so all variants are labeled on the same basis. A label difference never means a changed certification decision; the "decisions changed" column is the only one that does.

## Summary per variant

| variant | run 11: 20 | run 11: 24 | run 11 final version, active families | run 9: activations (point: families) | run 9 final version | poison at 24 | false accepts | false rejects | candidate decisions changed vs recorded | active-family verdicts changed by sparse arbitration |
|---|---|---|---|---|---|---|---|---|---|---|
| recorded | rejected | rejected | v1: `file_edit:success:other`, `start:none:none` | 20: `file_edit:success:other`, `start:none:none` | v1 | rejected | 0 | 1 | 0 | 0 |
| m=1 | rejected | rejected | v1: `file_edit:success:other`, `start:none:none` | 20: `file_edit:success:other`, `start:none:none` | v1 | rejected | 0 | 1 | 0 | 2 |
| m=2 | rejected | promoted | v2: `file_edit:success:other`, `shell_exec:success:tests_passed`, `start:none:none` | 20: `file_edit:success:other`, `start:none:none` | v1 | rejected | 0 | 0 | 1 | 3 |
| m=3 | rejected | promoted | v2: `file_edit:success:other`, `shell_exec:success:tests_passed`, `start:none:none` | 20: `file_edit:success:other`, `start:none:none` | v1 | rejected | 0 | 0 | 1 | 3 |
| m=5 | rejected | promoted | v2: `file_edit:success:other`, `shell_exec:success:tests_passed`, `start:none:none` | 20: `file_edit:success:other`, `start:none:none` | v1 | rejected | 0 | 0 | 1 | 3 |
| m=8 | rejected | promoted | v2: `file_edit:success:other`, `shell_exec:success:tests_passed`, `start:none:none` | 20: `file_edit:success:other`, `start:none:none` | v1 | rejected | 0 | 0 | 1 | 3 |

## Active-family re-certification, run 11

| variant | point | family | n fresh | evidence | probes cov. / agr. | fresh: gate-accepted / covered / disagreements | gate acc. | ECE | verdict |
|---|---|---|---|---|---|---|---|---|---|
| recorded | 20 | `file_edit:success:other` | 1 | held-out | 1.000 / 0.938 |  | 1.000 | 0.000 | rejected (retention) |
| recorded | 20 | `start:none:none` | 0 | held-out |  |  | n/a | n/a | insufficient (no_held_out_evidence) |
| recorded | 24 | `file_edit:success:other` | 1 | held-out | 1.000 / 1.000 |  | 0.000 | 0.000 | rejected (trust) |
| recorded | 24 | `start:none:none` | 0 | held-out |  |  | n/a | n/a | insufficient (no_held_out_evidence) |
| m=1 | 20 | `file_edit:success:other` | 1 | held-out | 1.000 / 0.938 |  | 1.000 | 0.000 | rejected (retention) |
| m=1 | 20 | `start:none:none` | 0 | probes_only | 1.000 / 1.000 |  | 1.000 | 0.000 | active (probe_recertified) |
| m=1 | 24 | `file_edit:success:other` | 1 | held-out | 1.000 / 1.000 |  | 0.000 | 0.000 | rejected (trust) |
| m=1 | 24 | `start:none:none` | 0 | probes_only | 1.000 / 1.000 |  | 1.000 | 0.000 | active (probe_recertified) |
| m=2 | 20 | `file_edit:success:other` | 1 | probes_only | 1.000 / 0.938 | 1 / 1 / 0 | 1.000 | 0.042 | rejected (retention) |
| m=2 | 20 | `start:none:none` | 0 | probes_only | 1.000 / 1.000 |  | 1.000 | 0.000 | active (probe_recertified) |
| m=2 | 24 | `file_edit:success:other` | 1 | probes_only | 1.000 / 1.000 | 0 / 0 / 0 | 1.000 | 0.009 | active (probe_recertified) |
| m=2 | 24 | `start:none:none` | 0 | probes_only | 1.000 / 1.000 |  | 1.000 | 0.000 | active (probe_recertified) |
| m=3 | 20 | `file_edit:success:other` | 1 | probes_only | 1.000 / 0.938 | 1 / 1 / 0 | 1.000 | 0.042 | rejected (retention) |
| m=3 | 20 | `start:none:none` | 0 | probes_only | 1.000 / 1.000 |  | 1.000 | 0.000 | active (probe_recertified) |
| m=3 | 24 | `file_edit:success:other` | 1 | probes_only | 1.000 / 1.000 | 0 / 0 / 0 | 1.000 | 0.009 | active (probe_recertified) |
| m=3 | 24 | `start:none:none` | 0 | probes_only | 1.000 / 1.000 |  | 1.000 | 0.000 | active (probe_recertified) |
| m=5 | 20 | `file_edit:success:other` | 1 | probes_only | 1.000 / 0.938 | 1 / 1 / 0 | 1.000 | 0.042 | rejected (retention) |
| m=5 | 20 | `start:none:none` | 0 | probes_only | 1.000 / 1.000 |  | 1.000 | 0.000 | active (probe_recertified) |
| m=5 | 24 | `file_edit:success:other` | 1 | probes_only | 1.000 / 1.000 | 0 / 0 / 0 | 1.000 | 0.009 | active (probe_recertified) |
| m=5 | 24 | `start:none:none` | 0 | probes_only | 1.000 / 1.000 |  | 1.000 | 0.000 | active (probe_recertified) |
| m=8 | 20 | `file_edit:success:other` | 1 | probes_only | 1.000 / 0.938 | 1 / 1 / 0 | 1.000 | 0.042 | rejected (retention) |
| m=8 | 20 | `start:none:none` | 0 | probes_only | 1.000 / 1.000 |  | 1.000 | 0.000 | active (probe_recertified) |
| m=8 | 24 | `file_edit:success:other` | 1 | probes_only | 1.000 / 1.000 | 0 / 0 / 0 | 1.000 | 0.009 | active (probe_recertified) |
| m=8 | 24 | `start:none:none` | 0 | probes_only | 1.000 / 1.000 |  | 1.000 | 0.000 | active (probe_recertified) |

## Active-family re-certification, runs 9A/9B (counterfactual)

| variant | point | family | n fresh | evidence | probes cov. / agr. | fresh: gate-accepted / covered / disagreements | gate acc. | ECE | verdict |
|---|---|---|---|---|---|---|---|---|---|
| recorded | 24 | `file_edit:success:other` | 6 | held-out | 1.000 / 0.947 |  | 1.000 | 0.048 | rejected (retention) |
| recorded | 24 | `start:none:none` | 4 | held-out | 1.000 / 1.000 |  | 1.000 | 0.000 | active (quality_trust_retention_pass) |
| recorded | 28 | `file_edit:success:other` | 7 | held-out | 0.947 / 0.944 |  | 0.857 | 0.102 | rejected (calibration,retention) |
| recorded | 28 | `start:none:none` | 4 | held-out | 1.000 / 1.000 |  | 1.000 | 0.000 | active (quality_trust_retention_pass) |
| recorded | 32 | `file_edit:success:other` | 7 | held-out | 0.947 / 0.944 |  | 0.857 | 0.179 | rejected (calibration,retention) |
| recorded | 32 | `start:none:none` | 3 | held-out | 1.000 / 1.000 |  | 1.000 | 0.000 | active (quality_trust_retention_pass) |
| m=1 | 24 | `file_edit:success:other` | 6 | held-out | 1.000 / 0.947 |  | 1.000 | 0.048 | rejected (retention) |
| m=1 | 24 | `start:none:none` | 4 | held-out | 1.000 / 1.000 |  | 1.000 | 0.000 | active (quality_trust_retention_pass) |
| m=1 | 28 | `file_edit:success:other` | 7 | held-out | 0.947 / 0.944 |  | 0.857 | 0.102 | rejected (calibration,retention) |
| m=1 | 28 | `start:none:none` | 4 | held-out | 1.000 / 1.000 |  | 1.000 | 0.000 | active (quality_trust_retention_pass) |
| m=1 | 32 | `file_edit:success:other` | 7 | held-out | 0.947 / 0.944 |  | 0.857 | 0.179 | rejected (calibration,retention) |
| m=1 | 32 | `start:none:none` | 3 | held-out | 1.000 / 1.000 |  | 1.000 | 0.000 | active (quality_trust_retention_pass) |
| m=2 | 24 | `file_edit:success:other` | 6 | held-out | 1.000 / 0.947 |  | 1.000 | 0.048 | rejected (retention) |
| m=2 | 24 | `start:none:none` | 4 | held-out | 1.000 / 1.000 |  | 1.000 | 0.000 | active (quality_trust_retention_pass) |
| m=2 | 28 | `file_edit:success:other` | 7 | held-out | 0.947 / 0.944 |  | 0.857 | 0.102 | rejected (calibration,retention) |
| m=2 | 28 | `start:none:none` | 4 | held-out | 1.000 / 1.000 |  | 1.000 | 0.000 | active (quality_trust_retention_pass) |
| m=2 | 32 | `file_edit:success:other` | 7 | held-out | 0.947 / 0.944 |  | 0.857 | 0.179 | rejected (calibration,retention) |
| m=2 | 32 | `start:none:none` | 3 | held-out | 1.000 / 1.000 |  | 1.000 | 0.000 | active (quality_trust_retention_pass) |
| m=3 | 24 | `file_edit:success:other` | 6 | held-out | 1.000 / 0.947 |  | 1.000 | 0.048 | rejected (retention) |
| m=3 | 24 | `start:none:none` | 4 | held-out | 1.000 / 1.000 |  | 1.000 | 0.000 | active (quality_trust_retention_pass) |
| m=3 | 28 | `file_edit:success:other` | 7 | held-out | 0.947 / 0.944 |  | 0.857 | 0.102 | rejected (calibration,retention) |
| m=3 | 28 | `start:none:none` | 4 | held-out | 1.000 / 1.000 |  | 1.000 | 0.000 | active (quality_trust_retention_pass) |
| m=3 | 32 | `file_edit:success:other` | 7 | held-out | 0.947 / 0.944 |  | 0.857 | 0.179 | rejected (calibration,retention) |
| m=3 | 32 | `start:none:none` | 3 | held-out | 1.000 / 1.000 |  | 1.000 | 0.000 | active (quality_trust_retention_pass) |
| m=5 | 24 | `file_edit:success:other` | 6 | held-out | 1.000 / 0.947 |  | 1.000 | 0.048 | rejected (retention) |
| m=5 | 24 | `start:none:none` | 4 | probes_only | 1.000 / 1.000 | 4 / 4 / 0 | 1.000 | 0.000 | active (probe_recertified) |
| m=5 | 28 | `file_edit:success:other` | 7 | held-out | 0.947 / 0.944 |  | 0.857 | 0.102 | rejected (calibration,retention) |
| m=5 | 28 | `start:none:none` | 4 | probes_only | 1.000 / 1.000 | 4 / 4 / 0 | 1.000 | 0.000 | active (probe_recertified) |
| m=5 | 32 | `file_edit:success:other` | 7 | held-out | 0.947 / 0.944 |  | 0.857 | 0.179 | rejected (calibration,retention) |
| m=5 | 32 | `start:none:none` | 3 | probes_only | 1.000 / 1.000 | 3 / 3 / 0 | 1.000 | 0.000 | active (probe_recertified) |
| m=8 | 24 | `file_edit:success:other` | 6 | probes_only | 1.000 / 0.947 | 6 / 6 / 0 | 1.000 | 0.059 | rejected (retention) |
| m=8 | 24 | `start:none:none` | 4 | probes_only | 1.000 / 1.000 | 4 / 4 / 0 | 1.000 | 0.000 | active (probe_recertified) |
| m=8 | 28 | `file_edit:success:other` | 7 | probes_only | 1.000 / 0.947 | 6 / 6 / 0 | 1.000 | 0.068 | rejected (retention) |
| m=8 | 28 | `start:none:none` | 4 | probes_only | 1.000 / 1.000 | 4 / 4 / 0 | 1.000 | 0.000 | active (probe_recertified) |
| m=8 | 32 | `file_edit:success:other` | 7 | probes_only | 1.000 / 0.947 | 6 / 6 / 1 | 1.000 | 0.053 | rejected (fresh_disagreement,retention) |
| m=8 | 32 | `start:none:none` | 3 | probes_only | 1.000 / 1.000 | 3 / 3 / 0 | 1.000 | 0.000 | active (probe_recertified) |

## Verdict per compile point

| variant | record | point | outcome | reason | version after | newly active |
|---|---|---|---|---|---|---|
| recorded | run11 | 16 | promoted | families_activated:laruche:file_edit:success:other,laruche:start:none:none | v1 | `file_edit:success:other`, `start:none:none` |
| recorded | run11 | 20 | rejected | active_family_regressed:laruche:file_edit:success:other,laruche:start:none:none | v1 |  |
| recorded | run11 | 24 | rejected | active_family_regressed:laruche:file_edit:success:other,laruche:start:none:none | v1 |  |
| recorded | run9 | 20 | promoted | families_activated:laruche:file_edit:success:other,laruche:start:none:none | v1 | `file_edit:success:other`, `start:none:none` |
| recorded | run9 | 24 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| recorded | run9 | 28 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| recorded | run9 | 32 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=1 | run11 | 16 | promoted | families_activated:laruche:file_edit:success:other,laruche:start:none:none | v1 | `file_edit:success:other`, `start:none:none` |
| m=1 | run11 | 20 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=1 | run11 | 24 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=1 | run9 | 20 | promoted | families_activated:laruche:file_edit:success:other,laruche:start:none:none | v1 | `file_edit:success:other`, `start:none:none` |
| m=1 | run9 | 24 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=1 | run9 | 28 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=1 | run9 | 32 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=2 | run11 | 16 | promoted | families_activated:laruche:file_edit:success:other,laruche:start:none:none | v1 | `file_edit:success:other`, `start:none:none` |
| m=2 | run11 | 20 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=2 | run11 | 24 | promoted | families_activated:laruche:shell_exec:success:tests_passed | v2 | `shell_exec:success:tests_passed` |
| m=2 | run9 | 20 | promoted | families_activated:laruche:file_edit:success:other,laruche:start:none:none | v1 | `file_edit:success:other`, `start:none:none` |
| m=2 | run9 | 24 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=2 | run9 | 28 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=2 | run9 | 32 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=3 | run11 | 16 | promoted | families_activated:laruche:file_edit:success:other,laruche:start:none:none | v1 | `file_edit:success:other`, `start:none:none` |
| m=3 | run11 | 20 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=3 | run11 | 24 | promoted | families_activated:laruche:shell_exec:success:tests_passed | v2 | `shell_exec:success:tests_passed` |
| m=3 | run9 | 20 | promoted | families_activated:laruche:file_edit:success:other,laruche:start:none:none | v1 | `file_edit:success:other`, `start:none:none` |
| m=3 | run9 | 24 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=3 | run9 | 28 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=3 | run9 | 32 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=5 | run11 | 16 | promoted | families_activated:laruche:file_edit:success:other,laruche:start:none:none | v1 | `file_edit:success:other`, `start:none:none` |
| m=5 | run11 | 20 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=5 | run11 | 24 | promoted | families_activated:laruche:shell_exec:success:tests_passed | v2 | `shell_exec:success:tests_passed` |
| m=5 | run9 | 20 | promoted | families_activated:laruche:file_edit:success:other,laruche:start:none:none | v1 | `file_edit:success:other`, `start:none:none` |
| m=5 | run9 | 24 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=5 | run9 | 28 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=5 | run9 | 32 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=8 | run11 | 16 | promoted | families_activated:laruche:file_edit:success:other,laruche:start:none:none | v1 | `file_edit:success:other`, `start:none:none` |
| m=8 | run11 | 20 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=8 | run11 | 24 | promoted | families_activated:laruche:shell_exec:success:tests_passed | v2 | `shell_exec:success:tests_passed` |
| m=8 | run9 | 20 | promoted | families_activated:laruche:file_edit:success:other,laruche:start:none:none | v1 | `file_edit:success:other`, `start:none:none` |
| m=8 | run9 | 24 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=8 | run9 | 28 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |
| m=8 | run9 | 32 | rejected | active_family_regressed:laruche:file_edit:success:other | v1 |  |

## Poison control at 24, run 11, per variant

| variant | outcome | reason | file_edit verdict |
|---|---|---|---|
| recorded | rejected | active_family_regressed:laruche:file_edit:success:other,laruche:start:none:none | rejected (quality,calibration,trust,retention) |
| m=1 | rejected | active_family_regressed:laruche:file_edit:success:other | rejected (quality,calibration,trust,retention) |
| m=2 | rejected | active_family_regressed:laruche:file_edit:success:other | rejected (retention,calibration) |
| m=3 | rejected | active_family_regressed:laruche:file_edit:success:other | rejected (retention,calibration) |
| m=5 | rejected | active_family_regressed:laruche:file_edit:success:other | rejected (retention,calibration) |
| m=8 | rejected | active_family_regressed:laruche:file_edit:success:other | rejected (retention,calibration) |
