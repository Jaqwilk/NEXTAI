# PC-01 telemetry lifecycle migration V1

## Scope and immutable plan

- Experiment ID: none; this was a no-training, no-scoring maintenance cycle.
- Immutable plan: `research/plans/PC-01-TELEMETRY-LIFECYCLE-MIGRATION-V1.json`.
- Authority: `research/laboratory/PC-01-TELEMETRY-LIFECYCLE-MIGRATION-20260905-V1.json`.
- The preregistration's mistyped final-series canonical hash was not overwritten. The append-only addendum records the original and corrected values with the exact Git derivation.

## Objective observations

- The terminal PC-01 bundle is now checked against commit `f08cd02fb1cc80ed169b63c1917eb1b979c0b238`. The closure verifies the v3 manifest, V7 certificate and its committed source/test files, conformance report, final-series bytes, plan/attempt ledgers, five plans, five results, and their preserved runtime receipts.
- All runtime artifacts for the fifth attempt, previously local and ignored, were committed without changing their bytes. This closes the reproducibility gap found by the first targeted run.
- The historical V1 reader still deterministically propagates `FileNotFoundError`. The live reader now treats only transient path absence as temporary unavailability; malformed content and unrelated errors still fail closed, and the parent one-second continuous-gap deadline is unchanged.
- The first complete regression report is preserved: 933 tests, 8 failures, 0 errors, 0 skips, 133.029 seconds. Every failure was an obsolete live-PC-01 configuration assumption or stale preflight identity exposed by the migration.
- After updating only lifecycle fixtures, historical transition resolution, and the preflight identity, the second complete regression passed: 933 tests, 0 failures, 0 errors, 0 skips, 141.366 seconds.
- The focused migration regression passed: 59 tests, 0 failures, 0 errors, 0 skips, 11.434 seconds.
- The new live identity is `wt01_causal_revalidation_preparation_v1`, status `maintenance`, evaluator `783dcc676c4294e9a4505476710ffbbb8e7a03e334cf76638a9f2df7908a7b9e`. It has no scoring entry point.
- Re-authentication after migration returned the unchanged PC-01 decision: paired deltas `[5.559899971855426, 5.634094730026742, 5.528301116150491]`, mean `5.574098606010886`, sample SD `0.054307210323858456`, lower 95% t bound `5.439192016820712`.
- No model was trained, no benchmark was scored, no final data was accessed, and no dependency or dataset was installed/downloaded.

## Interpretation and confidence

The lifecycle divergence is resolved: terminal PC-01 evidence no longer depends on mutable live source or evaluator paths, while the prospective telemetry fix is active only under a fresh maintenance identity. Confidence is high for repository reproducibility and gate behavior because the result is backed by exact Git-object verification, deliberate substitution/current-file fault tests, a preserved failed full run, and a zero-failure complete rerun. This cycle adds no evidence for architectural capability, economic advantage, or transfer.

## Decision

**Keep** the Git-backed closure and live telemetry V2 behavior. PC-01 remains `positive_control_pass`, one-corpus diagnostic only; architecture promotion, economic advantage, and transfer remain false. Do not rerun PC-01.

## Integrity and budget

- Migration service charge: 30 minutes conservatively charged of the separate 60-minute cap.
- Training: 0 seconds; scoring runs: 0; final-data access: none.
- Full regression success condition: met on V2, with V1 failure preserved.
- Manifest, preflight certificate, report provenance, doctor, and laboratory gates: required to pass at final readback.
- Historical budgets and the eight-experiment G1 window were not reset or reinterpreted.

## Exact next discriminating experiment

After explicit user review, prepare—but do not score—a fresh WT-01 causal revalidation contract. It must freeze the claim (causal learned mechanism effect, not economics or transfer), legal observations, learned candidate, source-identical causal ablation, competent classical controls, matched end-to-end accounting, seed policy, effect sizes, decision thresholds, development budget, and untouched evaluation data before any implementation or result access.
