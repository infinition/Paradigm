# P2.4 Type B Skill Acquisition Report

Type B tests whether Paradigm can acquire a genuinely new action policy from validated deliberative experience. The `dependency_error` family requires four actions the known families never use (inspect_dependency, search_registry, modify_dependency_file, install_dependency) and cannot be solved by the known sequence: apply_fix changes nothing for it. Capability is measured independently of any trust gate; Time-to-Capability uses a criterion fixed before the sweep ran.

Narrative interpretation: `INTERPRETATION.md` in this directory.

## qwen3:4b-instruct

### Teacher traces

- Novel episodes: 16, success 75%, contract 100%
- Invalid LLM actions on novel episodes: 0
- Mean steps: 7.0; distinct successful sequences: 1; modal sequence share: 100%
- Modal sequence: ['run_tests', 'inspect_dependency', 'modify_dependency_file', 'install_dependency', 'run_tests', 'finish']
- Novel-episode tokens: 33128; LLM latency: 54.6 s
- Known-family success: 100%

### k = 0 control (mature known-family reference accuracy 100%)

- Decision accuracy on held-out novel decisions: 50% (min 50%)
- Exact sequence accuracy: 0%
- Forced-replay episode success: 0%; invalid reflex actions per ordering: 4.8
- Gate acceptance: 0.00
- Result class (offline): `CAPABILITY_AND_CERTIFICATION_SUCCEEDED`

### Capability and trust versus novel training evidence

| Novel train episodes | Decision accuracy mean (min) | Exact sequence | Replay success | Replay invalid | Gate acceptance mean (min) | Recent promote | Family-aware promote | Retention pass | TTC criterion met |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 50% (50%) | 0% | 0% | 4.8 | 0.00 (0.00) | 0% | 0% | 0% | 0% |
| 1 | 50% (50%) | 0% | 0% | 24.0 | 0.12 (0.00) | 0% | 0% | 100% | 0% |
| 2 | 50% (50%) | 0% | 0% | 25.6 | 0.33 (0.00) | 0% | 0% | 100% | 0% |
| 3 | 50% (50%) | 0% | 0% | 24.0 | 0.52 (0.00) | 40% | 40% | 40% | 0% |
| 4 | 87% (67%) | 60% | 60% | 11.2 | 0.61 (0.25) | 60% | 40% | 60% | 60% |
| 5 | 92% (75%) | 75% | 75% | 0.0 | 0.61 (0.25) | 60% | 40% | 100% | 60% |
| 6 | 100% (100%) | 100% | 100% | 0.0 | 0.80 (0.25) | 80% | 80% | 100% | 100% |
| 8 | 100% (100%) | 100% | 100% | 0.0 | 0.97 (0.88) | 100% | 100% | 100% | 100% |

Time-to-Capability (novel episodes to reach decision accuracy >= 95% and forced-replay success 100% on the held-out episodes): median 4, range [4, 6], 5 of 5 orderings reached it. Per ordering: [6, 4, 6, 4, 4].

### Online acquisition, family_aware certification authoritative

- Episodes 69, online success 93%, baseline success 93%
- LLM call reduction 47%, token reduction 43%
- Novel-family success 71%, first novel episode 14, deployed at 64, first fast path None
- Time-to-reflex 12 (learning {'episodes': 5, 'decisions': 30}, certification {'episodes': 7, 'decisions': 42}), outcome promoted
- Unknown false fast-path rate 0%; invalid reflex actions 0
- Acquisition debt {'episodes': 17, 'decisions': 122, 'tokens': 36466, 'llm_latency_ms': 59190.97916398459, 'reflex_reached': False}; reflex dividend 0 calls, -12 tokens over 1 episodes; debt recovery (tokens) None
- Known-family success after representation 1.0, fast path 1.0
- Novel fast path after representation: 0.0

