# Project state

## Current version

`0.1.0`

## Current claim level

Research prototype. Paradigm-specific evidence consists of controlled Core experiments plus a local coding-agent vertical with static and online reflex compilation. A static hybrid benchmark (Agent P2.2), an online acquisition run (Agent P2.3), a 24-run replication across two teacher models, four arrival orders, and three seeds (Agent P2.3R), a certification comparison with retention probes and a negative control (Agent P2.3R-bis), and a fixed-certification learning-threshold sweep (Agent P2.3T) have been executed against real local language models. Those recorded a coverage acquisition (Type A): the reflex was capable on the novel family before it was trusted there. Agent P2.4 then recorded a skill acquisition (Type B) on a dependency-resolution family with four new actions: capability 50% at zero evidence, 100% after four to six validated demonstrations from `qwen3:4b-instruct`, promoted online, executed without the teacher, and generalizing on frozen held-out tasks to a prompt wording the teacher itself fails on, while the trust gate kept that unevidenced region deliberative.

## Implemented

- validated trace schema
- exact-cache and nearest-neighbor baselines
- tree, calibrated-tree, random-forest, and calibrated-forest reflex backends
- minimal-complexity reflex selection
- confidence threshold selection against a deliberative reference
- confidence-based fallback
- experimental PCA trusted-subspace gate in input space
- nearest-distance, Mahalanobis, and nonlinear reconstruction OOD controls
- reflex-level PCA signature gates with disjoint fit and threshold-calibration pools
- parameter signatures for compact reflexes
- behavior signatures measured on fixed anchor states
- measured local perturbation-based deliberative surrogate
- accuracy, Brier, ECE, coverage, selective accuracy, OOD AUROC, latency, and reflex-space poison detection measurements
- active and candidate registry
- behavioral drift comparison
- reproducible Core P0 through P0.5 and P1.0 through P1.4 result files
- content-addressed reflex artifact store with SHA-256 verification
- persistent registry state, provenance, lifecycle events, multi-window shadow evaluation, and archived rollback
- exact-scaled spectral drift-budget matrix update with Newton-Schulz orthogonalization
- two-layer NumPy reflex benchmark with SGD, Adam, replay, diagonal EWC, periodic joint retraining, and Drift Contract
- explicit neural parameter-delta trusted-space control
- family-conditioned cosine prototype gates for parameter and fixed-anchor behavior deltas
- risk-conditioned epsilon schedule and replay plus Drift Contract combined baseline
- persistent immutable family registry with unknown routing, manifest evidence, quarantine, and reload
- P2 coding-agent vertical with structured state encoding, safe local tool sandbox, compiled controller reflex, OOD fallback, and deliberative-policy interface
- in-process and subprocess `unittest` runners for agent experiments
- recorded Agent P2.0 result with task success, fast-path coverage, deliberative-call reduction, and OOD deferral
- outcome-filtered online agent experience buffer with candidate-only promotion
- separate bounded softmax reflex candidate trained with Drift Contract updates
- recorded Agent P2.1 stream with online acquisition of a previously unseen task family
- real OpenAI-compatible LLM slow-path controller with token, latency, cost, and invalid-action telemetry
- recorded Agent P2.2 live benchmark against a local language model with compilation cost separated from evaluation savings
- reflex amortization metric comparing one-time compilation cost against measured per-use savings
- recorded Agent P2.3 online acquisition of an unseen family with a real language model as the only teacher, with per-episode cumulative cost curves, time-to-reflex, unknown false fast-path rate, and old-family retention
- P2.3R replication matrix over teacher models, novel-family arrival orders, and seeds, with per-candidate promotion audit, learning versus certification evidence, acquisition debt, reflex dividend, separate debt recovery ratios, teacher efficiency, and an automatically generated certification-boundary table
- native Ollama transport with thinking disabled for hybrid reasoning models
- opt-in family-aware certification with immutable per-family retention probes, per-family shadow acceptance, incumbent-relative coverage regression check, and promoted / rejected / insufficient_evidence verdicts
- P2.3R-bis paired certification benchmark with shadow certifier, disagreement matrix, and a negative-control candidate that damages a mature family
- P2.3T offline learning-threshold sweep with fixed certification set separating capability accuracy from gate acceptance
- opt-in extended action vocabulary with a deterministic dependency-resolution sandbox (local package registry), Type B Outcome Contract, and per-family valid-action rules
- P2.4 Type B runner: teacher trace statistics, k = 0 control, capability-versus-evidence sweep with forced-replay evaluation and pre-registered Time-to-Capability, online acquisition parametrized by novel family, and a frozen post-stream evaluation with LLM-only, hybrid, and reflex-only arms
- notebook sequence for Core, Agent, Structured, and World directions
- generic integration surface (`paradigm.integration`): structured state contract, typed `decide` results (reflex or deliberate), verified-outcome `observe` and `close_episode` over the existing online compiler, per-family trust manifest, per-decision telemetry, persistence, and a localhost JSON service (`paradigm serve`)
- LaRuche adapter (Level 2: whitelisted tools with validated argument templates) and a Rust bridge in LaRuche wrapping the engine's `Fournisseur` and `Outils` traits, exercised end to end through the real engine loop against the live service with a fixture provider

