# P2.4 Interpretation: Type B skill acquisition

Type B asks whether Paradigm can acquire a genuinely new action policy from validated deliberative experience, as opposed to the Type A coverage acquisition established in P2.3, P2.3R, and P2.3T. All numbers are from `core_p24_type_b.json`. The Type A artifacts are untouched; the extended action vocabulary used here is opt-in and every earlier protocol runs byte-identically on the base vocabulary.

## Family

`dependency_error`: a module imports a package that is not installed. The workspace has a `requirements.txt` with a defect (misspelled name or no declaration) and a local package registry. Four new actions exist for it (`inspect_dependency`, `search_registry`, `modify_dependency_file`, `install_dependency`), each with the known actions still available as valid but wrong alternatives at every step. `apply_fix` changes nothing for this family, so the known sequence cannot solve it. The Outcome Contract requires the dependency file to be corrected, the required package installed, tests passing, and code files unchanged.

The pre-registered signature: capability materially below mature level at k = 0; capability rising with validated novel evidence; a candidate eventually executing the new sequence reliably; certification following capability; mature families intact; uncertified states kept deliberative; no threshold lowered. Time-to-Capability criterion, fixed before the sweep: held-out decision accuracy at least 95% and forced-replay episode success 100% on the four held-out novel episodes.

## Was the family genuinely Type B

Yes. With zero novel episodes in the train split, the candidate's decision accuracy on held-out novel decisions is 50% for both teachers' traces (only the generic `run_tests` and `finish` steps), exact-sequence accuracy 0%, forced-replay success 0%, and the mature known-family reference is 100%. The candidate predicted `inspect_file` where `inspect_dependency` was required and never emitted any dependency action. On the fixture teacher the k = 0 figure was 43%.

## Teachers

The two teachers differ sharply here, unlike in every Type A experiment.

| Teacher | Novel success | Contract on successes | Invalid actions | Distinct successful sequences | Novel tokens / latency |
|---|---|---|---|---|---|
| qwen3:4b-instruct | 12 / 16 (75%) | 100% | 0 | 1 | 33,128 / 54.6 s |
| qwen3:8b | 4 / 16 (25%) | 100% | 0 | 1 | 49,011 / 83.3 s |

Both teachers use the same six-step policy when they succeed (`run_tests, inspect_dependency, modify_dependency_file, install_dependency, run_tests, finish`), skipping the registry search the reference policy uses. Both fail the same way: after modifying the dependency file they re-run the tests instead of installing, then loop. The 4B teacher does this only on one prompt wording (every fourth task); the 8B teacher on three of the four wordings, and additionally falls back to `inspect_file, apply_fix`, after which the environment only allows `run_tests`, trapping it. The outcome filter excluded every failed episode from acquisition.

The larger teacher was the worse teacher on this procedure: fewer validated demonstrations at higher cost. With four validated episodes, exactly the size of the fixed certification set, the 8B sweep could test only k = 0. Its result class is `INSUFFICIENT_EVIDENCE`: the family is Type B, but the teacher did not supply enough validated evidence to fit any candidate. The 8B online loop was not run, per protocol, because the offline sweep could not show acquisition. This is the first setting in this project where teacher quality changed the outcome, and it did so through the number of validated demonstrations, not through the quality of the successful ones.

## Capability rose with evidence (4B traces, 5 orderings)

| Novel train episodes | Decision accuracy | Exact sequence | Replay success | Gate acceptance | Recent promote | Family-aware promote | Retention pass |
|---|---|---|---|---|---|---|---|
| 0 | 50% | 0% | 0% | 0.00 | 0% | 0% | 0% |
| 1 | 50% | 0% | 0% | 0.12 | 0% | 0% | 100% |
| 2 | 50% | 0% | 0% | 0.33 | 0% | 0% | 100% |
| 3 | 50% | 0% | 0% | 0.52 | 40% | 40% | 40% |
| 4 | 87% | 60% | 60% | 0.61 | 60% | 40% | 60% |
| 5 | 93% | 75% | 75% | 0.61 | 60% | 40% | 100% |
| 6 | 100% | 100% | 100% | 0.80 | 80% | 80% | 100% |
| 8 | 100% | 100% | 100% | 0.97 | 100% | 100% | 100% |

Capability is flat at 50% through three novel episodes, jumps at four, and is complete at six. Time-to-Capability: median 4 novel episodes, range 4 to 6, reached in 5 of 5 orderings. Gate acceptance rises separately and more slowly, crossing the 0.65 floor between five and six episodes. Certification followed capability rather than substituting for it: no candidate was promoted below 87% decision accuracy, and 100% promotion coincides with 100% capability.

The retention column records a real acquisition-versus-retention interaction, with a caveat. At k = 0, 3, and 4 the plain tree failed the quality constraint on the mixed validation set, the minimal selector escalated to calibrated backends, and those under-covered the known-family probes (coverage 0.40 against an incumbent of 1.00). Every such candidate was already rejected on quality. On quality-feasible candidates at and above the TTC, retention passed in every ordering. The first classification rule counted the infeasible candidates and returned `RETENTION_FAILURE`; it was refined after this sweep to judge retention on quality-feasible candidates only, and both verdicts are stored (`offline_class`, `offline_class_original_rule`). The refined verdict is `CAPABILITY_AND_CERTIFICATION_SUCCEEDED`.

## Online acquisition (4B, interleaved arrival, 69 episodes)

