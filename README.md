# Paradigm

**Trusted procedural memory for adaptive AI agents.**

Paradigm is a procedural learning and trust layer for AI agents. It learns from validated deliberative decisions, compiles stable behaviors into specialized reflexes, and keeps uncertain or unsupported states on the deliberative path.

The central idea is simple:

1. A deliberative system handles unfamiliar or difficult cases.
2. Validated trajectories are stored as experience.
3. Repeated and stable behavior is compiled into a smaller reflex.
4. The reflex is calibrated and tested before promotion.
5. Low-confidence or out-of-distribution cases return to deliberation.
6. New candidates never replace the active reflex without evaluation.

Paradigm is not a claim that every task should be compressed into a reflex. The research question is when this transition is useful, safe, and measurable.

## Architecture

```mermaid
flowchart TD
    A[Input or event] --> B{Active reflex available?}
    B -- no --> D[Deliberative system]
    B -- yes --> C[Fast reflex]

    C --> G{Confidence and OOD gates}
    G -- accept --> H[Action]
    G -- reject --> D

    D --> V[Validation and outcome]
    V --> E[Experience store]
    E --> P[Pattern selection]
    P --> RC[Reflex compiler]
    RC --> TS[Trusted subspace checks]
    TS --> DB[Drift and behavior checks]
    DB --> Q[Candidate reflex]
    Q --> T[Offline evaluation and shadow tests]
    T -->|pass| R[Promote candidate]
    T -->|fail| X[Reject or revise]
    R --> C

    H --> M[Runtime monitoring]
    M --> E
```

### Core invariant

```text
unfamiliar -> deliberate -> validate -> accumulate evidence
familiar   -> reflex     -> monitor  -> fall back when uncertain
```

### Current Core trust lifecycle

```mermaid
flowchart TD
    U[Candidate update] --> FR{Family router}
    FR -- represented --> PG[Parameter family gate]
    PG --> BG[Behavior family gate]
    BG --> SM[Semantic subgroup manifest]
    SM --> EP[Risk-conditioned epsilon policy]
    EP --> SH[Shadow promotion]
    FR -- unknown or ambiguous --> DL[Deliberation and validation]
    DL --> NF[Register new immutable family]
    NF --> FR
    SH --> PM[Post-promotion monitoring]
    PM -- stable --> AC[Remain active]
    PM -- regression --> Q[Quarantine, split, or rollback]
```

Family geometry can reject, route, or identify unrepresented behavior. It does not approve a candidate by itself.

## Three research directions

```mermaid
flowchart LR
    P[Paradigm]
    C[1. Core\ncompile and gate reflexes]
    S[2. Structured\nchoose task-matched reflexes]
    W[3. World\nuse predictive state before action]

    P --> C
    C --> S
    C --> W

    Z[z-manifold] -. trusted spaces .-> C
    D[drift-contract] -. bounded plasticity .-> C
    G[ga-vs-scalarization] -. structure selection .-> S
    F[FluidWorld] -. predictive substrate .-> W
```

### 1. Paradigm Core

Compile recurring validated behavior into calibrated reflexes.

Focus:

- trajectory collection and validation
- pattern discovery
- reflex training
- calibrated confidence
- out-of-distribution fallback
- active and candidate separation
- promotion and rollback
- bounded adaptation

Research foundations:

