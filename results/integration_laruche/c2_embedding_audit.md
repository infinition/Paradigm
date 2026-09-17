# C2 audit: the LaRuche memory embedding as goal representation (offline)

Encoder latency: median 11.0 ms, max 55.5 ms per sentence. Leave-one-phrasing-out over the 9 C1 phrasings (48 missions); unseen phrasings scored by models trained on all 48.

## Target T2 (intent under the outcome contract: capture / no capture), leave-one-phrasing-out

| representation | model | coverage | sel. acc. | ECE | false fast paths (C1 negatives) | recall unseen-wording positives | gate acc. pos / neg | unseen 7: pos recall | unseen 7: neg fallback | unseen 7: false fast paths |
|---|---|---|---|---|---|---|---|---|---|---|
| A_lexical | prototype | 0.08 | 0.00 | 0.34 | 4 | 0.00 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| A_lexical | knn3 | 1.00 | 0.25 | 0.75 | 16 | 0.38 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| A_lexical | logreg | 0.08 | 0.00 | 0.41 | 4 | 0.00 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| A_lexical | tree | 1.00 | 0.33 | 0.67 | 8 | 0.25 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| B_embedding | prototype | 0.08 | 0.00 | 0.20 | 4 | 0.00 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| B_embedding | knn3 | 1.00 | 0.58 | 0.42 | 16 | 0.88 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| B_embedding | logreg | 0.08 | 0.00 | 0.38 | 4 | 0.00 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| B_embedding | tree | 1.00 | 0.58 | 0.42 | 8 | 0.62 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| B'_embedding_classification_prefix | prototype | 0.08 | 0.00 | 0.20 | 4 | 0.00 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| B'_embedding_classification_prefix | knn3 | 1.00 | 0.58 | 0.42 | 16 | 0.88 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| B'_embedding_classification_prefix | logreg | 0.08 | 0.00 | 0.50 | 4 | 0.00 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| B'_embedding_classification_prefix | tree | 1.00 | 0.58 | 0.42 | 8 | 0.62 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| C_lexical+embedding | prototype | 0.08 | 0.00 | 0.35 | 4 | 0.00 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| C_lexical+embedding | knn3 | 1.00 | 0.50 | 0.50 | 16 | 0.75 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| C_lexical+embedding | logreg | 0.08 | 0.00 | 0.33 | 4 | 0.00 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |
| C_lexical+embedding | tree | 1.00 | 0.50 | 0.50 | 16 | 0.75 | 0.00 / 0.00 | 0.00 | 1.00 | 0 |

## Target T1 (teacher's literal first action), leave-one-phrasing-out

| representation | model | coverage | sel. acc. | ECE | feasible |
|---|---|---|---|---|---|
| A_lexical | prototype | 0.08 | 0.50 | 0.06 | False |
| A_lexical | knn3 | 0.67 | 0.38 | 0.53 | False |
| A_lexical | logreg | 0.08 | 0.50 | 0.20 | False |
| A_lexical | tree | 0.33 | 0.25 | 0.36 | False |
| B_embedding | prototype | 0.08 | 0.50 | 0.07 | False |
| B_embedding | knn3 | 0.83 | 0.40 | 0.53 | False |
| B_embedding | logreg | 0.08 | 0.50 | 0.11 | False |
| B_embedding | tree | 0.67 | 0.38 | 0.51 | False |
| B'_embedding_classification_prefix | prototype | 0.08 | 0.50 | 0.09 | False |
| B'_embedding_classification_prefix | knn3 | 0.92 | 0.36 | 0.61 | False |
| B'_embedding_classification_prefix | logreg | 0.08 | 0.50 | 0.19 | False |
| B'_embedding_classification_prefix | tree | 0.67 | 0.06 | 0.65 | False |
| C_lexical+embedding | prototype | 0.08 | 0.50 | 0.08 | False |
| C_lexical+embedding | knn3 | 0.42 | 0.25 | 0.45 | False |
| C_lexical+embedding | logreg | 0.08 | 0.50 | 0.22 | False |
| C_lexical+embedding | tree | 0.42 | 0.60 | 0.30 | False |

## Unseen phrasings, T2, logistic regression on each representation

| id | text | label | A_lexical | B_embedding | B'_embedding_classification_prefix | C_lexical+embedding |
|---|---|---|---|---|---|---|
| U+1 | Fais-moi un portrait. | capture | no_capture 0.75 OOD | capture 0.71 OOD | capture 0.70 OOD | no_capture 0.65 OOD |
| U+2 | Capture une image de moi avec la caméra. | capture | capture 0.76 OOD | capture 0.61 OOD | capture 0.62 OOD | capture 0.72 OOD |
| U+3 | Je veux une photo de moi maintenant. | capture | capture 0.87 covered OOD | capture 0.74 OOD | capture 0.72 OOD | capture 0.88 covered OOD |
| U-1 | Allume la caméra sans capturer. | no_capture | no_capture 0.64 OOD | no_capture 0.56 OOD | capture 0.52 OOD | no_capture 0.73 OOD |
| U-2 | Liste les caméras disponibles. | no_capture | capture 0.68 OOD | no_capture 0.51 OOD | capture 0.55 OOD | capture 0.56 OOD |
| U-3 | Combien de photos ai-je prises hier ? | no_capture | no_capture 0.57 OOD | capture 0.67 OOD | capture 0.66 OOD | no_capture 0.53 OOD |
| U-4 | Vérifie que la webcam fonctionne, sans photo. | no_capture | no_capture 0.74 OOD | capture 0.57 OOD | capture 0.59 OOD | no_capture 0.74 OOD |

## Teacher's first action at start per phrasing (T1 evidence)

| id | text | first actions over its missions |
|---|---|---|
| N1 | Fais une capture d'écran. | other 4 |
| N2 | Trouve mes dernières photos. | other 4 |
| N3 | Est-ce que j'ai une webcam ? | list 4 |
| N4 | Ouvre la caméra sans prendre de photo. | list 4 |
| P1 | Prends-moi en photo. | capture 5, list 3 |
| P2 | Fais une photo de moi. | list 4, capture 4 |
| P3 | Tu peux me prendre en photo ? | capture 5, list 2, capture_index0 1 |
| P4 | Prends une photo avec la webcam. | list 2, capture 2 |
| P5 | Photographie-moi. | capture 2, list 2 |
