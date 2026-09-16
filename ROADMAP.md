# Roadmap

Paradigm is split into three directions. Core must establish value first. Structured and World remain optional until Core has a measurable baseline.

## Phase 0: Research scaffold

Status: implemented in the initial repository.

- [x] define trace, reflex, candidate, active, promotion, and fallback concepts
- [x] calibrated reference reflex compiler
- [x] confidence threshold and selective evaluation
- [x] experimental trusted-subspace OOD gate
- [x] behavioral drift comparison between active and candidate reflexes
- [x] notebook-first experiment layout
- [x] research map linking Paradigm to the source repositories and papers
- [x] explicit limitations and non-transfer of guarantees

Exit criterion:

- package installs
- unit tests pass
- minimal synthetic example runs end to end

## Phase 1: Paradigm Core P0

Status: synthetic quality benchmark executed. Real efficiency evidence is still pending.

Goal: establish whether reflex compilation provides a real efficiency-quality tradeoff.

Experiments:

- [x] deterministic synthetic routing task
- [x] noisy routing task with ambiguous regions
- [x] distribution-shift split
- [x] repeated workflow traces with stable and unstable patterns
- [x] measured local expensive deliberative surrogate
- [ ] real agent, planner, or domain-specific deliberative reference

Baselines:

- [x] direct reference policy for quality
- [x] exact cache
- [x] nearest-neighbor cache
- [x] decision tree
- [x] random forest without fallback
- [x] calibrated reflex with confidence fallback
- [x] minimal-complexity reflex selector
- [x] measured local surrogate for latency and compute
- [ ] measured real deliberative path for external validity

Required measurements:

- accuracy
- selective accuracy
- coverage
- ECE
- Brier score
- latency
- fallback rate
- compute saved relative to deliberation

Go criterion:

- at least 50% reflex coverage
- selective accuracy within 1 percentage point of the deliberative reference on accepted cases
- ECE below 0.05 after calibration
- clear latency or compute reduction against the reference path

No-go action:

If a decision tree or cache matches the reflex at lower complexity, retain the simpler mechanism and narrow the neural reflex claim.

First result: this condition occurred. The calibrated forest was not justified as a universal default. Paradigm now selects the simplest backend that satisfies the declared quality and calibration constraints. See `results/core_p0/REPORT.md`.

P0.1 result: a measured local perturbation-based deliberative surrogate now replaces the assumed cost ratio. All four recorded scenarios pass the local benchmark, but the noisy task requires a calibrated forest and has a much smaller efficiency margin. See `results/core_p01/REPORT.md`. This remains a surrogate, so Phase 1 still requires a real deliberative system before a broader efficiency claim.

## Phase 2: Trusted compilation

Research source:

- https://github.com/infinition/z-manifold
- https://arxiv.org/abs/2607.05300

Questions:

- can validated reflexes define a useful trusted representation or parameter subspace?
- does candidate training outside that space correlate with unsafe or invalid behavior?
- can failure-to-fit identify genuinely novel tasks rather than merely hard ones?

Experiments:

- [x] compare PCA subspace, nonlinear autoencoder, distance-based OOD, and ordinary confidence in input space
- [x] weak-pool input benchmark where the trusted set misses valid latent support
- [x] poisoning control showing input-space gates do not address label corruption
- [x] near-manifold invalid control
- [x] move the trusted-space experiment into reflex behavior or parameter/update-proxy space
- [x] weak trusted reflex pool that omits a legitimate behavior family
- [x] poisoned candidate benchmark at reflex level
- [x] adaptive invalid candidate aligned with common trusted parameter directions
- [x] independent behavior-space check for a parameter-aligned candidate
- [x] behavior-aligned signature stress control
- [x] repeat with neural reflexes and explicit update deltas rather than compact linear-policy parameters
- [ ] add semantic subgroup manifests to promotion rather than relying on geometry alone

Required control:

The z-manifold result is not assumed to transfer from LoRA adapter space to reflex space. Paradigm must establish its own evidence.

