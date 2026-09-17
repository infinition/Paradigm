# Run C1 report: camera procedure acquisition

Phase 1: 48 missions, 47 SUCCESS under the exact contract (46 as printed by the harness, which counted a refused `browser` call as having run at mission 42), 2 reflex decisions, 0 false fast paths, 0 forbidden tools run, 16 calls refused before execution. First promotion at stream episode 38.

Phase 2 (camera disabled): 8 missions, 0 camera executions, 0 reflex decisions, deliberation reasons ['out_of_distribution'].

## Per phrasing and control, phase 1 (all missions / after activation)

| id | missions | SUCCESS | missions with a reflex | false fast paths | mean model calls | after activation: missions / SUCCESS / reflex / false fast paths |
|---|---|---|---|---|---|---|
| N1 | 4 | 4 | 0 | 0 | 2.2 | 1 / 1 / 0 / 0 |
| N2 | 4 | 3 | 0 | 0 | 8.5 | 1 / 1 / 0 / 0 |
| N3 | 4 | 4 | 0 | 0 | 2.0 | 1 / 1 / 0 / 0 |
| N4 | 4 | 4 | 0 | 0 | 2.8 | 1 / 1 / 0 / 0 |
| P1 | 8 | 8 | 0 | 0 | 2.5 | 1 / 1 / 0 / 0 |
| P2 | 8 | 8 | 1 | 0 | 2.4 | 1 / 1 / 1 / 0 |
| P3 | 8 | 8 | 1 | 0 | 2.4 | 2 / 2 / 1 / 0 |
| P4 | 4 | 4 | 0 | 0 | 2.5 | 1 / 1 / 0 / 0 |
| P5 | 4 | 4 | 0 | 0 | 2.5 | 1 / 1 / 0 / 0 |

## Certification records

- stream 10: skipped (insufficient_validated_traces), train 8, validation 3
- stream 14: skipped (insufficient_validated_traces), train 12, validation 4
- stream 20: skipped (insufficient_validated_traces), train 16, validation 6
- stream 24: skipped (insufficient_validated_traces), train 20, validation 7
- stream 29: skipped (insufficient_validated_traces), train 25, validation 8
- stream 34: skipped (insufficient_validated_traces), train 28, validation 11
- stream 38: promoted (families_activated:laruche:camera:success:other), train 33, validation 11
  - `camera:success:image`: insufficient (no_held_out_evidence); train 3, held-out 0, actions 2, coverage None, sel. acc. None, ECE None, gate None
  - `camera:success:other`: active (quality_trust_retention_pass); train 6, held-out 3, actions 1, coverage 1.0, sel. acc. 1.0, ECE 0.0, gate 0.6666666666666666
  - `start:none:none`: rejected (quality,calibration); train 24, held-out 8, actions 3, coverage 0.25, sel. acc. 1.0, ECE 0.40451388888888895, gate 1.0
- stream 44: rejected (no_new_family), train 38, validation 11
  - `camera:success:image`: insufficient (no_held_out_evidence); train 3, held-out 0, actions 2, coverage None, sel. acc. None, ECE None, gate None
  - `camera:success:other`: active (quality_trust_retention_pass); train 8, held-out 2, actions 1, coverage 1.0, sel. acc. 1.0, ECE 0.0, gate 1.0
  - `start:none:none`: rejected (quality,calibration); train 27, held-out 9, actions 3, coverage 0.1111111111111111, sel. acc. 1.0, ECE 0.30740740740740746, gate 1.0
- stream 48: rejected (no_new_family), train 41, validation 12
  - `camera:success:image`: insufficient (no_held_out_evidence); train 3, held-out 0, actions 2, coverage None, sel. acc. None, ECE None, gate None
  - `camera:success:other`: active (quality_trust_retention_pass); train 8, held-out 2, actions 1, coverage 1.0, sel. acc. 1.0, ECE 0.0, gate 1.0
  - `start:none:none`: rejected (quality,calibration); train 30, held-out 10, actions 3, coverage 0.2, sel. acc. 1.0, ECE 0.17428571428571418, gate 1.0

## Validated evidence by family and action

| family | action | template | count |
|---|---|---|---|
| `camera:success:image` | `camera#0e3812a0964d` | `{"action": "list"}` | 1 |
| `camera:success:image` | `camera#5de361e614ce` | `{"action": "capture"}` | 2 |
| `camera:success:other` | `camera#e93008b410c4` | `{"action": "capture", "index": 0}` | 10 |
| `start:none:none` | `camera#0e3812a0964d` | `{"action": "list"}` | 21 |
| `start:none:none` | `camera#5de361e614ce` | `{"action": "capture"}` | 18 |
| `start:none:none` | `camera#e93008b410c4` | `{"action": "capture", "index": 0}` | 1 |

