# Pre-registration: behavioral equivalence for quality and calibration (offline)

Written before any code change. Offline only, on the frozen records (run 12, run 11, runs 9A/9B). No live run. No canonicalizer change (`| cat` stays a distinct action key). No threshold change.

## Hypothesis

Quality and calibration should be scored against verified behavioral equivalence classes rather than literal teacher action identity, when the domain provides an outcome contract capable of distinguishing equivalent from procedurally distinct actions.

## Equivalence contract, minimal and conservative

One class is introduced, derived from rules the LaRuche adapter already enforces:

```text
TEST_EXECUTION
  - shell_exec whose canonical command matches the existing shell allowlist
    (pytest, cargo test|check|build, npm test, go test);
  - postcondition already verified by the adapter: a test report is present in the output;
  - read-only: the command contains no file redirection (>, >>) and no tee, which is the
    guard hook's existing rule for what may run;
  - so no forbidden side effect.

every other action key
  - literal identity only.
```

`file_read`, `read_extract` and `file_list` are not grouped. Consequences on the run 12 keys: `python -m pytest -q` and `python -m pytest -q | cat` are TEST_EXECUTION; `python -m pytest -q > /tmp/pytest_out.txt` and `python -m pytest -q | tee /tmp/pytest_out.txt` are not (they write a file; the guard refused them and they were never validated); `file_read#...` keys keep their identity.

The contract is materialized at every certification as the explicit mapping of the action keys present in the split and the probes, with a version string and a SHA-256 digest of the mapping, stored in the certification record. A later change of the adapter's classes cannot silently change what a recorded certification meant.

## Where it applies

Per-family certification only: threshold selection (selective accuracy against the teacher), ECE, probe agreement, and the fresh-disagreement classification are computed in class space. The confidence of a class is the sum of the probabilities of its member actions. The whole-candidate selector (backend choice) stays literal; in family-scoped mode it does not decide adoption. Default contract is identity, so nothing changes where no contract is given.

Two metrics are kept side by side: literal teacher-action agreement (diagnostic) and behavioral-equivalence accuracy (certification).

## Predictions

1. Point 25, `file_edit`: the candidate's `file_read` is not equivalent to the teacher's test execution; remains rejected under every variant (held-out: quality or calibration; probe branch: candidate regression).
2. Point 33, `file_edit`: 7 of 7 equivalent-correct in held-out; selective accuracy 1.0, ECE within the floor; passes quality and calibration; literal agreement stays 6 of 7 and is reported.
3. Candidate at 33 becomes `no_new_family` in every `m` branch (all four active families re-certified).
4. Run 11 and the runs 9A/9B record replay identically under the contract (no equivalent pair is at stake there: `| tail -N` and `2>&1` are already folded by the canonicalizer).
5. Every earlier compile point of run 12 (16, 20, 25, 29) keeps its verdicts.

If any earlier record changes unexpectedly, stop and report before extending the contract.

## Not done

No canonicalizer change, no threshold change, no live run, no grouping of read actions, no `m` selected.

## Outcome (written after the replay, `behavioral_equivalence_audit.md`)

Contract `laruche-equivalence-1`, digest `d7d6df94a13503f9bc4b5cc034438334c6d9025d5c8592318477f883353416ca` on the run 12 keys. Only two keys leave identity: `python -m pytest -q` and `python -m pytest -q | cat`, both TEST_EXECUTION. The two file-writing pytest phrasings stay literal, as pre-registered.

Prediction 1 held: point 25 rejected under every variant (`file_read` is not TEST_EXECUTION; held-out calibration, probe-branch candidate regression).

Prediction 2 held: point 33, `file_edit`, held-out branch: selective accuracy 1.0 (equivalent), ECE 0.0; literal agreement 0.857 reported alongside; active under `recorded` and every `m` up to 5; the naive veto at `m = 8` no longer fires either, since the disagreement is not one in class space.

Prediction 3 held: the candidate at 33 is `no_new_family` under every variant.

Prediction 5 held: run 12 points 16, 20, 25 and 29 keep their verdicts.

Prediction 4 held for candidate decisions, and not at the reason level for the runs 9A/9B record, which is reported here as the pre-registration requires. Run 11 replays identically at every level. In the runs 9A/9B record, every candidate decision is unchanged (all rejected), but the family verdict of `file_edit` at 24 (and at 28 and 32 for `m = 8`) changes from rejected (retention 18 of 19 probes, 0.947) to active, and the candidate's reason from "active family regressed" to "no new family". The cause is the same phenomenon as at run 12 point 33: the 19 probes frozen for `file_edit` in that record contain one `python -m pytest -q | cat` occurrence; the candidate replays `python -m pytest -q` on it, literally wrong, equivalently right. The "27 of 30 consistent" family of the sensitivity study is 28 of 30 in class space, the other two being reads. So the retention failure that blocked that family at every `m` in the sensitivity study was, for one of its two missing probes, a phrasing difference. This does not change any adoption decision in that record (there was no new family to activate), and it is consistent with the hypothesis rather than against it, but it is a change the pre-registration did not predict at the family level; it is recorded before any extension of the contract.

Stopped here. No canonicalizer change, no threshold change, no live run, no grouping of read actions, no `m` selected. The contract is used by no live configuration yet: `serve` does not pass it, and the default remains identity.
