# ADR 006: Real LLM slow path stays replaceable

## Status

Accepted for P2.2.

## Decision

Paradigm treats the language model as a deliberative controller behind a narrow interface. The first real-LLM integration compiles only repeated tool-control decisions. It does not fine-tune the external language model and does not claim to compile free-form code generation.

The reference adapter uses an OpenAI-compatible chat-completions endpoint so the same benchmark can run against local llama.cpp, Ollama-compatible gateways, LM Studio, or hosted providers exposing that interface.

Every LLM call records:

- prompt tokens
- completion tokens
- total tokens
- wall-clock latency
- optional estimated monetary cost
- invalid action count
- deterministic repairs of invalid actions

Compilation cost is reported separately from evaluation savings.

## Safety boundary

The model receives only a constrained action set. An invalid model action is counted and replaced by a deterministic safe action. This repair is observable in the metrics and is never treated as a successful raw LLM decision.

The withheld OOD family must remain on the deliberative path unless represented evidence is later promoted through the normal lifecycle.

## Consequences

A live P2.2 result requires an external model endpoint. Repository snapshots without one must record P2.2 as not executed live rather than substituting fixture results.
