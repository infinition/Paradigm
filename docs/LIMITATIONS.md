# Limitations

Paradigm begins as a research scaffold. The following limitations are explicit.

## Reflex compilation can preserve mistakes

A repeated decision is not automatically a correct decision. Only validated outcomes should enter the trusted compilation set.

## Confidence is not correctness

Calibration can improve probability quality, but distribution shift can invalidate calibration.

## Trusted spaces depend on coverage

A trusted-subspace method can reject useful novel behavior when the trusted pool is incomplete. This is a central result to test, not an edge case to hide.

## Similar invalid behavior may remain reachable

The z-manifold adaptive-backdoor result shows why proximity to trusted behavior matters. A trusted region is not a proof of harmlessness.

## Drift bounds are local quantities

The Drift Contract preprint bounds a specific weight-induced pre-activation change under stated assumptions. Paradigm cannot translate that into a behavioral safety guarantee without new evidence.

## Structured inductive bias does not solve all OOD

The GA versus scalarization study reports strong directional generalization from equivariance but failure on invariant magnitude extrapolation. Structured reflexes still need OOD gates.

## World models can be wrong

Predicted futures should not be treated as ground truth. A predictive gate adds another signal, not an oracle.

## Real-time control needs independent safety layers

Future robotics experiments must keep collision limits, joint limits, emergency stop, and other deterministic controls outside learned reflex promotion.


## Persistent storage is not a security boundary

P0.5 uses local pickle artifacts, JSON state, and append-only JSONL evidence. This is sufficient for a research lifecycle benchmark, not for hostile multi-user deployment. Pickle files must only be loaded from a trusted store.

## Shadow windows cannot cover unseen failure slices

The P0.5 delayed-regression control deliberately passes promotion because the defective slice is absent from the observed windows. Promotion evidence only supports the distributions it measures. Post-promotion monitoring remains necessary.

## Bounded updates are not bounded behavior

P1.0 numerically checks the matrix-level conditional bound from Drift Contract. A small pre-activation step can still accumulate, interact with other layers, or cause a semantically important decision change. Promotion and runtime checks remain separate.

## A small update is not retained knowledge

P1.1 shows that reducing measured per-step pre-activation drift does not by itself prevent forgetting across successive shifts. Bounded plasticity and memory mechanisms address different problems.

## A global neural update subspace can become permissive

The P1.1 parameter-delta experiment becomes less selective when heterogeneous validated update families are merged into one PCA space. In the recorded run, pool expansion improves acceptance of legitimate novelty but also raises poisoned-update acceptance to 100%. Update-space membership must therefore remain an auxiliary signal, not a promotion certificate.


## Family conditioning depends on correct lineage and family identity

P1.2 becomes selective only after candidates share a common parent lineage and update trust is conditioned on a represented behavior family. Parameter deltas from independently initialized or permutation-equivalent neural models are not directly comparable in this construction. A wrong family assignment can invalidate the gate.

## Prototype separation on synthetic families is not a semantic guarantee

The recorded P1.2 families are deliberately distinct representation shifts. Perfect rejection of the recorded poison and cross-family controls does not imply that a semantically harmful update cannot align with the same directional prototype. The semantic subgroup manifest remains mandatory.

## Smaller epsilon can preserve the wrong behavior

The P1.2 risk sweep shows that reducing epsilon preserves more of the protected mapping but can materially slow useful adaptation. High-risk does not mean zero adaptation, and a small drift budget cannot establish that retained behavior is correct.


## Family registries can fragment or overlap

P1.3 tests distinct synthetic families. Real behavior may form overlapping, nested, or drifting clusters. Returning `ambiguous` and deferring is safer than forced assignment, but the current registry does not yet learn when a family should split, merge, reactivate, or retire.

## Quarantine is operational state, not model rollback

P1.3 removes a family from routing without rewriting its immutable definition. This preserves evidence, but a production system must also coordinate family state with the actual active reflex version and runtime permissions. That combined rollback path remains a later benchmark.


## Fixed evolution probes are not future-proof

P1.4 prevents measured permissivity increases only on the clean and negative suites supplied to the evolution guard. A family proposal can still fail on an unmeasured region. The guard is a regression barrier, not a proof that the evolved topology is globally safe.

## Split discovery is still declared, not learned

The P1.4 benchmark validates the lifecycle mechanics of a split but supplies the two successor modes explicitly. Automatic detection of persistent multimodality, merge decisions, and family-boundary drift remain open research problems.

## P2.0 does not distill language reasoning

The first Agent vertical compiles controller actions such as test, inspect, search, repair, and finish. The controlled repair operator already knows the validated task fix. This isolates policy routing but does not demonstrate code-generation distillation.

## The P2.0 reference deliberator is not an LLM

The reference controller is deterministic and performs configurable local analysis work to provide a measurable slow path. The 89.4% recorded deliberative-call reduction is therefore a controller-call result, not an LLM token or cost claim. A real LLM benchmark is required for that claim.

## The first agent task distribution is deliberately small

Four represented coding families and one withheld OOD family are enough to test the runtime contract but not enough to establish robustness on natural software engineering tasks. Prompt diversity, repository scale, ambiguous failures, adversarial observations, and unsafe tool requests remain open.

## P2.1 online learning is supervised imitation, not autonomous reinforcement learning

The current online loop learns only from deliberative decisions attached to successful episodes. It does not infer a long-horizon reward function, perform credit assignment across trajectories, or optimize exploration. A successful episode can still contain locally unnecessary decisions, so outcome filtering is weaker than causal credit assignment.

## Online promotion does not make self-training safe by default

