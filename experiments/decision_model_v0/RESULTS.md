# B0 on the frozen `a3-code-1` trace: does the state carry the procedure

Protocol and verdict thresholds fixed before the run in `results/d1_experience/a3_code_prereg.md`. Dataset: the frozen trace (sha256 in `TRACE_SHA256.txt`), 69 decisions over 12 missions, candidate set of 36 available actions, 5 taken tools, 9 writes kept as learnable. Leave one mission out, five seeds.

```text
trivial baseline, always shell_exec        0.420
uniform over 36 candidates                 0.028

B0-A  goal                    top-1  0.362 +/- 0.013
B0-B  goal + state            top-1  0.754 +/- 0.018
B0-C  goal + action           top-1  0.339 +/- 0.012
B0-D  goal + state + action   top-1  0.652 +/- 0.022
```

## SIGNAL CLAIR, on the narrow question only

`goal + state` beats `goal only` by 0.39, about twenty times the spread of the seeds, and beats the trivial baseline by 0.33. The state carries the procedure: given where the agent is, the next action is largely predictable. That is the core of a `state to action` representation and it holds under a split that never lets a step of a mission appear on both sides.

Three things this does not say, and must not be read as saying.

It says nothing about language. The block carries two distinct goal texts for 69 steps, so `goal only` is near the trivial baseline by construction and the comparison measures the state, not the phrasing. Generalization to new formulations needs goal variation and waits for the camera block.

The action-conditioned formulation does not win, and the comparison does not judge the architecture. It judges this formulation of it. `goal + state + action`, which scores each candidate and takes the argmax, lands at 0.652 against 0.754 for the plain multi-class arm on the same features, a gap well outside the seed spread. On this data, turning the decision into a per-candidate scoring problem costs accuracy rather than adding anything: the same information is spread over 36 rows per decision, of which one is positive, and the head has 69 positives to learn from. The two families also do not see the same training signal: the multi-class arm learns from 69 examples over 5 classes under one loss on the decision, while the scoring arm learns from 2484 rows carrying 69 positives, as 36 independent binary problems per decision. The decision and the metric were equalized, the loss was not. A fair test of the scoring architecture would put a softmax over the candidates of one decision, a listwise loss, instead of independent binary classifications. So the statement this run supports is that this formulation loses on this data, not that conditioning on the candidate is worse in principle. What is established here is that the state pays.

The sample is small. 69 decisions, 12 groups, 5 tools actually used out of 36 candidates. The seed spread is narrow, but it measures initialization, not sampling: a different set of twelve missions could move these numbers more than the seeds do.

## What follows

The narrow result is kept as a narrow result. The full question, whether a representation conditioned on goal, state and action generalizes to new phrasings, needs the camera block, whose preflight is still failing on the machine. No B1, no wiring, no change to the engine, no modification of the frozen missions to manufacture goal variation.
