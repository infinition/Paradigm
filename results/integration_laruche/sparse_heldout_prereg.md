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
