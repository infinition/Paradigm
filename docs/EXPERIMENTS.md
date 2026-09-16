# Experiments

Notebooks are the primary format for exploratory experiments. Stable components move into `src/paradigm` only after the notebook result is reproducible.

## P0 sequence

### Notebook 00: core concept

Purpose:

- generate a controlled decision dataset
- define a reference deliberative policy
- inspect action frequencies and ambiguity

Output:

- dataset summary
- train, validation, and OOD splits

### Notebook 01: reflex compilation

Compare:

- decision tree
- random forest
- calibrated compiled reflex

Measure:

- accuracy
- latency
- probability quality

### Notebook 02: confidence and OOD

Compare:

- confidence threshold only
- PCA trusted-subspace residual
- distance-to-training baseline

Measure:

- selective accuracy versus coverage
- OOD false accept rate
- OOD false reject rate

### Notebook 03: candidate promotion

Train active and candidate reflexes on sequential data windows.

Measure:

- improvement on new data
- regression on anchor data
- label disagreement
- total variation drift

A candidate is promoted only when it passes a declared manifest.


### Notebook 04: bounded plasticity

Bridge to the Drift Contract work. Compare ordinary optimizers, replay, and the spectral drift-budget rule while the active model stays frozen. Measure both activation-level and external behavior drift.

## Structured direction

Notebook 10 is a bridge to `ga-vs-scalarization`.

The first experiment should not copy the whole repository. Use two matched tasks:

1. single rotation
2. composed rotations

Compare a simple equivariant scalarized reflex against a geometric reflex. Confirm the published qualitative boundary before adding automatic architecture selection.

## World direction

Notebook 20 is a bridge to `FluidWorld`.

Start with saved latent states or a small external adapter. Do not make FluidWorld a hard dependency of Paradigm Core.

First question:

Does predictive state improve the accept or defer decision compared with current state alone?

## Reproducibility rules

Every claimed result should include:

- fixed seeds
- exact split construction
- baseline settings
- raw result files under `results/`
- a command or notebook that regenerates figures
- negative and failed controls
- hardware information for latency measurements

## Core P0.1: measured deliberation surrogate

Script: `benchmarks/core_p01_measured_deliberation.py`

Purpose: replace the assumed Core P0 cost model with a measured local fallback path. The deliberator samples a neighborhood around a state, evaluates the reference policy across those probes, and returns the majority action. This creates a deterministic, measurable expensive path without depending on a remote service.

This is deliberately scoped as a surrogate. It is useful for measuring compilation mechanics, but it is not evidence about LLM or planner latency.

Raw results: `results/core_p01/core_p01_measured.json`.

## Core P0.2: trusted compilation controls

Script: `benchmarks/core_p02_trusted_compilation.py`

Compared signals:

- classifier confidence
- nearest trusted neighbor distance
- Mahalanobis distance
- PCA residual from a trusted subspace
- nonlinear reconstruction error

Controls:

- explicit off-manifold OOD
- legitimate weak-pool novelty that remains on the trusted manifold
- deliberately invalid near-manifold inputs
- label poisoning of the compiled reflex

The experiment is intentionally an input-space proxy. It tests whether trusted geometry adds signal beyond ordinary confidence. It does not reproduce the adapter-space mechanism from z-manifold.

Raw results: `results/core_p02/core_p02_trust.json`.

## Core P0.3: trusted reflex space

Script: `benchmarks/core_p03_reflex_space.py`

Purpose: move the trust experiment from input geometry to the compiled reflex itself.

Compared representations:

- flattened parameter vectors from validated compact policies
- behavior vectors built from class probabilities on a fixed anchor suite

Candidate controls:

- independent clean reflexes
- label-poisoned reflexes
- valid weak-pool reflexes trained with shifted support
- an adaptive candidate generated inside the trusted parameter subspace
- a signature-only behavior-aligned stress control

A separate calibration pool defines the residual threshold. This avoids calibrating acceptance on the same reflexes used to fit the PCA basis.

The weak-pool experiment is repeated after expanding the trusted pool with validated examples from the missing behavior family. The purpose is to distinguish "not represented by this pool" from "invalid".

Raw results: `results/core_p03/core_p03_reflex_space.json`.

## Core P0.4: promotion manifest

