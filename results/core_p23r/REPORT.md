# P2.3R Replication Report

P2.3 repeated across seeds, models, and novel-family arrival orders with one transport, prompt, schema, temperature, output budget, compiler configuration, and promotion rule. Time-to-reflex (TTR) counts validated novel-family episodes before the first promotion that represents the family. A run where the reflex is never reached within the stream is a valid outcome. Debt recovery ratio is reflex dividend divided by acquisition debt, reported separately for tokens, LLM calls, and LLM latency.

Runs in the primary matrix: 24

## Per run

| Model | API | Arrival | Seed | Success | LLM calls | Tokens | TTR (learn + certify) | Outcome | Deployed at | Exposure after | Debt tokens | Dividend tokens | Recovery tokens / calls / latency | False FP | Promoted / rejected |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen3:4b-instruct | ollama | burst | 0 | 100% | -70% | -69% | 12 (6 + 6) | promoted | 44 | 5 | 15519 | 6298 | 41% / 40% / 40% | 0% | 3 / 2 |
| qwen3:4b-instruct | ollama | burst | 1 | 100% | -70% | -69% | 12 (6 + 6) | promoted | 44 | 5 | 15540 | 6295 | 41% / 40% / 40% | 0% | 3 / 2 |
| qwen3:4b-instruct | ollama | burst | 2 | 100% | -70% | -69% | 12 (6 + 6) | promoted | 44 | 5 | 15537 | 6316 | 41% / 40% / 43% | 0% | 3 / 2 |
| qwen3:4b-instruct | ollama | interleaved | 0 | 100% | -76% | -76% | 7 (4 + 3) | promoted | 34 | 10 | 9079 | 12586 | 139% / 137% / 139% | 0% | 2 / 2 |
| qwen3:4b-instruct | ollama | interleaved | 1 | 100% | -76% | -76% | 7 (4 + 3) | promoted | 34 | 10 | 9071 | 12590 | 139% / 137% / 140% | 0% | 2 / 2 |
| qwen3:4b-instruct | ollama | interleaved | 2 | 100% | -76% | -76% | 7 (4 + 3) | promoted | 34 | 10 | 9067 | 12603 | 139% / 137% / 137% | 0% | 2 / 2 |
| qwen3:4b-instruct | ollama | periodic | 0 | 100% | -77% | -76% | 7 (4 + 3) | promoted | 37 | 5 | 9068 | 6276 | 69% / 69% / 70% | 0% | 2 / 2 |
| qwen3:4b-instruct | ollama | periodic | 1 | 100% | -77% | -76% | 7 (4 + 3) | promoted | 37 | 5 | 9079 | 6277 | 69% / 69% / 72% | 0% | 2 / 2 |
| qwen3:4b-instruct | ollama | periodic | 2 | 100% | -77% | -76% | 7 (4 + 3) | promoted | 37 | 5 | 9075 | 6289 | 69% / 69% / 72% | 0% | 2 / 2 |
| qwen3:4b-instruct | ollama | rare | 0 | 100% | -74% | -74% | 7 (4 + 3) | promoted | 68 | 0 | 9066 | 0 | 0% / 0% / 0% | 0% | 2 / 4 |
| qwen3:4b-instruct | ollama | rare | 1 | 100% | -74% | -74% | 7 (4 + 3) | promoted | 68 | 0 | 9080 | 0 | 0% / 0% / 0% | 0% | 2 / 4 |
| qwen3:4b-instruct | ollama | rare | 2 | 100% | -74% | -74% | 7 (4 + 3) | promoted | 68 | 0 | 9064 | 0 | 0% / 0% / 0% | 0% | 2 / 4 |
| qwen3:8b | ollama | burst | 0 | 100% | -70% | -69% | 12 (6 + 6) | promoted | 44 | 5 | 15720 | 6377 | 41% / 40% / 40% | 0% | 3 / 2 |
| qwen3:8b | ollama | burst | 1 | 100% | -70% | -69% | 12 (6 + 6) | promoted | 44 | 5 | 15710 | 6384 | 41% / 40% / 40% | 0% | 3 / 2 |
| qwen3:8b | ollama | burst | 2 | 100% | -70% | -69% | 12 (6 + 6) | promoted | 44 | 5 | 15674 | 6391 | 41% / 40% / 42% | 0% | 3 / 2 |
| qwen3:8b | ollama | interleaved | 0 | 100% | -76% | -76% | 7 (4 + 3) | promoted | 34 | 10 | 9172 | 12713 | 139% / 137% / 141% | 0% | 2 / 2 |
| qwen3:8b | ollama | interleaved | 1 | 100% | -76% | -76% | 7 (4 + 3) | promoted | 34 | 10 | 9159 | 12729 | 139% / 137% / 140% | 0% | 2 / 2 |
| qwen3:8b | ollama | interleaved | 2 | 100% | -76% | -76% | 7 (4 + 3) | promoted | 34 | 10 | 9157 | 12725 | 139% / 137% / 140% | 0% | 2 / 2 |
| qwen3:8b | ollama | periodic | 0 | 100% | -77% | -76% | 7 (4 + 3) | promoted | 37 | 5 | 9164 | 6363 | 69% / 69% / 71% | 0% | 2 / 2 |
| qwen3:8b | ollama | periodic | 1 | 100% | -77% | -76% | 7 (4 + 3) | promoted | 37 | 5 | 9171 | 6356 | 69% / 69% / 67% | 0% | 2 / 2 |
| qwen3:8b | ollama | periodic | 2 | 100% | -77% | -76% | 7 (4 + 3) | promoted | 37 | 5 | 9124 | 6356 | 70% / 69% / 70% | 0% | 2 / 2 |
| qwen3:8b | ollama | rare | 0 | 100% | -74% | -74% | 7 (4 + 3) | promoted | 68 | 0 | 9160 | 0 | 0% / 0% / 0% | 0% | 2 / 4 |
| qwen3:8b | ollama | rare | 1 | 100% | -74% | -74% | 7 (4 + 3) | promoted | 68 | 0 | 9162 | 0 | 0% / 0% / 0% | 0% | 2 / 4 |
| qwen3:8b | ollama | rare | 2 | 100% | -74% | -74% | 7 (4 + 3) | promoted | 68 | 0 | 9163 | 0 | 0% / 0% / 0% | 0% | 2 / 4 |