## Executed results

### Core P0

Four synthetic routing scenarios establish the first quality baseline. A calibrated forest is not justified as a universal default. `MinimalReflexSelector` evaluates backends from simple to complex and stops at the first candidate that satisfies the declared constraints.

With seed 11, the selector chooses a raw tree on three scenarios and a calibrated tree on the noisy case. All four synthetic quality gates pass.

### Core P0.1

The assumed P0 cost ratio is replaced by a measured local deliberative surrogate. With seed 23 and 512 neighborhood probes, all four scenarios pass the local quality and efficiency gates in the recorded run.

The noisy scenario selects a calibrated forest and has a much smaller efficiency margin than the tree-based cases. Calibration cost can therefore erase much of the value of reflex compilation.

This does not close the real-world efficiency claim. A later phase must benchmark against an actual agent, planner, or domain-specific deliberative path.

### Core P0.2

Input-space OOD controls are compared on a low-rank trusted manifold. PCA residual and Mahalanobis distance detect explicit off-manifold shift, while classifier confidence does not. All input-space gates still accept most deliberately invalid near-manifold inputs, and label poisoning remains outside their threat model.

Conclusion: input-space trust is useful as an auxiliary fallback signal, not as a trusted-compilation mechanism by itself.

### Core P0.3

Trust is moved to the reflex itself. Compact linear policies provide two signatures:

1. flattened parameters
2. class probabilities on a fixed anchor suite

With seed 1337, both spaces accept at least 98% of clean candidates and reject all recorded candidates trained with 16% label corruption. Valid weak-pool reflexes are accepted less reliably: 74% in parameter space and 70% in behavior space. After adding validated weak-pool reflexes to the trusted pool, acceptance recovers to 100% in both spaces while the recorded poisoned candidates remain rejected.

An adaptive candidate generated directly inside the trusted parameter subspace keeps 95.9% overall accuracy but falls to 11.1% accuracy on a selected target slice. The parameter gate accepts it by construction. The independent behavior gate rejects it.

A separate signature-only control then shows the remaining boundary: a convex mixture of trusted behavior signatures passes the behavior gate while reducing target-slice accuracy from 94.4% for the ensemble mean to 72.2%, with 95.8% overall anchor accuracy.

Conclusion: reflex-level geometry is useful evidence, but neither parameter-space nor behavior-space membership is a semantic certificate. Promotion needs geometry plus explicit quality, subgroup, calibration, and drift checks.

### Core P0.4

A multi-signal promotion manifest now combines quality, calibration, parameter trust, behavior trust, drift, per-class quality, and a protected-slice check. With seed 1337, all five declared benchmark decisions match expectation.

The important case is the weak-pool candidate: it has 98.1% accuracy and good calibration but is rejected only because the initial trusted pool does not represent it. After validated weak-pool reflexes are added, the same candidate is approved with unchanged quality metrics.

The parameter-aligned adaptive candidate passes parameter-space trust but is rejected by behavior-space and semantic quality checks. This operationalizes the P0.3 conclusion that no trusted subspace can promote a candidate by itself.

The P0.4 in-memory registry result is retained as the promotion-policy baseline. P0.5 replaces its deployment mechanics with immutable version identifiers, persistent provenance, sequential shadow evidence, and archived rollback.

### Core P0.5

The active and candidate lifecycle is persisted to disk. Each serialized reflex receives a SHA-256-derived immutable version identifier. Promotion evidence, provenance, shadow observations, and rollback events are stored separately from the immutable payload.

A deliberately defective candidate passes two initial shadow windows because its corrupted region is absent from those windows. A later hidden-slice window exposes the failure: active accuracy falls to 0.2% versus 98.3% for the previous clean version. Paradigm rolls back to the archived clean content ID and recovers 98.3% on the delayed slice and 91.5% on the broad future window.

