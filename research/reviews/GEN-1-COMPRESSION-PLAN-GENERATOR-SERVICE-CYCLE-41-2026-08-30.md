# Compression plan-generator service correction

## Defect observed before preregistration

All start gates passed for the intended `EXP-20260830-0044` quick, but `nextai plan new` contains branches only for cross-family and nonstationary protocols. The active schema requires `compression_protocol` for `heldout_repository_sequence_*`, so the official command necessarily creates an invalid document and cannot register the plan.

No immutable plan, candidate implementation, scoring seed, runner call or result exists for EXP-0044. Manually writing or registering a plan would bypass the operational contract. This wake is therefore restricted to a protected service correction.

## Minimal authorized correction

Add one configuration-to-plan mapping for the already frozen `[compression]` fields: corpus ID, whole-file SHA-256 split, evaluator-only test access, predict-then-reveal, shared candidate, mandatory baselines, frozen shared slow state, forbidden test tuning, declared horizons, state budget and invalidation rules. Add a focused regression that validates the generated mapping through the experiment-plan schema.

Do not change the benchmark, corpus, metric directions, seed policy, budgets, candidates or scientific success criteria. Re-freeze the evaluator only after the full test suite passes and verify that the candidate bundle digest is unchanged. EXP-0044 remains the exact next experiment for a later wake.