## Success and savings by model and arrival order

| Model | Arrival | Seeds | Online success | Baseline success | LLM call reduction mean [min, max] | LLM call reduction median | Token reduction mean [min, max] | Token reduction median | Latency reduction mean | Invalid actions |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen3:4b-instruct | burst | 3 | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 69.6% [69.6%, 69.6%] | 69.6% (IQR 0.0%) | 68.7% [68.7%, 68.8%] | 68.7% (IQR 0.1%) | 69.5% | 0 [0, 0] |
| qwen3:4b-instruct | interleaved | 3 | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 76.2% [76.2%, 76.2%] | 76.2% (IQR 0.0%) | 76.2% [76.1%, 76.2%] | 76.1% (IQR 0.0%) | 76.5% | 0 [0, 0] |
| qwen3:4b-instruct | periodic | 3 | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 76.5% [76.5%, 76.5%] | 76.5% (IQR 0.0%) | 76.2% [76.1%, 76.2%] | 76.2% (IQR 0.0%) | 77.0% | 0 [0, 0] |
| qwen3:4b-instruct | rare | 3 | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 74.5% [74.5%, 74.5%] | 74.5% (IQR 0.0%) | 74.3% [74.3%, 74.3%] | 74.3% (IQR 0.0%) | 75.2% | 0 [0, 0] |
| qwen3:8b | burst | 3 | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 69.6% [69.6%, 69.6%] | 69.6% (IQR 0.0%) | 68.8% [68.8%, 68.9%] | 68.8% (IQR 0.1%) | 69.8% | 0 [0, 0] |
| qwen3:8b | interleaved | 3 | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 76.2% [76.2%, 76.2%] | 76.2% (IQR 0.0%) | 76.2% [76.2%, 76.2%] | 76.2% (IQR 0.0%) | 77.0% | 0 [0, 0] |
| qwen3:8b | periodic | 3 | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 76.5% [76.5%, 76.5%] | 76.5% (IQR 0.0%) | 76.3% [76.2%, 76.3%] | 76.2% (IQR 0.1%) | 77.2% | 0 [0, 0] |
| qwen3:8b | rare | 3 | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 74.5% [74.5%, 74.5%] | 74.5% (IQR 0.0%) | 74.4% [74.4%, 74.4%] | 74.4% (IQR 0.0%) | 75.5% | 0 [0, 0] |

