# GEN-1 — protected DronePropA evaluator migration, cycle 77

## Scope

This was one user-authorized protected service cycle. It created and froze the data, split, contract and semantic controls for `heldout_dronepropa_factor_recombination_v1`, but deliberately leaves the cohort in `maintenance`: the protected `run_suite` execution path is not yet implemented and therefore cannot honestly be advertised as active. It created no hypothesis, experiment ID, immutable experiment plan, runner seed, shared learner, predictive score, result or external model/API call.

The prior evaluator manifest is preserved at `research/manifests/heldout_mechanism_recombination_v3-protocol-v2-6a18643e051d.json`. The intermediate maintenance snapshot is preserved at `research/manifests/heldout_dronepropa_factor_recombination_v1-protocol-v2-755464845fd0.json`.

## Frozen evaluator and data boundary

The active manifest is `research/eval_manifest.json`, file SHA-256 `da143c9c01391b62b744aaeba5713377ed13419245472c8b8b2c823e78d098df`. It protects 465 files and reports:

- evaluator SHA-256 `b4774cd14f11e83a522238ee0a1f1b7e6d27f3f9d270566628b77973d18851a4`;
- candidate-bundle SHA-256 `95b15878aba75a63e1f9cbac24c641e2b724b9f57e42e79593427beb3c5e2d6a`;
- protocol v2;
- benchmark status `maintenance`.

The protected data boundary now includes the acquisition manifest, the 130-file numeric/hash manifest and the anonymous split. The split remains 64 train, 8 validation, 24 unseen-pair test, 8 healthy-D2/D3 OOD diagnostic and 26 reserved t4 files; SHA-256 `8381cc9d8e245059cf6ce49a5ba988bb50a588a14de445e73cb72709fdaffed0`. The existing 4.44 GB archive and 4.54 GB extraction are reused in place; no download or duplicate cache was created.

The evaluator module SHA-256 is `c4c994b30ebc0eef1d2e92d6a7741b21342066a70e6584b7c632f607388b93ec`. Its dependency-free MATLAB-v5 loader verifies the raw SHA-256, supports the single previously verified incomplete zlib trailer, validates the 1 kHz monotonic time axis and exposes only motor rows 47/49/51/53 plus state rows 27–32. Bad ESC rows 48/50/52/54 are never selected. A real 87,837-sample flight produced finite arrays `(87837,4)` and `(87837,6)` plus the frozen `32×320 → 32×6` adaptation examples.

Adaptation uses 32 deterministic anchors in the first fifth of the central usable interval. Evaluation uses 128 runner-random anchors from disjoint guarded bins; history plus 50-step target windows cannot overlap. One-step evaluation is teacher-forced. Ten/50-step evaluation is recursive with identical evaluator-supplied future motor controls and hidden future state targets.

## Semantic baselines

`config/baseline_semantics.json` SHA-256 is `9a59803ec1d9bf88f8ff4851f37b6feadfc7d8ae838449f60fda221e592976dc`. The pre-seed gate now recognizes `dronepropa_protocol` and requires all ten exact controls:

1. persistence state;
2. affine ridge ARX;
3. predict-then-update RLS ARX with covariance `1000 I` and forgetting 1;
4. nearest adaptation-fitted operator template without labels;
5. source-identical independent ARX;
6. no-sharing pooled ARX;
7. empirical Gaussian joint with exact conditioning;
8. contextual Gaussian Chow–Liu residual tree;
9. fully charged privileged condition specialist;
10. privileged same-condition oracle.

Each record contains an exact ID, version, algorithm specification, wrapper hash, shared implementation hash and pytest node/hash. The common implementation SHA-256 is `26b968b80a6623d46c4ab123d8f11ce3deb348387454b60b946e354a5e6620d6`; the semantic fixture file SHA-256 is `a3d7e96f603f5a7c315dd434902feec482e3f51f9fe3af949797614b9b3fdcde`. The gate executed seven unique discriminating nodes for all ten controls and passed. The privileged specialist and oracle use `oracle_` naming and are excluded from implementable Pareto evidence.

## Metrics and full cost

The protected plan/result schemas and aggregation now carry teacher-forced NRMSE, 10/50 rollout NRMSE, mean/worst-flight/worst-condition NRMSE, stable-rollout rate, oracle-gap closure, minimum condition/trajectory transfer gain, preprocessing and adaptation cost, plus the existing acquisition, fit/meta-fit, query/update, bytes touched, resident/peak state and R1/R4/R16 totals. Full workload charges both the 4,438,911,840-byte archive boundary and 4,537,694,153 extracted bytes before model-specific work.

The plan schema requires the exact anonymous split, candidate boundary, horizon/anchor contract, all ten controls and every principal quality/cost axis. Baseline semantic fixtures execute before runner seed realization. Status `maintenance` is covered by an isolated hard-gate test and prevents plan creation or scoring while the execution path is incomplete.

## Verification and decision

- focused real-MAT loader: PASS;
- semantic baseline gate: 10/10 records, seven unique fixtures PASS;
- candidate source audit: 294 candidates PASS;
- complete test suite: `268 passed`;
- integrity: PASS, 465 protected files;
- doctor: PASS;
- pending plans: 0;
- predictive scoring: none.

Decision: `inconclusive`; keep the protected migration in maintenance. Confidence is `0.995` that the data/interface/split and pre-seed semantic gates are enforced as specified, but only `0.10` that the cohort is execution-ready because `run_suite` currently refuses every candidate. No scientific conclusion or hypothesis-confidence change follows from infrastructure work.

## Exact next discriminating experiment

In the next wake, perform one further service-only cycle with no hypothesis, EXP ID, plan or seed: implement and test the generic DronePropA `run_suite` path for the already registered baseline interfaces, including normalization from training/adaptation only, teacher-forced 1-step and recursive 10/50-step evaluation, aggregation and complete R1/R4/R16 accounting. Prove a tiny synthetic end-to-end candidate run and a real one-flight smoke path, then freeze and activate only if the full suite, integrity and doctor pass. Only a later wake may preregister HYP-0023 and EXP-20260830-0058 before implementing `shared_operator_subspace_arx`.
