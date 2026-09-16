# P2.3R Interpretation

Primary matrix: 2 teacher models (`qwen3:4b-instruct`, `qwen3:8b`) x 4 novel-family arrival orders (burst, interleaved, periodic, rare) x 3 seeds = 24 runs, all through Ollama's native API with thinking disabled, identical prompt, JSON schema, temperature 0, 64-token output budget, task streams, compiler cadence, thresholds, outcome filter, and promotion rule. Two earlier `qwen3:4b-instruct` runs over the OpenAI-compatible endpoint are kept as a transport control only. Numbers below are from `core_p23r_summary.json`, which is regenerated from the per-episode logs of every run.

## Pre-registered expectation for rare arrival

Written before the rare cells completed. Novel episodes: 7, spacing 1 in 8, thresholds, compiler cadence, and validation unchanged.

- A. insufficient_evidence: no candidate ever gets enough novel evidence in train; 0% fast path; continue deliberation.
- B. rejected: a candidate includes novel evidence in train but fails certification; 0% fast path; continue deliberation.
- C. promoted: sparse evidence nevertheless satisfies certification; late reflex acquisition; record exact TTR and evidence composition.

Observed: C on all 6 rare runs (both models), with the qualifier below.

## Stable across seeds

Every cell has zero interquartile range on every acquisition metric. Across the three seeds of each (model, arrival) cell the following are identical: task success (100% online and baseline), LLM call reduction, time-to-reflex, learning and certification evidence composition, number of rejected candidates, deployment episode, post-promotion exposure, false fast-path rate (0.0%, 0 of 50 or more unrepresented decisions per run), invalid actions (0), and old-family success (100%). Only token counts (within about 20 tokens per run) and wall-clock latency vary. Seeds change the task instances; they do not change the dynamics. On this benchmark the acquisition trajectory is determined by the evidence-arrival pattern and the compiler protocol, not by instance variation.

## Sensitive to arrival order

| Arrival | TTR | Learning + certification episodes | Rejected before | Deployed at | Novel exposure after | LLM call reduction | Token recovery ratio |
|---|---|---|---|---|---|---|---|
| burst | 12 | 6 + 6 | 2 | 44 | 5 | 69.6% | 41% |
| interleaved | 7 | 4 + 3 | 2 | 34 | 10 | 76.2% | 139% |
| periodic | 7 | 4 + 3 | 2 | 37 | 5 | 76.5% | 69% |
| rare | 7 | 4 + 3 | 4 | 68 | 0 | 74.5% | 0% |

Same values for both models.

Time-to-reflex is not a pure learning quantity. The candidate that was eventually promoted contained 4 novel episodes in its train split in three of the four orders and 6 in burst. The burst difference is a cadence artifact: a second known-only promotion at episode 23 shifted the compile schedule so that candidates were tested with 3 and then 6 novel training episodes, never 4. TTR therefore combines capability evidence, certification evidence, and the compile cadence relative to the arrival pattern.

Deployment episode and exposure vary much more than TTR. Interleaved deploys earliest (34) and gets 10 novel episodes of exposure, enough to recover 139% of its acquisition tokens within the stream. Rare deploys at episode 68 of 69 and is never exercised.

## Sensitive to teacher size

No. All 12 `qwen3:8b` runs reproduce the 12 `qwen3:4b-instruct` runs exactly on TTR, evidence composition, rejected candidates, deployment episode, exposure, false fast-path rate, success, and the certification boundary. The shadow acceptances of every candidate are identical to two decimals across the two models. The reason is visible in the traces: both teachers emit the same five-decision policy on every family in this vertical, the candidate is fitted on state features that do not depend on the teacher, and the certification gate is a function of those features. When two teachers agree on the policy, the compiler cannot distinguish them.