## Novel family acquisition

| Model | Arrival | Promoted (certified) | Exercised after promotion | Outcomes promoted / rejected / insufficient | TTR median (IQR) | TTR mean [min, max] | Learning episodes | Certification episodes | Rejected before | Novel fast path after | Novel success | False fast path |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen3:4b-instruct | burst | 3/3 | 3/3 | 3 / 0 / 0 | 12 (IQR 0) | 12.0 [12.0, 12.0] | 6.0 [6.0, 6.0] | 6.0 [6.0, 6.0] | 2.0 [2.0, 2.0] | 96.0% [96.0%, 96.0%] | 100.0% [100.0%, 100.0%] | 0.0% [0.0%, 0.0%] |
| qwen3:4b-instruct | interleaved | 3/3 | 3/3 | 3 / 0 / 0 | 7 (IQR 0) | 7.0 [7.0, 7.0] | 4.0 [4.0, 4.0] | 3.0 [3.0, 3.0] | 2.0 [2.0, 2.0] | 96.0% [96.0%, 96.0%] | 100.0% [100.0%, 100.0%] | 0.0% [0.0%, 0.0%] |
| qwen3:4b-instruct | periodic | 3/3 | 3/3 | 3 / 0 / 0 | 7 (IQR 0) | 7.0 [7.0, 7.0] | 4.0 [4.0, 4.0] | 3.0 [3.0, 3.0] | 2.0 [2.0, 2.0] | 96.0% [96.0%, 96.0%] | 100.0% [100.0%, 100.0%] | 0.0% [0.0%, 0.0%] |
| qwen3:4b-instruct | rare | 3/3 | 0/3 | 3 / 0 / 0 | 7 (IQR 0) | 7.0 [7.0, 7.0] | 4.0 [4.0, 4.0] | 3.0 [3.0, 3.0] | 4.0 [4.0, 4.0] | n/a | 100.0% [100.0%, 100.0%] | 0.0% [0.0%, 0.0%] |
| qwen3:8b | burst | 3/3 | 3/3 | 3 / 0 / 0 | 12 (IQR 0) | 12.0 [12.0, 12.0] | 6.0 [6.0, 6.0] | 6.0 [6.0, 6.0] | 2.0 [2.0, 2.0] | 96.0% [96.0%, 96.0%] | 100.0% [100.0%, 100.0%] | 0.0% [0.0%, 0.0%] |
| qwen3:8b | interleaved | 3/3 | 3/3 | 3 / 0 / 0 | 7 (IQR 0) | 7.0 [7.0, 7.0] | 4.0 [4.0, 4.0] | 3.0 [3.0, 3.0] | 2.0 [2.0, 2.0] | 96.0% [96.0%, 96.0%] | 100.0% [100.0%, 100.0%] | 0.0% [0.0%, 0.0%] |
| qwen3:8b | periodic | 3/3 | 3/3 | 3 / 0 / 0 | 7 (IQR 0) | 7.0 [7.0, 7.0] | 4.0 [4.0, 4.0] | 3.0 [3.0, 3.0] | 2.0 [2.0, 2.0] | 96.0% [96.0%, 96.0%] | 100.0% [100.0%, 100.0%] | 0.0% [0.0%, 0.0%] |
| qwen3:8b | rare | 3/3 | 0/3 | 3 / 0 / 0 | 7 (IQR 0) | 7.0 [7.0, 7.0] | 4.0 [4.0, 4.0] | 3.0 [3.0, 3.0] | 4.0 [4.0, 4.0] | n/a | 100.0% [100.0%, 100.0%] | 0.0% [0.0%, 0.0%] |

