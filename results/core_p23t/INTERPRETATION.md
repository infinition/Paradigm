# P2.3T Interpretation

One LLM-only trace set per model (32 known and 12 novel episodes, 220 model calls each, native transport, thinking disabled) was collected once and cached. Candidates were then fitted offline with k = 0 to 8 novel-family episodes in the train split, against a certification set fixed for every k (4 held-out novel episodes, 4 held-out known episodes) and fixed retention probes (4 further known episodes), over 5 shuffled novel-episode orderings. Numbers are from `core_p23t_threshold.json`.

## Capability precedes trust

Capability accuracy, the candidate's raw agreement with the teacher on the 20 held-out novel decisions independent of any gate, is 100% at k = 0 for both models and stays at 100% for every k and every ordering. A tree fitted only on the four known families already produces the correct action on every `syntax_error` decision. Nothing about the required behavior was learned from novel episodes.

Gate acceptance, the shadow OOD acceptance of those same decisions, rises with k: 0.00 (k = 0), 0.12 (1), 0.35 (2), 0.50 (3), 0.56 (4), 0.78 (5), 0.81 (6), 0.92 (7), 0.94 (8). What novel evidence buys is support in the gate's train distribution, so that the novel state region stops being flagged as out of distribution.

This fixes the reading of P2.3 and P2.3R as coverage acquisition (Type A): the reflex was capable before it was trusted, and the online loop expanded the trust boundary. It is the intended behavior of a system that must keep unknown regions on the deliberative path until validated, but it is not acquisition of a new action policy (Type B).

## Teacher independence, explained

The two models' tables are identical to two decimals. Capability depends on the teacher's labels, and both teachers emit the same policy on this family, so capability is identical. Gate acceptance depends only on state features, which do not involve the teacher at all, so the acceptance curve is identical by construction. Under this vertical, teacher size cannot influence acquisition dynamics unless the teachers disagree on the policy.

## The certification boundary is protocol-specific

In the live P2.3R runs every candidate with four novel training episodes reached acceptance 0.93 to 0.95, and none with three exceeded 0.64. Here, with the same gate but a fixed known train set of 24 episodes, four novel episodes reach only 0.56 on average and the 0.65 floor is crossed reliably at five to seven. The larger known train set tightens the gate's covariance estimate, so the same amount of novel evidence covers less of the novel region. The boundary observed in P2.3R therefore describes that protocol and cadence, not a fixed number of episodes.

## Pooled versus per-family certification, again

With the fixed mixed certification set, the pooled recent rule promotes at k = 2 in 60% of orderings and at k = 4 in all, while novel acceptance on its own is 0.35 to 0.56, because the 20 known validation decisions are accepted and lift the pooled figure over the floor. The per-family rule waits until the novel family passes on its own (k = 7 to 8 for 100%). In the live P2.3R runs the self-focusing buffer made the validation split almost entirely novel, which hid this difference. At runtime the pooled rule's early promotion does not create false fast paths, since the gate still rejects most novel states; it creates thin coverage.

## What this does not establish

No learning threshold was measured, because capability never had to rise. The threshold sweep design is ready for a family whose required action sequence includes decisions the known families never use, where k = 0 capability should be low and capability itself must rise with k before trust follows. That is the next experiment.
