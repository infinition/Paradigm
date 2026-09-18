# B2.1: objects described by attributes, and generalization to objects never seen

Objects carry a hue, a size and a shape instead of a name, goals name those attributes, and
slot order is shuffled in every scene, so the policy cannot learn a fixed mapping from goal
to slot and has to match the goal's description against what the scene contains.

Sanity check before training, on 3,000 sampled states: the goal changes the expert action on
100% of them, three or four distinct actions each, eleven of twelve primitives present,
majority class 22%.

## Result

12,870 training samples, 2,600 scenes, five seeds.

```text
unseen hue            a band of hue absent from every training scene
  goal only       0.247 +/- 0.009      trivial baseline 0.223
  state only      0.399 +/- 0.011
  goal + state    0.884 +/- 0.003

unseen combination    a shape and size pairing absent from training, both seen apart
  goal only       0.214 +/- 0.014      trivial baseline 0.266
  state only      0.403 +/- 0.028
  goal + state    0.866 +/- 0.004

unseen scene          never seen, attributes in distribution
  goal only       0.220 +/- 0.007      trivial baseline 0.218
  state only      0.373 +/- 0.003
  goal + state    0.864 +/- 0.005
```

## What changed against B2, and why it matters

In B2 the goal alone reached 0.66, because the dominant primitive was an approach to the
goal's own object and the action label named that object. Here the goal alone falls back to
the trivial baseline on all three splits: with slots shuffled and objects described rather
than named, the goal cannot guess which slot to act on without reading the scene. The
comparison is therefore no longer contaminated by that shortcut.

The defensible conclusion: the model learns a compositional correspondence between the
attributes of the goal and the attributes present in the scene, and that correspondence
holds for attribute values and attribute combinations that were never in training. It is not
memorising identities.

The gap is the result to keep:

```text
unseen hue           0.399 -> 0.884
unseen combination   0.403 -> 0.866
unseen scene         0.373 -> 0.864
```

## What this does not say

The attributes are handed to the model exactly, with no noise, no occlusion and no
perception. Nothing here is about images, about estimating a hue or a size from an
observation, about contact or dynamics, or about hardware. Synthetic generalization is not
robotic generalization.