Conclusion: pre-promotion evidence cannot cover unobserved slices. Post-promotion monitoring and real rollback are part of the lifecycle rather than optional operational features.

### Core P1.0

The first bounded-plasticity experiment implements the matrix update geometry from Drift Contract without importing the original local-learning accuracy claims. The exact shape-scaled strict variant respects the tested conditional pre-activation drift bound on 8x64, 64x64, and 128x64 matrices.

Risk-conditioned epsilon values produce proportionate measured change. In a five-seed synthetic basis-rotation shock, the fast contract budget reaches 69.3% mean shifted accuracy with a 0.0354 maximum per-step pre-activation drift, compared with Adam at 67.7% and 0.0603. A conservative contract retains 87.0% of old-task accuracy but reaches only 27.7% on the shifted task.

Conclusion: epsilon acts as an explicit plasticity budget in this microbenchmark. The result is a stability-speed tradeoff, not evidence that the contract is universally superior.


### Core P1.1

The bounded-plasticity experiment is extended to a two-layer 24-48-4 neural reflex across three successive representation shifts with fixed task geometry and variable sampled data. Drift Contract reaches 67.4% mean current-task accuracy versus Adam at 68.2%, while reducing the recorded mean maximum per-step pre-activation drift from 0.0521 to 0.0241. Final mean forgetting is essentially unchanged at 37.6% for both methods. Replay retains more previous behavior, and periodic joint retraining gives the best final mean seen accuracy and lowest forgetting in this synthetic benchmark at greater adaptation cost.

P1.1 also replaces the compact linear proxy with explicit neural parameter deltas. The result is negative: the first global PCA update space accepts only 50% of held-out clean updates and 50% of poisoned updates. After pool expansion, legitimate novel-shift acceptance rises to 75%, but poisoned-update acceptance rises to 100%. The raw neural update space is therefore not used as a promotion certificate.

Conclusion: bounded plasticity controls local update magnitude, not memory. Trusted update geometry also needs behavior-family separation and semantic evidence.

### Core P1.2

P1.2 replaces the single global update manifold with family-conditioned trust inside one shared active-to-candidate model lineage. Twenty-four validated clean candidates per family define directional parameter and fixed-anchor behavior signatures, with disjoint fit, calibration, and held-out samples. Six targeted poisoned candidates per family and held-out clean candidates from other families provide negative controls.

In the recorded run, joint parameter and behavior geometry accepts 100% of held-out clean candidates in all three families and rejects 100% of targeted poisoned candidates and cross-family candidates. The full geometry plus semantic manifest accepts 100%, 83.3%, and 100% of held-out clean candidates across families 1, 2, and 3. The family-2 rejection is retained as a conservative semantic false reject.

Risk-conditioned epsilon values produce the intended tradeoff on a controlled family: epsilon 0.030 reaches 59.2% current accuracy with 30.1% protected accuracy and 0.02863 maximum step drift, while epsilon 0.0075 reaches 33.1% current accuracy with 59.9% protected accuracy and 0.00721 maximum step drift.

The combined baseline shows complementary effects. Drift Contract plus replay lowers final mean forgetting from 36.8% for Drift Contract alone to 30.1% while keeping the mean maximum step drift near 0.024. Plain replay records slightly higher mean-seen accuracy at 41.0% versus 40.4%, but its measured step drift is more than twice as large.

Conclusion: update geometry becomes useful when the comparison is lineage-aware and family-conditioned, but it remains rejection and routing evidence. Semantic checks and lifecycle evidence are still required for promotion.

### Core P1.3

P1.3 connects the P1.2 family evidence to a persistent registry. Each family definition is content-addressed from its prototypes, thresholds, semantic floors, risk class, epsilon limit, and parent lineage. Operational state is stored separately so quarantine or retirement never rewrites the trusted family definition.

All three represented held-out candidates route to their expected families and pass their family manifests. A fourth clean representation shift is initially returned as unknown. After a separate validated candidate pool is registered as a new family, the same held-out candidate routes to the new family. SHA-256 hashes of the original three family definitions are unchanged by expansion.

Two controls keep routing and approval separate. A semantic-regression control preserves the clean family-2 signatures but sets subgroup evidence below the calibrated floor, so routing passes and the manifest fails. A high-risk family-3 control uses epsilon 0.030 against a maximum family budget of 0.0075 and is rejected by the plasticity check.

