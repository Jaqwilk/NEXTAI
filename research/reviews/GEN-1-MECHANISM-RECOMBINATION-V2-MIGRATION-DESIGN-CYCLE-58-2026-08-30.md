# GEN-1 — mechanism recombination v2 migration design, cycle 58

## Scope

This was a design-only service cycle. It created no experiment plan, scoring seed, candidate execution or protected-file mutation. A protected cohort migration remains prohibited until explicit user approval.

## Corrected artifact observation

The prior EXP-0055 analysis correctly classified the run as scientifically unusable but incorrectly said its realized seed was not durably recoverable. `research/tmp/EXP-20260830-0055/runtime-plan.json` survives with SHA-256 `93598633fd6ed32a3ef758f154b8bc7d8a3e6321208b1e3822b20fd7dcc134e7` and seed `1598672193`. All eight worker JSON outputs also survive. Their exact paths and hashes are frozen in `research/audits/EXP-20260830-0055-postseed-artifacts.json`.

These artifacts remain diagnostic history only. EXP-0055 is terminally invalidated, has no validated result or ledger rows and cannot become evidence, change confidence, falsify HYP-0021 or be rerun.

## Root causes

1. The experiment-plan schema requires `minimum_combination_accuracy`, and metrics aggregation emits it, but the closed result-summary schema omitted the property. No cross-schema regression asserted that every configured/preregisterable metric can be serialized.
2. The runner writes the realized runtime plan and worker outputs atomically under `research/tmp`, but this durability is implicit. Its exception handler records only `last_failure_at`; it writes no append-only event pointing to the seed and artifact hashes and does not automatically invalidate a post-seed plan.
3. `config/baseline_semantics.json` and conformance tests are currently assigned to the evaluator-role digest. Because their hashes necessarily follow candidate implementation, this conflicts with the rule that candidates are implemented only after preregistration while only the candidate-bundle digest may change. EXP-0054 exposed this classification defect.

## Minimal authorized v2 migration

The smallest complete correction is one service-only cohort migration, with no plan or scoring:

1. Create `heldout_mechanism_recombination_v2` as a thin versioned evaluator entry over the unchanged v1 scientific boundary; update config and plan-schema cohort condition without changing maps, split, oracle, metrics, directions, budgets or seed policy.
2. Add `minimum_combination_accuracy` to the closed experiment-result summary schema with numeric/null type and `[0,1]` bounds.
3. Treat `config/baseline_semantics.json` and every conformance-test path referenced by that registry as candidate-bundle files in role digests. Keep all other tests and harness files in the evaluator digest. Add a test proving a post-plan candidate/registry/conformance change alters only the candidate bundle.
4. Immediately after audited seed realization and atomic runtime-plan write, append and fsync an `experiment_scoring_started` event containing experiment ID, plan hash, seed policy, realized seeds and runtime-plan path/hash.
5. On an unexpected exception after that event, append and fsync `experiment_runner_postseed_failure` with exception class/message plus hashes of every surviving worker artifact, and append terminal plan invalidation automatically. Never include candidate summaries in evidence or ledger rows on this path.
6. Add an integration-style monkeypatched runner regression that forces final result validation failure and proves: seed event exists, runtime plan survives, failure event points to it, plan is invalidated, no result/ledger row exists, state is cleared and a rerun is rejected.
7. Add a schema regression validating a complete recombination result containing `minimum_combination_accuracy`, plus full schema, semantic, audit and cohort tests.
8. Freeze v2, verify the old v1/EXP-0054/EXP-0055 artifacts remain byte-identical, and run full tests, integrity and doctor.

No dependency, external model/API, cooldown or scientific threshold changes are required.

## Exact next experiment after service

Only the wake after the authorized v2 service cycle may preregister `EXP-20260830-0056` as the scientific-field-identical child of EXP-0055 against the frozen v2 evaluator. It must use K=`8/32`, D=`1/4/6`, Q=`8`, one newly realized runner-random seed and the same eight candidates and full-cost axes. One seed cannot promote.
