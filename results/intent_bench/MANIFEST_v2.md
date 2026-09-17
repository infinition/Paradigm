# Intent benchmark dataset, version 2 (C6R)

`phrases_v2.jsonl` is the concatenation, in this order, of `phrases_v2_gen_a.jsonl`, `phrases_v2_gen_b.jsonl` and `phrases_v2_synthetic_user_style.jsonl`. SHA-256 in `DATASET_v2_SHA256.txt`. Written after the C6R pre-registration and after the frozen model (`c6r_frozen_model.sha256`); frozen before any score of the frozen model was computed on it. Nothing is edited afterwards.

Provenance:

```text
c*   generated_by = generator A, written without any v2 score
g*   generated_by = generator B, written without any v2 score
u*   generated_by = generator B simulating the user's writing style; synthetic, not human. The sentences were supplied as a raw list; role, transformation, intent and tags were assigned mechanically by generator A before the freeze, the text is untouched.
```

No sentence in version 2 was written by a human. New in version 2: the `conditional` transformation and the tags `long`, `oral`, `ambiguous`. Sentences tagged `ambiguous` form the DIAGNOSTIC slice of C6R; everything else is the PRIMARY slice.

## Relabeling note (after all experiments of the line)

Same relabeling as version 1: `gen_a`, `gen_b`, `synthetic_user_style`; texts and labels unchanged. Hash before relabeling: `dc9a31adc710b9a70fb3d3afca7f63ea76f85bacab080d730dec569a456588f3`; after: `3fe4c90ec5c108a83970a561492c1f146f42e6483a30aca9c566e464fcab26e2`. No result was recomputed.
