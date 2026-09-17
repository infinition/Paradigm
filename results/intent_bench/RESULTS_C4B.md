# C4b results: extractor version 2 (last experiment of the line)

## Extractor outputs, version 1 dataset then version 2 dataset (v1 extractor -> v2 extractor)

### dataset v1

| sentences | n | categories v1 | categories v2 | actionable v1 -> v2 |
|---|---|---|---|---|
| base_or_variant | 135 | CONDITIONAL 6, FUTURE 1, NOW 8, PAST_REFERENCE 3, UNSPECIFIED 117 | CONDITIONAL 1, FUTURE 1, NOW 9, PAST_REFERENCE 3, UNSPECIFIED 121 | 118 -> 123 |
| negation | 37 | NOW 1, UNSPECIFIED 36 | NOW 1, UNSPECIFIED 36 | 2 -> 2 |
| temporal | 37 | FUTURE 35, UNSPECIFIED 2 | FUTURE 37 | 2 -> 0 |
| past_question | 37 | PAST_REFERENCE 37 | PAST_REFERENCE 37 | 0 -> 0 |
| object_change | 37 | NOW 5, PAST_REFERENCE 1, UNSPECIFIED 31 | NOW 5, PAST_REFERENCE 1, UNSPECIFIED 31 | 34 -> 34 |
| inspection_only | 37 | CONDITIONAL 16, UNSPECIFIED 21 | UNSPECIFIED 37 | 20 -> 35 |
| conditional | 0 |  |  | 0 -> 0 |

Sentences whose category or actionability changed: 23

| text | class | transformation | v1 | v2 | actionable v1 -> v2 |
|---|---|---|---|---|---|
| Regarde si tu peux me prendre en photo, sans le faire. | CHECK_CAMERA | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| Fais une photo de moi avec la webcam quand je te le dirai. | OTHER | temporal | UNSPECIFIED | FUTURE | True -> False |
| Dis-moi juste si la webcam répond. | CHECK_CAMERA | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| Indique-moi seulement si la caméra est détectée. | CHECK_CAMERA | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| Regarde si la caméra s'ouvre, sans l'ouvrir vraiment. | CHECK_CAMERA | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| Dis-moi si la webcam renvoie une image, sans me la montrer. | CHECK_CAMERA | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| Ouvre mes photos quand j'aurai fini. | OTHER | temporal | UNSPECIFIED | FUTURE | True -> False |
| Vérifie juste si le dossier Photos existe. | FIND_EXISTING_PHOTOS | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| Vérifie juste si la caméra marche. | CHECK_CAMERA | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| Regarde si la webcam est dispo, c'est tout. | CHECK_CAMERA | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| Check vite fait si le Mac voit la cam. | CHECK_CAMERA | None | CONDITIONAL | NOW | False -> True |
| Vérifie juste si la caméra est disponible, ne cherche aucun fichier. | CHECK_CAMERA | inspection_only | CONDITIONAL | UNSPECIFIED | False -> False |
| Dis-moi juste si la webcam répond. | CHECK_CAMERA | None | CONDITIONAL | UNSPECIFIED | False -> True |
| Check si la cam est opérationnelle. | CHECK_CAMERA | None | CONDITIONAL | UNSPECIFIED | False -> True |
| Dis-moi seulement si le dossier de photos existe, sans lister son contenu. | OTHER | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| Vérifie seulement si le Mac est branché au chargeur. | OTHER | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| regarde juste si la camera marche | CHECK_CAMERA | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| check juste si la webcam est dispo | CHECK_CAMERA | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| check si la cam est detectée | CHECK_CAMERA | None | CONDITIONAL | UNSPECIFIED | False -> True |
| test si la camera fonctionne | CHECK_CAMERA | None | CONDITIONAL | UNSPECIFIED | False -> True |
| regarde juste si le dossier photo existe | OTHER | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| regarde juste si la webcam est dispo | CHECK_CAMERA | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| check juste si le mac est branché | OTHER | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |

### dataset v2

