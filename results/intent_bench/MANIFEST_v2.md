# Intent benchmark dataset, version 2 (C6R)

`phrases_v2.jsonl` is the concatenation, in this order, of `phrases_v2_claude.jsonl`, `phrases_v2_chatgpt.jsonl` and `phrases_v2_synthetic_user_style.jsonl`. SHA-256 in `DATASET_v2_SHA256.txt`. Written after the C6R pre-registration and after the frozen model (`c6r_frozen_model.sha256`); frozen before any score of the frozen model was computed on it. Nothing is edited afterwards.

Provenance:

```text
c*   generated_by = Claude (this session), written without any v2 score
g*   generated_by = ChatGPT, written without any v2 score
u*   generated_by = ChatGPT simulating the user's writing style; synthetic, not human. The sentences were supplied as a raw list; role, transformation, intent and tags were assigned mechanically by Claude before the freeze, the text is untouched.
```

No sentence in version 2 was written by a human. New in version 2: the `conditional` transformation and the tags `long`, `oral`, `ambiguous`. Sentences tagged `ambiguous` form the DIAGNOSTIC slice of C6R; everything else is the PRIMARY slice.
