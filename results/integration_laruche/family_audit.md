# Family-scoped audit of the frozen 32-mission record

Pre-registered: Family-scoped activation activates only families that independently satisfy the existing quality, trust and retention criteria; no threshold is changed. Prediction recorded before scoring: laruche:start:none:none and laruche:file_edit:success:other pass; the post-failure read families do not.

Whole-candidate verdict on the same split: backend `tree`, feasible False, coverage 0.35, selective accuracy 1.00, ECE 0.236 (train 56, validation 23 traces).

| Family | train / validation traces | distinct actions | threshold | coverage | selective accuracy | ECE | gate acceptance | verdict | reason |
|---|---|---|---|---|---|---|---|---|---|
| laruche:file_edit:success:other | 23 / 7 (7 ep) | 4 | 0.75 | 71% | 100% | 0.179 | 0.86 | rejected | calibration |
| laruche:start:none:none | 13 / 3 (3 ep) | 1 | 0.00 | 100% | 100% | 0.000 | 1.00 | active | quality_trust_retention_pass |
| laruche:file_read:success:other | 11 / 4 (4 ep) | 5 | 0.55 | 100% | 0% | 0.545 | 0.75 | rejected | quality,calibration |
| laruche:shell_exec:success:tests_passed | 4 / 3 (3 ep) | 3 | 0.50 | 100% | 67% | 0.167 | 0.00 | rejected | quality,calibration,trust |
| laruche:shell_exec:success:tests_failed | 2 / 3 (3 ep) | 2 | 0.50 | 100% | 0% | 0.500 | 0.67 | rejected | quality,calibration |
| laruche:file_write:success:other | 1 / 1 (1 ep) | 1 | 0.00 | 100% | 100% | 0.000 | 0.00 | rejected | trust |
| laruche:shell_exec:success:other | 1 / 1 (1 ep) | 2 | 0.50 | 100% | 0% | 0.500 | 0.00 | rejected | quality,calibration,trust |
| laruche:read_extract:failure:other | 1 / 0 (0 ep) | 1 | n/a | n/a | n/a | n/a | n/a | insufficient | no_held_out_evidence |
| laruche:shell_exec:failure:other | 0 / 1 (1 ep) | 1 | 0.50 | 100% | 0% | 0.500 | 0.00 | rejected | quality,calibration,trust |

Outcome against the prediction: `laruche:start:none:none` passes every criterion on its own. `laruche:file_edit:success:other` is right whenever it is confident (selective accuracy 100% at 71% coverage) but fails the ECE floor (0.179 against 0.10) on 7 held-out traces, because 3 of its 30 occurrences were a re-read before re-running the tests. The floor is unchanged; the family stays deliberative until its held-out calibration meets it. Every other family is rejected or has no held-out evidence.