## Acquisition debt, reflex dividend, and recovery

Only runs whose novel family was promoted contribute to debt and dividend cells. A promoted reflex with no later novel exposure has a dividend of zero.

| Model | Arrival | Deployed at episode | Novel exposure after | Debt episodes | Debt decisions | Debt tokens | Debt latency s | Dividend calls | Dividend tokens | Dividend latency s | Recovery tokens | Recovery calls | Recovery latency |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen3:4b-instruct | burst | 44 [44, 44] | 5 [5, 5] | 12 [12, 12] | 60 [60, 60] | 15532 [15519, 15540] | 28.2 | 24 [24, 24] | 6303 [6295, 6316] | 11.5 | 41% [41%, 41%] | 40% [40%, 40%] | 41% [40%, 43%] |
| qwen3:4b-instruct | interleaved | 34 [34, 34] | 10 [10, 10] | 7 [7, 7] | 35 [35, 35] | 9072 [9067, 9079] | 16.6 | 48 [48, 48] | 12593 [12586, 12603] | 23.0 | 139% [139%, 139%] | 137% [137%, 137%] | 139% [137%, 140%] |
| qwen3:4b-instruct | periodic | 37 [37, 37] | 5 [5, 5] | 7 [7, 7] | 35 [35, 35] | 9074 [9068, 9079] | 16.4 | 24 [24, 24] | 6281 [6276, 6289] | 11.7 | 69% [69%, 69%] | 69% [69%, 69%] | 71% [70%, 72%] |
| qwen3:4b-instruct | rare | 68 [68, 68] | 0 [0, 0] | 7 [7, 7] | 35 [35, 35] | 9070 [9064, 9080] | 16.4 | 0 [0, 0] | 0 [0, 0] | 0.0 | 0% [0%, 0%] | 0% [0%, 0%] | 0% [0%, 0%] |
| qwen3:8b | burst | 44 [44, 44] | 5 [5, 5] | 12 [12, 12] | 60 [60, 60] | 15701 [15674, 15720] | 32.9 | 24 [24, 24] | 6384 [6377, 6391] | 13.4 | 41% [41%, 41%] | 40% [40%, 40%] | 41% [40%, 42%] |
| qwen3:8b | interleaved | 34 [34, 34] | 10 [10, 10] | 7 [7, 7] | 35 [35, 35] | 9163 [9157, 9172] | 19.2 | 48 [48, 48] | 12722 [12713, 12729] | 26.9 | 139% [139%, 139%] | 137% [137%, 137%] | 140% [140%, 141%] |
| qwen3:8b | periodic | 37 [37, 37] | 5 [5, 5] | 7 [7, 7] | 35 [35, 35] | 9153 [9124, 9171] | 19.2 | 24 [24, 24] | 6358 [6356, 6363] | 13.4 | 69% [69%, 70%] | 69% [69%, 69%] | 69% [67%, 71%] |
| qwen3:8b | rare | 68 [68, 68] | 0 [0, 0] | 7 [7, 7] | 35 [35, 35] | 9162 [9160, 9163] | 19.1 | 0 [0, 0] | 0 [0, 0] | 0.0 | 0% [0%, 0%] | 0% [0%, 0%] | 0% [0%, 0%] |

## Old family retention

| Model | Arrival | Known success before novel | Known success after representation | Known fast path after representation |
|---|---|---|---|---|
| qwen3:4b-instruct | burst | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] |
| qwen3:4b-instruct | interleaved | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] |
| qwen3:4b-instruct | periodic | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] |
| qwen3:4b-instruct | rare | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] |
| qwen3:8b | burst | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] |
| qwen3:8b | interleaved | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] |
| qwen3:8b | periodic | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] |
| qwen3:8b | rare | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] |

## Teacher efficiency