| Episode | Family | Source | LLM calls | Reflex calls | Success | Baseline success |
|---|---|---|---|---|---|---|
| 14 | dependency_error | LLM | 10 | 0 | False | False |
| 18 | dependency_error | LLM | 6 | 0 | True | True |
| 21 | dependency_error | LLM | 6 | 0 | True | True |
| 24 | dependency_error | LLM | 6 | 0 | True | True |
| 28 | dependency_error | LLM | 10 | 0 | False | False |
| 31 | dependency_error | LLM | 6 | 0 | True | True |
| 34 | dependency_error | LLM | 6 | 0 | True | True |
| 38 | dependency_error | LLM | 6 | 0 | True | True |
| 41 | dependency_error | LLM | 10 | 0 | False | False |
| 44 | dependency_error | LLM | 6 | 0 | True | True |
| 48 | dependency_error | LLM | 6 | 0 | True | True |
| 51 | dependency_error | LLM | 6 | 0 | True | True |
| 54 | dependency_error | LLM | 10 | 0 | False | False |
| 58 | dependency_error | LLM | 6 | 0 | True | True |
| 61 | dependency_error | LLM | 6 | 0 | True | True |
| 64 | dependency_error | LLM | 6 | 0 | True | True |
| 68 | dependency_error | LLM | 10 | 0 | False | False |

Post-stream exposure on 8 fresh dependency tasks with the final agent (version 2): success 75% versus LLM-only 75%; 4 solved with zero LLM calls; LLM calls 22 versus 56; tokens 7096 versus 16557; false fast-path failures 0.

Reflex-only diagnostic arm (no gate, no teacher) success: 1.0. Evaluation is frozen: reflex version 2, no learning during evaluation.

| Task | Prompt variant | Sources | LLM calls | Reflex calls | Fallback | Hybrid success | LLM-only success | Reflex-only success |
|---|---|---|---|---|---|---|---|---|
| dependency-900 | 0 | L L L L L L L L L L | 10 | 0 | {'out_of_distribution': 10} | False | False | True |
| dependency-901 | 1 | R R R R R R | 0 | 6 | {} | True | True | True |
| dependency-902 | 2 | R R R R R R | 0 | 6 | {} | True | True | True |
| dependency-903 | 3 | R R R L R R | 1 | 5 | {'out_of_distribution': 1} | True | True | True |
| dependency-904 | 0 | L L L L L L L L L L | 10 | 0 | {'out_of_distribution': 10} | False | False | True |
| dependency-905 | 1 | R R R R R R | 0 | 6 | {} | True | True | True |
| dependency-906 | 2 | R R R R R R | 0 | 6 | {} | True | True | True |
| dependency-907 | 3 | R R R L R R | 1 | 5 | {'out_of_distribution': 1} | True | True | True |

### Online acquisition, recent certification authoritative

- Episodes 69, online success 93%, baseline success 93%
- LLM call reduction 61%, token reduction 58%
- Novel-family success 71%, first novel episode 14, deployed at 50, first fast path 51
- Time-to-reflex 8 (learning {'episodes': 5, 'decisions': 30}, certification {'episodes': 3, 'decisions': 18}), outcome promoted
- Unknown false fast-path rate 0%; invalid reflex actions 0
- Acquisition debt {'episodes': 11, 'decisions': 78, 'tokens': 23147, 'llm_latency_ms': 37461.8076689585, 'reflex_reached': True}; reflex dividend 22 calls, 6168 tokens over 6 episodes; debt recovery (tokens) 0.26647081695252084
- Known-family success after representation 1.0, fast path 1.0
- Novel fast path after representation: 0.5

