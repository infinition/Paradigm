# P2.3T Learning Threshold Sweep

Candidates are fitted offline from LLM-only traces with k novel-family episodes in the train split, while the certification set (four held-out novel episodes plus four held-out known episodes) and the retention probes (four further known episodes) stay fixed for every k. Novel episode order is shuffled per ordering. Capability accuracy is the candidate's raw agreement with the teacher on the held-out novel decisions, independent of the gate. Gate acceptance is the shadow OOD acceptance of those decisions. This separates what the tree can reproduce from what the certification gate will admit.

Narrative interpretation: `INTERPRETATION.md` in this directory.

## qwen3:4b-instruct

Known train episodes 24, certification 4 known + 4 novel episodes, probes 4 known episodes, 5 orderings, acceptance floor 0.65.

| Novel train episodes | Capability accuracy mean (min) | Gate acceptance mean [min, max] | Recent promote rate | Family-aware promote rate |
|---|---|---|---|---|
| 0 | 100% (100%) | 0.00 [0.00, 0.00] | 0% | 0% |
| 1 | 100% (100%) | 0.12 [0.00, 0.20] | 0% | 0% |
| 2 | 100% (100%) | 0.35 [0.20, 0.45] | 60% | 0% |
| 3 | 100% (100%) | 0.50 [0.20, 0.70] | 80% | 40% |
| 4 | 100% (100%) | 0.56 [0.45, 0.70] | 100% | 40% |
| 5 | 100% (100%) | 0.78 [0.45, 0.95] | 100% | 80% |
| 6 | 100% (100%) | 0.81 [0.45, 1.00] | 100% | 80% |
| 7 | 100% (100%) | 0.92 [0.90, 0.95] | 100% | 100% |
| 8 | 100% (100%) | 0.94 [0.90, 1.00] | 100% | 100% |

## qwen3:8b

Known train episodes 24, certification 4 known + 4 novel episodes, probes 4 known episodes, 5 orderings, acceptance floor 0.65.

| Novel train episodes | Capability accuracy mean (min) | Gate acceptance mean [min, max] | Recent promote rate | Family-aware promote rate |
|---|---|---|---|---|
| 0 | 100% (100%) | 0.00 [0.00, 0.00] | 0% | 0% |
| 1 | 100% (100%) | 0.12 [0.00, 0.20] | 0% | 0% |
| 2 | 100% (100%) | 0.35 [0.20, 0.45] | 60% | 0% |
| 3 | 100% (100%) | 0.50 [0.20, 0.70] | 80% | 40% |
| 4 | 100% (100%) | 0.56 [0.45, 0.70] | 100% | 40% |
| 5 | 100% (100%) | 0.78 [0.45, 0.95] | 100% | 80% |
| 6 | 100% (100%) | 0.81 [0.45, 1.00] | 100% | 80% |
| 7 | 100% (100%) | 0.92 [0.90, 0.95] | 100% | 100% |
| 8 | 100% (100%) | 0.94 [0.90, 1.00] | 100% | 100% |

