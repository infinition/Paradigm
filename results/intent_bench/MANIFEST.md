# Intent benchmark dataset, version 1

`phrases.jsonl` is the concatenation, in this order, of `phrases_claude.jsonl`, `phrases_chatgpt.jsonl` and `phrases_synthetic_user_style.jsonl`. Its SHA-256 is in `DATASET_SHA256.txt`. Frozen before the first embedding was computed; nothing is added, edited or removed afterwards. A correction would be a version 2 with its own hash and its own results.

Provenance, without ambiguity:

```text
claude-*  generated_by = Claude (this session), written before any score
g*        generated_by = ChatGPT, written before any score
u*        generated_by = ChatGPT simulating the user's writing style (short, oral, with typos and abbreviations); synthetic, not human
```

No sentence in this version was written by a human. The pre-registration's "three sources" are therefore three generators with distinct styles, not two models and a person; the `u*` part must not be described as human data anywhere.

Each group holds one base sentence, its variants (same intent), and hard negatives obtained by minimal transformation (`negation`, `temporal`, `past_question`, `object_change`, `inspection_only`), each labeled with the class it belongs to. Splits are by group only.
