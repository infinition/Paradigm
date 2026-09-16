# P2.3R-bis Family-Aware Certification Report

Each stream is run twice with the same model, tasks, compiler cadence, and thresholds. In one run the P2.1 recent-split rule decides promotion and family-aware certification is evaluated in shadow; in the other the roles are reversed. Family-aware certification requires every family in the validation split to have enough episodes and pass shadow acceptance on its own, and every mature family to pass coverage and agreement on an immutable retention probe set frozen at its first promotion. A negative control candidate that preserves the novel family but relabels one mature family's decisions is certified under both rules on the final buffer.

Narrative interpretation: `INTERPRETATION.md` in this directory.

## Live stream comparison

| Arrival | Seed | Rule | Success | LLM calls | TTR | Deployed at | Outcome | False FP | Known success after | Known fast path after | Candidates promoted / rejected / insufficient | Probe evaluations | Shadow disagreements |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| interleaved | 0 | recent | 100% | -76% | 7 | 34 | promoted | 0% | 100% | 100% | 2 / 2 / 0 | 0 | 2 |
| interleaved | 0 | family_aware | 100% | -30% | 11 | 48 | promoted | 0% | 100% | 100% | 1 / 2 / 8 | 0 | 10 |

## Certifier disagreement on live candidates

Every candidate compiled in any run, classified by the verdict each rule gave (one of them authoritative, the other in shadow). Live streams contain no deliberately damaged candidates, so retention catches on live candidates are not expected; the negative control section reports the deliberate damage case.

| Recent | Family-aware | Count | Interpretation |
|---|---|---|---|
| promote | promote | 1 | agreement |
| reject | reject | 2 | agreement |
| promote | insufficient | 10 | evidence availability: a family was absent from the validation split |
| promote | reject | 2 | conservative: novel family below floor on its own while the overall rule passed |

Negative control verdicts (a rule discriminates only when it promotes the clean candidate): family-aware caught 1, missed 0, non-discriminating 0, inversions 0; recent caught 0, missed 1, non-discriminating 0, inversions 0, out of 1 pairs. Additional deliberative decisions across pairs: 160. Diagnostic yield (regressions caught by family-aware per additional deliberative decision): 0.0063.

## Certification delay and negative control

| Arrival | Seed | Novel deployment delay (episodes) | Additional deliberative decisions | Damaged family | Poisoned traces | Damaged family in validation | Clean: recent / family-aware | Poisoned: recent / family-aware | Verdict recent / family-aware | Poisoned probe agreement on damaged family | Poisoned probe agreement on novel family |
|---|---|---|---|---|---|---|---|---|---|---|---|
| interleaved | 0 | 14 | 160 | missing_import | 8 | True | promoted / promoted | promoted / rejected | missed / caught | 80% | 100% |