P0.2 input-space result: PCA residual and Mahalanobis distance detect the explicit off-manifold shift while retaining most legitimate weak-pool novelty. Classifier confidence does not. However, all input-space gates accept most near-manifold invalid controls, so input-space geometry is retained only as an auxiliary fallback signal. See `results/core_p02/REPORT.md`.

P0.3 reflex-space result: parameter and anchor-behavior PCA gates reject all recorded label-poisoned candidates in the synthetic linear-policy task. The original trusted pool rejects part of a valid weak-pool family, and adding validated weak-pool reflexes restores acceptance to 100% in the recorded run. A candidate generated directly inside the trusted parameter subspace is accepted by the parameter gate while reducing a target slice to 11.1% accuracy; the behavior gate catches that candidate. A separate behavior-aligned signature control still passes the behavior gate while degrading a subgroup. Trusted geometry is therefore retained as a promotion signal, not a certificate. See `results/core_p03/REPORT.md`.

## Phase 3: Bounded plasticity

Status: P1.4 family evolution benchmark executed. The next step is coordinating family state with reflex rollback and real deliberative workloads.

Research source:

- https://github.com/infinition/drift-contract
- https://infinition.github.io/infinition/assets/papers/drift-bounded-spectral-updates.pdf

Paper status: public preprint, arXiv submission pending approval.

Questions:

- can a drift budget stabilize continual reflex adaptation?
- should the budget depend on action risk?
- does activation-space drift predict behavioral drift?

Baselines:

- Adam
- SGD
- replay
- EWC
- LoRA or low-rank adaptation where applicable
- frozen active model plus periodic full retraining

Important distinction:

The current `BehaviorDriftGate` measures output behavior on anchor states. It is not the Drift Contract optimizer. P1.0 now implements the matrix update rule separately and verifies its conditional pre-activation drift bound numerically on synthetic matrices and a small linear reflex. The original local-learning accuracy and depth claims are not transferred to Paradigm.

P1.0 result: the exact-scaled strict variant respects the tested conditional matrix bound on contracting, square, and expanding shapes. Risk-conditioned epsilon values produce proportionate measured change. In a five-seed synthetic distribution shock, a fast contract budget reaches similar shifted-task accuracy to Adam with a smaller largest per-step pre-activation change, while a conservative budget retains much more of the old mapping but adapts too slowly. See `results/core_p10/REPORT.md`.

P1.1 result: on a two-layer neural reflex across three successive representation shifts, Drift Contract reaches similar current-task accuracy to Adam while reducing the recorded per-step pre-activation drift, but it does not reduce final forgetting. Replay and periodic joint retraining retain more prior behavior. A PCA gate over explicit normalized neural parameter deltas is not reliable: it accepts only part of held-out clean updates and becomes more permissive to poisoned updates after a single global pool is expanded. See `results/core_p11/REPORT.md`.

P1.2 result: trusted updates are now conditioned on behavior family and evaluated within one shared active-to-candidate parameter lineage. A cosine prototype gate over normalized parameter deltas is paired with an independent fixed-anchor behavior-delta gate and semantic subgroup floors. In the recorded synthetic run, joint geometry accepts all held-out clean candidates and rejects all targeted poisoned candidates and cross-family candidates. The full manifest retains one conservative clean false rejection in family 2. Risk-conditioned epsilon values expose the intended adaptation-retention tradeoff, and replay plus Drift Contract reduces forgetting relative to Drift Contract alone without giving up the smaller measured step drift. See `results/core_p12/REPORT.md`.

Completed P1.2 controls:

- [x] family-conditioned trusted update spaces instead of one global PCA
- [x] behavior-delta signatures on neural anchor suites
- [x] semantic subgroup manifests linked to update families
- [x] risk-conditioned epsilon schedules linked to promotion policy
- [x] replay plus Drift Contract as a combined baseline

P1.3 result: family definitions are content-addressed and immutable, operational status is stored separately, and unknown or quarantined families are not force-assigned. All three represented held-out candidates route to their correct families. A fourth shift is initially unknown and only becomes represented after a separate validated family is registered. Existing family definition hashes remain unchanged. Semantic subgroup failure and a high-risk epsilon violation both block the manifest despite valid family routing. Quarantine persists across reload. See `results/core_p13/REPORT.md`.

