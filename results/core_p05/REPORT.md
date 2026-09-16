# Core P0.5 report

## Question

Can Paradigm preserve the active and candidate lifecycle across process restarts, keep immutable reflex versions and provenance, detect a regression that appears only after promotion, and restore a previous archived version?

P0.5 turns the in-memory lifecycle from P0.4 into a persistent sequential benchmark.

## Persistent model

Each compiled reflex is archived as a content-addressed artifact:

```text
serialized reflex
      |
   SHA-256
      |
rfx-<content id>
```

The model payload is immutable. Registry state only stores version identifiers. Provenance, staging, promotion, shadow observations, rejection, and rollback are written as append-only lifecycle events.

## Sequence

Seed: `2026`

1. Train and archive a bootstrap active reflex.
2. Stage a clean candidate.
3. Evaluate it on two shadow windows.
4. Promote it.
5. Re-open the registry from disk.
6. Stage a second candidate containing corruption in a rare hidden slice.
7. Evaluate it on two shadow windows that do not contain that slice.
8. Promote it because the declared evidence passes.
9. Re-open the registry again.
10. Observe a later window concentrated on the previously unseen slice.
11. Detect the delayed regression.
12. Roll back to the content-addressed clean version.
13. Re-open the registry and evaluate the restored artifact.

## Initial shadow promotion

The clean candidate passes both shadow windows:

| Window | Accuracy | ECE | Regression vs active |
|---|---:|---:|---:|
| shadow A | 90.8% | 0.037 | -0.33 pp |
| shadow B | 91.2% | 0.042 | +0.33 pp |

The clean version is promoted and the same version identifier is recovered after reopening the registry from disk.

## Delayed failure control

The deliberately defective candidate also passes the initial shadow windows:

| Window | Accuracy | ECE | Regression vs active |
|---|---:|---:|---:|
| shadow A | 90.9% | 0.050 | -0.13 pp |
| shadow B | 92.4% | 0.039 | -1.20 pp |

This is intentional. The hidden slice is absent from the promotion evidence, so the lifecycle cannot certify behavior it has not observed.

On the delayed hidden-slice window:

- defective active accuracy: **0.2%**
- previous clean accuracy: **98.3%**
- regression versus previous active: **98.1 percentage points**

The delayed monitor fails and triggers rollback.

## Rollback result

After rollback and another registry reload:

- restored version equals the earlier clean content ID
- hidden-slice accuracy returns to **98.3%**
- broad future-window accuracy is **91.5%**

If the defective version had remained active:

- hidden-slice accuracy would be **0.2%**
- broad future-window accuracy would be **79.7%**

## Persistence evidence

The recorded run contains three immutable reflex artifacts and twelve lifecycle events:

```text
provenance
bootstrap_active
provenance
stage
shadow_observation
promote
provenance
stage
shadow_observation
promote
shadow_observation
rollback
```

Every archived version has at least one persistent provenance record.

## Interpretation

P0.5 establishes the lifecycle mechanics, not a safety guarantee.

The important result is negative as well as positive: **passing promotion evidence does not rule out a delayed failure on an unobserved slice**. Paradigm therefore needs both pre-promotion shadow evaluation and post-promotion monitoring with a real rollback path.

The active model can now be treated as an immutable deployed artifact rather than a mutable Python object.

## What this does not show

- The store is a local research implementation, not a hardened distributed registry.
- Append-only JSONL is not a tamper-evident audit log.
- The benchmark uses synthetic routing data.
- The hidden-slice regression is deliberately constructed.
- No claim is made that two shadow windows are sufficient for a real deployment.
- Artifact serialization currently uses Python pickle and therefore assumes a trusted local store.

## Reproduce

```bash
python benchmarks/core_p05_persistent_lifecycle.py --seed 2026
```

Raw result:

`results/core_p05/core_p05_lifecycle.json`
