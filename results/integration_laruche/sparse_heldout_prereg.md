# Pre-registration: sparse fresh held-out evidence versus frozen probes (sensitivity study)

Written before any code change. Exploratory, read-only, offline. No DeepSeek. The previous pre-registration (`probe_recertification_prereg.md`, verdict unsupported) is final and is not edited.

## Question

When fresh held-out evidence for an already-active family is too sparse to be statistically meaningful, should frozen retention probes remain the primary re-certification evidence?

## Rule family under study

For an already-active family (incumbent threshold and frozen probes exist), with `n_fresh` the number of its deliberative held-out traces in the current split and `m` a minimum fresh support:

- if `n_fresh >= m`: the existing held-out certification rule, unchanged;
- if `n_fresh < m`: re-certification on the frozen probes at the incumbent threshold, with every probe safeguard (coverage and agreement floors, no coverage regression, gate acceptance floor, ECE floor);
- every fresh held-out observation is still reported: how many the candidate gate accepts, how many the candidate covers at the incumbent threshold, how many covered ones disagree with the teacher;
- hard veto: a covered fresh observation on which the candidate disagrees with the teacher rejects the family regardless of the probes;
- an OOD rejection of an isolated fresh state is not by itself a behavioral regression.

Families that are not active are judged exactly as before. No floor is changed.

`m` in {1, 2, 3, 5, 8}. `m = 1` is the rule of the previous pre-registration (probes only when `n_fresh = 0`) and is the control. The recorded rule of run 11 (no probe re-certification at all) is reported alongside as the baseline.

## Material

- Run 11 state (`engine_state_family_scoped_after_24.pkl`, tag `laruche-family-scoped-run11`): sequential family-scoped replay at compile points 16, 20, 24 with the state carried forward, per `m`. Plus the damaged-`file_edit` negative control at 24 per `m`.
- Runs 9A and 9B state (`engine_state_after_32.pkl`): the 32 validated episodes replayed under family-scoped certification at compile points 20, 24, 28, 32, sequentially, per `m`. This record was produced without any active reflex, so its post-activation held-out traces are counterfactual (in a live run the reflex would have served those states and produced no teacher trace); it is reported as such.

## Reported per `m`

- active-family re-certification verdicts and the evidence they rested on (held-out or probes), with the fresh observation report;
- new-family activations and their compile point;
- the point-20 and point-24 verdicts on run 11;
- the poison verdict;
- false accept: the damaged candidate promoted, or a family activated on probes while a covered fresh observation disagreed with the teacher;
- false reject: a clean candidate rejected while every active family passes its probes and no covered fresh observation disagrees;
- decisions changed relative to the recorded rule, and among them the number changed solely because sparse-held-out arbitration switched the evidence source.

## Not done

No `m` is selected. No live run. If a stable region appears, a separate prospective rule is pre-registered before any live confirmation.

## Outcome (written after the replay, `sparse_heldout_sensitivity.md`)

Reproducibility: the `recorded` variant reproduces the run 11 verdicts at 16, 20 and 24.

Run 11. Point 20 is rejected for every `m`: `file_edit` agrees with its probes on 15 of 16 whatever the evidence source. Point 24 is rejected under `recorded` and `m = 1` and promoted (version 2, `tests_passed` activated) under every `m >= 2`: `file_edit` is then judged on its 16 probes (coverage 1.000, agreement 1.000, gate acceptance on probes 1.000, ECE 0.009) and its single fresh trace is reported as gate-rejected, covered 0, disagreements 0. `start` is on probes for every `m >= 1`. The poison is rejected for every `m`. False accepts: 0 for every `m`. False rejects: 1 under the recorded rule and under `m = 1` (the same point-24 decision, labeled retrospectively on the same basis for all variants), 0 for every `m >= 2`. `m = 1` is behaviorally identical to the recorded rule; its only difference is that `start` is reported `active (probe_recertified)` instead of `insufficient`, which changes no candidate decision. Candidate decisions changed relative to the recorded rule: exactly one (point 24), for every `m >= 2`.

Run 11 cannot separate `m = 2` from `m = 8`: after activation, every active family has 0 or 1 fresh trace per split, so every `m >= 2` routes them identically.

Runs 9A/9B (counterfactual, no reflex ever active in the record). Family-scoped certification promotes `start` and `file_edit` at 20. Then `file_edit` is rejected at 24, 28 and 32 for every `m`: on held-out evidence (`m <= 5`, 6 to 7 fresh traces, agreement 0.944 to 0.947 against the probes) and on probes (`m = 8`, agreement 0.947, plus one covered fresh disagreement at 32 caught by the veto). This is the family that was 27 of 30 consistent in that record; the probes reject it at every `m`, so a large `m` does not open a false accept here. `start` re-certifies on either evidence at every `m`. No new family activates in that record under any `m`.

Reading, without selecting an `m`: on the available records, the region `m >= 2` is stable in the sense that every variant in it produces the same decisions, no false accept, no false reject, and the only changed decision relative to the recorded rule is the point-24 case where one gate-rejected fresh state had overridden 16 passing probes. The records contain no compile point where 2 to 7 fresh traces of an active family exist together with a promotion decision that depends on them, so the upper part of the region is untested. A prospective rule, if pre-registered, would need a live record with intermediate fresh support to be tested; nothing is selected here and no live run was made.
