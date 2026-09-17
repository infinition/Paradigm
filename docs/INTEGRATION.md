# Integration surface

Paradigm sits inside an application's decision loop. The application supplies a structured state, the actions available in that state, and a verified outcome after execution. Paradigm owns acquisition, compilation, certification, retention, promotion, and routing. LaRuche is the first client; the core never imports application code.

```text
application state
      |
paradigm.decide(state)
      |
+-----------------------------+
| trusted reflex available    | -> ReflexDecision(action, ...)
| not sufficiently trusted    | -> DeliberateDecision(reason, ...)
+-----------------------------+
      |
execute (reflex action, or the application's own model)
      |
verify outcome
      |
paradigm.observe(state, action, verified_outcome, source)
      |
paradigm.close_episode(verified_outcome)
```

## Two invariants

1. `observe` receives a verified outcome (`SUCCESS`, `FAILURE`, `UNKNOWN`). Only `SUCCESS` steps inside `SUCCESS` episodes become teacher evidence. An absent error, a timeout, or a missing verifier is `UNKNOWN` and is never positive evidence. Reflex-sourced steps are never teacher labels.
2. `decide` may return `DeliberateDecision` for a state the reflex could handle. The decision carries `proposed_action` and `reflex_confidence` for audit and shadow evaluation, but Paradigm never executes them. Capability is not authorization. This is the P2.4 result made operational: the compiled reflex solved eight of eight held-out tasks while the gate, lacking validated evidence on two of them, kept those deliberative.

Both come from the P2.1 to P2.4 experiments and are enforced by the engine, not by the adapter.

## State contract

`paradigm.integration.ParadigmState`:

| Field | Meaning |
|---|---|
| `domain` | application identifier (`laruche`, `coding`, `robot`) |
| `phase` | coarse position in the workflow (`start`, `after_tool`, `testing`) |
| `available_actions` | actions the application would accept now |
| `goal` | short goal text; hashed, never fed as prose |
| `last_action`, `last_outcome`, `recent_actions`, `step` | structural history |
| `features` | small structured values: booleans, numbers, short strings |
| `risk` | `low`, `medium`, `high`; the reflex policy caps what a reflex may act on |
| `family_hint` | behavior family assigned by the adapter; trust is per family |
| `context_refs` | opaque references (session id, workspace), never encoded |

`GenericStateEncoder` turns it into a fixed-width vector by feature hashing. It contains nothing about which model produced past decisions.

## Decide

`Paradigm.decide(state, actions=None)` returns one of two typed results.

`ReflexDecision`: `action`, `arguments` (template, when the adapter registered one), `confidence`, `family`, `reflex_id` (active version), `latency_ms`, `source="reflex"`.

`DeliberateDecision`: `reason`, `family`, `trust_status`, `reflex_confidence`, `proposed_action`, `latency_ms`, `source="deliberative"`.

A reflex acts only when every check agrees, in this order: an active reflex exists; the state passes the OOD gate; confidence reaches the certified threshold; the proposed action is available; the state's family is `ACTIVE`; the action is inside the `ReflexPolicy` whitelist; the state's risk is within the policy. Each failing check is a distinct `reason`. `Paradigm.explain(state)` returns the same analysis without logging or acting.

## Observe and close

`Paradigm.observe(state, action, VerifiedOutcome, source, metadata)` records one executed step. `metadata` may carry `llm_tokens` and `llm_latency_ms` for deliberative steps, which feed the telemetry estimates. `Paradigm.close_episode(VerifiedOutcome)` ends the episode; a `SUCCESS` episode is handed to `OnlineReflexCompiler.ingest`, which is the same acquisition, certification, retention-probe, and atomic-promotion path measured in P2.1 through P2.4. `FAILURE` and `UNKNOWN` episodes are counted and dropped.

