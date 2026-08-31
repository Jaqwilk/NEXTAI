# GEN-1 — report Pareto provenance v5 service cycle 110

## Scope

This was exactly one protected service-only cycle. It created no hypothesis, experiment plan,
scoring seed or scored result and did not invoke `nextai run`. All completed plans, results,
analyses and ledgers remain append-only. The report generated before the correction is preserved
at `research/reports/REPORT-PRE-PARETO-PROVENANCE-FIX-CYCLE-109-2026-08-31.md` with SHA-256
`7fdbea44584e80c4785f005200ef4cf755cfd8c25e6282d7cb174ae6ba18e102`.

## Defect and correction

The audited runner stored the correct universal v4 axes in immutable result `pareto_metrics`, but
`report.py` independently reconstructed axes from the broader plan `primary_metrics`. That made
candidate-specific `shared_vs_independent_gain` and `cross_family_transfer_gain` appear to be
universal Pareto axes even though protocol v2 defines them only as promotion gates.

V5 makes immutable result artifacts the sole report source for Pareto axes. Promotion-only gates
remain visible on a separate line. Reports no longer intersect, guess or silently delete axes.
If a valid legacy result lacks `pareto_metrics`, or valid results in one benchmark/budget cohort
disagree, that cohort explicitly says its frontier is unavailable and computes no Pareto marker.
The audit found 35 legacy results without stored contracts and one inconsistent historical cohort,
`cross_family_shared_representation_v3/quick`; both conditions are now visible rather than hidden.

## Verification

The v4 quick report now lists only transfer accuracy, minimum-family accuracy and stability as
maximized axes, plus the twelve universal quality/full-cost minimized axes stored by EXP-0005.
The two causal contrasts are displayed separately as promotion-only gates. A focused regression
also proves missing and inconsistent immutable contracts fail closed.

All 338 tests passed. All ten unique required semantic baseline nodes passed. Integrity passed for
509 protected files and doctor passed. Active v5 evaluator SHA-256 is
`b6f103415a7500e943008057c0bcb5b2708e1f5f1f76a8f0fa8a55afb09cc683`; candidate bundle is
`c9f3bc45fc089dae6bfc5832ac6fa37d3da11d1e9705eaf50538bc3797d41fef`; preflight certificate is
`8f69959910194735e63c37bad79d911a0a503430f9393e1820e851417b9768d2`.
The final v4 manifest is archived at
`research/manifests/heldout_three_family_continuous_transfer_v4-protocol-v2-f93217e51069.json`
with file SHA-256 `da22865bf6f07e3e24611a8d2757926cb556f95b9439373f2e414e1c56228271`.

## Decision

`keep` the v5 reporting and integrity infrastructure. This service correction changes no metric,
result, scientific validity, evidence, hypothesis confidence or conclusion from EXP-0005.

## Exact next discriminating experiment

The next wake is one no-scoring mechanism-selection review on the unchanged benchmark inventory.
Compare at most three genuinely different principles, excluding direct parameter sharing, fixed
expert mixtures, bounded residual tuning and predictive hashing already tested. Select at most one
only if it has a preregisterable qualitative signature beyond small accuracy gains: matched-quality
cost scaling over at least three K values, local updates without global retraining and OOD operator
reuse. Create no benchmark, schema, hypothesis, plan, seed or scoring in that review. If no proposal
survives, record that result rather than manufacturing a variant.
