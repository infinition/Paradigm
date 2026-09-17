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

## Outcome (written after the run; raw artifacts frozen, hashes in `run12_raw_sha256.txt`)

Live: 36 of 36 missions verified, 0 unsafe actions, 0 false fast paths (reflex outcomes: 11 SUCCESS, 6 UNKNOWN, 0 FAILURE). Promotion at 16 (version 1) with four families, not two: `start`, `file_edit:success`, `file_read:success`, `tests_passed` (43 validated traces at that point against 32 in run 11; the teacher was more regular). No later version was adopted. The live rule is reproduced exactly by the `recorded` replay. Reports: `run12_shadow_report.md`, `run12_shadow_ledger.md`.

Prediction 1: held, with two more families than predicted. Prediction 2: partly held. Fresh counts for `file_edit` at compile points 20, 25, 29, 33 (stream episodes; buffer sizes 20, 24, 28, 32): 2, 3, 6, 7; `tests_passed`: 1, 4, 4, 1; `file_read`: 1, 0, 1, 4; `start`: 2, 1, 1, 2. Bands 1, 2 to 3, 4 to 5 and 6 to 7 were reached; 8 or more was not (a mission with no validated trace shifted the cadence by one). Prediction 3: cost higher than predicted: 53 shadow-sample calls (470k tokens) against 17 reflex decisions; net calls avoided after sampling overhead: -36. Realized sampling per band: 0.43, 0.64, 0.71, 1.00 against 0.25, 0.50, 0.75, 1.00 scheduled (14 eligible decisions per band). Prediction 4: held.

Main result. Shadow sampling restores fresh evidence for active families, but run 12 does not identify a preferred `min_fresh_support`: every pre-registered `m` produces the same candidate-level certification decision at every compile point. Three levels: the evidence path changed at 1, 7, 10, 14, 16 family-points for `m` = 1, 2, 3, 5, 8; one family verdict changed (`file_read` at 25, `insufficient` under the recorded rule, `active` on probes under every `m`); zero candidate adoption decisions changed. The arbitration source can change without changing the final decision, on this record.

Why the decisions coincide: the probes are checked in both branches (the held-out branch also runs the retention check), and the fresh evidence is checked in both branches (as the held-out verdict, or through the disagreement veto). At 20, `file_edit` fails on its probes (13 of 14 at the incumbent threshold) whatever the route. At 29, all four families pass in every route with 6 fresh `file_edit` observations agreeing, and the candidate is refused only because there is no new family to activate. At 25 and 33 the gate-covered disagreements decide, in every route.

The two gate-covered disagreements are of different kinds, and the record can tell them apart:

- Point 25, `file_edit`, 3 fresh, 1 disagreement. The candidate tree predicts `file_read` on a fresh post-edit state where the teacher ran the tests and where version 1 also predicts the tests. This is a candidate regression relative to the incumbent, caught by the held-out verdict (`m` up to 3) and by the veto (`m` 5 and 8). A high `m` did not mask it.
- Point 33, `file_edit`, 7 fresh, 1 disagreement. The teacher ran `python -m pytest -q | cat`, a phrasing the canonicalizer does not fold into `python -m pytest -q`, so it is a distinct action key. The candidate and version 1 both predict the canonical form; the reflex replay would have been valid and verified. This is a teacher alternative (an equivalent phrasing), not reflex invalidity, and it blocked `file_edit` re-certification in every route: quality and calibration on held-out evidence, `fresh_disagreement` on probes. The pre-registered veto has no minimum count and no incumbent check, so a single alternative observation dominated regardless of `m`. The record suggests the distinguishing feature: at 25 the incumbent agrees with the teacher and the candidate does not; at 33 neither does. That distinction is a new hypothesis to pre-register, not a change made here.

Shadow-sample ledger, 53 samples: 32 agreements; 14 where the teacher finished the mission instead of the reflex's read after passing tests (`tests_passed` family; a control call is never observed, so these never reach certification, and a replayed read there is a wasted but harmless action); 6 where the teacher went straight to `file_edit` instead of the reflex's second read (`file_read` family; `file_edit` is not reflex-capable, so the step is UNKNOWN and never evidence); 1 verified alternative trajectory (mission 33 above). No shadow sample produced an invalid action or a failed mission. Teacher disagreement, reflex invalidity and mission failure are three different things in this record, and only the first occurred.

Not concluded: which `m` is right. Not done: any change to the veto, the canonicalizer, or the thresholds.
