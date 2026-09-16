# P2.3 Real LLM Online Acquisition Report

P2.3 repeats the P2.1 online loop with the deterministic teacher replaced by a real language model. The stream, compiler thresholds, and outcome filter are unchanged. The model is the only source of teacher labels. The active reflex is never modified in place.

## Controller

- Model: `qwen3:8b`
- Endpoint: `http://127.0.0.1:11435`

## End-to-end result

- Episodes: 69
- Baseline success: 100.0%
- Online success: 100.0%
- Online fast-path coverage: 76.5%
- Baseline LLM calls: 345
- Online LLM calls: 81
- LLM call reduction: 76.5%
- Token reduction: 76.2%
- LLM latency reduction: 77.3%
- Invalid LLM actions (online / baseline): 0 / 0
- Invalid reflex actions reaching tools: 0
- Promotions: 2
- Active reflex version at end: 2

## Novel family acquisition

- First novel-family episode: 13
- Phase B (novel only) fast-path coverage: 0.0%
- Phase C (mixed) novel-family fast-path coverage: 0.0%
- Novel-family overall success: 100.0%
- First novel-family fast-path episode: 38
- Novel-family episodes before first fast path: 7
- Acquisition tokens before first fast path: 9164
- Novel family represented from promotion at episode: 37
- Unknown false fast-path rate: 0.0% (0 of 35 decisions while unrepresented)

## Time-to-reflex

- Validated novel-family episodes before representation: 7
- Validated novel-family LLM decisions before representation: 35
- Candidates rejected by shadow validation before representation: 2
- Novel-family episodes before mature reflex (>= 95% fast path, success, no invalid action): 11

## Acquisition debt and reflex dividend

- Acquisition debt: 7 episodes, 35 LLM decisions, 9164 tokens, 19.4 s of LLM latency before the novel family's first fast path
- Reflex reached within stream: True
- Reflex dividend on the novel family after representation: 24 LLM calls, 6363 tokens, 13.8 s saved over 5 episodes
- Total tokens saved across the stream: 63532
- Debt recovery ratio (novel dividend tokens / acquisition debt tokens): 69.4%

## Old family retention

- Known-family success, phase A: 100.0%
- Known-family success, phase C: 0.0%
- Known-family fast-path coverage, phase A: 31.7%
- Known-family fast-path coverage, phase C: 0.0%

## Learning curve

| Episodes | Success | Fast path | LLM calls | Reflex calls |
|---|---|---|---|---|
| 1-10 | 100% | 20.0% | 40 | 10 |
| 11-20 | 100% | 66.0% | 17 | 33 |
| 21-30 | 100% | 66.0% | 17 | 33 |
| 31-40 | 100% | 88.0% | 6 | 44 |
| 41-50 | 100% | 98.0% | 1 | 49 |
| 51-60 | 100% | 100.0% | 0 | 50 |
| 61-69 | 100% | 100.0% | 0 | 45 |

## Cumulative cost

| Episode | Baseline tokens | Online tokens | Saved |
|---|---|---|---|
| 6 | 7033 | 7025 | 8 |
| 12 | 14229 | 9682 | 4547 |
| 18 | 21829 | 13804 | 8025 |
| 24 | 28815 | 13996 | 14819 |
| 30 | 36311 | 18111 | 18200 |
| 36 | 43348 | 18303 | 25045 |
| 42 | 50936 | 19614 | 31322 |
| 48 | 58173 | 19614 | 38559 |
| 54 | 65434 | 19790 | 45644 |
| 60 | 72662 | 19790 | 52872 |
| 66 | 79667 | 19790 | 59877 |
| 69 | 83322 | 19790 | 63532 |

## Amortization

- LLM tokens spent on compilation: 0
- Local compile and validation wall-clock: 0.02 s
- Cumulative tokens saved: 63532
- Cumulative LLM latency saved: 153.6 s
- Episode at which saved LLM latency exceeds compile wall-clock: 9

Online acquisition spends no extra LLM tokens on compilation: teacher labels come from deliberative calls the LLM-only baseline also pays for. Token savings are therefore net from the first reflex use. The only extra cost is local compile and validation wall-clock, compared here against cumulative LLM latency saved.

## Outcome filtering

- Failed control episode success: False
- Failed control episode admitted traces: 0
- Reflex self-labels ignored as teacher labels: 264

## Limitations

- Single model, single seed, one 69-episode stream in the full run. Not a robust estimate.
- Supervised imitation of LLM decisions from successful episodes only. No credit assignment, no RL.
- The compiled reflex covers tool-control decisions. apply_fix remains a validated repair primitive.
- Latency comparison mixes local compile wall-clock with remote model latency on one machine.

