# Core P1.4 report: guarded family evolution

## Purpose

P1.4 tests whether Paradigm can evolve its procedural family map without silently widening routing acceptance.

This is a synthetic topology benchmark. It evaluates lifecycle mechanics and regression guardrails, not semantic safety.

## Split control

The benchmark begins with one broad root family that accepts two distinct validated modes.

The root is replaced by two narrower immutable successor families. The evolution guard evaluates the post-split topology with the parent removed.

Recorded result:

- split approved: yes
- negative capture delta: 0.0000
- clean ambiguity delta: 0.0000
- exact clean-family routing: 0.0000 to 1.0000
- parent state after split: retired

A probe centered between both successors matches both families with cosine similarity 0.9439 and is returned as `ambiguous`. It therefore defers instead of being force-assigned.

## Retirement and reactivation

One successor is retired temporarily.

- route while retired: `unknown`
- route after reactivation: `represented`
- immutable definition hash changed: no

Operational state changes therefore do not rewrite the trusted family definition.

## Sequential growth

Six additional narrow families are proposed and evaluated one by one.

All six pass the evolution guard. The fixed negative suite records:

| Stage | Unsafe negative capture |
|---|---:|
| after split | 0.0000 |
| after narrow-2 | 0.0000 |
| after narrow-3 | 0.0000 |
| after narrow-4 | 0.0000 |
| after narrow-5 | 0.0000 |
| after narrow-6 | 0.0000 |
| after narrow-7 | 0.0000 |
| final | 0.0000 |

This does not prove future negatives will remain rejected. It shows that the recorded additive growth did not weaken the fixed regression suite.

## Unsafe overlap control

A near-duplicate proposal is constructed close to an existing successor.

The proposal is rejected before activation because:

- clean ambiguity would increase by 0.1250
- exact clean-family routing would decrease by 0.1250
- negative capture would remain unchanged

This control shows that a family can be rejected even when it does not capture negative probes, because it damages routing uniqueness for known valid behavior.

## Unsafe broadening control

A deliberately broad family is proposed.

The proposal is rejected because it would:

- increase negative capture by 0.3654
- increase clean ambiguity by 1.0000
- reduce exact clean-family routing by 1.0000

The rejected definition is never activated.

## Interpretation

P1.4 adds a topology-level guardrail around family growth.

The key design change is that family evolution is no longer equivalent to widening a threshold. A split creates new immutable successors and retires the old parent. A new family must demonstrate that it does not materially worsen the declared clean and negative routing probes before activation.

The result remains limited by the probe suite. The guard can only detect regressions that are represented in its evaluation data.

## Reproduce

```bash
PYTHONPATH=src python benchmarks/core_p14_family_evolution.py
```

Raw result: `results/core_p14/core_p14_family_evolution.json`.
