# P2.3R-bis Family-Aware Certification Report

Each stream is run twice with the same model, tasks, compiler cadence, and thresholds. In one run the P2.1 recent-split rule decides promotion and family-aware certification is evaluated in shadow; in the other the roles are reversed. Family-aware certification requires every family in the validation split to have enough episodes and pass shadow acceptance on its own, and every mature family to pass coverage and agreement on an immutable retention probe set frozen at its first promotion. A negative control candidate that preserves the novel family but relabels one mature family's decisions is certified under both rules on the final buffer.

Narrative interpretation: `INTERPRETATION.md` in this directory.

## Live stream comparison

| Arrival | Seed | Rule | Success | LLM calls | TTR | Deployed at | Outcome | False FP | Known success after | Known fast path after | Candidates promoted / rejected / insufficient | Probe evaluations | Shadow disagreements |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| burst | 0 | recent | 100% | -70% | 12 | 44 | promoted | 0% | 100% | 100% | 3 / 2 / 0 | 0 | 3 |
| burst | 0 | family_aware | 100% | -59% | 12 | 44 | promoted | 0% | 100% | 100% | 2 / 2 / 2 | 240 | 2 |
| interleaved | 0 | recent | 100% | -76% | 7 | 34 | promoted | 0% | 100% | 100% | 2 / 2 / 0 | 0 | 2 |
| interleaved | 0 | family_aware | 100% | -53% | 6 | 32 | promoted | 0% | 100% | 100% | 1 / 4 / 2 | 0 | 6 |
| periodic | 0 | recent | 100% | -77% | 7 | 37 | promoted | 0% | 100% | 100% | 2 / 2 / 0 | 0 | 2 |
| periodic | 0 | family_aware | 100% | -56% | 6 | 28 | promoted | 0% | 100% | 100% | 2 / 1 / 4 | 100 | 5 |
| rare | 0 | recent | 100% | -74% | 7 | 68 | promoted | 0% | 100% | 100% | 2 / 4 / 0 | 0 | 2 |
| rare | 0 | family_aware | 100% | -67% | None | None | insufficient_evidence | 0% | n/a | n/a | 1 / 1 / 2 | 80 | 2 |

## Certifier disagreement on live candidates

Every candidate compiled in any run, classified by the verdict each rule gave (one of them authoritative, the other in shadow). Live streams contain no deliberately damaged candidates, so retention catches on live candidates are not expected; the negative control section reports the deliberate damage case.

| Recent | Family-aware | Count | Interpretation |
|---|---|---|---|
| promote | promote | 5 | agreement |
| reject | reject | 14 | agreement |
| promote | insufficient | 19 | evidence availability: a family was absent from the validation split |
| promote | reject | 4 | conservative: novel family below floor on its own while the overall rule passed |
| reject | promote | 1 | family-aware accepts what recent blocks |

Negative control verdicts (a rule discriminates only when it promotes the clean candidate): family-aware caught 3, missed 0, non-discriminating 1, inversions 0; recent caught 0, missed 2, non-discriminating 2, inversions 0, out of 4 pairs. Additional deliberative decisions across pairs: 215. Diagnostic yield (regressions caught by family-aware per additional deliberative decision): 0.0140.

## Certification delay and negative control

| Arrival | Seed | Novel deployment delay (episodes) | Additional deliberative decisions | Damaged family | Poisoned traces | Damaged family in validation | Clean: recent / family-aware | Poisoned: recent / family-aware | Verdict recent / family-aware | Poisoned probe agreement on damaged family | Poisoned probe agreement on novel family |
|---|---|---|---|---|---|---|---|---|---|---|---|
| burst | 0 | 0 | 36 | missing_import | 4 | False | promoted / promoted | promoted / rejected | missed / caught | 80% | 100% |
| interleaved | 0 | -2 | 81 | missing_import | 6 | True | promoted / promoted | promoted / rejected | missed / caught | 80% | 100% |
| periodic | 0 | -9 | 71 | missing_import | 6 | False | rejected / promoted | rejected / rejected | non_discriminating / caught | 80% | 100% |
| rare | 0 | None | 27 | missing_import | 4 | False | rejected / rejected | rejected / rejected | non_discriminating / non_discriminating | 80% | n/a |