Finally, family 2 is quarantined after a synthetic delayed subgroup regression. Its immutable definition hash remains unchanged, new candidates no longer route to it, and the quarantined state survives a registry reload.

Conclusion: trusted-family growth can be additive rather than permissive. Unknown behavior creates a validation path instead of widening existing family boundaries.

## Raw results

- `results/core_p0/core_p0_suite.json`
- `results/core_p0/REPORT.md`
- `results/core_p01/core_p01_measured.json`
- `results/core_p01/REPORT.md`
- `results/core_p02/core_p02_trust.json`
- `results/core_p02/REPORT.md`
- `results/core_p03/core_p03_reflex_space.json`
- `results/core_p03/REPORT.md`
- `results/core_p04/core_p04_promotion.json`
- `results/core_p04/REPORT.md`
- `results/core_p05/core_p05_lifecycle.json`
- `results/core_p05/REPORT.md`
- `results/core_p10/core_p10_bounded_plasticity.json`
- `results/core_p10/REPORT.md`
- `results/core_p11/core_p11_multilayer.json`
- `results/core_p11/REPORT.md`
- `results/core_p12/core_p12_family_trust.json`
- `results/core_p12/REPORT.md`
- `results/core_p13/core_p13_family_lifecycle.json`
- `results/core_p13/REPORT.md`
- `results/core_p14/core_p14_family_evolution.json`
- `results/core_p14/REPORT.md`
- `results/core_p20/core_p20_agent.json`
- `results/core_p20/REPORT.md`
- `results/core_p21/core_p21_online_learning.json`
- `results/core_p21/REPORT.md`
- `results/core_p22/core_p22_llm.json`
- `results/core_p22/REPORT.md`
- `results/core_p23/core_p23_online_llm.json`
- `results/core_p23/REPORT.md`
- `results/core_p23r/core_p23r_summary.json`
- `results/core_p23r/REPORT.md`
- `results/core_p23r/INTERPRETATION.md`
- `results/core_p23r_bis/core_p23r_bis_summary.json`
- `results/core_p23r_bis/REPORT.md`
- `results/core_p23r_bis/INTERPRETATION.md`
- `results/core_p23t/core_p23t_threshold.json`
- `results/core_p23t/REPORT.md`
- `results/core_p23t/INTERPRETATION.md`
- `results/core_p24/core_p24_type_b.json`
- `results/core_p24/REPORT.md`
- `results/core_p24/INTERPRETATION.md`

## Integration surface

`docs/INTEGRATION.md` describes the public API built after v0.1.0. Recorded smoke run through LaRuche's real engine loop with a fixture provider: 24 missions, model calls per mission 3 for missions 1 to 20 and 1 for missions 21 to 24 after the promotion at mission 20, 8 reflex decisions, 0 failures. Mission-ending control calls always deliberate in this version because the engine intercepts them before the tool layer.

## Next experiment

P2.4 answered the Type B question. The open problem it exposed is trust extension: the compiled reflex is capable on a region (a prompt wording the teacher fails on) for which no validated evidence exists, and the density gate correctly refuses autonomy there, so the hybrid cannot exceed its teacher. The highest-value next experiment is a mechanism that can extend trust into capable-but-unevidenced regions without lowering the gate, for example shadow execution of the reflex on such states with outcome verification feeding a family-scoped trust manifest (P1.3 registry). It is a new research question and was not started.

Earlier note on the Core line: P1.4 should test how the family lifecycle behaves when boundaries themselves evolve.

Required controls:

1. overlapping families that both accept the same candidate
2. explicit ambiguous routing to deliberation
3. family split when one validated family becomes persistently multimodal
4. retirement of obsolete families without deleting historical evidence
5. rollback interactions between reflex versions and family operational state
6. a long sequential run combining family creation, quarantine, reactivation, split, and retirement

The main question is whether Paradigm can evolve its procedural family map without turning family growth into an ever-wider acceptance region.

## Research dependencies

Core research context:

- https://github.com/infinition/z-manifold
- https://arxiv.org/abs/2607.05300
- https://github.com/infinition/drift-contract
- https://infinition.github.io/infinition/assets/papers/drift-bounded-spectral-updates.pdf

Structured direction:

- https://github.com/infinition/ga-vs-scalarization
- https://arxiv.org/abs/2607.06634

World direction:

- https://github.com/infinition/FluidWorld
- https://arxiv.org/abs/2603.21315
- https://github.com/infinition/FluidVLA
- https://github.com/infinition/FluidLM


