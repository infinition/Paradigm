# Safety boundary

Paradigm is not a standalone safety layer.

## Learned decisions remain fallible

Confidence, trusted-space distance, and predictive state are statistical signals. None proves that an action is safe.

## Deterministic controls remain external

High-impact deployments should keep hard constraints outside the learned reflex, including examples such as:

- filesystem and permission boundaries
- transaction limits
- robot joint and collision limits
- emergency stop
- network isolation policy
- explicit human approval for irreversible actions

## Promotion does not equal certification

Passing a benchmark means the candidate met the declared test conditions. It does not establish behavior outside those conditions.

## Real-world action is later work

Initial experiments should use synthetic tasks, offline traces, and simulation. Real-world control belongs after the fallback and regression behavior is characterized.

## Agent vertical boundary

P2.0 exposes no arbitrary shell action to the reflex. The benchmark tool surface is limited to test execution, file inspection, symbol search, a controlled repair operation, and finish. Deterministic action-validity checks run before a reflex action reaches a tool.

A future real agent integration must keep permission checks, destructive-operation approval, filesystem scope, credential access, and network policy outside the learned reflex. Paradigm may recommend an action, but it must not become the security boundary that authorizes that action.

## Online learning boundary

Online learning is candidate-only. The active reflex is immutable between promotions.

Trusted online labels currently require all of the following:

- the decision came from the deliberative path
- the episode completed successfully
- the trace is stored with its task and family provenance
- the candidate is evaluated on held-out recent episodes before promotion

Reflex predictions are not accepted as teacher labels by default. Failed episodes are excluded from the trusted training buffer. A future human override or external verifier should be represented as stronger evidence rather than merged silently with model-generated labels.

## External LLM controller boundary

P2.2 constrains the language model to the action set exposed by the coding-agent sandbox. An unsupported or phase-invalid model action is counted and replaced by a deterministic safe recovery action. The repair does not erase the original failure from telemetry.

This mechanism is not prompt-injection resistance. Adversarial tool output and prompt-injection controls remain required before treating the agent vertical as a security boundary.