| sentences | n | categories v1 | categories v2 | actionable v1 -> v2 |
|---|---|---|---|---|
| base_or_variant | 118 | CONDITIONAL 2, NOW 30, PAST_REFERENCE 6, UNSPECIFIED 80 | NOW 30, PAST_REFERENCE 6, UNSPECIFIED 82 | 100 -> 102 |
| negation | 28 | CONDITIONAL 1, UNSPECIFIED 27 | CONDITIONAL 1, UNSPECIFIED 27 | 1 -> 1 |
| temporal | 30 | CONDITIONAL 1, FUTURE 19, PAST_REFERENCE 1, UNSPECIFIED 9 | CONDITIONAL 1, FUTURE 26, PAST_REFERENCE 1, UNSPECIFIED 2 | 9 -> 2 |
| past_question | 28 | FUTURE 2, PAST_REFERENCE 26 | FUTURE 2, PAST_REFERENCE 26 | 0 -> 0 |
| object_change | 23 | CONDITIONAL 1, NOW 4, UNSPECIFIED 18 | CONDITIONAL 1, NOW 4, UNSPECIFIED 18 | 18 -> 18 |
| inspection_only | 15 | CONDITIONAL 3, UNSPECIFIED 12 | UNSPECIFIED 15 | 11 -> 13 |
| conditional | 17 | CONDITIONAL 11, FUTURE 4, NOW 2 | CONDITIONAL 13, FUTURE 2, NOW 2 | 2 -> 2 |

Sentences whose category or actionability changed: 14

| text | class | transformation | v1 | v2 | actionable v1 -> v2 |
|---|---|---|---|---|---|
| Immortalise-moi avec la caméra quand j'aurai fini de me recoiffer. | OTHER | temporal | UNSPECIFIED | FUTURE | True -> False |
| Regarde si la caméra du Mac peut faire une photo d'identité, sans la prendre. | CHECK_CAMERA | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| Allume la webcam pour le cadrage quand je te le demanderai. | OTHER | temporal | UNSPECIFIED | FUTURE | True -> False |
| Regarde si tu peux me prendre, mais ne le fais pas. | CHECK_CAMERA | inspection_only | CONDITIONAL | UNSPECIFIED | False -> False |
| Attends que je sois revenu devant le Mac avant de me prendre en photo. | OTHER | temporal | UNSPECIFIED | FUTURE | True -> False |
| Quand j'aurai fini mon appel, vérifie quelles webcams sont connectées. | OTHER | temporal | UNSPECIFIED | FUTURE | True -> False |
| Si jamais la visio déconne plus tard, regarde à ce moment-là si une caméra est détectée. | OTHER | conditional | FUTURE | CONDITIONAL | False -> False |
| Vérifie seulement si le dossier qui contient mes photos existe, sans chercher les fichiers dedans. | OTHER | inspection_only | CONDITIONAL | UNSPECIFIED | False -> True |
| regarde si la webcam répond | CHECK_CAMERA | None | CONDITIONAL | UNSPECIFIED | False -> True |
| check si la webcam est accessible | CHECK_CAMERA | None | CONDITIONAL | UNSPECIFIED | False -> True |
| attends avant de prendre la photo | OTHER | temporal | UNSPECIFIED | FUTURE | True -> False |
| quand je te dis go tu prends la photo | OTHER | temporal | UNSPECIFIED | FUTURE | True -> False |
| fait la photo une fois que j'ai fini | OTHER | temporal | UNSPECIFIED | FUTURE | True -> False |
| si jamais je te demande apres tu pourra me prendre | OTHER | conditional | FUTURE | CONDITIONAL | False -> False |

## C4 protocol on version 1: A+S+T_v1 against A+S+T_v2, under the gate

| representation | model | unseen positive recall | FFP hard | per transformation: negation, temporal, past_question, object_change, inspection_only | coverage | sel. acc. | feasible | criterion |
|---|---|---|---|---|---|---|---|---|
| A+S+T_v1 | prototype | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False |  |
| A+S+T_v1 | knn3 | 0.46 | 2 | 0, 1, 0, 1, 0 | 0.66 | 0.96 | False |  |
| A+S+T_v1 | logreg | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False |  |
| A+S+T_v1 | tree | 0.59 | 3 | 0, 1, 0, 1, 1 | 0.81 | 0.83 | False |  |
| A+S+T_v2 | prototype | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False |
| A+S+T_v2 | knn3 | 0.46 | 2 | 0, 0, 0, 1, 1 | 0.64 | 0.95 | False | False |
| A+S+T_v2 | logreg | 0.00 | 0 | 0, 0, 0, 0, 0 | 0.00 | 1.00 | False | False |
| A+S+T_v2 | tree | 0.52 | 3 | 0, 0, 0, 2, 1 | 0.76 | 0.80 | False | False |

