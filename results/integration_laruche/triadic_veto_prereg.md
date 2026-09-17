# Pre-registration: triadic veto (incumbent / candidate / teacher) on frozen run 12

Written before any code change. Offline only, on the frozen run 12 record (`run12_raw_sha256.txt`). No live run. No canonicalizer change (`| cat` stays a distinct action). No threshold change.

## Rule under test

For each gate-covered fresh observation of an active family, with `y` the verified teacher action, `c` the candidate's prediction and `i` the incumbent's prediction:

- `i = y` and `c != y`: candidate regression; veto.
- `i != y`, `c = i`, and the incumbent action remains valid: alternative trajectory; no veto from the disagreement alone.
- otherwise: ambiguous; reported, no veto, and no new rule invented in this experiment.

"Remains valid" is operationalized on the frozen record as: the incumbent's predicted action is a verified teacher action of that family in the training traces or probes (an action the family has executed and verified before).

The triadic rule replaces only the `fresh_disagreement` veto of the probe branch. The held-out branch (quality, calibration, trust, retention) is left exactly as it is, so the second question below can be answered.

## Predictions

1. Point 25 (stream episode), `file_edit`: the candidate predicts `file_read` where the teacher ran the tests and the incumbent predicts the tests; classified candidate regression; the veto fires in the probe branch; the family stays rejected under every `m`.
2. Point 33, `file_edit`: the teacher ran `python -m pytest -q | cat`, the incumbent and the candidate both predict `python -m pytest -q`, which is a verified action of the family; classified alternative trajectory; the `fresh_disagreement` veto no longer fires in the probe branch (`m = 8`, the only pre-registered value that routes 7 fresh traces to probes), and the family is active on its probes there.
3. Then, explicitly: under the held-out branch (`m` up to 5 at point 33), `file_edit` remains rejected, because the alternative teacher action is counted as a classification error by the existing quality and calibration calculation (selective accuracy 6 of 7 against the teacher, ECE above the floor). If so, stop: quality and calibration are not modified in this experiment. That result establishes that the problem is not only the veto but the assumption that teacher-action equality defines correctness.

## Reported

For every compile point and active family: counts of covered fresh observations by class (agreement, candidate regression, alternative trajectory, ambiguous); the family verdict under the naive veto and under the triadic veto for `m` in {1, 2, 3, 5, 8}; the candidate decision. Nothing in the live record is rewritten; the recorded verdicts stay alongside.

## Not done

No change to quality, calibration, trust, retention, thresholds or canonicalization. No `m` selected. No live run.

## Outcome (written after the replay, `triadic_veto_audit.md`)

Reproducibility: the `recorded` replay reproduces the live run 12 verdicts at every compile point.

Prediction 1 held. Point 25, `file_edit`, 3 fresh, 1 covered disagreement classified candidate regression (incumbent agrees with the teacher, candidate predicts `file_read`). The triadic veto fires in the probe branch (`m` 5 and 8: `candidate_regression,retention`); the held-out branch rejects on calibration. Rejected under every variant.

Prediction 2 held. Point 33, `file_edit`, 7 fresh, 1 covered disagreement classified alternative trajectory (teacher `python -m pytest -q | cat`; incumbent and candidate `python -m pytest -q`, a verified action of the family). Under the naive veto at `m = 8`: rejected (`fresh_disagreement`). Under the triadic veto at `m = 8`: active (`probe_recertified`, 14 of 14 probes), and the candidate decision at 33 becomes `no_new_family` (all four active families re-certified, nothing new to activate).

Prediction 3 held, and this is the result. In the held-out branch (`m` up to 5 at point 33), `file_edit` remains rejected with reason `quality,calibration`: selective accuracy 0.857 (6 of 7 against the teacher) and ECE 0.143, because the alternative teacher action is counted as a classification error. Stopped here, as pre-registered: quality and calibration were not modified.

What this establishes on the record: the problem is not only the veto. The quality and calibration criteria assume that equality with the teacher's action defines correctness. On a state where two actions are both valid and verified (`python -m pytest -q` and `python -m pytest -q | cat`), a reflex that replays the certified one is scored as wrong, and one such observation among seven is enough to fail the family in the held-out branch. The next hypothesis, to pre-register separately, is that action equality is the wrong supervision target when several actions lead to the same valid outcome, and that quality should be scored against an outcome-aware equivalence rather than the teacher's literal action. The canonicalizer (`| cat`) was deliberately left unchanged so that this result is attributable to the scoring rule, not to a normalization fix.

No candidate adoption decision changed under any variant except the reason at 33 under the triadic veto with `m = 8`. No `m` selected. No live run.
