# Glossary

**Deliberation**: the expensive decision path used for unfamiliar or difficult cases.

**Trace**: structured state, chosen action, validation status, outcome, and provenance from a decision episode.

**Reflex**: a compact policy trained or constructed to reproduce a stable decision pattern with low execution cost.

**Compilation**: the process that turns validated traces into a reflex.

**Coverage**: fraction of inputs accepted by the reflex path.

**Selective accuracy**: accuracy measured only on accepted reflex decisions.

**Fallback**: transfer from reflex execution to deliberation because confidence, OOD, or another gate rejects the reflex.

**Active reflex**: the currently deployed reflex.

**Candidate reflex**: a newly trained version that cannot affect live behavior until promotion.

**Anchor set**: stable reference states used to detect candidate regressions.

**Trusted space**: a region estimated from validated behavior. In Paradigm v0.1 this is experimental and does not imply a safety guarantee.

**Behavior drift**: change in outputs between active and candidate reflexes on a reference distribution.

**Bounded plasticity**: the research direction that constrains how much a reflex can change during adaptation.
