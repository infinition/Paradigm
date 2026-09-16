# Architecture

## Objective

Paradigm separates expensive deliberation from fast repeated behavior.

A reflex is useful only when three properties hold together:

1. the behavior is recurrent enough to justify compilation
2. accepted predictions are reliable enough to execute
3. uncertainty sends unfamiliar cases back to deliberation

## Lifecycle

```text
input
  |
  v
active reflex
  |
  +-- confident and in distribution --> action --> monitor
  |
  +-- uncertain or OOD --------------> deliberation
                                           |
                                           v
                                      validation
                                           |
                                           v
                                       experience
                                           |
                                  pattern selection
                                           |
                                           v
                                     compilation
                                           |
                                           v
                                       candidate
                                           |
                               offline + shadow tests
                                           |
                           pass ------------+------------ fail
                            |                              |
                            v                              v
                         promote                         reject
```

## Components

### Experience store

Stores structured states, decisions, validation status, outcomes, and provenance. Raw private application data should remain outside the core package.

### Pattern selector

Finds stable repeated decisions worth compiling. Early versions can use frequency and outcome stability. Later versions may use clustering or representation learning.

### Reflex compiler

Fits a compact policy from validated traces. Paradigm does not assume one universal backend. The current selector tries simple trees before calibrated or heavier models and keeps the first backend that satisfies declared constraints.

### Confidence gate

Executes only above a configured probability threshold. Evaluation must report both coverage and selective accuracy.

### Trusted spaces

Paradigm currently evaluates three distinct trust views: input-space OOD signals, reflex parameter signatures, and reflex behavior signatures on fixed anchors. These are transfer experiments inspired by z-manifold, not the z-manifold algorithm itself. No space is treated as a semantic certificate.

### Behavior drift gate

Compares active and candidate predictions on an anchor set using label disagreement and total variation distance.

This is intentionally distinct from Drift Contract. Drift Contract bounds weight-induced pre-activation change under stated conditions. Behavior drift is an external regression measure.

### Promotion manifest

Promotion keeps independent checks visible. The current reference manifest can combine quality, calibration, parameter-space trust, behavior-space trust, drift, class-level quality, and protected-slice quality. Any failed check blocks promotion.

### Active and candidate registry

Training never mutates the active reflex. A candidate is staged, archived under an immutable content-derived version ID, evaluated, then promoted or rejected. The persistent registry records provenance, manifest evidence, shadow observations, and rollback events. Rollback resolves and reloads the previous archived artifact instead of relying on an in-memory object.

## Interfaces planned after P0

```python
ExperienceStore.append(trace)
PatternSelector.select(experience)
Compiler.fit(pattern)
Evaluator.compare(candidate, baselines)
Registry.stage(candidate)
Registry.promote(manifest)
Runtime.decide(state)
```

The initial package keeps these interfaces small until the benchmark determines which abstractions are necessary.


### Persistent artifact store

P0.5 separates immutable model payloads from lifecycle state. A reflex is serialized once, verified with SHA-256, and addressed by a stable `rfx-...` identifier. Registry state stores only identifiers and history. Provenance and lifecycle evidence are append-only events that reference those versions.

The current store is intentionally local and simple. It is not a tamper-evident or distributed registry.

### Sequential shadow monitoring

Promotion can consume several named shadow windows. Post-promotion monitoring uses later windows against the previous archived active version. A delayed regression can therefore trigger rollback even when the candidate passed the original promotion evidence.

### Bounded plasticity experiment

P1.0 adds a separate matrix update path based on the Drift Contract preprint. It uses momentum, five-step Newton-Schulz orthogonalization, shape-aware spectral scaling, and an input-conditioned epsilon budget. This component is experimental and does not replace the external behavior and promotion checks.

### Family-conditioned trusted plasticity

P1.2 replaces one global neural update space with family-conditioned directional evidence inside a single active-to-candidate parameter lineage. Each represented family can carry:

- a normalized parameter-update prototype
- a calibrated parameter similarity threshold
- a normalized fixed-anchor behavior-delta prototype
- a calibrated behavior similarity threshold
- semantic quality floors
- a risk class
- a maximum epsilon plasticity budget

Parameter and behavior geometry are evaluated independently. Passing both makes a candidate represented by that family. It does not make the candidate promotable without semantic and lifecycle evidence.

### Persistent family registry

P1.3 stores family definitions as immutable content-addressed records. Operational state is separate.

```text
immutable definition
  family id
  prototypes
  thresholds
  semantic floors
  risk
  epsilon limit
  lineage

mutable operational state
  active
  quarantined
  retired
```

Routing returns one of three states:

- `represented`: exactly one active family accepts both signatures
- `unknown`: no active family accepts both signatures
- `ambiguous`: more than one active family accepts both signatures

Unknown and ambiguous candidates defer. A validated new behavior creates a new family definition instead of broadening an existing threshold. Quarantine removes a family from routing without rewriting its historical evidence.


### Family evolution guard

P1.4 separates family-map evolution from ordinary routing. A proposed family addition or split is evaluated against fixed clean and negative probe suites before its topology becomes active. The guard tracks:

- change in negative probe capture
- change in clean ambiguity
- change in exact clean-family routing

A split is evaluated as a replacement topology with the parent removed and the proposed children active. This avoids penalizing a valid split only because parent and child definitions would overlap during a temporary transition.

Family definitions remain immutable. Split creates new child IDs and retires the parent. Retirement, quarantine, and reactivation are operational states stored separately from definition content.

## Agent vertical

The Agent vertical treats Paradigm as a controller fast path rather than a text generator.

```text
task + observation
       |
       v
structured agent state
       |
       +--> OOD / confidence / deterministic validity gates
       |             |
       |             +--> reject --> deliberative controller
       v
compiled controller reflex
       |
       v
tool action
       |
       v
observation --> next state
```

The deliberative controller uses the same action interface as the reflex. This keeps the first experiment provider-agnostic and allows an external LLM, planner, or human-approved controller to replace the local reference policy without changing the fast-path contract.
