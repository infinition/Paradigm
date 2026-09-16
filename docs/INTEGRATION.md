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

Default certification is family-aware with retention probes (P2.3R-bis), with the recent-split rule in shadow. The compiler's cadence and thresholds are the P2.x values; nothing is lowered for integration.

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

## Not in this version

Argument synthesis by the reflex, generative content, family-scoped activation, trust extension into capable-but-unevidenced regions, persistent registry integration, and any change to historical benchmarks.
