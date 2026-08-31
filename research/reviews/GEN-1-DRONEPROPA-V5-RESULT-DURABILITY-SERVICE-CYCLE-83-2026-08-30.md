# GEN-1 — DronePropA v5 result semantics and durability service, cycle 83

## Scope and preserved failure

This is a protected service-only cycle after terminally invalid EXP-0058. It may not create a hypothesis, plan, scoring seed, runner scoring call, candidate score, result or evidence. EXP-0058, seed `747591598`, its immutable plan, runtime plan, ten worker artifacts, eleven logs, invalidation event and analysis remain unchanged.

Two predeclared infrastructure defects are repaired in a version-separated v5 cohort. First, continuous conditional log loss is a differential density score and must permit finite negative values. Second, worker JSON alone cannot preserve supervisor-created timeout or memory-limit outcomes, so every normalized candidate row must be atomically persisted before aggregate/result validation.

## Implemented mechanisms

- `conditional_log_loss` now accepts any finite JSON number or null; its formula and `minimize` direction are unchanged.
- The runner atomically writes `<candidate>.supervisor.json` immediately after every normalized candidate outcome and before cross-candidate aggregation, integrity, Pareto or final result validation.
- Worker artifacts and supervisor artifacts have separate hash manifests in every post-seed failure event. Raw worker outputs are not overwritten.
- Timeout, memory-limit, audit-failure and crash rows use the same durable supervisor path as complete rows.
- The thin v5 benchmark delegates the complete v4 corpus, split and numerical execution unchanged.

## Regressions and verification

The continuous-density regression validates both a negative trial and negative aggregate conditional log loss. The durability regression runs one complete fake worker plus one supervisor-only timeout, forces final validation failure, then proves that the realized seed, raw complete-worker artifact, two supervisor artifacts, timeout termination reason, runtime plan, invalidation and cleared active state all survive.

Focused result/durability and DronePropA tests passed. Maintenance and active snapshots each passed all 288 tests, integrity and doctor. Report generation passed after activation. No runner scoring call occurred.

- active benchmark: `heldout_dronepropa_factor_recombination_v5`;
- evaluator SHA-256: `d6beb273579df164e15a86f383f594c44c5086864ceeb3edee5dc7381d254644`;
- candidate-bundle SHA-256: `5bbf64713aecf5487524fa56cf1372b3b06c00050e1c1fd68da7f123c1c145fa`;
- manifest file SHA-256: `ffd4ef36cbc99753a9980e8f5a082042db58d2dd31f3602064abf95833fd069d`;
- v5 wrapper SHA-256: `bf63305e5326808fcfcb921e86000f84847b2f9988f3f19fe67792662da39c47`;
- free disk: `63.57 GiB`.

EXP-0058 remains invalid, resultless and excluded from evidence. Its immutable plan file SHA-256 remains `7c92724093c16154bae36b13abe3d512444684a12fc056d50007ae9234542f6c`; its runtime-plan SHA-256 remains `7541c5f46ac55c8bd1dc79d8885b5bbc2edfd1b583dc94b304272680c9e298be`.

## Decision and exact next experiment

Decision: `keep` the v5 result-integrity repair. Confidence is `0.999` that the two observed post-seed failure modes are now covered without altering candidate scores, corpus semantics or scientific gates. HYP-0023 remains proposed at confidence `0.22` with no evidence experiment.

In the next wake, preregister new quick `EXP-20260830-0059` against evaluator `d6beb273579df164e15a86f383f594c44c5086864ceeb3edee5dc7381d254644` as the unchanged corrected test after invalid EXP-0058. Do not use EXP-0058 as evidence or a replication parent. Reuse the already-frozen candidate bundle, rank 12, K=8/32, D=1, Q=128, one runner-random seed, all ten controls, metrics and outcome rules; make no candidate change and run exactly once.
