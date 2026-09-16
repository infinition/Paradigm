# Core P1.3 report: persistent family lifecycle

P1.3 connects the family-conditioned trust signals from P1.2 to a persistent lifecycle. Family definitions are immutable and content-addressed, while operational status is stored separately. Unknown and quarantined families are not force-assigned.

This is a synthetic lifecycle benchmark. The registry is research infrastructure, not a production authorization system.

## Setup

- three initially represented update families
- one shared active-to-candidate parameter lineage
- immutable family definitions with parameter and behavior prototypes, calibrated thresholds, semantic floors, risk, and maximum epsilon
- operational states: active, quarantined, retired
- fourth clean shift held out as an unknown-family control
- persisted candidate manifests and family lifecycle events

## Represented-family routing

| Candidate | Routed family | Expected | Correct |
|---|---|---|---:|
| family_1 | `fam-c5931201b7e9d1b9780452ad` | `fam-c5931201b7e9d1b9780452ad` | yes |
| family_2 | `fam-80ee0fd98e8a9b3adff9b6bc` | `fam-80ee0fd98e8a9b3adff9b6bc` | yes |
| family_3 | `fam-ae122447b65b9e644dafc472` | `fam-ae122447b65b9e644dafc472` | yes |

All three held-out represented-family candidates route to exactly one correct active family, and their recorded family manifests pass.

## Unknown-family expansion

Before validation, the fourth shift returns:

```text
status = unknown
family_id = null
```

After a separate validated pool is used to create a new immutable family:

```text
status = represented
family_id = fam-6f5e1af2aeea12301bb669e1
```

Existing family definition hashes remain unchanged. The new family is added rather than widening the thresholds of an existing family.

## Semantic control

The semantic-regression control uses the same accepted family geometry as a clean family-2 candidate but supplies a failed subgroup result. The family route passes and the manifest is rejected only by the subgroup check.

```text
geometry route       PASS
epsilon policy       PASS
overall quality      PASS
protected quality    PASS
subgroup accuracy    FAIL
promotion eligibility FAIL
```

This keeps family geometry and semantic evidence separate.

## Plasticity-budget control

The high-risk family allows a maximum epsilon of 0.0075. A control candidate presents otherwise valid family and quality evidence but declares epsilon 0.030. The manifest rejects it through the plasticity-budget check.

## Quarantine and persistence

Family 2 is quarantined after a synthetic delayed subgroup regression. Its immutable definition file is unchanged, but it is removed from active routing. The quarantine status remains after a registry reload.

| Check | Result |
|---|---:|
| epsilon violation blocks manifest | pass |
| family expansion does not modify existing definitions | pass |
| quarantine persists after reload | pass |
| quarantine removes family from routing | pass |
| represented families route correctly | pass |
| semantic failure blocks manifest | pass |
| unknown routes to deliberation | pass |
| validated new family routes after registration | pass |

Persistent store summary:

- events: 10
- active families after quarantine: 3
- total immutable family definitions: 4

## Consequence for Paradigm

P1.3 establishes a concrete lifecycle rule:

```text
candidate update
      |
      v
family router
  | represented
  |    -> family geometry
  |    -> semantic manifest
  |    -> epsilon policy
  |    -> shadow promotion
  |
  | unknown or ambiguous
  `----> deliberation / validation / new family

post-promotion monitor
  | stable       -> remain active
  | family drift -> quarantine / split / rollback
```

The family registry does not make a candidate safe. It prevents a different failure mode: silently broadening one trusted region until unrelated updates become acceptable.

## Next step

P1.4 should test family evolution over time: overlapping families, ambiguous routing, family split and merge criteria, retirement of obsolete families, and rollback interaction with active reflex versions.

Raw results: `core_p13_family_lifecycle.json`.
