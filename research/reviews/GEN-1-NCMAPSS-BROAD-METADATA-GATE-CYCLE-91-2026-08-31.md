# GEN-1 — broader N-CMAPSS metadata gate, cycle 91

## Scope

This was one metadata-only design gate. It created no hypothesis, EXP-0060 plan, seed, candidate, runner invocation, score, result, evaluator mutation, dependency or extraction. The active v6 cohort and immutable scientific history remain unchanged.

## Observation

The primary descriptor defines one common HDF5 contract across eight N-CMAPSS sets and 128 engines: scenario descriptors `W`, measured sensors `X_s`, virtual sensors `X_v`, private health parameters `T`, RUL target `Y`, and auxiliary unit/cycle/flight-class/health-state data `A`. DS01, DS02, DS03, DS05, DS06, DS07 and DS08 cover flight classes 1/2/3; DS04 covers 2/3. Fault support is subset-specific.

Pooling arbitrary subsets would not remove source routing because each subset is coupled to a distinct fault support. A cleaner metadata candidate is the single `DS08a-009` member. The primary descriptor says DS08a has 15 engines, all three flight classes, one shared failure mode affecting efficiency and flow in every rotating component. This removes subset identity as a dev/test cue and keeps one unchanged `W+X_s` contract.

The already verified official archive contains exactly `data_set/N-CMAPSS_DS08a-009.h5`, uncompressed size `3,236,762,200` bytes, compressed size `1,801,568,073`, CRC32 `b823a8fe`. No member was extracted in this wake. Current free space is 142,411,083,776 bytes, so extracting this one member leaves far more than the 40 GiB guard.

A secondary community loader documents units 1–9 as development and 10–15 as test. Combined with 15 total engines and three classes, DS08a is the only inspected single-subset candidate capable of providing exactly three development and two held-out engines per class. This class balance is only a possibility: the primary paper does not publish per-unit classes, and secondary metadata is not accepted as authoritative. Exact split and class counts must come from `A_dev/A_test` after extraction.

## Interpretation and uncertainty

DS08a deserves one bounded real-file gate because it can repair both structural defects found in DS02: one source-identical fault support and enough apparent test engines to balance all three flight classes. It is not yet an admissible evaluator. Even a balanced `Fc` count can leave public early trajectories split-routable, and a pooled no-adaptation control may again remove the intended transfer challenge.

Confidence is `1.00` in the official member identity, size and CRC, `1.00` in the primary aggregate 15-engine/all-class/full-fault description, `0.91` that the documented 9/6 split is correct, and only `0.55` that it contains at least two development and two test engines in every class. No claim depends on the secondary split until real-file verification.

## Decision

`authorize_ds08a_only_extraction`. Do not extract another subset, activate a cohort, create EXP-0060, realize a seed or score anything.

## Exact next discriminating step

Next wake: stream-extract only `N-CMAPSS_DS08a-009.h5` from the already verified archive, check length, CRC and local SHA-256, then inspect exact schema and per-unit flight classes. Before viewing router or predictive metrics, freeze the same candidate-visible `W+X_s` leakage, fixed-prefix leave-one-engine-out split-router and persistence/pooled/adapted diagnostic controls. Reject immediately if any class has fewer than two development or two test engines; otherwise run the real-file gate. Evaluator migration remains a separate later wake.
