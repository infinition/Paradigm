# Research map

This file records the direct relationship between Paradigm and the existing Infinition research program. The links are part of the project context and should remain current as the repositories evolve.

## Author index

Fabien Polly arXiv author search:

https://arxiv.org/search/cs?query=Polly%2C+F&searchtype=author&abstracts=show&order=-announced_date_first&size=50

## 1. Constrained adaptation and trusted spaces

Repository:

https://github.com/infinition/z-manifold

Paper:

**Learning Only What Valid Adapters Can Express: Subspace-Constrained Adaptation Against Fine-Tuning Poisoning**

https://arxiv.org/abs/2607.05300

Relevant established results:

- adaptation is restricted to coordinates derived from a trusted adapter pool
- on the evaluated covered tasks, constrained adaptation retains clean behavior under targeted label inversion substantially better than ordinary LoRA
- high adaptation loss acts as an out-of-distribution signal in the tested setup
- the method has an explicit weak-pool boundary
- an adaptive backdoor can partially succeed when the target behavior is already close to behavior represented by the trusted pool

Paradigm use:

- study whether validated reflexes can define a trusted region for later compilation
- use distance or failure-to-fit as a possible fallback signal
- explicitly benchmark weak coverage and near-manifold invalid behavior

What does not transfer automatically:

The paper studies LoRA adapter geometry on language-model adaptation. Paradigm initially operates on feature and policy spaces. Any safety or OOD property must be re-established experimentally.

## 2. Drift-bounded local learning

Repository:

https://github.com/infinition/drift-contract

Public preprint:

**Drift-Bounded Spectral Updates for Deep Local Learning**

https://infinition.github.io/infinition/assets/papers/drift-bounded-spectral-updates.pdf

Status:

Public preprint. arXiv submission pending approval as of September 2026.

Relevant established results:

- Muon-style spectral update geometry is evaluated for auxiliary-head local learning
- the tested spectral setting transfers across the reported width and depth sweeps better than local Adam
- the drift-contract form uses an input-conditioned step rule based on a change budget
- the paper reports both the measured bound behavior and the normalization caveat

Paradigm use:

- test bounded continual adaptation of reflexes
- compare parameter or activation change budgets with external behavioral drift
- explore risk-dependent plasticity budgets only after a basic fixed-budget replication

What does not transfer automatically:

The preprint studies local MLP training on controlled benchmarks. It does not establish a bound on end-to-end agent behavior or policy safety.

## 3. Structure selection

Repository:

https://github.com/infinition/ga-vs-scalarization

Paper:

**When Do Geometric Algebra Layers Beat Scalarization? A Controlled Study on SO(3)-Equivariant Vector Laws**

https://arxiv.org/abs/2607.06634

Relevant established results:

- exact equivariance is valuable in the controlled vector tasks
- scalarization is enough on the tested single-stage laws and is cheaper to train
- geometric algebra is useful on the tested tasks that compose rotations in depth, particularly in low data
- the advantage is not composition in general
- no tested method extrapolates invariant magnitudes on the reported radius and separation shifts

Paradigm use:

- architecture selection should prefer the simplest sufficient reflex
- geometric reflexes should be introduced only for task structures that justify them
- magnitude OOD must remain an explicit fallback condition

## 4. Predictive world state

Repository:

https://github.com/infinition/FluidWorld

Paper:

**FluidWorld: Reaction-Diffusion Dynamics as a Predictive Substrate for World Models**

https://arxiv.org/abs/2603.21315

Relevant established results:

- a reaction-diffusion PDE is used as the predictive substrate
- the model carries persistent spatial state through the BeliefField
- the paper compares the PDE predictor against parameter-matched Transformer and ConvLSTM baselines
- the architecture provides a direct path to persistent predictive state without making attention the only substrate

Repository extensions after the paper also study longer latent rollouts and perturbation recovery. Those repository results should be cited separately from the original paper when used.

Paradigm use:

- supply predictive state to a reflex gate
- test short counterfactual rollouts before action
- treat prediction uncertainty as an additional reason to defer

## 5. Adjacent reaction-diffusion work

FluidVLA:

https://github.com/infinition/FluidVLA

Potential Paradigm use:

- simulated robotics integration
- compact real-time action policies
- comparison between direct VLA action generation and compiled reflexes

FluidLM:

https://github.com/infinition/FluidLM

Potential Paradigm use:

- study whether alternative low-cost sequence substrates change the economics of deliberation versus reflex execution

These adjacent repositories are not required for Paradigm Core.

## Research boundary

Paradigm combines questions from these projects, not their conclusions.

The main new empirical object is the full lifecycle:

```text
validated experience
      -> pattern selection
      -> reflex compilation
      -> calibration and OOD gating
      -> candidate evaluation
      -> bounded promotion
      -> runtime monitoring
      -> fallback and recompilation
```

Each imported mechanism must be evaluated against simpler controls before it becomes part of the core claim.