Script: `benchmarks/core_p04_promotion_manifest.py`

Purpose: convert P0.3 trust signals into an explicit multi-signal promotion decision.

Checks in the first manifest:

- overall validation accuracy
- calibration error
- parameter-space compatibility
- behavior-space compatibility
- anchor label disagreement
- anchor total variation
- minimum per-class accuracy
- protected-slice accuracy

Controls:

- clean candidate
- poisoned candidate
- valid weak-pool candidate before and after trusted-pool expansion
- adaptive candidate generated inside the trusted parameter subspace

The benchmark is designed so that trusted-space membership cannot approve a candidate on its own.

Raw results: `results/core_p04/core_p04_promotion.json`.


## Core P0.5: persistent sequential lifecycle

Script: `benchmarks/core_p05_persistent_lifecycle.py`

Purpose: move the active/candidate lifecycle from memory into immutable artifacts plus persistent evidence.

Controls:

- clean candidate promoted across two shadow windows
- process-style registry reload after promotion
- delayed-regression candidate whose defective slice is absent from promotion windows
- later hidden-slice monitor
- rollback to the previous content-addressed artifact
- final evaluation after another registry reload

Raw results: `results/core_p05/core_p05_lifecycle.json`.

## Core P1.0: bounded plasticity mechanics

Script: `benchmarks/core_p10_bounded_plasticity.py`

Research source: `infinition/drift-contract` and the public Drift Contract preprint.

Purpose: test whether the matrix update geometry and explicit epsilon budget remain meaningful when used as a controlled adaptation mechanism for a compact reflex. This is not a reproduction of the source paper's deep local-learning benchmark.

Controls:

- exact-scale conditional bound check across contracting, square, and expanding matrices
- risk-conditioned epsilon scaling on the same gradient and input
- five-seed synthetic basis-rotation shock
- Adam
- Adam with replay
- fast drift budget
- conservative drift budget

Raw results: `results/core_p10/core_p10_bounded_plasticity.json`.

## Core P1.1: multi-layer continual reflex adaptation

Script: `benchmarks/core_p11_multilayer_continual.py`

Purpose: move bounded plasticity from a single linear matrix to a small neural reflex and test several successive representation shifts.

Compared methods:

- SGD
- Adam
- replay
- diagonal EWC
- periodic joint retraining
- Drift Contract transfer on both matrix layers

The task geometry is fixed across seeds while sampled examples and label noise vary. The benchmark records current-task accuracy, mean and worst accuracy across seen domains, forgetting, local adaptation time, and measured pre-activation step drift where available.

The same benchmark also creates explicit flattened neural parameter deltas for a trusted update-space control. The negative result is intentional: a single PCA space over normalized update deltas becomes too permissive after pool expansion and admits the recorded poisoned updates. This motivates family-conditioned spaces and independent behavior or semantic checks.

Raw results: `results/core_p11/core_p11_multilayer.json`.


## Core P1.2: family-conditioned trusted plasticity

Script: `benchmarks/core_p12_family_trusted_plasticity.py`

Purpose: replace the single global update manifold from P1.1 with family-conditioned trust inside one shared active-to-candidate model lineage.

Signals:

- normalized neural parameter delta
- normalized probability delta on fixed protected and family-specific anchor states
- family-conditioned cosine prototype similarity
- current and protected accuracy
- minimum class accuracy
- target subgroup accuracy
- measured pre-activation step drift

Controls:

- held-out validated clean candidates
- targeted label-poisoned candidates
- clean candidates from other represented families
- risk-conditioned epsilon sweep on the same family
- replay
- Drift Contract
- replay plus Drift Contract

The geometry gate can reject or route a candidate. It cannot approve a candidate without semantic evidence.

Raw results: `results/core_p12/core_p12_family_trust.json`.


## Core P1.3: persistent family lifecycle

Script: `benchmarks/core_p13_family_lifecycle.py`

Purpose: persist the family-conditioned trust model without widening existing trusted regions when a new behavior family appears.

Controls:

- correct routing for represented held-out families
- unknown-family routing before validation
- additive registration of a validated new family
- hash check that existing immutable family definitions do not change
- semantic failure with unchanged accepted geometry
- risk-conditioned epsilon violation
- family quarantine after delayed regression
- registry reload after quarantine

