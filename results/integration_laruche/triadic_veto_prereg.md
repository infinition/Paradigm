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
