# Pre-registration: shadow sampling for fresh evidence on active families (run 12)

Written before any code change. One live run. No `m` is chosen as a winner; every `m` is evaluated counterfactually on the same record afterwards.

## Hypothesis

Freshness and evidential sufficiency are distinct. For an already-active family, a small number of fresh observations should not automatically override a larger frozen retention set, while sufficiently supported fresh evidence must retain the ability to detect regression.

## Collection protocol

Active families remain eligible for their reflex, but a pre-declared subset of eligible decisions is routed deliberately to the teacher with reason `shadow_sample`. Shadow sampling affects evidence collection only. It does not modify quality, trust, calibration, retention, promotion, or risk thresholds. Sampling is fixed before the run and independent of candidate predictions or outcomes.

Sampling is deterministic: `u = hash(seed, episode index, family, step index)` mapped to `[0, 1)`, sampled when `u < p(episode index)`. Seed `20260917`. Episode index is the engine's count of episodes started since the fresh state (1 = first mission). Rate schedule by episode index, chosen so that the fresh count of an active family spans small to large values across compile points:

| episodes | p |
|---|---|
| 1 to 16 | 0 (no reflex expected yet; irrelevant if one exists) |
| 17 to 20 | 0.25 |
| 21 to 24 | 0.50 |
| 25 to 28 | 0.75 |
| 29 to 36 | 1.00 |

With one `file_edit` decision per mission and the validation window being the most recent 25% of validated episodes (5, 6, 7, 8, 9 episodes at points 20, 24, 28, 32, 36), the expected fresh count for `file_edit` is about 1 at 20, 2 to 3 at 24, 4 to 5 at 28, 6 to 7 at 32, 8 or more at 36. The `start` family follows the same schedule but its first test run is verifiable only when the model's phrasing exits 0 (about a third of the time in run 11), so `file_edit` is the primary family for the fresh-support question and `start` is reported as secondary.

## Live rule

The live compiler runs the run 11 rule unchanged (family-scoped certification, no probe re-certification), so the record is directly comparable to run 11. The counterfactual replays for `m` in {1, 2, 3, 5, 8} are computed afterwards on the same record with the sensitivity script, sequentially per `m`.

## Run

36 missions, fresh Paradigm state, same workspace, bug variants, model (`deepseek-v4-flash`), guard hook, canonicalization and thresholds as run 11. Nothing in the demo changes.

## Mandatory log per compile point and active family

fresh count; fresh gate acceptance; fresh covered count and agreement; probe count; probe agreement; probe gate acceptance; hard veto triggered; candidate verdict under `m` = 1, 2, 3, 5, 8. The hard veto is reported separately from sparse evidence: an isolated OOD fresh observation with passing probes is sparse evidence, not regression; a gate-covered fresh observation on which the candidate disagrees with the verified teacher action is a hard veto.

## Economy

Shadow-sample calls are an explicit experimental cost, never counted as avoided. Reported: natural model calls, shadow-sampling model calls, reflex decisions, model calls avoided, net calls avoided after sampling overhead.

## Predictions

1. First promotion around mission 16 with `start` and `file_edit` active, as in run 11.
2. The fresh count of `file_edit` at compile points 20, 24, 28, 32, 36 increases roughly as scheduled above, giving at least one compile point in each of the bands 1, 2 to 3, 4 to 5, 6 or more.
3. Shadow-sampling overhead is about 1 + 2 + 3 + 4 + 4 model calls for `file_edit` plus the same for `start`, about 28 calls over 36 missions, against reflex decisions of the order of 40.
4. 36 of 36 missions verified, 0 false fast paths, 0 unsafe actions.
5. No prediction on which `m` is right. The question is at what fresh support the counterfactual verdicts under different `m` start to differ, and whether any hard veto fires.

## Not done

No threshold change. No selection of `m`. No second live run in this pre-registration.