| Episode | Family | Source | LLM calls | Reflex calls | Success | Baseline success |
|---|---|---|---|---|---|---|
| 14 | dependency_error | LLM | 10 | 0 | False | False |
| 18 | dependency_error | LLM | 6 | 0 | True | True |
| 21 | dependency_error | LLM | 6 | 0 | True | True |
| 24 | dependency_error | LLM | 6 | 0 | True | True |
| 28 | dependency_error | LLM | 10 | 0 | False | False |
| 31 | dependency_error | LLM | 6 | 0 | True | True |
| 34 | dependency_error | LLM | 6 | 0 | True | True |
| 38 | dependency_error | LLM | 6 | 0 | True | True |
| 41 | dependency_error | LLM | 10 | 0 | False | False |
| 44 | dependency_error | LLM | 6 | 0 | True | True |
| 48 | dependency_error | LLM | 6 | 0 | True | True |
| 51 | dependency_error | mixed | 1 | 5 | True | True |
| 54 | dependency_error | LLM | 10 | 0 | False | False |
| 58 | dependency_error | reflex | 0 | 6 | True | True |
| 61 | dependency_error | reflex | 0 | 6 | True | True |
| 64 | dependency_error | mixed | 1 | 5 | True | True |
| 68 | dependency_error | LLM | 10 | 0 | False | False |

Post-stream exposure on 8 fresh dependency tasks with the final agent (version 2): success 75% versus LLM-only 75%; 4 solved with zero LLM calls; LLM calls 22 versus 56; tokens 7111 versus 16587; false fast-path failures 0.

Reflex-only diagnostic arm (no gate, no teacher) success: 1.0. Evaluation is frozen: reflex version 2, no learning during evaluation.

| Task | Prompt variant | Sources | LLM calls | Reflex calls | Fallback | Hybrid success | LLM-only success | Reflex-only success |
|---|---|---|---|---|---|---|---|---|
| dependency-900 | 0 | L L L L L L L L L L | 10 | 0 | {'out_of_distribution': 10} | False | False | True |
| dependency-901 | 1 | R R R R R R | 0 | 6 | {} | True | True | True |
| dependency-902 | 2 | R R R R R R | 0 | 6 | {} | True | True | True |
| dependency-903 | 3 | R R R L R R | 1 | 5 | {'out_of_distribution': 1} | True | True | True |
| dependency-904 | 0 | L L L L L L L L L L | 10 | 0 | {'out_of_distribution': 10} | False | False | True |
| dependency-905 | 1 | R R R R R R | 0 | 6 | {} | True | True | True |
| dependency-906 | 2 | R R R R R R | 0 | 6 | {} | True | True | True |
| dependency-907 | 3 | R R R L R R | 1 | 5 | {'out_of_distribution': 1} | True | True | True |

Result class: `CAPABILITY_AND_CERTIFICATION_SUCCEEDED`

## qwen3:8b

### Teacher traces

- Novel episodes: 16, success 25%, contract 100%
- Invalid LLM actions on novel episodes: 0
- Mean steps: 9.0; distinct successful sequences: 1; modal sequence share: 100%
- Modal sequence: ['run_tests', 'inspect_dependency', 'modify_dependency_file', 'install_dependency', 'run_tests', 'finish']
- Novel-episode tokens: 49011; LLM latency: 83.3 s
- Known-family success: 100%

### k = 0 control (mature known-family reference accuracy 100%)

- Decision accuracy on held-out novel decisions: 50% (min 50%)
- Exact sequence accuracy: 0%
- Forced-replay episode success: 0%; invalid reflex actions per ordering: 4.8
- Gate acceptance: 0.00
- Result class (offline): `INSUFFICIENT_EVIDENCE`

### Capability and trust versus novel training evidence

| Novel train episodes | Decision accuracy mean (min) | Exact sequence | Replay success | Replay invalid | Gate acceptance mean (min) | Recent promote | Family-aware promote | Retention pass | TTC criterion met |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 50% (50%) | 0% | 0% | 4.8 | 0.00 (0.00) | 0% | 0% | 0% | 0% |

Time-to-Capability (novel episodes to reach decision accuracy >= 95% and forced-replay success 100% on the held-out episodes): median None, range [None, None], 0 of 5 orderings reached it. Per ordering: [None, None, None, None, None].

Result class: `INSUFFICIENT_EVIDENCE`

