# GEN-1 — DronePropA v4 single-D schema service cycle, cycle 81

## Pre-change defect record

HYP-0023 revision 1 was append-only registered without evidence. The first attempt to create EXP-0058 then failed before writing a plan: the global experiment schema required at least two `reasoning_depths`, while the frozen DronePropA quick matrix deliberately uses D=`[1]`. DronePropA evaluates horizons 1/10/50 inside every cell; adding a second D would only duplicate identical trials and distort cost and sample counts.

No experiment plan, scoring seed, candidate implementation, runner scoring process or result was created. The smallest valid repair is a version-separated v4 cohort that delegates all v3 execution unchanged, permits one D only for DronePropA plans and preserves the historical two-D minimum for every other cohort. The benchmark remains in maintenance until focused and full gates pass.

## Implemented correction

- Added the thin `heldout_dronepropa_factor_recombination_v4` wrapper over v3.
- Changed the schema base minimum for `reasoning_depths` to one and added a conditional two-item minimum for every benchmark whose name does not start with `heldout_dronepropa_`.
- Added a focused regression proving a DronePropA plan with D=`[1]` validates while a mechanism-recombination plan with the same one-item D list still fails.
- Preserved the v3 split, roles, corpus, execution, candidates, baseline records, directions, K/Q values, horizons, budgets, thresholds and seed policy.

## Verification and activation

The focused 36-test DronePropA set passed. Maintenance and active snapshots each passed the complete 287-test suite and integrity. The report regenerated and doctor passed after activation. No plan, seed or scoring occurred.

- active benchmark: `heldout_dronepropa_factor_recombination_v4`;
- evaluator SHA-256: `ed1382186e00e9c6de1957ac23f0c20cd4e79dd14b52bab486c372e9d8a467f2`;
- candidate-bundle SHA-256: `6b362c3a96f886be0a506aa6214828c484c508f44fc79cb0e9949efd3ab6eacf`;
- manifest file SHA-256: `1999ee64f024d0a7e844b84c6861a06d6b83b43bae51f3113059d0b33c7fed8e`;
- v4 wrapper SHA-256: `e7d35235c05344e8827155d7578055dc26595ddc85f07dc2b2a50bbef087d207`;
- split SHA-256: `fddd1c98aae13460ec58af25dbbea94f6f25177486da59a1e94f6a25f844a0e4`;
- free disk: `63.64 GiB`.

## Decision and exact next experiment

Decision: `keep` the v4 schema correction. Confidence is `0.999` that it removes the single-D preregistration deadlock without altering any numerical experiment semantics. HYP-0023 remains `proposed` at confidence `0.22` with no evidence experiment.

In the next wake, preregister exactly one quick `EXP-20260830-0058` for HYP-0023 against evaluator `ed1382186e00e9c6de1957ac23f0c20cd4e79dd14b52bab486c372e9d8a467f2`, then and only then implement the frozen rank-12 `shared_operator_subspace_arx`. Use K=8/32, D=1, Q=128, one runner-random seed, all ten controls and all registered quality, transfer, oracle-gap and R1/R4/R16 costs. One seed cannot promote.