## P1.4

Status: executed.

Family topology can now evolve through explicit guarded operations. The recorded synthetic benchmark starts with one broad family that represents two validated modes, replaces it with two narrower immutable children, and routes their boundary as ambiguous. Retirement and reactivation are operational state changes only and preserve the content hash of the family definition.

The evolution guard compares the proposed topology against a fixed clean and negative probe suite before activation. Six narrow families are added sequentially with the recorded negative unsafe-capture rate remaining at 0.0. A near-duplicate proposal is rejected because clean ambiguity would rise by 0.125. A deliberately broad proposal is rejected because negative capture would rise by 0.3654, clean ambiguity by 1.0, and exact clean routing would fall by 1.0.

P1.4 remains a synthetic topology benchmark. It does not infer split points automatically and does not establish semantic safety. P1.5 should coordinate family operational state with reflex-version rollback and replace declared splits with data-derived evolution proposals.

### Agent P2.0

The first application vertical connects Paradigm to a local coding-agent control loop. Four repair families are used for compilation and a syntax-error family is withheld. The reflex controls tool selection only; patch synthesis remains outside the compiled policy.

In the recorded 36-episode test, both baseline and hybrid agents complete every task. The baseline uses 188 deliberative policy calls. The hybrid uses 20 deliberative calls and 168 reflex calls, a reduction of 89.4%. All represented-family controller decisions take the fast path in the recorded run, while the withheld syntax-error family uses deliberation for every decision. No invalid reflex action reaches a tool.

This result validates the runtime shape and measurement pipeline, not external LLM savings. The reference deliberator is deterministic and local. P2.1 must repeat the experiment against a real language-model or planner controller.

### Agent P2.1

P2.1 adds learning during normal agent use without mutating the active reflex in place. Only deliberative decisions from successful episodes enter the trusted experience buffer. Self-generated reflex actions are ignored as teacher labels. Candidate compilation is periodic, uses an episode-level train and recent-shadow split, and requires quality, calibration, and OOD shadow coverage before promotion.

Across the recorded 69-episode stream, baseline and online agents both complete 100% of tasks. The baseline uses 358 deliberative decisions. The online system uses 141 deliberative decisions and 217 reflex decisions, a 60.6% reduction in deliberative calls. Four candidate versions are promoted.

The syntax-error family is unseen at the start of the stream and first appears at episode 33. Its first eight episodes remain entirely deliberative. After validated fallback traces accumulate and a candidate passes shadow validation, the second half reaches 48.9% fast-path coverage while task success remains 100%. A deliberately failed control episode contributes zero trusted traces.

A separate linear softmax candidate is trained from the same trusted buffer with Drift Contract updates. On the final held-out split it records 100% selective accuracy, 100% coverage, ECE 0.0001, and maximum measured update drift 0.0221 at epsilon 0.03. The primary runtime still prefers the simplest feasible compiled backend.

Conclusion: the first online loop works as supervised imitation with outcome filtering and discrete promotion. It is not reinforcement learning, and it does not fine-tune the deliberative controller. The next application benchmark must use a real LLM or planner to measure tokens, latency, and monetary cost.


### Agent P2.2

P2.2 implements the first real language-model slow-path interface. `OpenAICompatibleCodingDeliberator` targets `/v1/chat/completions` style endpoints and records prompt, completion, and total token counts, wall-clock latency, optional price-based cost, request failures, invalid model actions, and deterministic repairs. The evaluation runner measures the same task stream in LLM-only and Paradigm-hybrid modes and reports compilation cost separately from evaluation savings.

The implementation is tested with a deterministic transport fixture, including token accounting, savings accounting, and invalid-action repair. These fixture results remain protocol tests only.

A live run was executed against a local Ollama-hosted `qwen3:4b-instruct` model through its OpenAI-compatible `/v1` endpoint (`PARADIGM_LLM_BASE_URL=http://127.0.0.1:11434/v1`), no external API and no configured price. Compilation used 140 LLM calls (32,648 tokens, 112.2 s of LLM wall-clock time) to gather 100 training and 40 validation traces, both with 100% episode success, and selected a plain decision tree as the reflex backend.