Completed P1.3 controls:

- [x] persistent family registry with immutable family identifiers
- [x] unknown-family routing to deliberation instead of forced assignment
- [x] persist family trust evidence and epsilon policy in candidate manifests
- [x] quarantine a drifting family without mutating its immutable definition
- [x] test family expansion without weakening existing family boundaries

P1.4 result: a synthetic topology-evolution benchmark now treats family-map changes as guarded replacements rather than threshold widening. A broad bimodal parent is retired and replaced by two narrower immutable children. A boundary probe is routed as `ambiguous`, retirement and reactivation persist without changing definition hashes, six narrow families are added sequentially with no increase in fixed negative-probe capture, and both a near-duplicate overlap proposal and a deliberately broad family are rejected before activation. See `results/core_p14/REPORT.md`.

Completed P1.4 controls:

- [x] overlapping-family and ambiguous-routing controls
- [x] explicit guarded split for a validated bimodal family
- [x] retirement and reactivation policy without deleting historical evidence
- [x] long sequential family growth with a fixed non-permissivity probe suite
- [x] reject a near-duplicate family that would create clean ambiguity
- [x] reject a broad family that would increase negative capture

Next bounded-plasticity step, P1.5:

- [ ] coordinate reflex-version rollback with family quarantine and retirement
- [ ] derive split proposals from measured multimodality rather than a synthetic declared split
- [ ] test merge proposals and prove they do not silently widen routing
- [ ] replace fixed synthetic probe suites with replayed validated and adversarial trajectories
- [ ] connect one real deliberative path so family creation cost is measured end to end

## Phase 4: Active and candidate lifecycle

Goal: make continual compilation operational without changing the live reflex during training.

- [x] candidate registry with immutable version identifiers
- [x] shadow evaluation
- [x] anchor-state regression checks in the P0.4 benchmark
- [x] multi-signal promotion manifest
- [x] persistent rollback to a content-addressed previous active reflex
- [x] explicit promotion failure reasons and evidence records
- [x] persistent per-reflex provenance
- [ ] retirement of obsolete reflexes

Promotion must use explicit thresholds for:

- quality
- calibration
- OOD behavior
- drift
- latency
- memory

P0.4 result: the first multi-signal manifest matches all five declared synthetic decisions. A clean candidate passes, a poisoned candidate fails, a high-quality weak-pool candidate is rejected only for trusted-pool incompatibility and passes after pool expansion, and a parameter-aligned candidate is rejected by behavior and subgroup checks despite passing parameter-space trust. See `results/core_p04/REPORT.md`.

P0.5 result: reflex payloads are stored under SHA-256-derived immutable version IDs, lifecycle evidence is persisted as append-only events, promotion uses multiple shadow windows, and delayed post-promotion monitoring can restore a previous archived version after a later regression. The benchmark deliberately includes a candidate that passes promotion because its defect lies outside the observed shadow windows, then falls to 0.2% accuracy on the delayed hidden slice. Rollback restores the previous version at 98.3% on that slice. See `results/core_p05/REPORT.md`.

## Phase 5: Paradigm Agent

Status: P2.0 through P2.4 executed. P2.2, P2.3, the P2.3R matrix, P2.3R-bis, P2.3T, and the P2.4 Type B experiment have live results against real local language models.

Goal: test whether repeated controller decisions in a tool-using agent can be compiled into a fast path while unfamiliar states remain on deliberation.

P2.0 scope:

- local coding tasks with real temporary workspaces
- fixed `unittest` tool semantics
- file inspection
- symbol search
- controlled repair application
- explicit finish action
- four represented repair families
- one withheld syntax-error OOD family
- deterministic reference deliberator behind the same interface expected from a future external LLM/controller

Recorded P2.0 result:

- 36 test episodes
- 100% baseline success
- 100% hybrid success
- 188 baseline deliberative policy calls
- 20 hybrid deliberative policy calls
- 168 compiled reflex calls
- 89.4% deliberative-call reduction
- 100% fast-path coverage on represented families
- 0% fast-path coverage on the withheld syntax-error family
- zero invalid reflex actions reaching tools

