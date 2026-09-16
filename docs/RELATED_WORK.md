# Related work

Paradigm sits near several established research areas. The initial project does not claim that System 2 to System 1 transfer, distillation, model routing, continual learning, or uncertainty gating are individually new.

## System 2 distillation

**Distilling System 2 into System 1** studies self-supervised compilation of higher-quality System 2 outputs into direct generations with lower inference cost.

https://arxiv.org/abs/2407.06023

Paradigm differs in scope by treating compilation as a lifecycle with explicit validation, selective fallback, candidate promotion, drift checks, and multiple possible reflex substrates.

## Procedural memory distillation

**Procedural Memory Distillation: Online Reflection for Self-Improving Language Models** accumulates procedural information across trajectories and distills it into model weights.

https://arxiv.org/abs/2607.01480

This is directly relevant to the question of how repeated experience becomes internalized. Paradigm focuses on separately deployable reflexes and explicit runtime escalation rather than requiring all procedural knowledge to end in one policy.

## Continual learning

Replay, regularization, parameter isolation, adapter methods, and constrained optimization are direct baselines for any continual Paradigm update. EWC, replay, periodic retraining, and low-rank adaptation should be measured before claiming an advantage for drift-bounded updates.

## Selective prediction

Abstention and selective classification are foundational to Paradigm. Coverage-risk curves and calibration should be treated as standard evaluation, not as new metrics.

## Model cascades and routing

Small-to-large cascades already trade cost against confidence. Paradigm extends the question from choosing an existing model to compiling stable behavior into a new specialized reflex and managing its lifecycle.
