# P2.2 Real LLM Controller Report

Paradigm's compiled control reflex is compared against the same OpenAI-compatible language model acting alone on the same evaluation stream. The model is queried only for the next tool-control action, never for patch synthesis. Compilation cost is measured separately from evaluation savings.

## Controller

- Model: `qwen3:4b-instruct`
- Endpoint: `http://127.0.0.1:11434/v1`
- Pricing configured: False

## Compilation cost

- LLM calls used to gather training and validation traces: 140
- Tokens spent compiling: 32648
- Wall-clock LLM time spent compiling: 112.2 s
- Selected backend: `tree`

## End-to-end result

- Evaluation episodes: 15
- Baseline success: 100.0%
- Hybrid success: 100.0%
- Success preserved: True
- Baseline LLM calls: 75
- Hybrid LLM calls: 16
- Hybrid reflex calls: 59
- LLM call reduction: 78.7%
- Token reduction: 77.1%
- LLM latency reduction: 79.0%
- Baseline invalid LLM actions / repairs: 0 / 0
- Hybrid invalid LLM actions / repairs: 0 / 0
- Invalid reflex actions reaching tools: 0

## Known versus withheld families

- Known-family fast-path coverage: 98.3% (59 reflex calls, 1 deliberative calls)
- Withheld syntax-error fast-path coverage: 0.0% (0 reflex calls, 15 deliberative calls)

The withheld family is expected to stay at 0% fast-path coverage. Paradigm does not force reflex coverage on a family it never compiled.

## Reflex amortization

- Reflex uses in this evaluation run: 59
- Tokens saved per reflex use: 233.6
- LLM latency saved per reflex use: 792.2 ms
- Break-even reflex uses (token cost basis): 139.7
- Break-even reflex uses (LLM latency basis): 141.7
- Fraction of compilation cost recovered in this run (tokens): 42.2%
- Break-even reached in this run: False

Compilation happens once; every additional represented episode adds reflex uses without adding compilation cost. A run that has not reached break-even is not a negative result by itself, but it means the measured evaluation stream was not long enough to recover the cost of training and validating this particular reflex.

## Limitations

- P2.2 compiles control-policy decisions only. It does not compile free-form code generation.
- The apply_fix tool remains a validated task repair primitive in this controlled vertical.
- LLM-output repair is counted explicitly and uses a deterministic safe action.
- Compilation cost is reported separately from evaluation savings.
- This benchmark is a static compile-then-evaluate design, not the P2.1 online acquisition loop. Whether savings grow with continued sequential use against a real model is not yet measured.
- The reflex amortization point compares tokens and latency only. It does not price compute, engineering time, or monitoring cost.

