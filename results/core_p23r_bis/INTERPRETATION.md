# P2.3R-bis Interpretation

Family-aware certification with retention probes was compared against the P2.1 recent-split rule on the same four arrival orders (seed 0, `qwen3:4b-instruct`, native transport, thinking disabled), with each rule authoritative in one run and evaluated in shadow in the other. Compiler cadence, thresholds, outcome filter, streams, and model are identical to P2.3R. The primary protocol requires at least one validation episode per family; a run with two is recorded separately as a sensitivity result. Numbers are from `core_p23r_bis_summary.json`.

## What family-aware certification changed

| Arrival | Rule | Online LLM calls | First promotion | Novel deployed at | Novel fast path after | Candidates promoted / rejected / insufficient |
|---|---|---|---|---|---|---|
| burst | recent | 105 | 8 | 44 | 96% | 3 / 2 / 0 |
| burst | family-aware | 141 | 16 | 44 | 96% | 2 / 2 / 2 |
| interleaved | recent | 82 | 8 | 34 | 96% | 2 / 2 / 0 |
| interleaved | family-aware | 163 | 32 | 32 | 95% | 1 / 4 / 2 |
| periodic | recent | 81 | 8 | 37 | 96% | 2 / 2 / 0 |
| periodic | family-aware | 152 | 28 | 28 | 60% | 2 / 1 / 4 |
| rare | recent | 88 | 8 | 68 | never exercised | 2 / 4 / 0 |
| rare | family-aware | 115 | 16 | never | never | 1 / 1 / 2 |

Task success stayed at 100% and the false fast-path rate at 0% in all eight runs. Old-family success and fast path after representation stayed at 100% wherever measurable.

## Retention blind spot: closed

The negative control relabels one mature family's failed-phase decisions (`inspect_file` to `search_symbol`, a valid but wasteful action that adds a tool call without failing any test) while leaving the novel family intact, then certifies the clean and the poisoned candidate under both rules on the final buffer.

A rule discriminates only when it promotes the clean candidate. Verdicts over the four orders: family-aware caught 3, missed 0, non-discriminating 1 (rare, where it rejected the clean candidate too); recent caught 0, missed 2, non-discriminating 2. In the two discriminating cases for the recent rule (burst, interleaved) the damaged family was absent from, or a small minority of, the recent validation split, and the poisoned candidate was promoted. Family-aware certification rejected it through probe agreement of 0.80 against the 0.95 floor on the damaged family's 20 frozen probes. On fixture traces the same control was caught through the incumbent-relative coverage check instead (the candidate became uncertain rather than confidently wrong), so both detection paths have fired.

This is the result the experiment was designed to test, and it holds: the recent-split rule has a measurable retention blind spot on this vertical, and immutable per-family probes close it.

## The cost is mostly not the probes

Family-aware certification cost 215 additional deliberative decisions across the four pairs (36, 81, 71, 27), a call-reduction loss of 11 to 23 percentage points. The promotion audit shows where it comes from:

- Evidence availability at the start. At episodes 8 and 12 one or two known families were absent from the 25% recent validation split, so the known-only candidate was `insufficient_evidence` rather than promoted. Every known family stayed deliberative until all four appeared in the split (episode 16).
- Atomic promotion. In interleaved order, from episode 16 to 28 all four known families passed their groups while the novel family's own acceptance was 0.0 to 0.5. The whole candidate was rejected each time, and the known families stayed deliberative until episode 32 even though they had independently passed. The disagreement matrix records this as 4 conservative rejections and 19 evidence-availability verdicts against 5 agreements on promotion.
- Under the recent rule those same candidates were promoted at episode 8, and the novel states were still routed to the model by the runtime OOD gate. The per-family novel-acceptance requirement therefore bought no safety in these runs; the gate already provided it. What bought safety was the retention probes, which cost 80 to 240 probe predictions per run and no LLM calls.

Stated carefully: retention probes closed a real blind spot in recent-buffer certification, but coupling all families into a single promotion decision introduced unnecessary deliberation. Uncertified novel families blocked already-certified mature families even when those mature families independently passed their retention checks. Diagnostic yield: 3 discriminative catches per 215 additional deliberative decisions, about 0.014, and most of the denominator is attributable to atomic promotion rather than to the probes.

## Novel certification timing

Family-aware certification promoted the novel family one to nine episodes earlier in interleaved and periodic order (TTR 6 instead of 7) and never in rare order. The promoted candidates still held four novel episodes in their train split; the difference is two rather than three novel validation episodes and a shifted compile cadence. This is not faster learning. In periodic order the earlier candidate also covered less of the novel region afterwards (60% versus 96% novel fast path), so earlier certification came with thinner coverage. In rare order the shifted cadence meant the seventh novel episode never triggered a compile attempt with the family in train: outcome `insufficient_evidence`, novel family fully deliberative, operationally identical to the recent rule's promote-at-68-and-never-exercise.

## Sensitivity: two validation episodes per family

Recorded under `sensitivity_min2/` for interleaved order only, with the primary protocol (one episode) unchanged. Requiring two validation episodes per family moved the first promotion from episode 32 to 48, delayed novel deployment by 14 episodes (TTR 11 instead of 6), produced 8 `insufficient_evidence` verdicts, and cost 160 additional deliberative decisions against 81 at one episode (call reduction 30% against 53%; the recent rule is at 76%). Negative-control discrimination did not change: family-aware still caught the poisoned candidate and the recent rule still missed it. On this vertical, demanding more per-family evidence buys delay, not discrimination.

## Reflex model plus trust manifest

The clean refinement is family-scoped activation: a single compiled artifact with a per-family authorization map, where certified families enter the fast path and uncertified ones stay deliberative, instead of an all-or-nothing verdict on the artifact. The Core line already has the persistent family registry (P1.3) that such a map would live in. This was not implemented or tuned during P2.3R-bis; the atomic-promotion cost above is part of the recorded result.

## Limitations

- One seed per order. P2.3R showed zero seed variance for the recent rule, but the family-aware rule was not replicated across seeds.
- One negative control design. It exercises a valid-but-wasteful relabelling; a regression that changes success rather than efficiency, or one that spans several families, was not tested.
- Probe sets are frozen at first promotion from the buffer's own traces, so they certify agreement with the teacher's decisions at that time, not correctness in any stronger sense.
- Family labels come from task metadata. A deployed system would need its own family assignment, for example from the P1.3 registry.
