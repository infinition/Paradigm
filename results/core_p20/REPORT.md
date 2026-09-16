# P2.0 Paradigm Agent Report

Paradigm is connected to a real local coding-agent loop with filesystem reads, symbol search, a fixed test runner, controlled repair application, and explicit finish semantics. The compiled reflex controls tool selection only. Patch synthesis remains outside the reflex in this phase.

## Result

- Baseline success: 100.0%
- Hybrid success: 100.0%
- Overall fast-path coverage: 89.4%
- Known-task fast-path coverage: 100.0%
- OOD fast-path coverage: 0.0%
- OOD success: 100.0%
- Deliberative calls avoided: 168
- Deliberative call reduction: 89.4%
- Invalid reflex actions reaching tools: 0

## Interpretation

P2.0 tests the first concrete use of Paradigm as a procedural fast path for an agent. It does not claim that a local decision tree replaces language-model reasoning or code generation. The reflex only replaces repeated controller decisions when the state is represented and confidence is sufficient. Unknown states fall back to the deliberative policy. The recorded latency is a local controller-policy measurement using a deterministic reference deliberator, not an external LLM latency claim.

## Subprocess integration smoke

The optional subprocess `unittest` runner was also exercised once on all five benchmark families. All five tasks completed successfully. The main metric run uses the in-process runner so process startup does not dominate controller measurements.