Cost-to-competence differs only through per-call cost. Acquisition tokens before maturity: 10,687 (4B) versus 10,795 (8B), about +1%. Acquisition LLM latency before maturity: 19.4 s versus 22.6 s, about +16%. Tokens per call: 237 versus 242. Latency per call: 468 ms versus 569 ms on the same GPU. On this benchmark the larger teacher buys nothing and costs slightly more. This should not be read as "teacher size never matters": it means the benchmark's novel family does not require a policy the smaller teacher gets wrong.

## Transport effect

The two `qwen3:4b-instruct` burst runs over the OpenAI-compatible endpoint (seeds 0 and 1) match the native-transport burst runs on every acquisition metric: TTR 12 (6 + 6), 2 rejections, deployment at 44, exposure 5, recovery 41% / 40% / 40 to 41%, 0% false fast path, 100% success. Debt tokens differ by fewer than 30 tokens (15,521 and 15,548 versus 15,519 to 15,540). Transport does not change behavior for this model.

## Cases that never mature

None. All 24 runs promoted the novel family. Post-hoc classification by outcome: 24 promoted, 0 rejected, 0 insufficient_evidence.

The rare cells are the important qualifier. In all 6 rare runs the promotion happened at episode 68, the last novel episode of the stream, after four rejected candidates (acceptances 0.29, 0.38, 0.23, 0.64 against a 0.65 floor). The reflex was certified and activated but never exercised: post-promotion novel exposure 0, realized novel-family dividend 0 calls, 0 tokens, 0 s. Operationally the novel family stayed 100% deliberative for the whole observed stream, the same behavior outcomes A and B would have produced. Paradigm waited for the seventh observation rather than lowering its requirement at 0.64.

## Certification boundary

Identical for both models. Grouping every candidate whose validation split contained the novel family by the number of novel episodes in its train split:

| Novel episodes in train | Candidates | Promoted | Acceptance range |
|---|---|---|---|
| 0 | 12 | 0 | 0.00 to 0.29 |
| 1 | 3 | 0 | 0.38 |
| 2 | 6 | 0 | 0.17 to 0.23 |
| 3 | 9 | 0 | 0.56 to 0.64 |
| 4 | 9 | 9 | 0.94 to 0.95 |
| 6 | 3 | 3 | 0.93 |

Per model: 0 of 30 candidates with three or fewer novel training episodes passed (maximum 0.64); 12 of 12 with four or more passed (minimum 0.93). This is an observation under the current compile cadence, which decided which configurations were tested. It is not a causal minimum: no run tested whether a 4-episode candidate was necessary rather than sufficient, and the P2.3T sweep addresses that with a fixed certification set.

## What was acquired

The P2.3T sweep on fixture traces, and inspection of the recorded decisions, show that the `syntax_error` family's required control sequence (run tests, inspect, apply fix, run tests, finish) is the same as the known families'. A candidate fitted with zero novel episodes already reproduces about 96% of the held-out novel decisions. What Paradigm acquired in P2.3 and P2.3R is therefore certified coverage of a previously unrepresented state region (new failure kind and prompt text), not a new action policy. The OOD gate correctly refused to trust the region until evidence existed; that is the intended behavior. Calling it acquisition of a new skill would overstate it. Testing acquisition of a genuinely different policy requires a family whose correct sequence includes actions the known families never use.

## Self-focusing acquisition buffer

Observed, not designed: once a family is on the fast path it stops producing deliberative traces, so the buffer fills with whatever is still deliberative. In interleaved order the validation split at the promoting candidate was 2 known / 15 novel traces despite known episodes outnumbering novel ones 3 to 1 in the stream. This resembles learning pressure toward unresolved behavior. No claim of a new active-learning method is made.

The same property is a structural weakness: after a family matures, fresh teacher evidence for it largely disappears, so the recent-split certification cannot certify old-family retention. Retention stayed at 100% success and 100% fast path in all 24 runs, but this was observed at runtime, not certified at promotion. P2.3R-bis tests explicit retention probes for this.
