# Benchmarks

Paradigm keeps compact benchmark scripts next to raw machine-readable results.

## Core P0

Synthetic routing benchmark with deterministic, noisy, shifted, and repeated-workflow scenarios.

```bash
python benchmarks/core_p0.py --seed 11
```

## Core P0.1

Measured local deliberative surrogate used to replace the original assumed cost ratio.

```bash
python benchmarks/core_p01_measured_deliberation.py --seed 23 --probes 512
```

## Core P0.2

Input-space trusted compilation controls: confidence, nearest distance, Mahalanobis distance, PCA residual, and nonlinear reconstruction.

```bash
python benchmarks/core_p02_trusted_compilation.py --seed 41
```

## Core P0.3

Reflex-level trusted-space benchmark using parameter signatures and behavior signatures on fixed anchors.

```bash
python benchmarks/core_p03_reflex_space.py --seed 1337
```

Each benchmark writes a JSON file under `results/`. Interpret results with the matching `REPORT.md`; synthetic results are not production safety evidence.

## Core P0.4

Multi-signal promotion manifest with explicit quality, calibration, trusted-space, drift, and subgroup checks.

```bash
python benchmarks/core_p04_promotion_manifest.py --seed 1337
```

## Core P0.5

Persistent active/candidate lifecycle with content-addressed versions, multi-window shadow evaluation, delayed regression, and archived rollback.

```bash
python benchmarks/core_p05_persistent_lifecycle.py --seed 2026
```

## Core P1.0

First bounded-plasticity transfer benchmark using the Drift Contract matrix update mechanics.

```bash
python benchmarks/core_p10_bounded_plasticity.py --seed 2026
```


## Core P1.1

Multi-layer continual neural reflex benchmark with SGD, Adam, replay, EWC, periodic retraining, Drift Contract, and a global update-space control.

```bash
python benchmarks/core_p11_multilayer_continual.py
```


## Core P1.2

Family-conditioned trusted plasticity with fixed-anchor behavior deltas, semantic subgroup checks, risk-conditioned epsilon, and replay plus Drift Contract.

```bash
python benchmarks/core_p12_family_trusted_plasticity.py
```


## Core P1.3

Persistent immutable family registry, unknown-family routing, family expansion, manifest controls, and quarantine persistence.

```bash
python benchmarks/core_p13_family_lifecycle.py
```


## Core P1.4

Guarded family evolution with split, ambiguous routing, retire/reactivate, sequential narrow-family growth, and rejection of overlap or broadening proposals.

```bash
python benchmarks/core_p14_family_evolution.py
```

## Agent P2.0

```bash
python benchmarks/core_p20_agent.py
```

P2.0 is the first application vertical. It compiles repeated coding-agent controller decisions while withholding syntax errors as an OOD family. The main metric run uses in-process `unittest` execution so process startup does not dominate policy timing. An optional subprocess runner is also available for integration smoke tests.

### P2.2 real LLM controller

```bash
PARADIGM_LLM_BASE_URL=http://127.0.0.1:11434/v1 \
PARADIGM_LLM_MODEL=qwen3:4b-instruct \
PYTHONPATH=src python benchmarks/core_p22_llm.py
```

The recorded run used a local `qwen3:4b-instruct` model served through Ollama's OpenAI-compatible endpoint. Any OpenAI-compatible endpoint works, including llama.cpp's server or a hosted provider; set `PARADIGM_LLM_BASE_URL` and `PARADIGM_LLM_MODEL` accordingly. Pass `--quick` for a smaller, faster version of the same benchmark. Optional pricing variables: `PARADIGM_LLM_INPUT_COST_PER_M` and `PARADIGM_LLM_OUTPUT_COST_PER_M`.

### P2.3 real LLM online acquisition

```bash
PARADIGM_LLM_BASE_URL=http://127.0.0.1:11434/v1 \
PARADIGM_LLM_MODEL=qwen3:4b-instruct \
PYTHONPATH=src python benchmarks/core_p23_online_llm.py
```

