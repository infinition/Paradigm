# Contributing

Paradigm is research software. Contributions should keep experiments reproducible and claims narrow.

## Before changing core code

Prototype the idea in a notebook when possible. Move it into `src/paradigm` after the experiment has a stable interface and a baseline comparison.

## Pull request checklist

- tests pass
- new behavior has a reproducible example or notebook
- metrics include a simple baseline
- limitations are documented
- results are not described beyond the evaluated setting
- active and candidate lifecycle semantics remain explicit

## Style

Python 3.10 or later. Keep dependencies minimal. Prefer standard scientific Python components unless a new dependency is necessary for the experiment.
