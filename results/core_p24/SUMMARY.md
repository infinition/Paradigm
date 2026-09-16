# P2.4 in one page: Type B procedural skill acquisition

Paradigm learned a procedure that was absent at zero evidence, compiled it into a local reflex, and that frozen reflex solved all eight held-out tasks, including two variants its teacher failed to solve. This is policy generalization from successful teacher demonstrations, not learning from teacher failures: no failed episode ever entered the acquisition buffer.

Every number below is loaded from `core_p24_type_b.json`; `paradigm benchmark p24 --from-cache` prints them from the committed artifact.

## The family

`dependency_error` requires four actions no previous family uses (`inspect_dependency`, `search_registry`, `modify_dependency_file`, `install_dependency`). The known repair sequence cannot solve it. Type B is confirmed by the control below.

## Control at zero evidence (k = 0)

| Metric | Value |
|---|---|
| Held-out decision accuracy | 50% (generic steps only) |
| Exact action-sequence accuracy | 0% |
| Forced-replay episode success | 0% |
| Mature known-family reference | 100% |

## Capability versus validated demonstrations (qwen3:4b-instruct traces, 5 orderings)

| Novel training episodes | 0 to 3 | 4 | 5 | 6 and above |
|---|---|---|---|---|
| Decision accuracy | 50% | 87% | 93% | 100% |

Time-to-Capability (criterion fixed before the sweep: 95% decision accuracy and 100% forced replay): median 4 validated episodes, range 4 to 6, reached in 5 of 5 orderings. Certification followed capability; no candidate was promoted below 87% capability. Mature-family retention remained intact on every quality-feasible candidate.

## Online acquisition (69-episode interleaved stream)

| Certification rule | Time-to-Reflex | Promoted at episode | Overall success | LLM calls avoided |
|---|---|---|---|---|
| recent | 8 | 50 | 93% (equal to the LLM-only baseline) | 61% |
| family-aware | 12 | 64 | 93% | 47% |

Under the recent rule, episodes 58 and 61 were solved by the reflex with zero LLM calls. Both runs: 0 invalid actions, 0.0% false fast-path rate, known families at 100% success and 100% fast path.

Prudence cost of family-aware certification: +54 LLM calls, +14,038 tokens, promotion 14 episodes later, for an identical frozen reflex capability and identical post-promotion routing.

## Frozen held-out evaluation (8 fresh tasks, no learning, same tasks in every arm)

| Arm | Success | LLM calls | Tokens |
|---|---|---|---|
| LLM-only (teacher) | 6 / 8 | 56 | 16,557 |
| Frozen hybrid (Paradigm) | 6 / 8 | 22 | 7,096 |
| Frozen reflex-only (diagnostic) | 8 / 8 | 0 | 0 |

False fast paths: 0. The hybrid stayed at 6 of 8 because the trust gate correctly rejected the two prompt variants for which no validated evidence existed and fell back to the teacher, which failed on them. The reflex alone solved both.

## Teachers

| Teacher | Validated successful demonstrations | Outcome |
|---|---|---|
| qwen3:4b-instruct | 12 / 16 | `CAPABILITY_AND_CERTIFICATION_SUCCEEDED` |
| qwen3:8b | 4 / 16 | `INSUFFICIENT_EVIDENCE` (too few demonstrations to fit any candidate) |

Both used the same six-step policy when they succeeded and failed the same way (re-running tests instead of installing). The larger model was the worse teacher for this procedure.

## Limitation

The experiment demonstrates genuine procedural skill acquisition in one controlled coding family, with one online seed and two teachers from one model line. It does not establish general procedural learning across arbitrary agents, domains, models, or environments. Trust did not follow capability into the region without validated evidence; learning where an acquired reflex can be trusted, without lowering the safety gate, is the open question this result leaves.

Details: `INTERPRETATION.md`, `REPORT.md`, `core_p24_type_b.json`, traces under `traces/`.