## Gate grid with A+S+E_RERANK+T_v2 (classifier refit, threshold by the rule = 0.5963, in-sample selector feasible True)

### Version 1, out of fold

| gate | acc. positives | acc. hard neg. | coverage | sel. acc. | hard FFP | FFP all | positive reflex coverage | fired | hard fired as CAPTURE (negation, temporal, past_question, object_change, inspection_only, conditional) | meets grid |
|---|---|---|---|---|---|---|---|---|---|---|
| G0 | 1.00 | 1.00 | 0.88 | 0.94 | 1 | 1 | 0.85 | 281 | 0, 0, 0, 1, 0, 0 | False |
| G1 | 0.91 | 0.90 | 0.81 | 1.00 | 0 | 0 | 0.83 | 260 | 0, 0, 0, 0, 0, 0 | True |
| G2_p90 | 1.00 | 1.00 | 0.87 | 0.94 | 1 | 1 | 0.85 | 279 | 0, 0, 0, 1, 0, 0 | False |
| G2_p95 | 1.00 | 1.00 | 0.88 | 0.94 | 1 | 1 | 0.85 | 282 | 0, 0, 0, 1, 0, 0 | False |
| G2_p99 | 1.00 | 1.00 | 0.88 | 0.94 | 1 | 1 | 0.85 | 282 | 0, 0, 0, 1, 0, 0 | False |
| G4 | 0.91 | 0.26 | 0.47 | 1.00 | 0 | 0 | 0.83 | 149 | 0, 0, 0, 0, 0, 0 | True |
| G2_p95+actionable_v2 | 0.98 | 0.34 | 0.50 | 0.96 | 1 | 1 | 0.85 | 160 | 0, 0, 0, 1, 0, 0 | False |
| G3exp_a0.05 | 0.96 | 0.96 | 0.88 | 0.94 | 1 | 1 | 0.85 | 282 | 0, 0, 0, 1, 0, 0 | False |
| G3exp_a0.1 | 0.87 | 0.94 | 0.88 | 0.94 | 1 | 1 | 0.85 | 282 | 0, 0, 0, 1, 0, 0 | False |

### Version 2, refit on all of version 1

| gate | acc. positives | acc. hard neg. | coverage | sel. acc. | hard FFP | FFP all | positive reflex coverage | fired | hard fired as CAPTURE (negation, temporal, past_question, object_change, inspection_only, conditional) | meets grid |
|---|---|---|---|---|---|---|---|---|---|---|
| G0 | 0.27 | 0.07 | 0.09 | 0.90 | 0 | 0 | 0.17 | 21 | 0, 0, 0, 0, 0, 0 | False |
| G1 | 0.00 | 0.02 | 0.01 | 1.00 | 0 | 0 | 0.00 | 3 | 0, 0, 0, 0, 0, 0 | False |
| G2_p90 | 0.90 | 0.60 | 0.51 | 0.90 | 0 | 1 | 0.67 | 124 | 0, 0, 0, 0, 0, 0 | False |
| G2_p95 | 0.97 | 0.74 | 0.62 | 0.88 | 0 | 1 | 0.70 | 150 | 0, 0, 0, 0, 0, 0 | False |
| G2_p99 | 1.00 | 1.00 | 0.79 | 0.90 | 0 | 1 | 0.70 | 193 | 0, 0, 0, 0, 0, 0 | False |
| G4 | 0.00 | 0.00 | 0.00 | n/a | 0 | 0 | 0.00 | 0 | 0, 0, 0, 0, 0, 0 | False |
| G2_p95+actionable_v2 | 0.93 | 0.15 | 0.29 | 0.87 | 0 | 1 | 0.70 | 70 | 0, 0, 0, 0, 0, 0 | False |
| G3exp_a0.05 | 0.80 | 0.95 | 0.79 | 0.90 | 0 | 1 | 0.70 | 193 | 0, 0, 0, 0, 0, 0 | False |
| G3exp_a0.1 | 0.77 | 0.93 | 0.79 | 0.90 | 0 | 1 | 0.70 | 193 | 0, 0, 0, 0, 0, 0 | False |
