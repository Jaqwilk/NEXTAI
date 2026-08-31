# GEN-1 — DronePropA v2 protected activation, cycle 79

## Scope

This was one user-authorized protected service migration with no hypothesis, experiment ID, immutable plan, scoring seed, candidate learner, predictive score, result, evidence or confidence update. It migrated the never-scored v1 maintenance cohort to `heldout_dronepropa_factor_recombination_v2` and activated v2 only after maintenance and active snapshots independently passed every gate.

## Corrected split and privileged boundary

V2 preserves all 130 raw files and the 64 train, 8 validation, 24 test and 8 healthy-OOD assignments. The 26 `t4` files are now explicitly `privileged_oracle_support` instead of unused adversarial reserve. Split SHA-256 is `fddd1c98aae13460ec58af25dbbea94f6f25177486da59a1e94f6a25f844a0e4`.

Implementable candidates receive none of these 26 support flights, their factors or metadata. `oracle_charged_condition_specialist_arx_v2` fits all 26 support flights and pays all preprocessing, fit and state. `privileged_same_condition_oracle_arx_v2` fits only the six support flights whose evaluator-private condition matches F1/SV3, F2/SV2 or F3/SV1. Both are excluded from implementable Pareto evidence and never inspect a queried test target.

## Execution and evidence accounting

The v2 evaluator reuses the v1 engine without copying it. It enforces training-only normalization; anonymous `DynamicsTraining -> adapt(FlightExamples) -> session.predict` access; 128 deterministic training and 32 deterministic adaptation anchors; runner-random disjoint evaluation anchors; teacher-forced horizon 1; recursive horizons 10/50; the 64 MiB state bound; and archive, preprocessing, fit, adaptation, query, update, bytes and R1/R4/R16 accounting.

After all candidates finish, the audited runner derives minimum condition and trajectory transfer gains against both the source-identical independent and no-sharing controls. Oracle-gap closure is `(independent NRMSE - candidate NRMSE) / (independent NRMSE - same-condition oracle NRMSE)` for the identical seed/K cell. These fields are now mandatory plan metrics.

The generic matrix now matches the protected evaluator rather than creating duplicate cells: `reasoning_depths=[1]`, `queries_per_cell=128`; K is 8/32 quick, 8/32/64 screen and 16/32/64 deep. Quick wall time is a hard 180 seconds per candidate, screen 600 and deep 1800. This is a versioned pre-score budget correction, not a cooldown.

## Integrity gates and verification

Before runner seed realization, v2 executes ten unique semantic/E2E nodes covering all ten controls and verifies the full corpus. The corpus gate passed for the 4,438,911,840-byte archive, all 130 extracted MAT files and the 2,550-byte generated file list: 8,976,605,993 bytes total.

- all eight implementable controls: common synthetic adapter E2E PASS;
- all eight implementable controls: common real-file one-step smoke PASS;
- both privileged controls: exact `t4` support semantic E2E PASS;
- both privileged controls: real train/test/`t4` one-step smoke PASS;
- cross-candidate transfer/oracle aggregation fixture: PASS;
- deliberate v1 undefined-condition refusal: PASS;
- complete suite in maintenance: 286 passed;
- complete suite after activation: 286 passed;
- integrity: PASS, 469 protected files;
- doctor: PASS, active;
- pending plans: 0;
- scoring: none.

Final active digests:

- manifest file SHA-256: `c309b8044fe8cc57289cec556482d4d61dca689839df15f88584f0e31e05872b`;
- evaluator SHA-256: `aa8a9e3dbb7c2a4c2f8ca89831285c05a45485569ea86cc0d8fffb22897a18bc`;
- candidate bundle SHA-256: `8b0f2576e82a9dd3369518ccca51b508d5124ec165023464b1c35f19ea36c669`;
- semantic registry SHA-256: `e1fbe22cb5d2baf0cba8bc60f5db4ed5f4573dc2a3d375ef24af120ab230f7c4`.

## Decision and exact next experiment

Decision: `keep`; v2 is execution-ready infrastructure, not scientific evidence. Confidence is 0.995 that its split, public/privileged boundary, named-control semantics, full-corpus gate and aggregation contract match the frozen specification. No claim is made about the unimplemented shared learner.

In the next wake, preregister HYP-0023 and exactly one quick EXP-20260830-0058 before implementing the tested candidate. The candidate is one rank-12 `shared_operator_subspace_arx`: fit one anonymous affine ARX operator per training flight, learn a pooled rank-12 operator SVD basis, and estimate only basis coefficients from each held-out flight's 32 adaptation examples. Compare unchanged against all ten frozen controls. Primary metrics are 1/10/50 NRMSE, worst flight/condition, minimum condition/trajectory gains, oracle-gap closure and every full-cost axis. One runner seed may discard the implementation or authorize an unchanged three-seed screen; it cannot promote. Rank, history, ridge, anchors, split, horizons, thresholds and budgets may not be tuned after any score.