Default certification is family-aware with retention probes (P2.3R-bis), with the recent-split rule in shadow. `--certification family_scoped` selects family-scoped activation (below); `--shadow-schedule` and `--equivalence laruche` are the instruments described in the record section. The compiler's cadence and thresholds are the P2.x values; nothing is lowered for integration.

## Family-scoped activation

`paradigm.family_scoped` certifies one compiled artifact per behavior family instead of as a whole. The candidate is a plain tree fitted on all validated traces. Each family seen in the split is then judged on its own held-out traces with the unchanged criteria: the selector's confidence threshold rule (selective accuracy within 0.01 of the teacher, coverage at least 0.55), ECE at most 0.10, shadow OOD acceptance at least 0.65, and, for a family with frozen probes, probe coverage at least 0.65, probe agreement at least 0.95 and no coverage regression beyond 0.10 against the incumbent. A family with no held-out trace is `insufficient`. Families that pass become `active` with their own confidence threshold; the others stay deliberative. A replacement artifact is adopted only if it activates at least one family and every currently active family re-certifies; otherwise the incumbent stays. `decide` uses the per-family threshold, and the trust manifest lists the active families.

## Trust manifest

`Paradigm.trust_manifest()` derives per-family authorization from the compiler lifecycle: `active` (the family has frozen retention probes, meaning it was represented in a promoted candidate), `candidate` (validated episodes in the buffer, not yet promoted), `deliberative` (never validated), `no_reflex` (nothing promoted yet). This is the per-family authorization map identified in P2.3R-bis; connecting it to the persistent P1.3 family registry is future work, and no second trust system was added.

## Telemetry

`Paradigm.telemetry()` exposes: reflex decisions, deliberative decisions, LLM calls avoided, tokens spent deliberating, estimated tokens and latency avoided (reflex decisions times the mean deliberative cost observed), active reflex version, active / candidate / deliberative-only families, the trust manifest, lifecycle counters, and buffer statistics. `Paradigm.decision_log()` returns per-decision rows: `source`, `family`, `trust_status`, `confidence`, `reason`, `reflex_id`, `decision_latency_ms`, `outcome`, `llm_tokens`, `llm_latency_ms`. That is enough for a line such as `run_tests  PARADIGM  0.4 ms` and for aggregate counters.

## Service

`paradigm serve --port 8765 --state-file state.pkl` exposes the engine as JSON over HTTP on localhost:

| Route | Purpose |
|---|---|
| `POST /v1/decide`, `POST /v1/observe`, `POST /v1/episode/close`, `POST /v1/explain` | generic contract |
| `POST /v1/laruche/decide`, `POST /v1/laruche/observe`, `POST /v1/laruche/close` | LaRuche wire shapes |
| `GET /v1/telemetry`, `GET /v1/manifest`, `GET /v1/log?last=N`, `GET /v1/health` | inspection |

The state file persists the compiler (reflex artifacts, probes, buffer) and the action templates after each closed episode.

## LaRuche adapter

Interception point in LaRuche (Rust, branch `paradigm-integration`): `laruche-essaim/src/paradigm_pont.rs` wraps the engine traits `Fournisseur` and `Outils` of `laruche-butinage`. `FournisseurParadigm::repondre` asks the service before each model call and, on a reflex decision, returns a `ReponseModele` with that single `Appel` without calling the model. `OutilsParadigm::executer` runs the tool unchanged and reports the `ResultatOutil` (`ok` is SUCCESS, `incertain` is UNKNOWN, otherwise FAILURE). `executer_avec_bilan` wires both only when `LARUCHE_PARADIGM_URL` is set and closes the episode from `Bilan.fin` (`Accomplie` is SUCCESS; `Erreur`, `Plafond`, `BoucleSterile`, `Budget`, `Escalade` are FAILURE; the rest UNKNOWN). Transport errors fail open to the model.

