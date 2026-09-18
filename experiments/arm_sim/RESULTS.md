# B2: the same question on a kinematic arm, with primitives as actions

Purely kinematic, deterministic, no contact, no dynamics, no noise, no language. A four
joint arm with forward kinematics, three objects and two zones on a table, twelve
parameterized primitives as actions, and a deterministic operator as the teacher. The
action carries its target, `approach(red)` and `approach(blue)` being different actions,
because the parameter is exactly what the goal has to determine.

## Design checks, before any training

States for the dataset are drawn independently of the goal, so the arm's pose cannot encode
an intention already under way. Two corrections were made at this stage and are recorded
rather than hidden:

- a hand full half the time made a third of the labels `release`, which a state-only policy
  predicts from the hand alone; holding is now rare;
- random joint angles almost never put the tip near an object, so `grasp` never appeared and
  `align` almost never; half the states now place one object near the tip, that object being
  drawn at random and never from the goal.

After both, on 4,000 sampled states:

```text
the goal changes the expert action     100% of states
three or four distinct actions         100% of states
all twelve primitives present          majority class 22%
```

## Result

37,800 samples, 1,400 scenes, 9 goals, 12 actions, one small head per arm, five seeds.

```text
unseen poses            placements from a lateral band never used in training
  goal only       0.661 +/- 0.000     trivial baseline 0.273
  state only      0.393 +/- 0.007
  goal + state    0.811 +/- 0.011

unseen scenes           whole scenes never seen
  goal only       0.538 +/- 0.000     trivial baseline 0.224
  state only      0.381 +/- 0.002
  goal + state    0.848 +/- 0.021

compositional pairing   object and zone both seen, that pairing never seen together
  goal only       0.129 +/- 0.000     trivial baseline 0.000
  state only      0.192 +/- 0.010
  goal + state    0.621 +/- 0.085
```

The combination wins on all three, by 0.42, 0.47 and 0.43 over the state alone. The result
of the grid world holds when the world becomes a kinematic arm.

Two things differ from the grid world and belong to the reading. The goal alone is no longer
at the trivial baseline: it reaches 0.66 and 0.54, because the dominant primitive is
`approach(the goal's object)`, which the goal determines without any state. And the
compositional split is both the hardest and the least stable, 0.621 with a spread of 0.085
across seeds, an order of magnitude wider than the other splits; it is the split to watch,
not to quote.

## Not attempted, and why

Holding out an object identity. With objects encoded by identity, a held-out object's
dimension is never active in training and the failure would be by construction rather than a
measure of generalization. It needs objects described by attributes, and waits for that.

## What this does not say

Nothing about contact, friction, dynamics, sensor noise, partial observation, continuous
control, images or transfer to hardware. A kinematic world with exact poses is still a
synthetic world, and the numbers here are not robotic performance.