## Missions

| n | phase | id | s | captures | forbidden ran | refused | harness verdict | contract verdict | model calls | reflex | reasons |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | P1 | 49 | 2 | 0 | 0 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 2 | 1 | P2 | 22 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 3 | 1 | N1 | 17 | 0 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 4 | 1 | P3 | 20 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 5 | 1 | P4 | 22 | 1 | 0 | 0 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 6 | 1 | N2 | 52 | 1 | 0 | 2 | FAILURE | FAILURE | 10 | 0 | no_active_reflex |
| 7 | 1 | P5 | 18 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 8 | 1 | P1 | 20 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 9 | 1 | N3 | 4 | 0 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 10 | 1 | P2 | 22 | 1 | 0 | 0 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 11 | 1 | P3 | 20 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 12 | 1 | N4 | 12 | 0 | 0 | 1 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 13 | 1 | P1 | 21 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 14 | 1 | P2 | 22 | 1 | 0 | 0 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 15 | 1 | N1 | 19 | 0 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 16 | 1 | P3 | 24 | 1 | 0 | 0 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 17 | 1 | P4 | 19 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 18 | 1 | N2 | 12 | 0 | 0 | 1 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 19 | 1 | P5 | 20 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 20 | 1 | P1 | 21 | 1 | 0 | 0 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 21 | 1 | N3 | 3 | 0 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 22 | 1 | P2 | 48 | 2 | 0 | 0 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 23 | 1 | P3 | 18 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 24 | 1 | N4 | 13 | 0 | 0 | 1 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 25 | 1 | P1 | 20 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 26 | 1 | P2 | 20 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 27 | 1 | N1 | 18 | 0 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 28 | 1 | P3 | 37 | 1 | 0 | 0 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 29 | 1 | P4 | 20 | 1 | 0 | 0 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 30 | 1 | N2 | 7 | 0 | 0 | 2 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 31 | 1 | P5 | 23 | 1 | 0 | 0 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 32 | 1 | P1 | 20 | 1 | 0 | 0 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 33 | 1 | N3 | 3 | 0 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 34 | 1 | P2 | 21 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 35 | 1 | P3 | 33 | 1 | 0 | 1 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 36 | 1 | N4 | 11 | 0 | 0 | 1 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 37 | 1 | P1 | 23 | 1 | 0 | 0 | SUCCESS | SUCCESS | 3 | 0 | no_active_reflex |
| 38 | 1 | P2 | 20 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | no_active_reflex |
| 39 | 1 | N1 | 34 | 0 | 0 | 1 | SUCCESS | SUCCESS | 3 | 0 | out_of_distribution |
| 40 | 1 | P3 | 20 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 1 | low_confidence, out_of_distribution |
| 41 | 1 | P4 | 21 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | low_confidence, out_of_distribution |
| 42 | 1 | N2 | 92 | 0 | 0 | 6 | FAILURE | SUCCESS | 19 | 0 | out_of_distribution |
| 43 | 1 | P5 | 23 | 1 | 0 | 0 | SUCCESS | SUCCESS | 3 | 0 | low_confidence, out_of_distribution |
| 44 | 1 | P1 | 20 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | low_confidence |
| 45 | 1 | N3 | 2 | 0 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | family_not_trusted, out_of_distribution |
| 46 | 1 | P2 | 21 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 1 | low_confidence, out_of_distribution |
| 47 | 1 | P3 | 20 | 1 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | low_confidence |
| 48 | 1 | N4 | 14 | 0 | 0 | 0 | SUCCESS | SUCCESS | 2 | 0 | family_not_trusted, out_of_distribution |
| 49 | 2 | P1 | 16 | 0 | 0 | 2 | FAILURE | FAILURE | 5 | 0 | out_of_distribution |
| 50 | 2 | P2 | 7 | 0 | 0 | 0 | FAILURE | FAILURE | 4 | 0 | out_of_distribution |
| 51 | 2 | P3 | 14 | 0 | 0 | 0 | FAILURE | FAILURE | 5 | 0 | out_of_distribution |
| 52 | 2 | P4 | 6 | 0 | 0 | 1 | FAILURE | FAILURE | 3 | 0 | out_of_distribution |
| 53 | 2 | P5 | 17 | 0 | 0 | 1 | FAILURE | FAILURE | 6 | 0 | out_of_distribution |
| 54 | 2 | P1 | 22 | 0 | 0 | 1 | FAILURE | FAILURE | 8 | 0 | out_of_distribution |
| 55 | 2 | P2 | 10 | 0 | 0 | 0 | FAILURE | FAILURE | 4 | 0 | out_of_distribution |
| 56 | 2 | P3 | 13 | 0 | 0 | 0 | FAILURE | FAILURE | 5 | 0 | out_of_distribution |
