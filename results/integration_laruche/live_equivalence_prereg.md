# Pre-registration: `laruche-equivalence-1` active in the live service (run 12b)

Written before any code change. One short live run to validate the wiring, not a new benchmark.

## What changes

`paradigm serve` gains an explicit option `--equivalence laruche` that passes the adapter's contract (`laruche-equivalence-1`: TEST_EXECUTION only) to the compiler. The contract is active from mission 1. Its version and digest are recorded in every certification artifact and in the telemetry. Identity remains the default outside this run.

Nothing else changes: thresholds, gates, splits, compile cadence, the live certification rule (family-scoped, no probe re-certification, as in runs 11 and 12), the shadow sampling schedule of run 12 (seed 20260917; bands 17 to 20 at 0.25 and 21 to 24 at 0.50 are the only ones reached), the guard, the canonicalizer (`| cat` stays a distinct key).

## Historical probes

A retention probe set records the contract it was frozen under (version, mapping, digest). It is evaluated under that contract. A probe set frozen before this field existed is evaluated under identity. It may be rescored diagnostically under the current contract, reported alongside, and its historical verdict is never rewritten. In this run every probe set is frozen under `laruche-equivalence-1`, so both views coincide; the rule matters for reloaded states.

## Run

24 missions, fresh Paradigm state, same workspace, bug variants, model (`deepseek-v4-flash`), guard, canonicalization and thresholds as run 12. Compile points expected at 8, 12, 16 (first promotion) and one or two after (20, 24 in stream episodes, shifted if a mission yields no validated trace).

## Reported side by side

Per compile point and family: literal teacher agreement, behavioral-equivalence agreement, family verdict, candidate adoption decision; the same record replayed without the contract, and every family verdict or adoption decision that differs (decisions changed by equivalence); the divergence from run 12 at the common compile points (16, 20, 24), family by family.

## Predictions

1. Behavioral agreement exceeds literal agreement only on families whose held-out or probe traces contain a test-command phrasing variant covered by `laruche-equivalence-1`; everywhere else the two are equal.
2. A candidate regression of the kind seen at run 12 point 25 (a non-test action where the teacher ran the tests) remains rejected if it occurs.
3. No family outside those containing TEST_EXECUTION actions changes verdict between the literal replay and the live contract.
4. No historical certification is altered: the run starts from a fresh state, and the earlier records are not touched.
5. Mission success and safety as before: 24 of 24 verified, 0 unsafe actions, 0 false fast paths.

Stop and report if any family that contains no TEST_EXECUTION action changes verdict because of the contract.

## Not done

No mechanism change, no threshold change, no `m` selected, no probe re-certification live, no run 13 decision.