P2.1 deliberately excludes reflex predictions from teacher labels. Reusing accepted reflex decisions as training targets would create a self-reinforcing feedback loop. Any future self-training path needs independent verification or outcome evidence stronger than the model's own confidence.

## The P2.1 teacher is still a deterministic reference controller

The online lifecycle is exercised end to end, but token savings, API cost savings, and language-model latency have not been measured. The 60.6% deliberative-call reduction is a controller-call result on the local benchmark. A real LLM or another genuinely expensive planner remains required for external efficiency claims.

## P2.2 live-controller limitations

A live run is now recorded against a local `qwen3:4b-instruct` model served through Ollama's OpenAI-compatible endpoint (`results/core_p22/core_p22_llm.json`). Several limitations remain:

- Single model, single endpoint, single seed, and a 15-episode evaluation stream. This is not a statistically robust estimate and has not been repeated across models, prompt phrasings, or task distributions.
- The benchmark is a static compile-then-evaluate design structurally similar to P2.0. It does not test whether fast-path coverage or amortization improve with continued sequential use, which is what the P2.1 online loop tests with a deterministic controller.
- Cost telemetry (`estimated_cost_usd`) is implemented and unit-tested with nonzero pricing, but this live run used a free local model with no configured price, so no live monetary cost figure exists yet.
- The reflex amortization metric recovered only about 42% of compilation cost in this run and did not reach break-even. This is preserved as measured evidence, not smoothed into a positive-sounding summary.
- The controlled coding vertical keeps repair synthesis outside the compiled policy. `apply_fix` is a validated repair primitive, so P2.2 measures control-policy compilation rather than autonomous code generation.

## P2.3 online-acquisition limitations

P2.3 records the full loop with a real model, but the evidence is narrow:

- One model, one seed, one 69-episode stream. Time-to-reflex of 10 validated episodes is a single observation, not a distribution.
- The novel family is one failure type inside a controlled vertical with a validated repair primitive. Acquisition of a behavior with ambiguous or multi-step repair semantics is untested.
- Shadow validation uses the most recent buffered episodes. When a novel family arrives in a burst, that split is dominated by the new family, which is why two candidates were rejected before one passed. This is conservative here but has not been tested against interleaved arrival.
- Outcome filtering is binary task success. It does not weight latency, tool-call count, retries, or human overrides.
- The reported latency saving mixes local model latency on one machine with negligible local compile cost. It is not a hosted-API cost result.

## P2.3R: coverage acquisition, not skill acquisition

The novel family used in P2.3 and P2.3R requires the same action sequence as the known families. A candidate fitted with zero novel episodes already reproduces about 96% of the held-out novel decisions. The recorded results therefore demonstrate online certification of a previously unrepresented state region, with the OOD gate correctly withholding trust until evidence existed. They do not demonstrate acquisition of a new action policy, and the identical behavior of the 4B and 8B teachers follows directly from both emitting the same policy. Acquisition of a genuinely different policy, and any teacher-size effect on it, remain untested.

## P2.3R: the certification boundary is observational

Every candidate with four or more novel training episodes passed the shadow gate and none with three or fewer did, for both models. The compile cadence decided which configurations were tested, so this is not a causal minimum. The learning-threshold sweep (P2.3T) fits candidates with a controlled number of novel episodes against a fixed certification set to separate the tree's capability from the gate's requirement.

## P2.3R: retention is observed at runtime, not certified at promotion

The acquisition buffer self-focuses on unresolved behavior. This is useful for acquisition and harmful for certification: after a family matures, its traces largely stop entering the buffer, so the recent-split validation cannot check that a new candidate preserves it. Old-family success and fast path stayed at 100% in all 24 runs, but the promotion gate never verified this. P2.3R-bis introduces explicit retention probes for that reason.

## P2.3R: time-to-reflex is protocol-dependent

TTR combines capability evidence, certification evidence, compile cadence, and arrival pattern. The burst value of 12 versus 7 elsewhere comes from a cadence shift, not from a larger evidence requirement. Deployment episode and post-promotion exposure are the operationally relevant quantities and vary much more; a rare behavior can be certified with zero realized dividend.

## P2.3R-bis: atomic promotion couples families

Family-aware certification as implemented issues one verdict for the whole candidate. An uncertified novel family therefore blocks mature families that independently passed their retention checks, and families absent from the recent validation split produce insufficient_evidence for the whole candidate. Most of the recorded extra deliberation comes from this coupling, not from the probes. The per-family novel-acceptance requirement did not add safety beyond the runtime OOD gate in these runs. Family-scoped activation is the untested refinement. One seed per order, one negative-control design, and probes frozen from the buffer's own traces further limit the result.

## P2.3T: no learning threshold has been measured

The sweep was designed to measure how much novel evidence a candidate needs to reproduce a behavior, but the novel family's behavior was already reproduced at zero evidence. The instrument works; the family did not exercise it. The certification boundary also moved between P2.3R (four novel episodes sufficient under the live cadence) and P2.3T (five to seven under a fixed 24-episode known train set), so no fixed episode count should be quoted.

## P2.4: trust does not follow capability into unevidenced regions

The compiled reflex generalized the dependency procedure to a prompt wording its teacher fails on, but the density gate had no validated evidence for that wording and kept it deliberative, so the hybrid system could not exceed its teacher. No mechanism for extending trust into capable-but-unevidenced regions was tested. The result rests on one family, one online seed, two teachers from one model line, and two held-out instances of the failing wording. The environment traps a wrong `apply_fix` (only `run_tests` is allowed afterwards), inherited from P2.0, which makes the teacher's fallback to the known sequence fatal. The offline classification rule was refined after the first 4B sweep to judge retention on quality-feasible candidates only; the original verdict is stored.
