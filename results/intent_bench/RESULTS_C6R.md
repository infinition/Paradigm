# C6R results: prospective replication on dataset version 2

Frozen model `f499123be5f4b1e2` (trained on v1, threshold 0.6179 by the pre-registered rule), dataset v2 `dc9a31adc710b9a7`, one pass.

## Verdict

**NOT REPLICATED** on the PRIMARY slice: selective accuracy 0.89 (>= 0.99 required), hard-negative false fast paths 0 (0 required), coverage 0.08 (>= 0.15 required).

## Slices

| slice | n | coverage under gate | sel. acc. | hard FFP | FFP all | positives | fired correct / wrong | positive reflex coverage | gate acc. | covered share | accuracy no gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PRIMARY | 243 | 0.08 | 0.89 | 0 | 0 | 30 | 5 / 0 | 0.17 | 0.14 | 0.78 | 0.81 |
| DIAGNOSTIC (ambiguous) | 16 | 0.00 | n/a | 0 | 0 | 5 | 0 / 0 | 0.00 | 0.00 | 0.62 | 0.50 |
| PRIMARY, source chatgpt | 97 | 0.05 | 0.80 | 0 | 0 | 10 | 1 / 0 | 0.10 | 0.12 | 0.78 | 0.85 |
| PRIMARY, source claude | 96 | 0.02 | 0.50 | 0 | 0 | 10 | 0 / 0 | 0.00 | 0.04 | 0.78 | 0.80 |
| PRIMARY, source synthetic_user_style | 50 | 0.24 | 1.00 | 0 | 0 | 10 | 4 / 0 | 0.40 | 0.34 | 0.76 | 0.78 |
| tag oral | 85 | 0.14 | 1.00 | 0 | 0 | 18 | 4 / 0 | 0.22 | 0.21 | 0.78 | 0.81 |
| tag long | 9 | 0.11 | 0.00 | 0 | 0 | 1 | 0 / 0 | 0.00 | 0.22 | 0.33 | 0.67 |

## Hard negatives of the PRIMARY slice, per transformation

| transformation | n | fired | fired as CAPTURE_PERSON | predicted CAPTURE_PERSON without gate | reranker capture yes mean |
|---|---|---|---|---|---|
| negation | 27 | 2 | 0 | 0 | 0.38 |
| temporal | 28 | 0 | 0 | 4 | 0.40 |
| past_question | 26 | 2 | 0 | 0 | 0.39 |
| object_change | 13 | 2 | 0 | 0 | 0.47 |
| inspection_only | 13 | 0 | 0 | 0 | 0.35 |
| conditional | 17 | 0 | 0 | 0 | 0.33 |

Reranker capture yes mean on positives: 0.91.

## Fired sentences that are wrong or predicted CAPTURE_PERSON

| text | true | pred | confidence | source | tags |
|---|---|---|---|---|---|
| Allume la webcam pour vérifier le cadrage, aucune capture. | OPEN_CAMERA_NO_CAPTURE | OTHER | 0.79 | claude |  |
| Utilise pas la webcam pour moi, capture plutôt la fenêtre qui est ouverte à l'écran. | SCREENSHOT | OTHER | 0.77 | chatgpt | long |
| Laisse la fenêtre tranquille et prends-moi plutôt en photo maintenant. | CAPTURE_PERSON | CAPTURE_PERSON | 0.78 | chatgpt |  |
| tu peux me faire une photo la | CAPTURE_PERSON | CAPTURE_PERSON | 0.93 | synthetic_user_style | oral |
| fais une photo vite fait stp | CAPTURE_PERSON | CAPTURE_PERSON | 0.76 | synthetic_user_style | oral |
| prends moi avec la webcam maintenant | CAPTURE_PERSON | CAPTURE_PERSON | 0.94 | synthetic_user_style | oral |
| fait moi une photo avec la cam | CAPTURE_PERSON | CAPTURE_PERSON | 0.83 | synthetic_user_style | oral |

Reference on v1 (in sample, recorded at the freeze): {"threshold": 0.6178501092262769, "selector_coverage": 0.88125, "selector_selective_accuracy": 0.9929078014184397, "selector_feasible": true, "in_sample_fired_share": 0.878125, "in_sample_selective_accuracy_under_gate": 0.9928825622775801, "in_sample_hard_false_fast_paths": 1, "in_sample_positive_reflex_coverage": 0.8913043478260869}