Scope of the first integration (Level 2): a reflex may replay a whitelisted tool with the exact argument template it was validated with. Whitelist: `file_read`, `file_list`, `file_search`, `lsp`, `tool_search`, `task_complete`, and `shell_exec` only for commands matching a small allowlist (`pytest`, `cargo test|check|build`, `npm test`, `go test`). `file_write`, `file_edit`, `git_push`, `delegate`, `computer`, `browser`, any other shell command, and any call whose arguments were never validated stay deliberative. Control calls the engine intercepts before `Outils` (`mission_accomplie`, `plan`, `clarify`) are never observed, so finishing a mission always deliberates in this version.

Behavior family in LaRuche: `laruche:<last tool>:<last outcome>:<output kind>`, derived from what just happened and how it went, not from the goal text.

## Smoke test

`laruche-essaim/tests/paradigm_smoke.rs` runs the real `butiner` engine through the real decorators against a live `paradigm serve`, with a fixture provider standing in for the model (three-step procedure) and mocked tools. Recorded run: 24 missions; fixture model calls per mission `3` for missions 1 to 20, `1` for missions 21 to 24 after promotion at mission 20; 8 reflex decisions, 0 failures, 0 false fast paths. Skipped unless `PARADIGM_SMOKE_URL` is set.

## Real-loop record: LaRuche with DeepSeek

`laruche-essaim/examples/paradigm_demo.rs` runs real LaRuche missions (real provider, real builtin tools) with the bridge on: a fixed project directory reset before each mission with one of three bugs in `calc.py`, the model asked to run the tests, fix the code, and finish. Provider `deepseek-v4-flash` through LaRuche's OpenAI-compatible path. Each mission is verified independently by `pytest` and the Paradigm episode is closed from that verification (`LARUCHE_PARADIGM_CLOSE=external`), not from the model's own claim of completion. Containment: LaRuche allows any shell command inside the working directory without asking, so the demo registers a blocking `pre_tool` hook that refuses installs, links, copies, moves, deletions, file redirections, and paths outside the workspace, and puts a `python`/`pytest` on PATH so the model has no reason to install anything. An earlier attempt without those measures saw the model install `pytest` into the user site and create `/opt/homebrew/bin/python`; both were reverted, and the guard exists because of it.

Logs and the final engine state are under `results/integration_laruche/`.

Run 9A, missions 1 to 20, family-aware certification primary, recent rule in shadow: 20 of 20 missions verified. Candidates at 8, 12, 16 rejected for insufficient traces (each mission yields about 2.5 reflex-capable validated decisions). At 20 the first real candidate, a plain tree on 34 traces with selective accuracy 1.0 and ECE 0.032, was rejected by family-aware certification because one one-episode family (`file_write:success`) failed its own acceptance while four other rare families had insufficient evidence; the recent rule in shadow would have promoted it (overall acceptance 0.89).

Run 9B, missions 21 to 32, the same 20 validated episodes reloaded with the recent rule primary and family-aware in shadow: 12 of 12 verified. Candidates at 24, 28, 32 rejected by both rules on quality: coverage 0.56, 0.43, 0.35 and ECE 0.235, 0.272, 0.236 against floors of 0.55 and 0.10.

Result: 32 of 32 missions verified, 0 unsafe actions executed after containment, 0 false fast paths, 0 reflex decisions, 0 LLM calls avoided. No reflex was promoted in the real loop under the current protocol.

Why, from the buffer (79 validated decisions in 9 families): the family "start" led to `python -m pytest -q` 16 times out of 16, and "after file_edit" led to it 27 times out of 30; every other family is small and inconsistent, because the model reads files through different tools and phrasings (`file_read`, `read_extract`, `cat`, batched or not). The whole-candidate certification, which judges one tree on the whole recent split, fails on calibration because of the inconsistent families and therefore never activates the two consistent ones. This is the family-scoped activation refinement identified in P2.3R-bis, observed here at the quality level rather than the trust level.

