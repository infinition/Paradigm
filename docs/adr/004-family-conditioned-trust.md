# ADR 004: Family-conditioned trusted plasticity

## Status

Accepted for the research scaffold after Core P1.2 and P1.3.

## Decision

Paradigm will not maintain one ever-expanding trusted update manifold. Update and behavior geometry are conditioned on an explicit validated family inside one model lineage.

A candidate can be routed as:

- represented by exactly one active family
- unknown
- ambiguous

Unknown and ambiguous candidates return to deliberation or validation. They are not force-assigned to the nearest family.

Family definitions are immutable. New validated behavior creates a new family definition rather than changing an existing threshold. Operational status such as quarantine or retirement is stored separately.

Family geometry is auxiliary evidence. Promotion still requires semantic quality checks, a compatible plasticity budget, shadow evidence, and runtime monitoring.

## Rationale

Core P1.1 showed that one global neural update PCA became more permissive as heterogeneous validated updates were merged. Core P1.2 showed that family-conditioned directional signatures within one parent lineage were much more selective on the recorded controls. Core P1.3 showed that additive family registration can preserve existing family boundaries and route unknown behavior explicitly.

## Consequences

- family identity becomes part of candidate provenance
- family coverage and false rejection must be measured
- family expansion requires validation evidence
- ambiguous routing is a first-class fallback state
- later work must define split, retirement, and rollback semantics
