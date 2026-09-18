# B1: does a procedural policy need the goal, the state, or both

A deterministic grid world, no language, no provider, no physics: an agent, coloured
objects, obstacles, two zones, and a deterministic expert whose tie-break is fixed, so a
label never depends on chance. Goals are symbolic, `PICK(color)` and `PLACE(color, zone)`.

## The design check that came before any training

The benchmark is only worth running if neither arm can win by construction, which is how
the two previous attempts at this question failed: once with a label that followed from
the goal alone, once with a label that followed from the state alone. Measured on 1,931
distinct states before any model was fitted:

```text
the goal changes the expert action            98% of states
three or four distinct actions across goals   79% of states
```

The same goal is also run on every layout, so both halves of the principle hold: one goal
reachable from many states, one state serving many goals.

## Result

15,413 samples, 9 goals, 200 layouts (180 seen, 20 held out), 7 actions, one small MLP per
arm, five seeds, mean and standard deviation.

```text
unseen goal/layout pairs            trivial baseline 0.201
  goal only       0.203 +/- 0.003
  state only      0.537 +/- 0.008
  goal + state    0.770 +/- 0.006

unseen layouts
  goal only       0.177 +/- 0.004
  state only      0.340 +/- 0.021
  goal + state    0.606 +/- 0.007
```

**Signal clair.** B1 supports a goal-conditioned procedural policy: neither the goal nor
the state alone is sufficient, and their combination generalizes substantially better both
to goal and layout pairings never seen together and to layouts never seen at all. The gain
over the state alone is 0.233 and 0.266, about thirty times the spread across seeds.

The goal alone sits at the trivial baseline, so it carries nothing without the state. The
state alone reaches 0.537 while 98% of states admit several actions depending on the goal,
which is the ceiling a state-only policy should be expected to hit.

## What this does not say

Nothing about natural language. The goals here are symbolic, and the question of whether a
phrasing carries procedural intent is untouched by this benchmark. Nothing about
authorization, calibration under distribution shift, or trajectory cost either.
