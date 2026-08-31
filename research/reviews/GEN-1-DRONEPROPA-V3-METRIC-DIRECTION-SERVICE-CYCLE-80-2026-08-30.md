# GEN-1 — DronePropA v3 metric-direction service cycle, cycle 80

## Pre-change defect record

The active v2 plan schema requires `workload_ops_r1` and `workload_ops_r4`, and the evaluator already computes both as full-cost axes. The global metric registry omitted their `minimize` directions. Consequently `nextai plan new` rejects the two required names as unknown, while omitting them produces a schema-invalid DronePropA plan. This was found before HYP-0023, EXP-0058, candidate implementation, scoring-seed realization or scoring.

The smallest protocol-conforming correction is a version-separated v3 cohort that reuses v2 data and execution semantics byte-for-byte and adds only the two missing metric directions. During the change the benchmark remains in maintenance. No thresholds, budgets, seeds, candidates, baselines, split, normalization, anchors, horizons or numerical metrics may change.

## Implemented correction

- Added the thin `heldout_dronepropa_factor_recombination_v3` entry, which delegates corpus verification, the frozen v2 split and all execution to v2.
- Registered only `workload_ops_r1` and `workload_ops_r4` as minimized costs. Their evaluator formulas and values were already present and are unchanged.
- Added a regression proving v3 reuses the v2 split, role counts and static contract, and that both required axes have configured directions.
- Added v3 to the semantic-registry cohort inventory without changing any baseline implementation, specification, conformance node or hash.
- Kept v2 and all earlier plans, results, logs, analyses and manifests immutable.

## Verification and activation

The maintenance snapshot and the final active snapshot each passed all 287 tests, integrity verification and doctor. The report regenerated successfully. The active manifest protects 470 files.

- active benchmark: `heldout_dronepropa_factor_recombination_v3`;
- evaluator SHA-256: `f687d3436edb045d0aa371c78f8b2333c506f5667126a5d1066354caf44ad29b`;
- candidate-bundle SHA-256: `c5291f9efb3d632d49551f3091d7ca4becc0152bd2ed513b0ecf1fb0a0b988fd`;
- manifest file SHA-256: `7efca3bfd109adf537dfa4d59b6241129d1d63a78fcc77456b40872867143452`;
- v3 wrapper SHA-256: `9a073452ff38a8417bc39965bfc4cd65348d7af695d0f946506949e95e1562ec`;
- split SHA-256: `fddd1c98aae13460ec58af25dbbea94f6f25177486da59a1e94f6a25f844a0e4`;
- free disk after verification: `63.64 GiB`.

No hypothesis, experiment plan, scoring seed, candidate learner, runner scoring call, scientific result, evidence or confidence update occurred in cycle 80.

## Decision and exact next experiment

Decision: `keep` the v3 infrastructure correction. Confidence is `0.999` that the missing-direction deadlock is removed without altering the v2 numerical task or scientific thresholds.

In the next wake, create HYP-0023 and preregister exactly one quick `EXP-20260830-0058` against evaluator `f687d3436edb045d0aa371c78f8b2333c506f5667126a5d1066354caf44ad29b` before implementing `shared_operator_subspace_arx`. Use the frozen rank 12, K=8/32, D=1, Q=128, one runner-random seed, all ten controls, 1/10/50 NRMSE, worst-flight/condition, condition/trajectory transfer, oracle-gap and every full-cost axis including R1/R4/R16. One seed may discard or authorize unchanged three-seed replication; it cannot promote.
