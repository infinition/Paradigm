# D1 cost and diversity pilot: frozen inputs

Recorded before the first provider call. The pilot's protocol is `pilot_prereg.md`; the missions it runs are `missions.json`, which the harness reads so it cannot drift from the pre-registration.

## Frozen mission set

```text
missions.json  sha256  a26e29fbdbd7b5d9e9ae1cfe60b738cdcc0caaf356f5da2c8341909b19d346c1
```

24 missions: 12 code (templates A, B, C over the three bug variants `wrong_constant`, `off_by_one`, `missing_import`), then 12 camera. Order and verbatim prompts are in the file.

Templates B and C carry the same request text on purpose. They differ only in the world: B has an injected bug, C does not. Whether the mission needs an edit therefore has to come from reading the code, never from the phrasing, which is what makes C a structural negative for `file_edit` rather than a differently worded task.

## Versions

```text
paradigm    repo /Users/infinition/Coding/paradigm   branch main
laruche     repo /Users/infinition/Coding/laruche    branch paradigm-integration   commit 1575651
python      3.14.7 (project venv)
provider    deepseek-v4-flash through LaRuche's OpenAI-compatible path
```

The paradigm commit of the launch is the one that carries this file and the trace sink; it is recorded in the outcome section of `pilot_prereg.md` once the attempt starts, together with the attempt id.

## Service parameters for the pilot

```text
paradigm serve
  --certification family_scoped
  --shadow-schedule 1-24:1.0
  --shadow-seed 20260917
  --trace-file <attempt trace>.jsonl
  --attempt-id <attempt id>
  --state-file <fresh per attempt>
```

Rate 1.0 over the whole episode range routes every reflex-eligible decision to the teacher, so no reflex is ever replayed and no promotion has behavioral effect. One service and one fresh state for both domains.

## Circuit breaker

```text
max_model_calls  200
max_tokens       2000000
```

Read from `/v1/telemetry` (`deliberative_decisions`, `llm_tokens_spent`), cumulative across both domains. A model call that produces no tool call is not observed by the bridge, so the breaker fires on a lower bound of the true cost.

## Attempts

Every launch carries an `attempt_id`, written on every trace row. A circuit-breaker stop or any harness incident invalidates the whole attempt: it is archived under its own id and never merged with the restart, which uses a new id, a fresh state and mission 1 again under the same protocol.

## Data hygiene

No image payload is written to the trace: an image is recorded as its count and the verdict derived from it. Camera negative controls run in a workspace confined by the `pre_tool` guard, which refuses any absolute or home path outside it, so no personal file name reaches the record.
