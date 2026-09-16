# Core P0.2: trusted compilation controls

## Purpose

This benchmark tests input-space trust gates as a deliberately limited proxy for the trusted-subspace idea. It does not claim to reproduce the adapter-space mechanism studied in z-manifold.

## Results

| Method | ID accept | Off-manifold false accept | Weak-pool valid accept | Near-manifold invalid false accept | OOD AUROC |
|---|---:|---:|---:|---:|---:|
| nearest_distance | 98.3% | 0.0% | 34.4% | 98.2% | 1.000 |
| mahalanobis | 98.7% | 0.0% | 79.0% | 93.7% | 1.000 |
| pca_trusted_subspace | 98.9% | 0.1% | 100.0% | 97.3% | 0.998 |
| nonlinear_autoencoder | 98.2% | 0.0% | 49.6% | 96.8% | 1.000 |
| classifier_confidence | 98.6% | 97.9% | 99.3% | 98.6% | 0.562 |

## Main findings

- Classifier confidence is not an OOD detector here. It accepts 97.9% of explicit off-manifold inputs.
- PCA residual is the cleanest geometric control in this synthetic setup: 98.9% ID retention, 0.1% off-manifold false accepts, and 100.0% acceptance of legitimate weak-pool novelty.
- Nearest-neighbor distance and the nonlinear reconstruction gate reject most off-manifold inputs but also reject too much legitimate weak-pool novelty.
- None of the input-space gates reliably catches the near-manifold invalid control. PCA still accepts 97.3% of it. This is an expected limitation, not a hidden failure.
- A 12% label-poisoning control reduces clean test accuracy from 0.950 to 0.919. Input-space gates are not expected to detect this semantic corruption.

## Consequence for Paradigm

Input geometry can provide a useful fallback signal, but it is not sufficient for trusted compilation. The next trusted-space experiment should move from input novelty toward reflex behavior or update-space structure, which is closer to the research question raised by z-manifold.

Raw data: `core_p02_trust.json`.
