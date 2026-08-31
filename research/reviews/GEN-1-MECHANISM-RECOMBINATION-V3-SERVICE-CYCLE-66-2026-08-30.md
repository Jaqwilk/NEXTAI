# heldout_mechanism_recombination_v3 — protected service migration

## Authorization and scope

The user explicitly authorized the protected `heldout_mechanism_recombination_v3` migration and future migrations of the same kind. This standing authorization covers only justified, versioned NEXTAI protocol/evaluator migrations that preserve the fixed objective, immutable scientific history, integrity gates, budgets, and bounded-cycle rule.

This cycle was service-only. It created no experiment plan, candidate implementation, scoring seed, runner invocation, scored result, or ledger row.

## Changes

- Activated `heldout_mechanism_recombination_v3` through a benchmark wrapper delegating to the unchanged v2 evaluator.
- Replaced the three HYP-0021 role IDs in active configuration with `operator_algebra_completion`, `operator_algebra_independent`, and `operator_algebra_no_relations`.
- Split plan validation by cohort: v1/v2 require the historical role triplet; v3 requires the operator-algebra triplet. All versions retain the same five controls, metrics, directions, task constants, horizons, budgets, and invalidation contract.
- Added regression tests proving immutable EXP-0056 still validates, a prospective v3 fixture validates, and cross-version role substitution fails in both directions.
- Updated the runner post-seed durability fixture to the active v3 cohort without changing its failure semantics.

No operator-algebra learner code was added. The candidate bundle remains unchanged.

## Verification

- Full suite: 250 tests passed.
- Historical EXP-0056 validation, v3 fixture, and bidirectional wrong-role rejection: PASS.
- Archived v2 manifest: `research/manifests/heldout_mechanism_recombination_v2-protocol-v2-242f01723801.json`, SHA-256 `50270b240526571ca806b2f879571b9c50157a80bdc32bcd44271a2ce0dc82ec`.
- Active manifest SHA-256: `4b9ca9131bd195d82fa937cac7c470db4205339a5006b8e3e624c6c92e0d12f6`.
- Active evaluator SHA-256: `c57762ee52133e5fa8cf732d8c5c844dd877bbdccabb58edb3cce4a0858ed553`.
- Candidate bundle SHA-256: `0aafca973bc4a5f112ad464051acdec6a7f8413634396a6fe6e30d9ca70c5395` (unchanged).
- Integrity: PASS, 442 protected files. Doctor: PASS.

## Scientific status and next experiment

This migration is infrastructure, not evidence. HYP-0022 remains `proposed` at confidence 0.14. In the next wake only, preregister EXP-20260830-0057 against the frozen v3 evaluator before implementing any candidate or realizing a seed. The quick screen must include the preregistered partial-permutation semantic fixture, K=8/32, D=1/4/6, Q=8, one runner-random seed, all three v3 roles, the five frozen controls, and every existing full-cost axis. One seed may discard the hypothesis or authorize unchanged replication; it cannot promote it.