Across a 15-episode evaluation stream (12 represented-family episodes across four known families, 3 withheld `syntax_error` episodes), both LLM-only and Paradigm-hybrid control reached 100% task success. The hybrid used 16 LLM calls and 59 reflex calls against 75 LLM calls for the LLM-only baseline: a 78.7% reduction in LLM calls, 77.1% reduction in tokens, and 79.0% reduction in LLM wall-clock latency. Known-family fast-path coverage reached 98.3%. The withheld `syntax_error` family stayed at 0% fast-path coverage for every episode, confirming that an unrepresented family returns to the model rather than being forced onto the reflex. No invalid LLM action, no repaired action, and no invalid reflex action reaching a tool was recorded in this run.

A new reflex amortization metric compares the one-time compilation cost against savings recovered during evaluation: `break-even reflex uses = compilation tokens / tokens saved per reflex use`. Compiling this reflex cost 32,648 tokens; each reflex use during evaluation saved about 233.6 tokens relative to the LLM-only baseline. Break-even is therefore around 140 reflex uses on a token basis, about 142 on a latency basis. The recorded run used the reflex only 59 times, recovering about 42% of the compilation cost. Break-even was not reached in this run. This is preserved as a cautionary result: a reflex that reduces LLM calls during evaluation is not automatically economical, and whether it pays for itself depends on how many times it is subsequently reused.

This remains a static compile-then-evaluate benchmark, structurally similar to P2.0, not the sequential online acquisition tested in P2.1. Whether savings compound further, and whether the amortization point is reached, over a longer sequential run against a real model is not yet measured. Cost telemetry is implemented and unit-tested with nonzero pricing, but this run used a local model with zero configured price, so no live monetary cost figure was produced.

`results/core_p22/core_p22_llm.json` and `results/core_p22/REPORT.md` record this run.

### Agent P2.3

P2.3 repeats the P2.1 online acquisition loop with the deterministic teacher replaced by the same local `qwen3:4b-instruct` model used in P2.2. The 69-episode stream, compiler thresholds, validation split, OOD shadow floor, and outcome filter are identical to P2.1. The model is the only source of teacher labels. Per-episode LLM usage is recorded so cumulative cost curves can be compared against an LLM-only baseline on the same stream.

Both baseline and online agents complete 100% of tasks. The baseline uses 345 LLM calls and 82,757 tokens. The online system uses 114 LLM calls and 27,671 tokens: a 67.0% reduction in LLM calls, 66.6% in tokens, and 66.8% in LLM wall-clock latency. No invalid LLM action, repair, or invalid reflex action occurs. Two candidates are promoted; three are rejected by the OOD shadow gate.

The `syntax_error` family first appears at episode 33. Its first ten episodes (50 decisions) are all routed `out_of_distribution` to the model. Two candidates trained while the family was in the buffer are rejected with shadow OOD acceptance of 0.17 and 0.16, below the 0.65 floor. The third candidate reaches 1.0 and is promoted at episode 42. From episode 43 onward every `syntax_error` decision takes the fast path, with 100% success. Phase B fast-path coverage is 16.7%, phase C is 100%. The unknown false fast-path rate while the family was unrepresented is 0.0% (0 of 50 decisions). Time-to-reflex is therefore 10 validated episodes, or 50 validated LLM decisions, and time-to-mature-reflex is also 10 episodes because coverage is complete immediately after promotion in this run.

Known families are not disturbed by the new family: 100% success in phases A and C, and 98.0% fast-path coverage in phase C, equal to the coverage window recorded before the new family appeared. The residual deliberation is four single-state OOD rejections spread across the run, two of which occur before the novel family exists.

Amortization behaves differently from P2.2. Online acquisition spends zero LLM tokens on compilation because teacher labels come from calls the LLM-only baseline also pays for, and local compile plus validation wall-clock totals 0.04 s. The cumulative online token curve is never above the baseline curve. The relevant cost is therefore acquisition rather than repayment: 13,981 tokens before the known families first reach the fast path and 12,958 tokens before the novel family does. The P2.2 finding that only 42% of compilation cost was recovered is specific to the offline compile-then-evaluate design, which pays for a separate training set.

This is the first recorded demonstration of the full Paradigm loop with a real language model: a previously unseen agent-control behavior was acquired online from successful model decisions, held on the deliberative path until a candidate passed shadow validation, then transferred to the fast path without reducing task success or introducing a false fast-path action in the evaluated sequence. It remains a single model, single seed, single stream, supervised imitation with outcome filtering, not RL.

`results/core_p23/core_p23_online_llm.json` and `results/core_p23/REPORT.md` record this run.

### Agent P2.3R