Interpretation:

The result validates the control-plane integration only. Patch synthesis and general language reasoning are not compiled in P2.0. The reference deliberator is deterministic and local, so latency and call-reduction results must be repeated against a real LLM or another genuinely expensive planner before making external efficiency claims.

P2.1 online-learning result:

- 69 sequential agent episodes
- 100% baseline success
- 100% online-hybrid success
- 358 baseline deliberative policy calls
- 141 online-hybrid deliberative calls
- 217 reflex calls
- 60.6% deliberative-call reduction
- four candidate promotions during the stream
- the unseen syntax-error family starts at 0% fast-path coverage
- the second half of syntax-error episodes reaches 48.9% fast-path coverage after validated fallback experience
- a deliberately failed episode contributes zero trusted training traces
- reflex decisions are not reused as teacher labels
- a separate Drift Contract softmax candidate is feasible on the final held-out split with 100% selective accuracy, 100% coverage, ECE 0.0001, and maximum measured update drift 0.0221 at epsilon 0.03

P2.1 is supervised imitation with outcome filtering. It is not RL. The live reflex is immutable between promotions. Learning happens in a separate candidate, followed by shadow validation and atomic replacement.

P2.2 implementation and next steps:

- [x] add a real OpenAI-compatible LLM/controller adapter
- [x] measure prompt tokens, completion tokens, wall-clock latency, optional estimated cost, fallback rate, and task success
- [x] compare LLM-only and Paradigm-hybrid control on the same evaluation stream
- [x] count invalid LLM actions and deterministic safety repairs explicitly
- [x] keep compilation cost separate from evaluation savings
- [x] execute the benchmark against a real external or local model endpoint
- [x] add a reflex amortization metric comparing compilation cost against measured per-use savings
- [x] repeat P2.1 online acquisition against this real controller and measure whether savings compound with continued sequential use (P2.3)
- [ ] exercise cost telemetry against a nonzero, priced endpoint rather than a free local model
- [ ] collect traces from natural repository observations beyond the controlled repair fixtures
- [ ] compare exact cache, rules, compiled reflex, bounded neural reflex, and full deliberation
- [ ] compile tool argument choice only if evidence supports it
- [ ] add approval and write-risk classes to the agent state
- [ ] attach agent behavior families to the persistent family registry
- [ ] connect online promotion to the persistent reflex artifact store and rollback path
- [ ] add adversarial prompts, prompt injection, and misleading test output as negative controls

Go criterion:

A real deliberative controller must preserve task success while a material fraction of repeated policy decisions move to the reflex. Unknown or adversarial states must not be force-routed to the fast path.

Recorded live result: against a local `qwen3:4b-instruct` model, both LLM-only and Paradigm-hybrid control preserved 100% task success. The hybrid reduced LLM calls by 78.7% and tokens by 77.1% over a 15-episode stream, with known-family fast-path coverage at 98.3% and the withheld syntax-error family held at 0% fast-path coverage. The go criterion is met on this single run. It is a static compile-then-evaluate benchmark with one model, one seed, and 15 evaluation episodes, so it is not yet a robust estimate. The reflex amortization metric shows the compiled reflex recovered only about 42% of its own compilation cost within this run, meaning break-even requires roughly 140 reflex uses and this run stopped well short of that. See `results/core_p22/REPORT.md`.

P2.3 online acquisition result with the same real model:

- 69 sequential episodes, 100% baseline success, 100% online success
- 345 baseline LLM calls, 114 online LLM calls, 67.0% call reduction, 66.6% token reduction
- zero invalid LLM actions, zero repairs, zero invalid reflex actions
- the unseen syntax-error family stays fully deliberative for 10 validated episodes (50 decisions), then reaches 100% fast-path coverage after the third candidate passes shadow validation; two earlier candidates are rejected at 0.17 and 0.16 shadow OOD acceptance
- unknown false fast-path rate while unrepresented: 0%
- time-to-reflex: 10 validated episodes; time-to-mature-reflex: 10 episodes
- known families retain 100% success and 98% fast-path coverage after the new family is added
- online acquisition spends zero LLM tokens on compilation and the cumulative online token curve never exceeds the baseline; acquisition cost is 12,958 tokens before the novel family's first fast path