Two adapter rules came out of this run and are part of the recorded protocol: equivalent shell phrasings canonicalize (a `cd <workspace> &&` prefix and output decorations such as `2>&1`, `| tail -N`, `; echo ...` are dropped, and the reflex replays the canonical form); and an allowlisted test command is verified by its report, not its exit code, since a test run that reports failures executed correctly.

### Offline audit of family-scoped activation on the frozen record

Pre-registered rule: family-scoped activation activates only families that independently satisfy the existing quality, trust and retention criteria; no threshold is changed. Prediction recorded before scoring: `start` and `file_edit:success` pass, the post-failure read families do not. Result on the 32-mission buffer (`results/integration_laruche/family_audit.md`): `laruche:start:none:none` passes every criterion (100% coverage, 100% selective accuracy, ECE 0.000, acceptance 1.00); `laruche:file_edit:success:other` is right whenever it is confident (100% selective accuracy at 71% coverage) but fails the ECE floor (0.179) on 7 held-out traces because 3 of its 30 occurrences were a re-read before re-running the tests; every other family is rejected or has no held-out evidence. Half of the prediction held. The floor was left as is.

### Run 11: one fresh live run with family-scoped activation

Fresh state, same workspace, model, guard, canonicalization and thresholds, family-scoped certification from mission 1, 24 missions (`results/integration_laruche/run11_family_scoped.md` has the full record).

24 of 24 missions verified, 0 unsafe actions, 0 false fast paths. Candidates at 8 and 12 had too few traces. At 16, the tree judged as a whole failed calibration again (ECE 0.195), while `laruche:start:none:none` (3 train, 2 held-out) and `laruche:file_edit:success:other` (12 train, 4 held-out) each passed with ECE 0.000 and acceptance 1.00, and were activated as version 1. From mission 17 the routing is the one predicted: `[PARADIGM] shell_exec` replaying `python -m pytest -q` at the start of the mission, `[LLM]` for the read and the edit, `[PARADIGM] shell_exec` after the edit, then the model finishes. 15 reflex decisions in 8 missions; the 7 post-edit replays verified SUCCESS by their test report, the 8 start-of-mission replays UNKNOWN because LaRuche's shell tool returns only the exit code message for a failing command (the model's own identical call gets the same). Missions 17 to 23: 4.3 model calls, 37k tokens and 7.2 s per mission against 5.9 calls, 56k tokens and 10.9 s for missions 1 to 16. Mission 24 was an outlier (18 calls, 74.5 s of self-verification by the model after the same start replay; still verified) and is included in the record. The candidates at 20 and 24 were rejected and v1 kept: `start` had no new deliberative held-out trace (the reflex now serves it), and `file_edit` missed its probe agreement floor at 20 (15 of 16) and had its single new held-out trace outside the gate at 24 while passing 16 of 16 probes.

Two consequences are recorded rather than fixed. The start family activated on 5 validated traces because the pre-registered criteria have no per-family minimum count and the failing first test run is unverifiable through LaRuche's result. And once a family is served by the reflex, it stops producing deliberative held-out evidence, so under the rule as implemented it is `insufficient` at every later compile point and blocks any replacement; the frozen probes are the evidence meant for that case, and re-certifying an active family on them when it has no new held-out traces is the next refinement.

### After run 11: fresh evidence, teacher disagreement, and behavioral equivalence

Every step below was pre-registered and run offline on frozen records before anything went live; the pre-registration files under `results/integration_laruche/` carry their outcomes, including the ones that did not hold.

Probe-only re-certification (`probe_recertification_prereg.md`). The pre-registered probe-only re-certification rule was not supported as written because a single fresh held-out trace still dominated an otherwise passing probe set: at run 11 point 24, `file_edit` passed 16 of 16 probes but its one new held-out trace was outside the candidate gate, and the family was judged on that trace. A subsequent sparse-evidence sensitivity study (`sparse_heldout_prereg.md`) changed evidence routing across `m` in {1, 2, 3, 5, 8} but did not change candidate-level adoption decisions on the available records; no `m` was selected.

