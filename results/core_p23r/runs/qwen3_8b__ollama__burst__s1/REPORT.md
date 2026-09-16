# P2.3 Real LLM Online Acquisition Report

P2.3 repeats the P2.1 online loop with the deterministic teacher replaced by a real language model. The stream, compiler thresholds, and outcome filter are unchanged. The model is the only source of teacher labels. The active reflex is never modified in place.

## Controller

- Model: `qwen3:8b`
- Endpoint: `http://127.0.0.1:11435`

## End-to-end result

- Episodes: 69
- Baseline success: 100.0%
- Online success: 100.0%
- Online fast-path coverage: 69.6%
- Baseline LLM calls: 345
- Online LLM calls: 105
- LLM call reduction: 69.6%
- Token reduction: 68.8%
- LLM latency reduction: 70.4%
- Invalid LLM actions (online / baseline): 0 / 0
- Invalid reflex actions reaching tools: 0
- Promotions: 3
- Active reflex version at end: 3

## Novel family acquisition

- First novel-family episode: 33
- Phase B (novel only) fast-path coverage: 0.0%
- Phase C (mixed) novel-family fast-path coverage: 96.0%
- Novel-family overall success: 100.0%
- First novel-family fast-path episode: 49
- Novel-family episodes before first fast path: 12
- Acquisition tokens before first fast path: 15710
- Novel family represented from promotion at episode: 44
- Unknown false fast-path rate: 0.0% (0 of 60 decisions while unrepresented)

## Time-to-reflex

- Validated novel-family episodes before representation: 12
- Validated novel-family LLM decisions before representation: 60
- Candidates rejected by shadow validation before representation: 2
- Novel-family episodes before mature reflex (>= 95% fast path, success, no invalid action): 15

## Acquisition debt and reflex dividend

- Acquisition debt: 12 episodes, 60 LLM decisions, 15710 tokens, 33.0 s of LLM latency before the novel family's first fast path
- Reflex reached within stream: True
- Reflex dividend on the novel family after representation: 24 LLM calls, 6384 tokens, 13.2 s saved over 5 episodes
- Total tokens saved across the stream: 57786
- Debt recovery ratio (novel dividend tokens / acquisition debt tokens): 40.6%

## Old family retention

- Known-family success, phase A: 100.0%
- Known-family success, phase C: 100.0%
- Known-family fast-path coverage, phase A: 72.5%
- Known-family fast-path coverage, phase C: 100.0%

## Learning curve

| Episodes | Success | Fast path | LLM calls | Reflex calls |
|---|---|---|---|---|
| 1-10 | 100% | 20.0% | 40 | 10 |
| 11-20 | 100% | 94.0% | 3 | 47 |
| 21-30 | 100% | 98.0% | 1 | 49 |
| 31-40 | 100% | 20.0% | 40 | 10 |
| 41-50 | 100% | 60.0% | 20 | 30 |
| 51-60 | 100% | 98.0% | 1 | 49 |
| 61-69 | 100% | 100.0% | 0 | 45 |

## Cumulative cost

| Episode | Baseline tokens | Online tokens | Saved |
|---|---|---|---|
| 6 | 7019 | 7008 | 11 |
| 12 | 14249 | 9688 | 4561 |
| 18 | 21257 | 9880 | 11377 |
| 24 | 28459 | 10264 | 18195 |
| 30 | 35478 | 10264 | 25214 |
| 36 | 43176 | 15502 | 27674 |
| 42 | 51035 | 23350 | 27685 |
| 48 | 58400 | 25974 | 32426 |
| 54 | 65774 | 25974 | 39800 |
| 60 | 72996 | 26150 | 46846 |
| 66 | 80144 | 26150 | 53994 |
| 69 | 83936 | 26150 | 57786 |

## Amortization

- LLM tokens spent on compilation: 0
- Local compile and validation wall-clock: 0.03 s
- Cumulative tokens saved: 57786
- Cumulative LLM latency saved: 136.8 s
- Episode at which saved LLM latency exceeds compile wall-clock: 9

Online acquisition spends no extra LLM tokens on compilation: teacher labels come from deliberative calls the LLM-only baseline also pays for. Token savings are therefore net from the first reflex use. The only extra cost is local compile and validation wall-clock, compared here against cumulative LLM latency saved.

## Outcome filtering

- Failed control episode success: False
- Failed control episode admitted traces: 0
- Reflex self-labels ignored as teacher labels: 240

## Limitations

- Single model, single seed, one 69-episode stream in the full run. Not a robust estimate.
- Supervised imitation of LLM decisions from successful episodes only. No credit assignment, no RL.
- The compiled reflex covers tool-control decisions. apply_fix remains a validated repair primitive.
- Latency comparison mixes local compile wall-clock with remote model latency on one machine.

