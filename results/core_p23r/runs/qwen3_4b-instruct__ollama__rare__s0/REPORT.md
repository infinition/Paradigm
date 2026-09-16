# P2.3 Real LLM Online Acquisition Report

P2.3 repeats the P2.1 online loop with the deterministic teacher replaced by a real language model. The stream, compiler thresholds, and outcome filter are unchanged. The model is the only source of teacher labels. The active reflex is never modified in place.

## Controller

- Model: `qwen3:4b-instruct`
- Endpoint: `http://127.0.0.1:11435`

## End-to-end result

- Episodes: 69
- Baseline success: 100.0%
- Online success: 100.0%
- Online fast-path coverage: 74.5%
- Baseline LLM calls: 345
- Online LLM calls: 88
- LLM call reduction: 74.5%
- Token reduction: 74.3%
- LLM latency reduction: 75.1%
- Invalid LLM actions (online / baseline): 0 / 0
- Invalid reflex actions reaching tools: 0
- Promotions: 2
- Active reflex version at end: 2

## Novel family acquisition

- First novel-family episode: 20
- Phase B (novel only) fast-path coverage: 0.0%
- Phase C (mixed) novel-family fast-path coverage: 0.0%
- Novel-family overall success: 100.0%
- First novel-family fast-path episode: None
- Novel-family episodes before first fast path: 7
- Acquisition tokens before first fast path: 9066
- Novel family represented from promotion at episode: 68
- Unknown false fast-path rate: 0.0% (0 of 35 decisions while unrepresented)

## Time-to-reflex

- Validated novel-family episodes before representation: 7
- Validated novel-family LLM decisions before representation: 35
- Candidates rejected by shadow validation before representation: 4
- Novel-family episodes before mature reflex (>= 95% fast path, success, no invalid action): None

## Acquisition debt and reflex dividend

- Acquisition debt: 7 episodes, 35 LLM decisions, 9066 tokens, 16.5 s of LLM latency before the novel family's first fast path
- Reflex reached within stream: False
- Reflex dividend on the novel family after representation: 0 LLM calls, 0 tokens, 0.0 s saved over 0 episodes
- Total tokens saved across the stream: 60157
- Debt recovery ratio: n/a

## Old family retention

- Known-family success, phase A: 100.0%
- Known-family success, phase C: 0.0%
- Known-family fast-path coverage, phase A: 31.7%
- Known-family fast-path coverage, phase C: 0.0%

## Learning curve

| Episodes | Success | Fast path | LLM calls | Reflex calls |
|---|---|---|---|---|
| 1-10 | 100% | 20.0% | 40 | 10 |
| 11-20 | 100% | 84.0% | 8 | 42 |
| 21-30 | 100% | 86.0% | 7 | 43 |
| 31-40 | 100% | 86.0% | 7 | 43 |
| 41-50 | 100% | 86.0% | 7 | 43 |
| 51-60 | 100% | 76.0% | 12 | 38 |
| 61-69 | 100% | 84.4% | 7 | 38 |

## Cumulative cost

| Episode | Baseline tokens | Online tokens | Saved |
|---|---|---|---|
| 6 | 6882 | 6891 | -9 |
| 12 | 13910 | 9469 | 4441 |
| 18 | 20790 | 9655 | 11135 |
| 24 | 28103 | 11326 | 16777 |
| 30 | 35064 | 12799 | 22265 |
| 36 | 42150 | 14282 | 27868 |
| 42 | 49253 | 14654 | 34599 |
| 48 | 56203 | 16128 | 40075 |
| 54 | 63306 | 17619 | 45687 |
| 60 | 70331 | 19100 | 51231 |
| 66 | 77385 | 19472 | 57913 |
| 69 | 80924 | 20767 | 60157 |

## Amortization

- LLM tokens spent on compilation: 0
- Local compile and validation wall-clock: 0.04 s
- Cumulative tokens saved: 60157
- Cumulative LLM latency saved: 120.7 s
- Episode at which saved LLM latency exceeds compile wall-clock: 9

Online acquisition spends no extra LLM tokens on compilation: teacher labels come from deliberative calls the LLM-only baseline also pays for. Token savings are therefore net from the first reflex use. The only extra cost is local compile and validation wall-clock, compared here against cumulative LLM latency saved.

## Outcome filtering

- Failed control episode success: False
- Failed control episode admitted traces: 0
- Reflex self-labels ignored as teacher labels: 257

## Limitations

- Single model, single seed, one 69-episode stream in the full run. Not a robust estimate.
- Supervised imitation of LLM decisions from successful episodes only. No credit assignment, no RL.
- The compiled reflex covers tool-control decisions. apply_fix remains a validated repair primitive.
- Latency comparison mixes local compile wall-clock with remote model latency on one machine.