Shadow sampling, run 12 (`shadow_sampling_prereg.md`, `run12_shadow_report.md`, `run12_shadow_ledger.md`). To restore fresh evidence on active families, a pre-declared, deterministic fraction of reflex-eligible decisions is routed to the teacher with reason `shadow_sample` (`serve --shadow-schedule`). 36 of 36 missions verified; fresh counts of 2 to 7 per active family were obtained; every pre-registered `m` still produced the same candidate decisions; 53 shadow-sample calls against 17 reflex decisions, a net cost, so the mechanism is an experimental instrument, not a product setting as scheduled. The ledger of all 53 samples separates teacher disagreement, reflex invalidity and mission failure: only the first occurred. Two gate-covered disagreements were of different kinds: at point 25 the candidate regressed where the incumbent agreed with the teacher; at point 33 the teacher ran `python -m pytest -q | cat` where the incumbent and the candidate both replay `python -m pytest -q`.

Triadic veto (`triadic_veto_prereg.md`, `triadic_veto_audit.md`). Classifying each covered disagreement against the incumbent (candidate regression, alternative trajectory, ambiguous) fixes the veto: point 25 stays vetoed, point 33 is an alternative trajectory. It does not fix the held-out branch, where the alternative teacher action is still counted as a classification error (selective accuracy 0.857, ECE 0.143). The problem is the supervision target, not the veto.

Behavioral equivalence (`behavioral_equivalence_prereg.md`, `behavioral_equivalence_audit.md`). `paradigm.equivalence.EquivalenceContract` lets an adapter declare equivalence classes derived from rules it already enforces; identity is the default. Per-family threshold selection, ECE, probe agreement and the fresh-disagreement classification are computed in class space, where the confidence of a class is the sum of its members' probabilities; literal teacher agreement is kept alongside as a diagnostic. The contract is materialized per certification as the explicit mapping of the keys in play, versioned and hashed, and stored in the certification record. A retention probe set records the contract it was frozen under and is scored under it; it may be rescored diagnostically under the current contract, and its historical verdict is never rewritten. The first LaRuche contract, `laruche-equivalence-1`, has one class, TEST_EXECUTION: an allowlisted test command whose output is verified by its report and which writes nothing (the guard's read-only rule); `file_read`, `read_extract` and `file_list` are not grouped. On the frozen run 12 record it turns point 33 from 0.857 literal agreement to 1.000 behavioral agreement and lets `file_edit` pass held-out quality and calibration, while point 25 (a `file_read` where the teacher ran the tests) stays rejected; run 11 replays identically; in the runs 9A/9B record one probe-set failure at 18 of 19 turns out to have been the same phrasing variant, with no adoption decision changed.

Run 12b (`live_equivalence_prereg.md`, `run12b_equivalence_report.md`). `serve --equivalence laruche` activates the contract from mission 1; version and digest are in the telemetry and in every certification record. A first attempt was invalidated for certification analysis by a persistence failure (a non-picklable callback; its log and telemetry are kept as `run12b_attempt1_*`), and the retry ran the same protocol after a serialization-only fix. 24 of 24 verified, 0 unsafe actions; the live certification is reproduced by the replay. At compile point 24, the version 2 promotion activates `file_edit` and `tests_failed` with the contract and `tests_failed` only without it, because the held-out split of `file_edit` held 4 canonical test runs and one `| cat` variant (literal 0.800, behavioral 1.000). This is the first live certification decision whose authorized family set depends on behavioral equivalence. No family without a TEST_EXECUTION action changed. Live discrimination of a procedurally distinct regression under the same contract did not occur in this run and remains shown offline only.

## Not in this version

Argument synthesis by the reflex, generative content, a per-family minimum evidence count, a selected minimum fresh support, equivalence classes beyond TEST_EXECUTION, canonicalization of `| cat`, trust extension into capable-but-unevidenced regions, persistent registry integration, and any change to historical benchmarks.
