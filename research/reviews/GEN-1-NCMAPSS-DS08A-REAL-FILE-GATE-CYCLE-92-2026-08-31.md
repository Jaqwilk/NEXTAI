# GEN-1 — N-CMAPSS DS08a real-file gate, cycle 92

## Scope

This was one service-only acquisition and prerequisite gate. It created no hypothesis, EXP-0060 plan, seed, candidate, runner invocation, score, result, evaluator mutation or dependency. The active v6 cohort and immutable scientific history remain unchanged.

## Observation

The single authorized member `data_set/N-CMAPSS_DS08a-009.h5` was streamed from the already verified official nested archive without materializing that archive or extracting another dataset. The final file is `3,236,762,200` bytes, CRC32 `b823a8fe`, and SHA-256 `10ddf52e5441a05e3d0d8d797a34e0e5a9ac73dce8ae35d7b22d1ef224d24836`. The atomic `.partial` file was renamed only after length, CRC and SHA verification. Free storage remained `129.61 GiB`, above the frozen `40 GiB` guard.

The real `A_dev` and `A_test` arrays confirm development units 1–9 and test units 10–15. Development flight-class counts are class 1: 3, class 2: 4, class 3: 2. Test counts are class 1: 2, class 2: 1, class 3: 3. Thus the previously frozen prerequisite of at least two development and two test engines in every class fails: class 2 has only test unit 11.

The failure was known before any early-prefix router, leakage statistic or predictive control was run. Those diagnostics were deliberately skipped, so no post-result redesign or scientific score exists.

## Interpretation and uncertainty

The official DS08a split cannot support the intended class-balanced unseen-engine comparison. With one held-out class-2 engine, class-conditioned uncertainty and replication cannot be separated from unit idiosyncrasy. This rejects this exact evaluator design, not shared representations or N-CMAPSS generally.

Confidence is `1.00` in the bytes, split and class counts because they were read directly from the verified file. There is no predictive uncertainty to report because predictive metrics were not computed.

## Decision

`reject_before_semantic_metrics_and_evaluator`. Keep the acquired file and all negative audit history. Do not activate DS08a, migrate a protected evaluator, create EXP-0060, realize a seed or score anything.

## Exact next discriminating step

In a later wake, perform one metadata-only search across already described source-identical datasets or a preregisterable immutable partition that preserves disjoint engines and gives at least two held-out engines per relevant class. Reject any design requiring test-engine reuse or benchmark-specific relabeling. Only after that prerequisite passes may a separate wake freeze and run leakage, router and no-adaptation diagnostics.