- [z-manifold](https://github.com/infinition/z-manifold) and [arXiv:2607.05300](https://arxiv.org/abs/2607.05300) for constrained adaptation and pool-relative out-of-distribution signals
- [drift-contract](https://github.com/infinition/drift-contract) and the [public preprint](https://infinition.github.io/infinition/assets/papers/drift-bounded-spectral-updates.pdf) for bounded update geometry and interpretable change budgets

### 2. Paradigm Structured

Choose the smallest reflex architecture that matches the structure of the task.

The default should not be a single universal neural architecture. A reflex may be a rule, linear model, tree, small MLP, geometric model, or another compact policy.

Research foundation:

- [ga-vs-scalarization](https://github.com/infinition/ga-vs-scalarization) and [arXiv:2607.06634](https://arxiv.org/abs/2607.06634)

The result that matters for Paradigm is selective use of structure. Scalarization is sufficient on simple equivariant vector laws, while geometric algebra becomes useful when the target computation composes rotations in depth. Paradigm should therefore select structure only when the task justifies it.

### 3. Paradigm World

Use predictive state to decide whether a reflex should execute, defer, or be rejected before acting.

Research foundations:

- [FluidWorld](https://github.com/infinition/FluidWorld) and [arXiv:2603.21315](https://arxiv.org/abs/2603.21315)
- adjacent research: [FluidVLA](https://github.com/infinition/FluidVLA) and [FluidLM](https://github.com/infinition/FluidLM)

The long-term direction is to expose a compact predictive state, such as a persistent latent belief field, to Paradigm. Candidate actions can then be evaluated against predicted consequences before execution.

## First concrete vertical: Paradigm Agent

P2 connects the Core lifecycle to a small coding agent. The first vertical compiles repeated **controller decisions**, not generated code. The deliberate path still owns unfamiliar diagnosis and repair semantics. Paradigm only takes the fast path when the current state is represented and the reflex action passes confidence, OOD, and deterministic action-validity checks.

```mermaid
flowchart TD
    U[Task] --> S[Agent state]
    S --> R{Represented state?}
    R -- no --> L[Deliberative policy]
    R -- yes --> F[Compiled controller reflex]
    F --> C{Confidence and action validity}
    C -- reject --> L
    C -- accept --> T[Tool action]
    L --> T
    T --> O[Observation]
    O --> S
    L --> V[Validated decision trace]
    V --> RC[Reflex compiler]
    RC --> F
```

P2.0 uses five local tools or tool semantics: test execution, file inspection, symbol search, controlled repair application, and finish. Four represented repair families are used for compilation. A fifth syntax-error family is withheld as OOD. The benchmark has both an in-process `unittest` runner for reproducibility and an optional subprocess runner for integration smoke tests.

P2.1 adds learning during normal use. Successful deliberative fallback decisions enter a trusted experience buffer. The active reflex is never modified in place. Paradigm periodically trains a separate candidate, evaluates it on recent held-out episodes, and promotes it only after quality, calibration, and OOD checks pass. Failed episodes are rejected from the training buffer, and reflex predictions are not reused as teacher labels.

P2.2 adds a real slow-path adapter for OpenAI-compatible language-model endpoints. The adapter records prompt tokens, completion tokens, total tokens, wall-clock latency, optional estimated cost, invalid action outputs, and deterministic repairs. The benchmark compares the same evaluation stream under LLM-only control and Paradigm hybrid control, while reporting compilation cost separately from evaluation savings. A live run against a local `qwen3:4b-instruct` model (served through Ollama's OpenAI-compatible endpoint) preserved 100% task success in both modes and reduced LLM calls by 78.7% and tokens by 77.1%, while the withheld `syntax_error` family stayed at 0% fast-path coverage. A new reflex amortization metric found that this particular reflex had recovered only about 42% of its own compilation cost within the recorded evaluation stream. See `results/core_p22/REPORT.md`.

```mermaid
flowchart TD
    A[Agent use] --> B{Reflex accepts state?}
    B -- yes --> C[Fast action]
    B -- no --> D[Deliberative controller]
    D --> E[Tool action and outcome]
    C --> E
    E --> F{Episode validated?}
    F -- no --> X[Do not train]
    F -- yes --> G[Store deliberative labels only]
    G --> H[Candidate training]
    H --> I[Shadow validation]
    I -- pass --> J[Atomic promotion]
    I -- fail --> K[Keep active reflex]
    J --> B
```

This vertical is deliberately narrow. It tests whether repeated agent-control decisions can move from deliberation to a fast reflex without reducing task success. It does not claim to distill code generation or general language reasoning.

## Using Paradigm in an agent loop

`paradigm.integration` is the public surface: an application supplies a structured `ParadigmState`, the available actions, and a `VerifiedOutcome` after execution; `Paradigm.decide` returns either a `ReflexDecision` or a `DeliberateDecision` (a first-class result carrying the reflex's proposal for audit but never executing it), and `Paradigm.observe` plus `close_episode` feed only verified successes into the same acquisition and certification path measured in P2.1 to P2.4. `paradigm serve` exposes it as a localhost JSON service, and `docs/INTEGRATION.md` documents the contract, the invariants, the LaRuche adapter, family-scoped activation, the recorded smoke run through LaRuche's real engine loop, and the real-provider runs with DeepSeek (runs 9A, 9B, 11, 12 and 12b). Literal teacher agreement is retained as a diagnostic metric, while certification can operate on adapter-defined behavioral equivalence classes. In the recorded run 12 case, literal agreement of 0.857 became 1.000 behavioral agreement for an already-certified test-execution variant, without making a procedurally different regression equivalent. `examples/integration_minimal.py` is the smallest working loop.

## Current evidence

Paradigm currently has eleven executed Core benchmarks, eight executed Agent phases, and a recorded real-agent integration line. The evidence includes live benchmarks, a 24-run replication, a certification comparison with a negative control, a learning-threshold sweep, a Type B skill-acquisition experiment against real local language models, and a fresh LaRuche + DeepSeek deployment with family-scoped activation.

| Benchmark | Result | Interpretation |
|---|---|---|
| Core P0 | 4/4 synthetic quality scenarios pass | simple trees are sufficient for most initial routing tasks |
| Core P0.1 | 4/4 measured local-surrogate scenarios pass | compilation can reduce measured decision latency, but noisy tasks may require a heavier reflex |
| Core P0.2 | PCA and Mahalanobis pass the synthetic OOD / weak-pool tradeoff | input geometry adds information beyond classifier confidence, but does not detect near-manifold semantic corruption |
| Core P0.3 | reflex parameter and behavior spaces reject the synthetic poisoned candidates | trusted reflex spaces add candidate-level signal, but remain pool-relative and are not semantic certificates |
| Core P0.4 | 5/5 declared promotion decisions match expectation | promotion now requires explicit quality, calibration, trust, drift, and subgroup checks |
| Core P0.5 | delayed post-promotion regression is detected and rolled back from persistent storage | active and candidate versions are immutable content-addressed artifacts with persistent provenance |
| Core P1.0 | exact-scaled spectral updates respect the tested conditional drift bound | epsilon behaves as an explicit plasticity budget in the first reflex-adaptation transfer test |
| Core P1.1 | multi-layer continual adaptation exposes a stability-retention split | Drift Contract reduces measured step drift but does not solve forgetting; a global neural update PCA also fails as a trusted promotion gate |
| Core P1.2 | family-conditioned trusted plasticity separates the recorded update families | family-specific parameter and behavior geometry rejects all recorded targeted poisons and cross-family updates; replay plus Drift Contract reduces forgetting while keeping the smaller drift budget |
| Core P1.3 | persistent family lifecycle routes unknown updates instead of broadening trusted regions | represented families route correctly, validated new families are added without mutating existing definitions, and quarantine persists across reload |
| Core P1.4 | guarded family evolution keeps topology explicit | a bimodal root is split into immutable successors, overlap and broadening proposals are rejected, and negative-probe capture remains unchanged through sequential family growth |
| Agent P2.0 | 100% task success with a compiled controller fast path in the recorded local benchmark | 89.4% of policy calls move to the reflex overall, 100% on represented families, while the withheld syntax-error family remains entirely on deliberation |
| Agent P2.1 | 100% success across a 69-episode online stream | 60.6% of policy calls move to the reflex while a previously unseen syntax-error family starts at 0% fast path and reaches 48.9% in its second half after validated fallback experience and promotion |
| Agent P2.2 | 100% task success with a real local LLM controller in the recorded live benchmark | 78.7% of LLM calls and 77.1% of tokens avoided across a 15-episode stream against `qwen3:4b-instruct`; the withheld syntax-error family stays at 0% fast-path coverage; the compiled reflex recovered about 42% of its own compilation cost within this run |
| Agent P2.3 | 100% success across a 69-episode online stream with a real LLM as the only teacher | 67.0% of LLM calls and 66.6% of tokens avoided; an unseen syntax-error family stays fully deliberative for 10 validated episodes with 0% false fast path, then reaches 100% fast-path coverage after passing shadow validation; known families keep 100% success and 98% fast path |
| Agent P2.3R | 24/24 runs at 100% success and 0% false fast path across two teachers, four arrival orders, three seeds | zero seed variance; TTR 12 (burst) or 7 (other orders); teacher size does not change acquisition dynamics; certification boundary between 3 and 4 novel training episodes for both models; rare arrival promotes at the last novel episode and is never exercised; what is acquired is certified coverage of a new state region, not a new action policy |
| Agent P2.3R-bis | retention probes catch a damaged candidate the recent rule promotes, in 3 of 4 orders with 0 misses | the extra deliberation (215 decisions over four pairs) comes mostly from atomic all-family promotion, not from the probes; demanding more evidence per family adds delay without discrimination |
| Agent P2.3T | 100% capability on the novel family with zero novel training episodes, for both teachers | gate acceptance rises with evidence from 0.00 to 0.94; capability precedes trust; the P2.3R boundary is protocol-specific; no learning threshold measured because capability never had to rise |
| Agent P2.4 | a new four-action procedure acquired from validated teacher episodes: capability 50% at zero evidence, 100% after 4 to 6 demonstrations, promoted online and executed with zero LLM calls | frozen held-out evaluation: reflex-only 8/8, hybrid 6/8 with 61% fewer LLM calls, LLM-only 6/8; the reflex generalizes to a wording its teacher fails on while the gate keeps that unevidenced region deliberative; 0 false fast paths; the 8B teacher supplied too few validated demonstrations |
| Real-agent integration, Run 11 | 24/24 missions independently verified by `pytest`; first family-scoped activation at mission 16; 15 reflex decisions; 15 model calls avoided; 0 false fast paths; 0 unsafe automated actions | stable repeated behaviors were activated independently while variable and risky behavior stayed deliberative; a later candidate that regressed an active family was rejected, while mission 24 was rejected for insufficient evidence |
| Real-agent integration, Runs 12 and 12b | 36/36 and 24/24 missions verified; shadow sampling restored 2 to 7 fresh traces per active family; every pre-registered minimum fresh support gave the same adoption decisions; a conservative behavioral-equivalence contract, active live, changed which families the version 2 promotion authorized | teacher disagreement is not reflex regression: one `pytest -q \| cat` variant scored 0.857 literal against 1.000 behavioral agreement; a `file_read` regression stayed rejected offline; live regression discrimination under the contract not yet observed |

A particularly important P0.2 control is negative: classifier confidence accepts almost all explicit off-manifold inputs in the current synthetic benchmark. PCA residual rejects those inputs while retaining legitimate on-manifold novelty, but still accepts most deliberately invalid near-manifold inputs. This keeps the current claim narrow: input-space trust is useful as an OOD signal, not as a complete safety mechanism.

P0.3 therefore moves trust to the reflex itself. Parameter and anchor-behavior signatures reject all recorded label-poisoned candidates, while valid weak-pool candidates are partly rejected until the trusted pool is expanded. An adaptive candidate generated directly inside the parameter subspace is accepted by the parameter gate despite severe degradation on a target slice, but is rejected by the independent behavior-space gate. A separate behavior-aligned signature control still passes the behavior gate while degrading a subgroup. The current design therefore treats trusted geometry as one promotion signal, never as proof of correctness.

P1.1 extends the bounded-plasticity test to a two-layer neural reflex and three successive shifts. Drift Contract reaches similar current-task accuracy to Adam while reducing the recorded mean maximum per-step pre-activation drift from 0.0521 to 0.0241, but its final mean forgetting remains essentially the same. Replay and periodic joint retraining retain more previous behavior. The explicit neural parameter-delta PCA experiment is negative: after trusted-pool expansion, the recorded global update space accepts all poisoned updates. Paradigm therefore keeps update geometry as routing or rejection evidence, not as a promotion certificate.

P1.2 narrows update trust to a single active-to-candidate lineage and separates update families instead of widening one global manifold. On the recorded synthetic benchmark, the joint family-conditioned parameter and behavior geometry accepts all held-out clean candidates, while rejecting all targeted poisoned candidates and all clean candidates from other families. The full semantic manifest accepts 100%, 83.3%, and 100% of held-out clean candidates across the three families, preserving one conservative false rejection rather than weakening subgroup checks. Drift Contract plus replay reduces mean forgetting from 36.8% to 30.1% relative to Drift Contract alone while keeping the mean maximum step drift near 0.024. Plain replay still has slightly higher mean-seen accuracy in this run.

P1.3 makes those families persistent. Family definitions are content-addressed and immutable, while active, quarantined, and retired status is stored separately. Three represented held-out candidates route to their correct families and pass their manifests. A fourth clean shift is initially routed as unknown, then becomes represented only after a separate validated family is registered. Existing family definition hashes remain unchanged. A semantic-regression control and a plasticity-budget violation are both blocked despite valid family routing, and quarantine removes a family from routing after reload without modifying its definition.

P1.4 adds topology evolution without letting registry growth silently widen acceptance. A broad bimodal root is replaced by two narrower immutable successors through a guarded split. A boundary probe becomes explicitly ambiguous and therefore defers. Retirement and reactivation change operational state without changing family hashes. Six additional narrow families are admitted sequentially while the fixed negative-probe capture rate remains 0%. A near-duplicate family is rejected because it creates 12.5% clean ambiguity, and a deliberately broad family is rejected because it would capture 36.5% of negative probes and make all clean probes ambiguous.

P2.0 is the first end-to-end application benchmark. The recorded run trains on 252 validated controller decisions and validates on 126. A simple tree is sufficient. Across 36 test episodes, baseline and hybrid agents both complete 100% of tasks. The hybrid executes 168 of 188 policy decisions through the reflex, reducing deliberative calls by 89.4%. All 32 represented-family episodes use the fast path for every controller decision, while all four withheld syntax-error episodes remain on the deliberative path. This is a controlled local benchmark with a deterministic reference deliberator, not evidence that the same reduction transfers directly to an external LLM.

P2.1 turns that static compile step into an online lifecycle. Across the recorded 69-episode stream, baseline and online agents both complete 100% of tasks. Paradigm avoids 217 of 358 deliberative policy calls, a 60.6% reduction. The syntax-error family first appears at episode 33. Its first half remains entirely deliberative. After successful fallback traces accumulate and a candidate passes shadow validation, its second-half fast-path coverage reaches 48.9%. Four candidate versions are promoted during the run. An explicit failed control episode contributes zero trusted traces. A separate Drift Contract softmax candidate reaches 100% selective accuracy and 100% coverage with ECE 0.0001 in the final held-out split, while keeping the maximum measured update drift at 0.0221 for epsilon 0.03. This remains a controlled local controller benchmark, not an external LLM token or cost result.


P2.2 replaces the synthetic slow-path interface with a real OpenAI-compatible controller adapter. The implementation supports local or hosted endpoints and records tokens, latency, optional price-based cost, request failures, invalid actions, and deterministic repairs. A live benchmark was run against a local Ollama-hosted `qwen3:4b-instruct` model over its OpenAI-compatible `/v1` endpoint. Compilation used 140 LLM calls (32,648 tokens, 112.2 s of LLM wall-clock time) to gather validated traces and select a plain decision tree as the reflex. Across a 15-episode evaluation stream, both LLM-only and Paradigm-hybrid control reached 100% task success. The hybrid used 16 LLM calls and 59 reflex calls against 75 baseline LLM calls, a 78.7% call reduction, 77.1% token reduction, and 79.0% LLM latency reduction. Known-family fast-path coverage reached 98.3%; the withheld `syntax_error` family stayed at 0% fast-path coverage, confirming it correctly returns to the model instead of being forced onto the reflex. No invalid LLM action, repaired action, or invalid reflex action was recorded.

A new reflex amortization metric divides one-time compilation cost by the measured savings per reflex use. In this run, break-even is around 140 reflex uses on a token basis, but the reflex was only used 59 times, recovering about 42% of its compilation cost. Break-even was not reached. This is a genuine negative result worth keeping: a reflex that reduces LLM calls during evaluation is not automatically economical, and whether it pays for itself depends on how many times it is later reused. The benchmark remains a static compile-then-evaluate design, structurally similar to P2.0, not the sequential online acquisition tested in P2.1. Full results are in `results/core_p22/core_p22_llm.json` and `results/core_p22/REPORT.md`.

Example with a local OpenAI-compatible server (this run used Ollama):

```bash
PARADIGM_LLM_BASE_URL=http://127.0.0.1:11434/v1 \
PARADIGM_LLM_MODEL=qwen3:4b-instruct \
PYTHONPATH=src python benchmarks/core_p22_llm.py
```

`--quick` runs a smaller version of the same benchmark for fast iteration. Optional pricing variables `PARADIGM_LLM_INPUT_COST_PER_M` and `PARADIGM_LLM_OUTPUT_COST_PER_M` enable estimated USD savings; this run used a local model with no configured price, so no monetary figure was produced.

P2.3 closes the loop that P2.1 demonstrated with a deterministic teacher, using the same real model. The P2.1 online stream, compiler thresholds, and outcome filter are unchanged; `qwen3:4b-instruct` is the only source of teacher labels. Across the recorded 69-episode stream, baseline and online agents both complete 100% of tasks. The online system uses 114 LLM calls and 27,671 tokens against 345 calls and 82,757 tokens for the LLM-only baseline, a 67.0% call reduction and 66.6% token reduction, with zero invalid actions. The unseen `syntax_error` family appears at episode 33. Its first ten episodes, 50 decisions, are all routed to the model; two candidates containing its traces are rejected by the shadow OOD gate; the third is promoted at episode 42, after which every `syntax_error` decision takes the fast path with 100% success. Time-to-reflex is 10 validated episodes and the unknown false fast-path rate while unrepresented is 0%. Known families keep 100% success and 98% fast-path coverage after the new family is added. Because teacher labels come from calls the baseline also pays for, the online token curve never exceeds the baseline curve; the relevant cost is acquisition (12,958 tokens before the novel family's first fast path), not repayment. Full results are in `results/core_p23/REPORT.md`.

```bash
PARADIGM_LLM_BASE_URL=http://127.0.0.1:11434/v1 \
PARADIGM_LLM_MODEL=qwen3:4b-instruct \
PYTHONPATH=src python benchmarks/core_p23_online_llm.py
```

P2.3R replicates P2.3 as a 24-run matrix (`qwen3:4b-instruct` and `qwen3:8b` on the same native transport with thinking disabled; burst, interleaved, periodic, and rare arrival of the novel family; three seeds). All runs keep 100% success and a 0% false fast-path rate, with zero seed variance on every acquisition metric. Time-to-reflex is 12 validated novel episodes in burst order and 7 otherwise, and the promoted candidate held 4 novel episodes in its train split in most orders; the burst value is a compile-cadence artifact. Arrival order mostly changes when the reflex is deployed and how often it is used afterwards: interleaved recovers 139% of its acquisition tokens within the stream, rare promotes at episode 68 of 69 and is never exercised. The two teachers produce identical acquisition dynamics because they emit the same policy; the larger one only costs more per call. The certification boundary sits between three and four novel training episodes for both models under the current cadence. The `syntax_error` family's action sequence coincides with the known families', so what these runs establish is online certification of a new state region, not learning of a new policy. See `results/core_p23r/INTERPRETATION.md`.

P2.3R-bis tests family-aware certification with immutable per-family retention probes against the recent-split rule, on the same four orders with each rule shadowing the other. A negative control that damages one mature family while preserving the novel one is caught by the probes in 3 of 4 orders with no misses, and promoted by the recent rule in both orders where that rule promoted the clean candidate. The added deliberation (11 to 23 points of call reduction) comes mostly from promoting all families atomically, so an uncertified novel family blocked already-certified known ones; the per-family novel check bought no safety the runtime gate did not already provide. See `results/core_p23r_bis/INTERPRETATION.md`.

P2.3T fits candidates offline with 0 to 8 novel episodes against a fixed certification set. Capability on the novel family is 100% with zero novel episodes for both teachers; only gate acceptance rises with evidence. What P2.3 acquired was certified coverage of a new state region, not a new policy. See `results/core_p23t/INTERPRETATION.md`.

P2.4 is the Type B test: a `dependency_error` family that needs four actions the known families never use. With no novel evidence the candidate reaches 50% decision accuracy and 0% episode success; with four to six validated demonstrations from `qwen3:4b-instruct` it reaches 100% on held-out episodes, and certification follows capability. Online, the reflex is promoted at episode 50 and solves later dependency episodes with zero LLM calls. On eight frozen fresh tasks the reflex alone solves 8 of 8, including a prompt wording on which the teacher fails; the hybrid solves 6 of 8 (equal to the teacher) with 61% fewer LLM calls and no false fast path, because the gate keeps the unevidenced wording deliberative. The 8B teacher solved only 4 of 16 dependency episodes and supplied too few validated demonstrations to fit a candidate. See `results/core_p24/SUMMARY.md` for the one-page version and `results/core_p24/INTERPRETATION.md` for the full reading. After `pip install -e .`, `paradigm benchmark p24 --from-cache` prints the recorded result from the committed artifact without any model endpoint.

The real-agent integration then tests the same trust and reflex lifecycle inside LaRuche with `deepseek-v4-flash`, real tools, a reset coding workspace, independent `pytest` verification, command canonicalization, and a blocking `pre_tool` guard. Whole-candidate certification first reproduced the atomic-coupling failure observed in P2.3R-bis: stable test-running behavior and variable exploratory behavior were judged together, so no reflex could activate. A pre-registered family-scoped rule was then applied without changing any quality, trust, calibration, or retention threshold. In fresh Run 11, 24 of 24 missions were independently verified, two stable families became active at mission 16, and 15 later decisions were replayed by Paradigm instead of calling the model. No false fast path and no unsafe automated action were observed. On missions 17 to 23, the stable post-activation window, model calls, tokens, and wall time were lower than before activation; mission 24 is retained as an outlier and is not used to claim an overall post-activation average improvement. At mission 20, a later candidate was rejected because retention-probe agreement for an active family fell to 15/16, below the 0.95 floor. At mission 24, the candidate was rejected for insufficient evidence, not for a demonstrated regression. See `results/integration_laruche/run11_family_scoped.md` and `docs/INTEGRATION.md`.

Reports:

- `results/core_p0/REPORT.md`
- `results/core_p01/REPORT.md`
- `results/core_p02/REPORT.md`
- `results/core_p03/REPORT.md`
- `results/core_p04/REPORT.md`
- `results/core_p05/REPORT.md`
- `results/core_p10/REPORT.md`
- `results/core_p11/REPORT.md`
- `results/core_p12/REPORT.md`
- `results/core_p13/REPORT.md`
- `results/core_p14/REPORT.md`
- `results/core_p20/REPORT.md`
- `results/core_p21/REPORT.md`
- `results/core_p22/REPORT.md`
- `results/core_p23/REPORT.md`
- `results/core_p23r/REPORT.md`
- `results/core_p23r/INTERPRETATION.md`
- `results/core_p23r_bis/INTERPRETATION.md`
- `results/core_p23t/INTERPRETATION.md`
- `results/core_p24/INTERPRETATION.md`
- `results/integration_laruche/run11_family_scoped.md`
- `results/integration_laruche/family_audit.md`

## Current scope

Version `0.2.0` exposes Paradigm as an integration layer for AI agents while keeping the research lifecycle explicit.

The repository currently provides:

- a generic `decide`, `observe`, and `close_episode` integration API
- typed `ReflexDecision` and `DeliberateDecision` results
- verified-outcome-only acquisition
- calibrated confidence and out-of-distribution fallback
- active and candidate separation
- retention probes and regression checks
- family-scoped activation with per-family thresholds
- persistent reflex state, decision logs, and telemetry
- a localhost JSON service through `paradigm serve`
- a LaRuche adapter contract and a validated Rust bridge on the LaRuche integration branch
- controlled Type A and Type B acquisition benchmarks
- a recorded real-agent integration with DeepSeek and real tools
- reproducible cached benchmark output through `paradigm benchmark p24 --from-cache`

The current reflex surface is intentionally narrow. Read-only tools and exact validated test-command templates may be replayed. Writes, edits, pushes, arbitrary shell commands, delegation, browser or computer control, unsupported arguments, and uncertified families remain deliberative or blocked.

The implementation is an active research prototype, not a production safety system.

## Quick start

```bash
git clone https://github.com/infinition/Paradigm.git
cd Paradigm
python -m venv .venv
source .venv/bin/activate
pip install -e ".[research]"

# Public integration and recorded benchmark
paradigm benchmark p24 --from-cache
python examples/integration_minimal.py

# Minimal Core example
python examples/minimal.py
python benchmarks/core_p0.py --seed 11
python benchmarks/core_p01_measured_deliberation.py --seed 23 --probes 512
python benchmarks/core_p02_trusted_compilation.py --seed 41
python benchmarks/core_p03_reflex_space.py --seed 1337
python benchmarks/core_p04_promotion_manifest.py --seed 1337
python benchmarks/core_p05_persistent_lifecycle.py --seed 2026
python benchmarks/core_p10_bounded_plasticity.py --seed 2026
python benchmarks/core_p11_multilayer_continual.py
python benchmarks/core_p12_family_trusted_plasticity.py
python benchmarks/core_p13_family_lifecycle.py
python benchmarks/core_p14_family_evolution.py
python benchmarks/core_p20_agent.py
python benchmarks/core_p21_online_learning.py
pytest -q
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[research]"
paradigm benchmark p24 --from-cache
python examples/integration_minimal.py
python examples/minimal.py
python benchmarks/core_p0.py --seed 11
python benchmarks/core_p01_measured_deliberation.py --seed 23 --probes 512
python benchmarks/core_p02_trusted_compilation.py --seed 41
python benchmarks/core_p03_reflex_space.py --seed 1337
python benchmarks/core_p04_promotion_manifest.py --seed 1337
python benchmarks/core_p05_persistent_lifecycle.py --seed 2026
python benchmarks/core_p10_bounded_plasticity.py --seed 2026
python benchmarks/core_p11_multilayer_continual.py
python benchmarks/core_p12_family_trusted_plasticity.py
python benchmarks/core_p13_family_lifecycle.py
python benchmarks/core_p14_family_evolution.py
python benchmarks/core_p20_agent.py
python benchmarks/core_p21_online_learning.py
pytest -q
```

## Repository layout

```text
paradigm/
├── README.md
├── ROADMAP.md
├── pyproject.toml
├── references.bib
├── src/paradigm/
│   ├── baselines.py
│   ├── compiler.py
│   ├── evaluation.py
│   ├── gates.py
│   ├── model_selection.py
│   ├── p0.py
│   ├── p01.py
│   ├── p02.py
│   ├── p03.py
│   ├── p04.py
│   ├── p05.py
│   ├── p10.py
│   ├── p11.py
│   ├── p12.py
│   ├── p13.py
│   ├── integration/
│   ├── service.py
│   ├── family_scoped.py
│   ├── family_registry.py
│   ├── bounded.py
│   ├── lifecycle_scenarios.py
│   ├── persistent_registry.py
│   ├── promotion.py
│   ├── reflex_space.py
│   ├── reflex_space_scenarios.py
│   ├── reflex.py
│   ├── registry.py
│   ├── shadow.py
│   ├── storage.py
│   ├── runtime.py
│   ├── scenarios.py
│   ├── schema.py
│   ├── selection.py
│   └── synthetic.py
├── notebooks/
│   ├── 00_core_concept.ipynb
│   ├── 01_reflex_compilation.ipynb
│   ├── 02_confidence_and_ood.ipynb
│   ├── 03_candidate_promotion.ipynb
│   ├── 04_bounded_plasticity.ipynb
│   ├── 05_core_p0_results.ipynb
│   ├── 06_measured_deliberation.ipynb
│   ├── 07_trusted_compilation.ipynb
│   ├── 08_reflex_space.ipynb
│   ├── 09_promotion_manifest.ipynb
│   ├── 09b_persistent_lifecycle.ipynb
│   ├── 11_multilayer_continual.ipynb
│   ├── 12_family_trusted_plasticity.ipynb
│   ├── 13_family_lifecycle.ipynb
│   ├── 10_structured_direction.ipynb
│   └── 20_world_direction.ipynb
├── docs/
│   ├── ARCHITECTURE.md
│   ├── RESEARCH_MAP.md
│   ├── EXPERIMENTS.md
│   ├── EVALUATION.md
│   ├── LIMITATIONS.md
│   ├── NOVELTY_BOUNDARY.md
│   ├── PAPER_PLAN.md
│   ├── GLOSSARY.md
│   ├── SAFETY_BOUNDARY.md
│   ├── RELATED_WORK.md
│   ├── INTEGRATION.md
│   └── adr/
├── benchmarks/
├── examples/
├── tests/
├── data/
├── paper/
└── results/
```

## Research principles

Paradigm follows a few constraints from the start:

- **Baselines before novelty.** A reflex compiler must beat simple rules, cached decisions, trees, and ordinary distillation on measurable cost or quality.
- **Active is immutable during evaluation.** Learning produces a candidate. Promotion is a separate event.
- **Fallback is part of the model.** Coverage matters as much as raw accuracy.
- **Confidence must be measured.** A high-confidence error is more important than average accuracy.
- **Structure is conditional.** Specialized architectures are introduced only where controlled experiments justify them.
- **No safety claims transfer automatically.** Results from adapter subspaces or drift-bounded local learning are hypotheses to test in Paradigm, not guarantees for this system.
- **Negative results stay visible.** A component that fails its benchmark is removed or narrowed in scope.

## First benchmark target

The first useful result should answer one question:

> Can a compact reflex replace a meaningful fraction of repeated deliberative decisions while preserving target accuracy through calibrated fallback?

Primary metrics:

- reflex coverage
- selective accuracy
- fallback rate
- expected decision latency
- expected compute cost
- ECE and Brier score
- out-of-distribution rejection
- active-to-candidate behavioral drift

See [EXPERIMENTS.md](docs/EXPERIMENTS.md) and [EVALUATION.md](docs/EVALUATION.md).

## Research lineage

The project is designed to connect several existing research threads by Fabien Polly without merging their claims:

| Work | Result used by Paradigm | Role here |
|---|---|---|
| [Learning Only What Valid Adapters Can Express](https://arxiv.org/abs/2607.05300) | constrained adaptation within a trusted adapter-derived subspace, plus failure-to-fit as an OOD signal on tested tasks | motivates trusted reflex spaces and rejection gates |
| [Drift-Bounded Spectral Updates for Deep Local Learning](https://infinition.github.io/infinition/assets/papers/drift-bounded-spectral-updates.pdf) | interpretable per-layer update budgets under the stated assumptions | motivates bounded plasticity experiments |
| [When Do Geometric Algebra Layers Beat Scalarization?](https://arxiv.org/abs/2607.06634) | simple structure is often enough, but nested group composition can justify geometric products | motivates architecture selection for structured reflexes |
| [FluidWorld](https://arxiv.org/abs/2603.21315) | reaction-diffusion dynamics as a predictive world-model substrate with persistent spatial state | motivates predictive reflex gating |

The Drift Contract manuscript is currently a public preprint with an arXiv submission pending approval. The repository and preprint are the canonical references until an arXiv identifier is available.

Full mapping: [docs/RESEARCH_MAP.md](docs/RESEARCH_MAP.md)

## Status

`0.2.0` is an active research prototype with a working integration surface.

Paradigm has demonstrated, within the recorded experimental scope:

- replicated Type A certified coverage acquisition
- Type B procedural skill acquisition from validated deliberative experience
- retention-probe protection against regressions
- family-scoped activation without lowering existing thresholds
- integration into a real LaRuche agent loop with DeepSeek and real tools

The strongest real-agent result so far is Run 11. In one fresh 24-mission run, all 24 missions were independently verified by `pytest`. Two stable procedural families became active at mission 16, and Paradigm later replayed 15 certified decisions without a model call. Variable and unsupported behavior remained deliberative, no false fast path was observed, and no unsafe action was automated.

The stable post-activation window is missions 17 to 23. On that window, model calls, tokens, and wall time were lower than before activation. Mission 24 is retained as an outlier with 18 model calls and 74.5 seconds of model self-verification, so the project does not claim an overall post-activation average improvement when that outlier is included. The robust count is 15 reflex decisions and therefore 15 model calls avoided, with no mission broken.

Two limitations from Run 11 remain explicit. First, the start-of-mission family activated on only five validated traces because LaRuche drops detailed output for some failing shell commands; no retrospective minimum-evidence rule was added. Second, once an active family is served by the reflex, fresh deliberative held-out evidence disappears, so later replacement candidates can become `insufficient` even when frozen retention probes still pass. Re-certifying active families from probes when fresh teacher evidence is absent is the next targeted experiment.

See `results/integration_laruche/run11_family_scoped.md`, `docs/INTEGRATION.md`, and `PROJECT_STATE.md`.

## Citation

A Paradigm preprint is included under `paper/` and is the preferred research reference once it has a public archival identifier.

Until then, cite the software repository:

```bibtex
@software{polly2026paradigm,
  author = {Fabien Polly},
  title = {Paradigm: Procedural Learning and Trust for AI Agents},
  year = {2026},
  url = {https://github.com/infinition/Paradigm}
}
```

## License

MIT. External research repositories keep their own licenses. Paradigm does not vendor FluidWorld code.
