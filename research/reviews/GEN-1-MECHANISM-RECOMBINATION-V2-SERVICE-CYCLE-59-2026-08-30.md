# GEN-1 — heldout mechanism recombination v2 service cycle 59

## Scope and authorization

The user explicitly authorized the protected `heldout_mechanism_recombination_v2` migration. This was one service-only cycle: no experiment plan, scoring-seed realization, candidate scoring process, result or ledger row was created. No external model/API, dependency or cooldown was added.

## Corrections

V2 is a thin versioned entry over the unchanged v1 scientific task. Its worlds, opaque-state construction, train/held-out composition split, public/privileged boundary, metrics, directions, budgets, controls and seed policy are unchanged.

The migration makes four infrastructure corrections:

1. The closed result-summary schema now permits bounded `minimum_combination_accuracy`. A complete-result regression and a general aggregate-output/schema-coverage regression prevent another preregisterable metric from being rejected after scoring.
2. `config/baseline_semantics.json`, every registered conformance test and registered candidate implementation are assigned to the candidate-bundle digest. A regression proves their post-plan mutation changes the candidate bundle while preserving the evaluator digest.
3. After audited seed realization and atomic runtime-plan creation, the runner appends and fsyncs `experiment_scoring_started` with the plan hash, policy, realized seeds and runtime-plan hash.
4. Any unexpected post-seed failure appends and fsyncs `experiment_runner_postseed_failure` with error and surviving worker hashes, clears active state and automatically invalidates a result-less plan. A forced final-validation regression proves seed/artifact survival, no result/ledger commit and terminal rerun rejection.

## Verification

All 249 tests passed before freeze. An in-memory future v2 child plan validates and all five required semantic baseline nodes pass. The active manifest contains 441 protected files:

- evaluator SHA-256: `0f3be05e3843e424be4e3a98a115000972a729ef49c25f6c5d671da70c78e3b0`;
- candidate-bundle SHA-256: `0aafca973bc4a5f112ad464051acdec6a7f8413634396a6fe6e30d9ca70c5395`;
- manifest file SHA-256: `50270b240526571ca806b2f879571b9c50157a80bdc32bcd44271a2ce0dc82ec`;
- archived v1 manifest: `research/manifests/heldout_mechanism_recombination_v1-protocol-v2-0cf208fa5706.json`;
- archived v1 manifest SHA-256: `d914f34697a786fca61d1238ec6e234bdcaf7b0cbf40437598dfcbf8ee73d8b8`.

Historical integrity checks passed: the v1 evaluator file remains SHA-256 `01e817792651340b8c4db659fca2badb2efb2284be7e60a1d10262743d8efc4a`; EXP-0054 and EXP-0055 still match registered canonical hashes `fdfbd6d651313e3a12dd50011d257447ee0319299091ad6f3d2475077f710f1f` and `a5567c8bf1995e7fee91df537e1b7c08ced3a744daeccf93c15695edf904ebcf`; all nine EXP-0055 diagnostic artifacts still match their correction manifest.

## Decision and exact next experiment

Keep the corrected v2 infrastructure. It is not scientific evidence and HYP-0021 confidence remains `0.18`. In the next wake, preregister `EXP-20260830-0056` quick as the scientific-field-identical child of invalid EXP-0055 against evaluator `0f3be05e3843e424be4e3a98a115000972a729ef49c25f6c5d671da70c78e3b0`. Use K=`8/32`, D=`1/4/6`, Q=`8`, one runner-random seed, the same eight candidates and every registered quality/full-cost axis. Do not change candidate code or semantic records before scoring. One seed cannot promote.
