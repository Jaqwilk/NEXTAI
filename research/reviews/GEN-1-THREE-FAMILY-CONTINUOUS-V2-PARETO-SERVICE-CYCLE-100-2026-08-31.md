# Three-family continuous v2 Pareto service cycle 100

## Scope

This was one protected service-only migration authorized by the user's standing approval. It created no hypothesis, experiment plan, scoring seed, runner call, result, evidence or confidence update. Historical `heldout_three_family_continuous_transfer_v1` plans, results and analyses were not modified.

## Defect

`EXP-20260831-0001` retained its preregistered axes, but its implementable Pareto frontier was empty because `shared_vs_independent_gain` and `cross_family_transfer_gain` exist only on their respective intervention rows. Requiring those fields on every ordinary baseline made a capability frontier impossible even when all candidates completed.

## Minimal correction

`heldout_three_family_continuous_transfer_v2` reuses the v1 evaluator and changes only prospective decision semantics. Its immutable plan contract names fifteen universal capability/full-cost Pareto axes. The two intervention-specific gains remain required primary metrics but are separate hard promotion gates, each aggregated as the minimum over all family/K/seed cells. A missing, zero or negative gain blocks `promising` and `promoted`. Completed candidates retain a frontier when another candidate times out; a mandatory-control timeout still blocks promotion.

No world, split, tensor, normalization, loss, causal assignment, baseline algorithm, metric value, budget or candidate implementation changed.

## Verification

- Historical plan/result schema validation: PASS.
- Seven registered tensor baseline semantic tests and hashes: PASS.
- Synthetic complete-control Pareto regression: PASS and non-empty without causal fields on ordinary controls.
- Positive/zero causal promotion gate regression: PASS.
- Timeout/missing-metric regression: PASS.
- Full pytest: 319 PASS.
- Integrity: PASS, 494 protected files.
- Doctor: PASS.
- Plans/results/registry/ledger stayed at 61/53/61/384.

## Decision and next discriminator

Keep v2 active. The next wake may preregister one quick experiment for a source-identical, permutation-invariant bounded residual learner that treats channels exchangeably and predicts clipped increments around persistence under shared, independent, cross-family-only and support-only assignments. It must use the v2 capability frontier and both causal gates; one seed can only discard or authorize unchanged replication.