Runs the P2.1 online stream with the configured model as the only teacher, then the same stream LLM-only as the baseline. The full run makes roughly 460 model calls. `--quick` uses the short stream, which in the recorded configuration is too short for the novel family to reach the fast path; use it only as a smoke test.

### P2.3R replication across seeds, models, and arrival orders

```bash
PYTHONPATH=src python benchmarks/core_p23r_replication.py \
  --model "qwen3:4b-instruct|openai|http://127.0.0.1:11435/v1" \
  --model "qwen3:8b|ollama|http://127.0.0.1:11435" \
  --seeds 0 1 2 --arrivals burst interleaved periodic rare
```

Each `--model` spec is `model|api_style|base_url`. `api_style=openai` uses `/v1/chat/completions`. `api_style=ollama` uses Ollama's native `/api/chat` with `think: false`, which is required for hybrid thinking models such as `qwen3:8b` that otherwise spend the whole completion budget on hidden reasoning. The matrix is resumable: existing run directories under `results/core_p23r/runs/` are skipped. The recorded run used an SSH tunnel to a remote RTX 4070 Ti Ollama server on local port 11435.

The single-run P2.2 and P2.3 benchmarks also accept `PARADIGM_LLM_API=ollama` and `PARADIGM_LLM_THINK=1` to select the native API and enable thinking.

### P2.3R-bis family-aware certification with retention probes

```bash
PYTHONPATH=src python benchmarks/core_p23r_bis_certification.py \
  --model "qwen3:4b-instruct|ollama|http://127.0.0.1:11435" \
  --seeds 0 --arrivals burst interleaved periodic rare
```

Runs each stream twice: once with the P2.1 recent-split rule deciding promotion and family-aware certification in shadow, once reversed. Family-aware certification requires every family in the validation split to have at least `--min-family-validation-episodes` episodes (default 1) and pass shadow acceptance on its own, and every mature family to pass coverage, agreement, and no coverage regression against the incumbent on an immutable retention probe set frozen at its first promotion. A negative control candidate that preserves the novel family but relabels one mature family's failed-phase decisions is certified under both rules on the final buffer.

### P2.3T learning-threshold sweep

```bash
PYTHONPATH=src python benchmarks/core_p23t_threshold.py \
  --model "qwen3:4b-instruct|ollama|http://127.0.0.1:11435" \
  --model "qwen3:8b|ollama|http://127.0.0.1:11435" --orderings 5
```

Collects one LLM-only trace set per model (32 known and 12 novel episodes, cached under `results/core_p23t/traces/`), then fits candidates offline with k = 0..8 novel episodes in the train split against a fixed certification set and fixed retention probes, over several novel-episode orderings. Reports raw capability accuracy on held-out novel decisions separately from gate acceptance and promotion under both certification rules.

### P2.4 Type B skill acquisition

```bash
PYTHONPATH=src python benchmarks/core_p24_type_b.py \
  --model "qwen3:4b-instruct|ollama|http://127.0.0.1:11435" \
  --model "qwen3:8b|ollama|http://127.0.0.1:11435" --orderings 5 --online
```

Or, after `pip install -e .`, the same run through the console script, and the recorded result without any model endpoint:

```bash
paradigm benchmark p24 --model "qwen3:4b-instruct|ollama|http://127.0.0.1:11435" --online
paradigm benchmark p24 --from-cache
```

Collects LLM-only traces on 32 known and 16 `dependency_error` episodes per teacher (cached under `results/core_p24/traces/`), runs the k = 0 control and the capability-versus-evidence sweep with a fixed certification set, and, when the offline class is `CAPABILITY_AND_CERTIFICATION_SUCCEEDED`, runs the online loop under both certification rules followed by a frozen post-stream evaluation on 8 fresh dependency tasks. The dependency family uses the extended action vocabulary (`AgentFeatureEncoder(vocabulary="extended")`); the base vocabulary and every earlier protocol are unchanged.
