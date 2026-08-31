# GEN-1 — DronePropA execution-path audit, cycle 78

## Scope

This was one protected service-only cycle under the user's standing migration authorization. It created no hypothesis, experiment ID, immutable experiment plan, runner seed, shared learner, predictive result, ledger row or confidence update, and it performed no scoring. The benchmark stayed in `maintenance` throughout.

## Implemented execution boundary

The protected v1 evaluator now resolves the frozen 130-file inventory by raw SHA-256, parses private filename factors only inside the evaluator and exposes only anonymous slots to implementable candidates. It adds deterministic 128-anchor training examples, training-only feature/target normalization, the common `fit(DynamicsTraining) -> adapt(FlightExamples) -> session.predict()` learner contract, evaluator adapters for the registered controls, teacher-forced one-step prediction and recursive 10/50-step rollout with identical future motor controls.

The runtime reports per-horizon, mean, worst-flight, worst-condition and stable-rollout NRMSE; conditional log loss where a distribution exists; evaluator-private condition/trajectory aggregates; fit, preprocessing, adaptation, query and state estimates; bytes touched; and complete R1/R4/R16 workload including the archive and extracted corpus boundary. State over 64 MiB fails before a result can be returned.

## New pre-score blocker

The frozen split was joined to evaluator-private factors before any score. All test conditions are exactly `F1_SV3`, `F2_SV2` and `F3_SV1`; the intersection with training conditions is empty. Therefore both registered privileged v1 controls are scientifically undefined:

- `oracle_charged_condition_specialist_arx_v1` cannot dispatch an exact-condition model because no such training condition exists;
- `privileged_condition_oracle_arx_v1` has no legal same-condition training set.

The runtime now raises an explicit error when either control is asked to fall back from an unseen condition. It does not borrow a different condition, use test adaptation as if it were a condition oracle or silently consume reserved `t4` files. The protocol records this defect. Because mandatory controls cannot all execute, v1 must not be activated and no EXP-0058 may be preregistered against it.

## Verification

- synthetic end-to-end runtime with all horizons and R1/R16 accounting: PASS;
- real frozen MAT file to `128x320 -> 128x6` runtime examples: PASS;
- exact held-out-condition disjointness fixture: PASS;
- deliberate undefined-condition control refusal: PASS;
- focused DronePropA tests: 20 passed;
- complete suite: 271 passed;
- integrity: PASS, 465 protected files;
- evaluator SHA-256: `4f02a8657a4cdd2d0eb29903f47cb869c12194548d43d25edec0fc7ee3a5fdc3`;
- candidate-bundle SHA-256: `0257426260b5a920bbf471121cd07342761ccc5586a937878c66552ff3c9c618`;
- active manifest file SHA-256: `019db303cacdb22a2fe8e3cb454f4aa8c4f35f591b8c9b9853bc1444b24497b7`;
- doctor: PASS in `maintenance`;
- scoring: none.

## Decision and next service cycle

Decision: `inconclusive`; keep v1 as diagnostic history and do not activate it. Confidence is 0.99 that the condition-control contradiction is real because it is an exact set-disjointness fact over the frozen split, not a performance estimate.

The next wake must be another service-only protected migration to `heldout_dronepropa_factor_recombination_v2`. Create a new split role `privileged_oracle_support` for the 26 currently reserved `t4` flights. The fully charged specialist may fit all 26 support flights and dispatch by evaluator-private exact condition; the same-condition oracle may fit only the six `t4` support flights matching the three test conditions. Both remain privileged and excluded from Pareto evidence, every byte/fit/state cost is charged, and no implementable candidate may see their factors or samples. Freeze v2 and activate only after all ten controls complete a tiny semantic E2E fixture, real-file smoke paths pass, the full suite passes, integrity passes and doctor passes. No hypothesis, EXP ID, plan or seed is allowed in that migration wake.