P2.3R repeats P2.3 as a 24-run matrix: `qwen3:4b-instruct` and `qwen3:8b`, both through Ollama's native API with thinking disabled, four novel-family arrival orders (burst, interleaved, periodic, rare), three seeds each, with the prompt, output budget, streams, compiler cadence, thresholds, outcome filter, and promotion rule held fixed. Two `qwen3:4b-instruct` runs over the OpenAI-compatible endpoint are kept as a transport control outside the primary matrix. Aggregates are regenerated from per-episode logs.

All 24 runs reach 100% task success with zero invalid LLM actions, zero invalid reflex actions, and a 0.0% false fast-path rate on the novel family while it was unrepresented. Every acquisition metric has zero interquartile range across seeds. Time-to-reflex is 12 validated novel episodes in burst order and 7 in interleaved, periodic, and rare order, for both models. The promoted candidate contained 4 novel episodes in its train split in three orders and 6 in burst; the burst difference is a compile-cadence artifact, since a second known-only promotion shifted the schedule so that 3 and then 6 novel training episodes were tested and 4 never was.

Arrival order changes deployment and exposure far more than TTR. Interleaved deploys at episode 34 with 10 novel episodes of exposure afterwards and recovers 139% of its acquisition tokens within the stream; periodic deploys at 37 with 5 episodes and recovers 69%; burst deploys at 44 with 5 episodes and recovers 41%; rare deploys at episode 68 of 69 after four rejected candidates (the last at 0.64 against a 0.65 floor) and is never exercised, so its realized dividend is zero. Rare was pre-registered with three admissible outcomes; the observed one is late promotion with no post-promotion exposure, which is operationally indistinguishable from staying deliberative.

Teacher size does not change the dynamics. The 12 `qwen3:8b` runs reproduce the 12 `qwen3:4b-instruct` runs exactly on TTR, evidence composition, deployment, exposure, and every candidate's shadow acceptance. Both teachers emit the same five-decision policy on every family in this vertical and the compiler only sees state features, so it cannot distinguish them. Cost-to-competence differs only through per-call cost: about 1% more acquisition tokens and 16% more acquisition latency for the larger model, for no measured benefit.

The certification boundary is identical for both models: 0 of 30 candidates with three or fewer novel training episodes passed the shadow gate (maximum acceptance 0.64) and 12 of 12 with four or more passed (minimum 0.93). This is observational under the current cadence, not a causal minimum.

Two interpretive findings matter more than the numbers. First, the `syntax_error` family's required action sequence is the same as the known families'; a candidate fitted with no novel episodes already reproduces about 96% of its decisions. What P2.3 and P2.3R establish is online certification of a previously unrepresented state region (coverage acquisition), not acquisition of a new action policy (skill acquisition). Second, the acquisition buffer is self-focusing: mature families stop producing teacher traces, so the buffer concentrates on unresolved behavior. This helps acquisition and simultaneously removes the evidence the recent-split rule would need to certify old-family retention. Retention was 100% at runtime in all runs but was not certified at promotion.

`results/core_p23r/REPORT.md`, `results/core_p23r/INTERPRETATION.md`, `results/core_p23r/core_p23r_summary.json`, and `results/core_p23r/runs/` record this matrix.

### Agent P2.3R-bis

P2.3R-bis compares the P2.1 recent-split certification rule with family-aware certification on the four P2.3R arrival orders (seed 0, `qwen3:4b-instruct`), each rule authoritative in one run and shadowed in the other. Family-aware certification requires every family in the validation split to have at least one episode and pass shadow acceptance on its own, and every mature family to pass coverage, agreement, and no coverage regression against the incumbent on an immutable retention probe set frozen at its first promotion. Verdicts are promoted, rejected, or insufficient_evidence. A negative control candidate keeps the novel family intact while relabelling one mature family's failed-phase decisions with a valid but wasteful action.

Retention probes close a real blind spot. Over four orders the family-aware rule discriminated clean from poisoned candidates in 3 (caught 3, missed 0, non-discriminating 1); the recent rule produced no discriminative catch and promoted the poisoned candidate in the 2 orders where it promoted the clean one. Detection went through probe agreement (0.80 against a 0.95 floor) on real traces and through the incumbent-relative coverage check on fixture traces.