This is the first recorded end-to-end demonstration of the Paradigm loop with a real language model. It remains single-model, single-seed, and supervised imitation with outcome filtering.

Next steps after P2.3:

- [x] repeat P2.3 across seeds and at least one other model to estimate variance in time-to-reflex (P2.3R: zero seed variance, no teacher-size effect)
- [x] test whether time-to-reflex depends on how novel-family evidence arrives (P2.3R: burst 12, interleaved / periodic / rare 7; rare promotes at the last novel episode and is never exercised)
- [ ] P2.4 outcome-weighted learning: weight experiences by success, latency, tokens, tool calls, retries, and overrides instead of binary success filtering
- [ ] P2.5 contextual bandit over reflex choice, only if outcome weighting shows that imitation alone leaves measurable value unexploited
- [x] family-aware certification with retention probes and a negative control (P2.3R-bis: probes close a real retention blind spot; atomic all-family activation is the main cost)
- [x] learning-threshold sweep with fixed certification (P2.3T: capability 100% at zero novel episodes; only trust rises with evidence)
- [x] Type B family whose correct sequence uses actions the known families never use (P2.4: capability 50% at k = 0, 100% at 4 to 6 demonstrations; promoted online; frozen reflex 8/8 on fresh tasks; the 8B teacher gave insufficient validated evidence)
- [ ] trust extension into capable-but-unevidenced regions without lowering the gate (shadow execution with outcome verification feeding a family-scoped trust manifest)
- [ ] replicate P2.4 across seeds and a second Type B family; test a teacher from another model line
- [ ] family-scoped activation: one compiled artifact with a per-family authorization map connected to the P1.3 registry, so certified families enter the fast path while uncertified ones stay deliberative
- [ ] retention probes maintained from previously validated episodes rather than from the recent buffer, so per-family evidence does not depend on the recent split
- [ ] explicit evidence levels per family (observed, recurring, candidate, shadow validated, mature) exposed from the registry
- [ ] a decision rule that declines to compile a behavior when projected reuse does not justify acquisition or maintenance cost

No-go criterion:

If the reflex saves calls only by encoding benchmark-specific task labels, degrades success, or sends OOD states into the fast path, keep Paradigm as an offline analysis tool rather than an agent runtime.

## Phase 6: Paradigm Structured

Research source:

- https://github.com/infinition/ga-vs-scalarization
- https://arxiv.org/abs/2607.06634

Goal: select the smallest architecture that matches task structure.

Initial families:

- rule or table
- linear model
- tree
- MLP
- scalarized equivariant model
- geometric algebra model for nested rotation composition

Key benchmark:

Use matched single-stage and compositional SO(3) tasks. Paradigm should learn or infer when the extra structure is justified rather than defaulting to the most complex model.

Go criterion:

The architecture selector must choose a simpler model on tasks where it is sufficient and a structured model only where the measured sample-efficiency or OOD gain offsets its cost.

## Phase 7: Paradigm World

Research sources:

- https://github.com/infinition/FluidWorld
- https://arxiv.org/abs/2603.21315
- https://github.com/infinition/FluidVLA

Goal: use predictive latent state before executing a reflex.

Stages:

1. consume an external world-state embedding without training Paradigm on pixels
2. compare reflex decisions with and without predictive state
3. score candidate actions through short latent rollouts
4. use uncertainty or rollout disagreement as an additional fallback signal
5. test on simulated manipulation before any real-hardware control

No-go condition:

If predictive state does not improve selective success, OOD rejection, or planning efficiency over ordinary state features, keep Paradigm Core independent from the world model.

## Phase 8: Cross-domain validation

Only after Core succeeds.

Candidate domains:

- workflow routing
- local compute scheduling
- cybersecurity event triage in controlled datasets
- simulated robotics
- real robotics with a separate safety controller

The same claim must not be assumed across domains. Each deployment requires its own acceptance and fallback study.
