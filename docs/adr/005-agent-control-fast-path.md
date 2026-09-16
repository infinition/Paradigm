# ADR 005: Compile agent control before generation

## Status

Accepted for P2.

## Context

An agent mixes several different costs: understanding the task, generating or editing content, selecting tools, deciding whether to continue, and handling failures. Compiling all of that into one reflex would make the first application benchmark difficult to interpret.

## Decision

Paradigm Agent first compiles the repeated control policy:

- run tests
- inspect a file
- search for a symbol
- invoke a repair operation
- finish

The deliberative controller remains responsible for unfamiliar states and for the semantics of a repair. The reflex never receives an explicit task-family identifier. It receives structured runtime state and hashed task wording.

A deterministic action-validity layer runs before any reflex action reaches a tool. OOD or low-confidence states return to the deliberative controller.

## Consequences

This isolates the first measurable claim: repeated controller decisions can sometimes be removed from the deliberative path without reducing task success.

It does not establish that Paradigm can replace code generation, long-horizon planning, or language reasoning. Those are separate later experiments.
