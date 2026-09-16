# P2.3 Real LLM Online Acquisition Report

P2.3 repeats the P2.1 online loop with the deterministic teacher replaced by a real language model. The stream, compiler thresholds, and outcome filter are unchanged. The model is the only source of teacher labels. The active reflex is never modified in place.

## Controller

- Model: `qwen3:4b-instruct`
- Endpoint: `http://127.0.0.1:11434/v1`

## End-to-end result

- Episodes: 69
- Baseline success: 100.0%
- Online success: 100.0%
- Online fast-path coverage: 67.0%
- Baseline LLM calls: 345
- Online LLM calls: 114
- LLM call reduction: 67.0%
- Token reduction: 66.6%
- LLM latency reduction: 66.8%
- Invalid LLM actions (online / baseline): 0 / 0
- Invalid reflex actions reaching tools: 0
- Promotions: 2
- Active reflex version at end: 2

## Novel family acquisition

- First novel-family episode: 33
- Phase B (novel only) fast-path coverage: 16.7%
- Phase C (mixed) novel-family fast-path coverage: 100.0%
- Novel-family overall success: 100.0%
- First novel-family fast-path episode: 43
- Novel-family episodes before first fast path: 10
- Acquisition tokens before first fast path: 12958
- Novel family represented from promotion at episode: 42
- Unknown false fast-path rate: 0.0% (0 of 50 decisions while unrepresented)

## Time-to-reflex

- Validated novel-family episodes before representation: 10
- Validated novel-family LLM decisions before representation: 50
- Learning evidence (novel share of the promoted candidate's train split): 4 episodes, 20 decisions
- Certification evidence (novel share of its validation split): 6 episodes, 30 decisions
- Outcome: promoted
- Candidates rejected by shadow validation before representation: 2
- Novel-family episodes before mature reflex (>= 95% fast path, success, no invalid action): 10

## Acquisition debt and reflex dividend

- Acquisition debt: 10 episodes, 50 LLM decisions, 12958 tokens, 40.6 s of LLM latency before the novel family's first fast path
- Reflex reached within stream: True
- Reflex dividend on the novel family after representation: 35 LLM calls, 9080 tokens, 28.3 s saved over 7 episodes
- Total tokens saved across the stream: 55086
- Debt recovery ratio (novel dividend tokens / acquisition debt tokens): 70.1%

## Old family retention

- Known-family success, phase A: 100.0%
- Known-family success, phase C: 100.0%
- Known-family fast-path coverage, phase A: 61.3%
- Known-family fast-path coverage, phase C: 98.0%

## Learning curve

| Episodes | Success | Fast path | LLM calls | Reflex calls |
|---|---|---|---|---|
| 1-10 | 100% | 0.0% | 50 | 0 |
| 11-20 | 100% | 78.0% | 11 | 39 |
| 21-30 | 100% | 98.0% | 1 | 49 |
| 31-40 | 100% | 20.0% | 40 | 10 |
| 41-50 | 100% | 78.0% | 11 | 39 |
| 51-60 | 100% | 98.0% | 1 | 49 |
| 61-69 | 100% | 100.0% | 0 | 45 |

## Cumulative cost

| Episode | Baseline tokens | Online tokens | Saved |
|---|---|---|---|
| 6 | 6908 | 6897 | 11 |
| 12 | 13988 | 13981 | 7 |
| 18 | 20938 | 13981 | 6957 |
| 24 | 28063 | 14167 | 13896 |
| 30 | 34974 | 14353 | 20621 |
| 36 | 42597 | 19531 | 23066 |
| 42 | 50373 | 27311 | 23062 |
| 48 | 57583 | 27311 | 30272 |
| 54 | 64898 | 27491 | 37407 |
| 60 | 71985 | 27671 | 44314 |
| 66 | 79054 | 27671 | 51383 |
| 69 | 82757 | 27671 | 55086 |

## Amortization

- LLM tokens spent on compilation: 0
- Local compile and validation wall-clock: 0.04 s
- Cumulative tokens saved: 55086
- Cumulative LLM latency saved: 176.3 s
- Episode at which saved LLM latency exceeds compile wall-clock: 13

Online acquisition spends no extra LLM tokens on compilation: teacher labels come from deliberative calls the LLM-only baseline also pays for. Token savings are therefore net from the first reflex use. The only extra cost is local compile and validation wall-clock, compared here against cumulative LLM latency saved.

## Promotion audit

Train and validation composition of every candidate, reconstructed from the per-episode log (traces = deliberative decisions of buffered successful episodes; validation = most recent 25% of episodes). Novel shadow acceptance is recorded only for runs made after per-family acceptance was added.

| Episode | Decision | Train known / novel | Validation known / novel | Novel share of validation | Overall shadow acceptance | Novel shadow acceptance | Reason |
|---|---|---|---|---|---|---|---|
| 8 | reject | 30 / 0 | 10 / 0 | 0% | 0% | n/a | ood_shadow_coverage_failed |
| 12 | promote | 45 / 0 | 15 / 0 | 0% | 93% | n/a | quality_and_trust_pass |
| 34 | reject | 60 / 0 | 2 / 10 | 83% | 17% | n/a | ood_shadow_coverage_failed |
| 38 | reject | 62 / 5 | 0 / 25 | 100% | 16% | n/a | ood_shadow_coverage_failed |
| 42 | promote | 62 / 20 | 0 / 30 | 100% | 100% | n/a | quality_and_trust_pass |

## Outcome filtering

- Failed control episode success: False
- Failed control episode admitted traces: 0
- Reflex self-labels ignored as teacher labels: 231

## Limitations

- Single model, single seed, one 69-episode stream in the full run. Not a robust estimate.
- Supervised imitation of LLM decisions from successful episodes only. No credit assignment, no RL.
- The compiled reflex covers tool-control decisions. apply_fix remains a validated repair primitive.
- Latency comparison mixes local compile wall-clock with remote model latency on one machine.

