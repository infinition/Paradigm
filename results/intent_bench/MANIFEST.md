# Intent benchmark dataset, version 1

`phrases.jsonl` is the concatenation, in this order, of `phrases_gen_a.jsonl`, `phrases_gen_b.jsonl` and `phrases_synthetic_user_style.jsonl`. Its SHA-256 is in `DATASET_SHA256.txt`. Frozen before the first embedding was computed; nothing is added, edited or removed afterwards. A correction would be a version 2 with its own hash and its own results.

Provenance, without ambiguity:

```text
gen_a-*  generated_by = generator A, written before any score
g*        generated_by = generator B, written before any score
u*        generated_by = generator B simulating the user's writing style (short, oral, with typos and abbreviations); synthetic, not human
```

No sentence in this version was written by a human. The pre-registration's "three sources" are therefore three generators with distinct styles, not two models and a person; the `u*` part must not be described as human data anywhere.

Each group holds one base sentence, its variants (same intent), and hard negatives obtained by minimal transformation (`negation`, `temporal`, `past_question`, `object_change`, `inspection_only`), each labeled with the class it belongs to. Splits are by group only.

## Relabeling note (after all experiments of the line)

The generator labels were replaced by neutral identifiers after the experiments: `gen_a` (assistant of the session), `gen_b` (a second language model), `synthetic_user_style` (the second model simulating the user's style). Sentence texts, order, roles, transformations, intents and tags are byte-for-byte unchanged; only the `source` values, the `id` prefixes and the part file names changed. Hash before relabeling: `b5ce90ed8b40ee79dc61012363dc0207d683829397a196c46b27b252c40b055b`; after: `68cc051d4003da4d237e3407a6ba2c81c73037514d62abe4db3f4545cc96f0b9`. The results files reference the hash before relabeling where they record it; the frozen C6R model records the hash before relabeling as its training-set identity. No result was recomputed.