The cost is mostly not the probes. Family-aware certification added 215 deliberative decisions across the four pairs (call reduction 11 to 23 points lower) because known families absent from the recent split produced insufficient_evidence at the start, and because an uncertified novel family blocked the whole candidate even when all four known families had independently passed. The disagreement matrix shows 19 evidence-availability verdicts and 4 conservative rejections against 5 agreements on promotion. The per-family novel-acceptance requirement bought no safety that the runtime OOD gate did not already provide. Requiring two validation episodes per family (sensitivity run) doubled the extra deliberation and delayed novel deployment by 14 episodes with no change in discrimination. Task success stayed at 100% and false fast path at 0% in all runs.

The refinement this points to is family-scoped activation: one compiled artifact with a per-family authorization map, so certified families enter the fast path while uncertified ones stay deliberative. It was not implemented during the experiment.

`results/core_p23r_bis/REPORT.md`, `results/core_p23r_bis/INTERPRETATION.md`, and `results/core_p23r_bis/core_p23r_bis_summary.json` record these runs.

### Agent P2.3T

P2.3T fits candidates offline from one LLM-only trace set per model with k = 0 to 8 novel episodes in the train split, against a certification set and retention probes that are fixed for every k, over five shuffled orderings. Capability accuracy (raw agreement with the teacher on 20 held-out novel decisions) is 100% at k = 0 and at every k for both models. Gate acceptance rises from 0.00 at k = 0 to 0.56 at k = 4 and 0.94 at k = 8. The reflex was capable on the novel family before any novel evidence existed; the evidence bought trust, not behavior. Both models' tables are identical because capability depends on teacher labels, which agree, and gate acceptance depends on state features only. The 3-to-4-episode boundary observed in P2.3R is not reproduced with the fixed 24-episode known train set, where the floor is crossed at five to seven novel episodes: the boundary is protocol-specific. No learning threshold was measured because capability never had to rise.

`results/core_p23t/REPORT.md`, `results/core_p23t/INTERPRETATION.md`, `results/core_p23t/core_p23t_threshold.json`, and cached traces under `results/core_p23t/traces/` record this sweep.

### Agent P2.4

P2.4 tests skill acquisition (Type B) on `dependency_error`, a family whose correct sequence needs four actions the known families never use and which the known sequence cannot solve. With zero novel training episodes a candidate reaches 50% held-out decision accuracy (generic steps only), 0% exact sequence, and 0% forced-replay success, against a 100% mature reference: the family qualifies.

Teachers differed for the first time. `qwen3:4b-instruct` solved 12 of 16 dependency episodes with one consistent six-step policy and failed all four on one prompt wording; `qwen3:8b` solved 4 of 16, failing on three wordings, at higher cost. Both failed the same way (re-running tests instead of installing). The outcome filter excluded every failure.

On the 4B traces capability rose from 50% at three novel episodes to 87% at four and 100% at six; Time-to-Capability median 4 (range 4 to 6, 5 of 5 orderings). Gate acceptance rose separately, crossing the floor at five to six episodes; certification followed capability. Retention on quality-feasible candidates passed in every ordering; infeasible intermediate candidates that under-covered the probes triggered the first classification rule, which was refined and both verdicts are stored. With 8B, four validated episodes left no k above zero to test: `INSUFFICIENT_EVIDENCE`, and its online loop was not run.

Online (4B, interleaved arrival, 69 episodes), the recent rule promoted the new reflex at episode 50 after 8 validated episodes (learning 5, certification 3) and three quality rejections; episodes 58 and 61 were then solved with six reflex decisions and zero LLM calls. Family-aware certification promoted at 64 with no solvable exposure left. Both runs: 93% overall success equal to the baseline, 71% novel success equal to the teacher, 0 invalid actions, 0.0% false fast path, known families at 100% success and 100% fast path.

A frozen post-stream evaluation on eight fresh tasks (two per wording, no learning, three arms) gave: LLM-only 6 of 8, frozen hybrid 6 of 8 with 22 LLM calls against 56 and four tasks solved with zero calls, frozen reflex-only 8 of 8. The two hybrid failures are the teacher's failing wording, which the gate kept deliberative because no validated episode of it ever entered the buffer. The reflex alone solved that wording: the compiled policy generalized beyond its teacher's successes, and the trust boundary did not follow. Both certification rules produced reflexes with identical frozen behavior.

Result classes: `qwen3:4b-instruct` `CAPABILITY_AND_CERTIFICATION_SUCCEEDED`; `qwen3:8b` `INSUFFICIENT_EVIDENCE`. `results/core_p24/REPORT.md`, `results/core_p24/INTERPRETATION.md`, `results/core_p24/core_p24_type_b.json`, and traces under `results/core_p24/traces/` record this experiment.
