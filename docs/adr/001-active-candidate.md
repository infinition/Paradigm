# ADR 001: Separate active and candidate reflexes

## Decision

Training never updates the active reflex in place.

A new reflex is staged as a candidate, evaluated against held-out and anchor data, then explicitly promoted or rejected.

## Reason

This makes regressions measurable, preserves rollback, and prevents an incomplete training run from changing live behavior.