Raw results: `results/core_p13/core_p13_family_lifecycle.json`.


## Core P1.4: guarded family evolution

Script: `benchmarks/core_p14_family_evolution.py`

Purpose: test whether the procedural family map can change shape without turning additive growth into a widening acceptance region.

Controls:

- one broad root family containing two validated modes
- guarded replacement of that root by two narrow immutable successor families
- a boundary candidate accepted by both successors and therefore routed as ambiguous
- retirement and reactivation of one child with hash stability
- six sequential narrow-family additions
- a fixed negative probe suite measured after every addition
- a near-duplicate proposal that would create clean ambiguity
- a deliberately broad proposal that would capture negative probes

Raw results: `results/core_p14/core_p14_family_evolution.json`.

## Agent P2.0: compiled coding-controller policy

P2.0 runs local temporary Python projects with five tool semantics: run tests, inspect file, search symbol, apply a controlled validated repair, and finish. Training and validation cover missing import, wrong constant, renamed symbol, and off-by-one families. Syntax error is withheld from compilation.

The recorded full run uses 252 training traces, 126 validation traces, and 36 test episodes. A decision tree is the minimal feasible reflex. Baseline and hybrid task success are both 100%. The hybrid moves 168 of 188 controller decisions to the reflex, while all withheld syntax-error decisions remain deliberative.

The main follow-up is P2.1 with a genuine external deliberative controller and natural repository tasks.

## Agent P2.1: outcome-filtered online reflex learning

Script: `benchmarks/core_p21_online_learning.py`

Purpose: test whether Paradigm can learn repeated controller decisions during normal agent use without modifying the active reflex in place.

Protocol:

- start with no active reflex
- route all unrepresented states to the deliberative controller
- admit only deliberative decisions from successful episodes to the trusted experience buffer
- do not use reflex actions as teacher labels
- periodically split trusted episodes into training and recent shadow validation sets
- compile a separate candidate
- require quality, calibration, and OOD shadow coverage before promotion
- introduce the syntax-error family only after the initial represented workflows
- measure whether the new family remains deliberative before evidence exists and becomes partly reflexive only after promotion
- train a separate linear softmax candidate with Drift Contract updates as a bounded neural fine-tuning control

Recorded full run:

- 69 episodes
- 100% baseline success
- 100% online success
- 358 baseline deliberative calls
- 141 online deliberative calls
- 217 reflex calls
- 60.6% deliberative-call reduction
- 4 candidate promotions
- syntax-error first-half fast-path coverage: 0%
- syntax-error second-half fast-path coverage: 48.9%
- failed control episode admitted traces: 0
- bounded neural candidate selective accuracy: 100%
- bounded neural candidate coverage: 100%
- bounded neural candidate ECE: 0.0001
- bounded neural candidate maximum measured update drift: 0.0221 at epsilon 0.03

Raw results: `results/core_p21/core_p21_online_learning.json`.

## P2.2: real LLM slow path

Implementation status: complete. Live experiment status: executed against a local model.

The benchmark first collects validated controller traces from represented coding families and compiles a reflex. It then evaluates the same held-out task stream twice: once with LLM-only control and once with the Paradigm hybrid. A syntax-error family is withheld from compilation as an OOD control.

Compilation tokens and latency are reported separately from held-out evaluation savings. Invalid model actions are counted even when the deterministic safety layer repairs them.

Recorded live run, `qwen3:4b-instruct` served locally through Ollama's OpenAI-compatible endpoint:

- compilation: 140 LLM calls, 32,648 tokens, 112.2 s LLM wall-clock time, tree backend selected
- 15 evaluation episodes, 100% baseline success, 100% hybrid success
- baseline: 75 LLM calls; hybrid: 16 LLM calls plus 59 reflex calls
- LLM call reduction 78.7%, token reduction 77.1%, LLM latency reduction 79.0%
- known-family fast-path coverage 98.3%; withheld syntax-error fast-path coverage 0.0%
- zero invalid LLM actions, zero repairs, zero invalid reflex actions
- reflex amortization: break-even at approximately 140 reflex uses (token basis); only 59 uses observed, recovering about 42% of compilation cost; break-even not reached in this run

Raw results: `results/core_p22/core_p22_llm.json`, `results/core_p22/REPORT.md`.