Per model across all arrival orders. Acquisition columns count only runs that reached a reflex.

| Model | Runs | Reflexes acquired | Validated episodes before maturity | Acquisition tokens before maturity | Acquisition latency s before maturity | Tokens per LLM call | Latency ms per LLM call | Online success | Invalid actions |
|---|---|---|---|---|---|---|---|---|---|
| qwen3:4b-instruct | 12 | 12 | 7 (IQR 4) | 10687 [9064, 15540] | 19.4 | 237 | 468 | 100.0% [100.0%, 100.0%] | 0 |
| qwen3:8b | 12 | 12 | 7 (IQR 4) | 10795 [9124, 15720] | 22.6 | 242 | 569 | 100.0% [100.0%, 100.0%] | 0 |

## Certification boundary

Shadow OOD acceptance of every candidate whose validation split contained the novel family, grouped by the number of novel-family episodes in its train split. This is observational: the compile cadence decides which configurations are tested, so it does not establish a minimum requirement.

| Model | Novel episodes in train | Candidates | Promoted | Acceptance min | Acceptance max | Acceptances |
|---|---|---|---|---|---|---|
| qwen3:4b-instruct | 0 | 12 | 0 | 0.00 | 0.29 | 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.09, 0.09, 0.09, 0.29, 0.29, 0.29 |
| qwen3:4b-instruct | 1 | 3 | 0 | 0.38 | 0.38 | 0.38, 0.38, 0.38 |
| qwen3:4b-instruct | 2 | 6 | 0 | 0.17 | 0.23 | 0.17, 0.17, 0.17, 0.23, 0.23, 0.23 |
| qwen3:4b-instruct | 3 | 9 | 0 | 0.56 | 0.64 | 0.56, 0.56, 0.56, 0.58, 0.58, 0.58, 0.64, 0.64, 0.64 |
| qwen3:4b-instruct | 4 | 9 | 9 | 0.94 | 0.95 | 0.94, 0.94, 0.94, 0.94, 0.94, 0.94, 0.95, 0.95, 0.95 |
| qwen3:4b-instruct | 6 | 3 | 3 | 0.93 | 0.93 | 0.93, 0.93, 0.93 |
| qwen3:8b | 0 | 12 | 0 | 0.00 | 0.29 | 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.09, 0.09, 0.09, 0.29, 0.29, 0.29 |
| qwen3:8b | 1 | 3 | 0 | 0.38 | 0.38 | 0.38, 0.38, 0.38 |
| qwen3:8b | 2 | 6 | 0 | 0.17 | 0.23 | 0.17, 0.17, 0.17, 0.23, 0.23, 0.23 |
| qwen3:8b | 3 | 9 | 0 | 0.56 | 0.64 | 0.56, 0.56, 0.56, 0.58, 0.58, 0.58, 0.64, 0.64, 0.64 |
| qwen3:8b | 4 | 9 | 9 | 0.94 | 0.95 | 0.94, 0.94, 0.94, 0.94, 0.94, 0.94, 0.95, 0.95, 0.95 |
| qwen3:8b | 6 | 3 | 3 | 0.93 | 0.93 | 0.93, 0.93, 0.93 |

## Transport control

Runs completed before the matrix was restarted so both models share the native Ollama transport. They use the OpenAI-compatible endpoint and are kept for comparison only; they are not part of the primary matrix.

| Model | API | Arrival | Seed | Success | LLM calls | Tokens | TTR (learn + certify) | Outcome | Deployed at | Exposure after | Debt tokens | Dividend tokens | Recovery tokens / calls / latency | False FP | Promoted / rejected |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen3:4b-instruct | openai | burst | 0 | 100% | -70% | -69% | 12 (6 + 6) | promoted | 44 | 5 | 15521 | 6302 | 41% / 40% / 40% | 0% | 3 / 2 |
| qwen3:4b-instruct | openai | burst | 1 | 100% | -70% | -69% | 12 (6 + 6) | promoted | 44 | 5 | 15548 | 6303 | 41% / 40% / 40% | 0% | 3 / 2 |

