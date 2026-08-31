# GEN-1 — preflight and outcome-contract v6 service, cycle 86

## Scope

One protected maintenance-only cycle authorized explicitly before any EXP-0060 work. No hypothesis, experiment plan, scoring seed, candidate scoring, result, evidence or confidence update was created. Completed plans, results and analyses were not edited.

## Changes

- Central final-result validation now requires finite metrics, NRMSE and charged costs `>= 0`, and accuracy/rate/precision/coverage/retention metrics in `[0,1]`. Continuous `conditional_log_loss` remains any finite real value.
- Exact final-schema tests cover complete, timeout, crash, memory-budget failure and a complete outcome with missing metrics. The existing runner writes one atomic supervisor artifact immediately after every candidate outcome and before comparisons/frontier/final aggregation; the forced post-seed failure regression now checks all outcome classes.
- Pareto axes are retained from the immutable plan contract. Only complete, integrity-valid, scientifically valid, non-privileged candidates with every declared axis may enter a frontier. Timeout and missing-metric rows remain visible failures but cannot erase axes or enter the frontier. A non-complete mandatory baseline is an explicit promotion-gate failure.
- V6 renames the two unstable v2 oracle-labelled implementations, without changing their computation, to `privileged_all_condition_support_arx_v3` and `privileged_same_condition_support_arx_v3`. They are excluded privileged support controls, not bounds. The signed comparison is `privileged_support_gain`, not an oracle-gap claim.
- `research/checks/preflight_certificate.json` binds the evaluator digest, runner, all schemas, semantic baseline registry and evaluation manifest. The audited runner verifies it after integrity and semantic conformance but before seed realization; doctor verifies it for an active cohort.

## Verification

- Semantic baseline gate: PASS, 10 required controls and 10 unique conformance nodes, including synthetic semantic checks and real MAT one-step smoke.
- Full pytest: PASS, 297 tests.
- Report generation: PASS.
- Integrity: PASS, 477 protected files.
- Doctor: PASS; no STOP, PAUSE, active lock or pending plan.
- Disk: 68,243,402,752 bytes free on C: after the cycle. No corpus download or duplicate archive was created.

The active cohort is `heldout_dronepropa_factor_recombination_v6`. Evaluator SHA-256 is `148b7acefdb9a9efdccd1cfc0bdee645df4982001295592929dcc2182da0b61a`; manifest file SHA-256 is `77d6ceb7195eb71835cd99739d558c2794f9f5fa09b86c71f26610f2afe052ea`; certificate content digest is `c48dd95aee6db30fc067fcc8de031eaedeb5352edf162ad09524364f8328f0a7` and certificate file SHA-256 is `da8131d7079b6f481fc160bbbc9f643653739e37ef82d8fa62b89f9079ea1bb5`.

## Decision and next discriminator

Decision: `keep` the v6 infrastructure; this maintenance is not scientific evidence. EXP-0060 remains absent. In the next wake, do not resurrect the rejected three-family native-contract proposal or treat the privileged support controls as bounds. The next justified discriminator is the already specified no-download primary-source/rights/identifiability gate for NASA C-MAPSS. Only if that gate yields an immutable, leakage-safe same-schema multi-unit task should EXP-0060 be preregistered in a later wake; otherwise record `reject_before_download` and leave EXP-0060 unused.