| Rule | Promoted at | TTR (learning + certification) | Candidates rejected before | LLM calls | Tokens | Overall success | Novel success | Known success / fast path after |
|---|---|---|---|---|---|---|---|---|
| recent | 50 | 8 (5 + 3) | 3 | 382 to 148 (-61%) | -58% | 93% (= baseline) | 71% (= baseline) | 100% / 100% |
| family-aware | 64 | 12 (5 + 7) | 2 | 382 to 202 (-47%) | -43% | 93% | 71% | 100% / 100% |

Both runs: 0 invalid LLM actions, 0 invalid reflex actions, 0.0% false fast-path rate. The 71% novel success equals the teacher's own rate on this stream; every failure is a failing-wording episode that the gate routed to the teacher (`out_of_distribution` on every state), and the teacher failed as in the baseline.

Under the recent rule the acquired procedure was exercised in the stream: episodes 58 and 61 were solved with six reflex decisions and zero LLM calls, episodes 51 and 64 with one LLM call on the first state. Learning evidence at promotion was five episodes, matching the offline TTC range. Acquisition debt before the first fast path: 11 episodes, 78 decisions, 23,147 tokens, 37.5 s of LLM latency (this counts the failed-wording episodes too); dividend within the stream: 22 calls and 6,168 tokens over 6 episodes, 27% token recovery.

Under family-aware certification the shadow verdict at episode 50 was `insufficient_evidence` because two known families were absent from the validation split (the atomic-coupling cost recorded in P2.3R-bis); promotion came at 64 and the only remaining novel episode was a failing-wording one. Exposure zero, dividend zero. The first online passes are preserved under `online_first_pass`; the re-run reproduced them exactly and added the frozen evaluation below.

## Price of prudence

The two certification rules produced reflexes with identical frozen behavior, so their difference is entirely when autonomy was granted and what that delay cost: family-aware certification spent 54 more LLM calls and 14,038 more tokens over the stream (202 against 148 calls, 55,043 against 41,005 tokens) and promoted 14 episodes later, in exchange for explicit retention checks on every mature family at each candidate. Retention held at 100% under both rules in this run, so the prudence bought no observed correction here; P2.3R-bis showed the case where it does.

## Frozen post-stream evaluation: eight fresh held-out tasks

Added after observing that the stream ended before the promoted reflex was exercised. Reflex, gate, registry, thresholds, and buffer were frozen (asserted: version and trace count unchanged; no ingest). Eight fresh dependency tasks, two per prompt wording, indices never used in any stream or trace collection, three arms on the same tasks. Both certification rules produced reflexes with identical behavior on all eight.

| Arm | Success | LLM calls | Tokens |
|---|---|---|---|
| LLM-only (teacher) | 6 / 8 | 56 | 16,557 |
| Frozen hybrid (Paradigm) | 6 / 8 | 22 | 7,096 |
| Frozen reflex-only (diagnostic) | 8 / 8 | 0 | 0 |

Four tasks were solved by the hybrid with zero LLM calls, two with a single LLM call on the first state, and two failed. False fast-path failures: 0. The two failures are the failing wording: the gate rejected every state of those episodes as out of distribution (no validated episode of that wording ever entered the buffer), handed them to the teacher, and the teacher failed.

The reflex-only arm solved those two tasks. The compiled reflex generalized the validated six-step policy to held-out instances that its own teacher fails on. It never ingested a failed episode; it applied a policy learned from the other wordings to a wording it had no evidence for. The trust gate, by design, did not extend autonomy to that region.

## Four separate conclusions

- Skill acquisition: yes. Capability went from 50% (no dependency action ever emitted) to 100% on held-out episodes with four to six validated demonstrations, and the promoted reflex executed the new procedure end to end without the teacher.
- Generalization: yes. The frozen reflex succeeded on eight of eight fresh tasks, including a prompt wording on which the teacher fails.
- Trust extension: deliberately conservative. The region where the reflex is capable but no validated evidence exists stayed deliberative, so the hybrid matched the teacher rather than exceeding it.
- System-level autonomy: bounded by the gate, not by the reflex. The hybrid saved 61% of LLM calls on the fresh tasks at equal success; the remaining failures are teacher failures in a region the system correctly declined to automate.

## Teacher size and cost-to-competence

Only the smaller teacher produced enough validated demonstrations to acquire the skill. Cost-to-competence for 4B: 33,128 teacher tokens over 16 novel episodes (12 validated) to reach a reflex that generalizes to eight of eight fresh tasks. The 8B teacher spent 49,011 tokens for four validated episodes and no reflex. This does not say larger teachers are worse in general; it says teacher quality on this procedure, not teacher size, decided acquisition.

## Result classes

- qwen3:4b-instruct: `CAPABILITY_AND_CERTIFICATION_SUCCEEDED` (offline and online). Original offline rule: `RETENTION_FAILURE`, disclosed above.
- qwen3:8b: `INSUFFICIENT_EVIDENCE` (four validated episodes, no k > 0 testable, online not run).

## Limitations

- One family, one seed for the online runs, two teachers from one model line. The offline sweep has five orderings of one trace set per teacher.
- The environment traps a wrong `apply_fix` (only `run_tests` is allowed afterwards), which makes the known-sequence extrapolation fatal rather than merely wasteful; this is inherited from P2.0.
- The reflex's generalization to the failing wording is a single wording with two held-out instances.
- The gate is a Mahalanobis density gate on state features; extending trust into capable-but-unevidenced regions is the open problem this result exposes, and no mechanism for it was tested.
- Family-scoped activation, the refinement identified in P2.3R-bis, was not implemented; its absence explains the family-aware run's late promotion.