## P2.3: real LLM online acquisition

Implementation status: complete. Live experiment status: executed against a local model.

P2.3 is the P2.1 online loop with the deterministic teacher replaced by a real OpenAI-compatible language model. Stream, compiler thresholds, validation split, OOD shadow floor, and outcome filter are unchanged. Per-episode LLM usage is recorded for both the online run and an LLM-only baseline on the same stream, giving cumulative token and latency curves, time-to-reflex, unknown false fast-path rate, and old-family retention.

Recorded live run, `qwen3:4b-instruct` served locally through Ollama's OpenAI-compatible endpoint:

- 69 episodes, 100% baseline success, 100% online success
- baseline 345 LLM calls and 82,757 tokens; online 114 LLM calls and 27,671 tokens
- LLM call reduction 67.0%, token reduction 66.6%, LLM latency reduction 66.8%
- zero invalid LLM actions, zero repairs, zero invalid reflex actions
- 2 promotions, 3 candidates rejected by the OOD shadow gate
- novel family first seen at episode 33; 10 validated episodes and 50 decisions fully deliberative; promoted at episode 42; 100% fast path from episode 43
- phase B novel fast path 16.7%, phase C 100%; unknown false fast-path rate 0.0% (0 of 50)
- time-to-reflex 10 validated episodes; time-to-mature-reflex 10 episodes
- known-family success 100% in phases A and C; known fast path 98.0% in phase C
- LLM tokens spent on compilation 0; local compile wall-clock 0.04 s; cumulative tokens saved 55,086
- acquisition tokens before the novel family's first fast path: 12,958

Raw results: `results/core_p23/core_p23_online_llm.json`, `results/core_p23/REPORT.md`.

## P2.3R: replication across teachers, arrival orders, and seeds

Script: `benchmarks/core_p23r_replication.py`

Design: 2 teacher models x 4 arrival orders x 3 seeds = 24 runs, native Ollama transport with thinking disabled for both models, everything else fixed. Arrival orders: burst (P2.1 layout, 17 novel episodes), interleaved (17 novel episodes spread evenly after a 12-episode warmup), periodic (blocks of 3 novel then 9 known, 12 novel), rare (1 in 8, 7 novel). Seeds offset task indices. The rare cell was pre-registered with three admissible outcomes before it ran. Two OpenAI-transport runs are kept as a transport control.

Recorded aggregate (identical for both models unless stated):

- 24/24 runs at 100% success, 0 invalid actions, 0.0% false fast path, zero IQR across seeds on all acquisition metrics
- TTR: burst 12 (learning 6 + certification 6, cadence artifact), interleaved / periodic / rare 7 (4 + 3)
- deployment episode: 44 / 34 / 37 / 68; post-promotion novel exposure: 5 / 10 / 5 / 0
- token debt recovery within stream: 41% / 139% / 69% / 0%
- rare: promoted at episode 68 after four rejections (last at 0.64), exercised 0/3 per model
- certification boundary: 0/30 candidates with 3 or fewer novel training episodes passed (max 0.64); 12/12 with 4 or more passed (min 0.93)
- teacher efficiency: acquisition tokens 10,687 (4B) versus 10,795 (8B); acquisition latency 19.4 s versus 22.6 s
- transport control matches the primary burst cell on every acquisition metric

Raw results: `results/core_p23r/core_p23r_summary.json`, `results/core_p23r/REPORT.md`, `results/core_p23r/INTERPRETATION.md`, per-run artifacts under `results/core_p23r/runs/`.

## P2.3R-bis: family-aware certification with retention probes

Script: `benchmarks/core_p23r_bis_certification.py`

Design: four arrival orders, seed 0, `qwen3:4b-instruct`, each stream run twice with one certification rule authoritative and the other in shadow. Family-aware certification: at least one validation episode per family (primary; two as a sensitivity run), per-family shadow acceptance, immutable 20-trace retention probes per mature family frozen at first promotion, probe coverage and agreement floors (0.65, 0.95) and no coverage regression beyond 0.10 against the incumbent. Verdicts: promoted, rejected, insufficient_evidence. Negative control: relabel one mature family's failed-phase `inspect_file` decisions to `search_symbol` on the final buffer and certify clean and poisoned candidates under both rules.

Recorded:

- 8/8 runs at 100% success and 0% false fast path
- negative control: family-aware caught 3, missed 0, non-discriminating 1; recent caught 0, missed 2, non-discriminating 2
- additional deliberative decisions with family-aware: 36, 81, 71, 27 (215 total); call reduction 11 to 23 points lower
- disagreement matrix: 5 agree-promote, 14 agree-reject, 19 evidence-availability verdicts, 4 conservative rejections, 1 rescue
- novel deployment: same in burst, 2 and 9 episodes earlier in interleaved and periodic (with thinner coverage in periodic), never in rare
- sensitivity (two validation episodes per family, interleaved): 160 additional decisions, novel deployment 14 episodes later, discrimination unchanged

Raw results: `results/core_p23r_bis/core_p23r_bis_summary.json`, `results/core_p23r_bis/REPORT.md`, `results/core_p23r_bis/INTERPRETATION.md`, per-run directories, `results/core_p23r_bis/sensitivity_min2/`.

## P2.3T: learning-threshold sweep with fixed certification

Script: `benchmarks/core_p23t_threshold.py`

Design: one LLM-only trace set per model (32 known and 12 novel episodes), cached. Candidates fitted with k = 0..8 novel episodes in train; certification set (4 held-out novel, 4 held-out known episodes) and retention probes (4 known episodes) fixed for every k; 5 shuffled orderings. Reports capability accuracy (raw agreement on held-out novel decisions) separately from gate acceptance and promotion under both rules.

Recorded (identical for both models):

- capability accuracy 100% at every k including k = 0
- gate acceptance 0.00, 0.12, 0.35, 0.50, 0.56, 0.78, 0.81, 0.92, 0.94 for k = 0..8
- pooled recent rule promotes at k = 2 in 60% of orderings and at k = 4 in all; per-family rule reaches 100% at k = 7

Raw results: `results/core_p23t/core_p23t_threshold.json`, `results/core_p23t/REPORT.md`, `results/core_p23t/INTERPRETATION.md`, traces under `results/core_p23t/traces/`.

## P2.4: Type B skill acquisition

Script: `benchmarks/core_p24_type_b.py`

Family: `dependency_error` with an extended, opt-in action vocabulary (`inspect_dependency`, `search_registry`, `modify_dependency_file`, `install_dependency`), a local package registry sandbox, and an Outcome Contract (dependency file corrected, package installed, tests pass, code unchanged). Design: LLM-only traces on 32 known and 16 novel episodes per teacher; k = 0 control; sweep over k = 0..12 with a fixed certification set and retention probes, five orderings; pre-registered TTC criterion (95% held-out decision accuracy and 100% forced-replay success); online interleaved stream under both certification rules when the offline class allows; frozen post-stream evaluation on 8 fresh tasks with LLM-only, hybrid, and reflex-only arms.

Recorded:

- k = 0: decision accuracy 50%, exact sequence 0%, replay 0% (both teachers' traces); mature reference 100%
- teachers: 4B 12/16 novel successes, 8B 4/16; both zero invalid actions; same six-step policy on successes
- 4B sweep: 50% through k = 3, 87% at 4, 100% at 6; TTC median 4 [4, 6], 5/5 orderings; gate acceptance 0.00 to 0.97; certification follows capability
- 8B sweep: only k = 0 testable, `INSUFFICIENT_EVIDENCE`
- 4B online, recent rule: promoted at 50 (TTR 8 = 5 + 3), episodes 58 and 61 solved with zero LLM calls, -61% calls, 93% success = baseline, 0 false fast path, known families 100% / 100%
- 4B online, family-aware: promoted at 64 (TTR 12 = 5 + 7), -47% calls, no solvable exposure after promotion
- frozen post-stream (8 fresh tasks, both rules identical): LLM-only 6/8, hybrid 6/8 with 22 vs 56 LLM calls, reflex-only 8/8, 0 false fast path
- offline class 4B: `CAPABILITY_AND_CERTIFICATION_SUCCEEDED` (original rule `RETENTION_FAILURE`, refined and disclosed)

Raw results: `results/core_p24/core_p24_type_b.json`, `results/core_p24/REPORT.md`, `results/core_p24/INTERPRETATION.md`, traces and teacher statistics under `results/core_p24/traces/`.
