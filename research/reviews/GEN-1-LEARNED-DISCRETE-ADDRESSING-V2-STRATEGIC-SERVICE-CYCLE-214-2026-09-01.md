# Learned discrete addressing v2 strategic service review — cycle 214

## Scope and evidence boundary

This was exactly one service-only cycle. It created no hypothesis event,
experiment plan, runner seed, main learned-address candidate, score, result or
scientific evidence. No completed plan, result, analysis or historical manifest
was edited. The strategy request's portfolio snapshot (91 experiments, 80 quick,
11 screen, 30 falsified) preceded valid EXP-20260901-0051. Durable state at the
start of this cycle was therefore 92 completed experiments: 81 quick, 11 screen,
0 deep; 31 hypotheses falsified, 22 dormant and only HYP-0012 testing. There are
still no `promising` or `promoted` hypotheses.

## Portfolio correction

Do not create `heldout_dronepropa_factor_recombination_v7` and do not continue
the sparse actuator-to-state Jacobian proposal. Its small fixed matrix and
equivalence to classical sparse system identification do not directly test the
remaining HYP-0012 barrier: learning an addressable representation from raw
observations without whole-knowledge access cost. This append-only correction
supersedes the earlier next-step recommendation without modifying its completed
analysis.

The retained pattern is mixed but consistent. Classical indexes demonstrate
local access but not learned routing. Experience compilation can reduce warm
query cost while acquisition, fit and index construction dominate. WT recurrent
residual replicated within one domain but did not transfer across families.
Learned pushdown transferred in depth and across a disjoint corpus but recovered
0/432 bytes under the adversarial inverse operation. EXP-0049 found useful
partition structure, yet the shuffled source-identical partition was better and
the full cost was about 15 times ridge. Across the portfolio, K-independent
queries, sparse updates, warm reuse or OOD depth sometimes occur separately;
learned representation, matched quality and full-cost non-dominance have not
occurred together.

Decision: end the sequence of hand-coded one-off predictors and run one direct,
falsifiable learned-discrete-addressing test under HYP-0012. Rigor is unchanged.

## Benchmark decision and frozen contract

`latent_entity_binding_retrieval_v1` is insufficient because it supplies paired
positive views and only K=8/32. A cohort-separated
`latent_entity_binding_retrieval_v2` is necessary and is now active. It exposes
only 24-dimensional dense nonlinear raw observations, unlabeled transition
bursts with an unknown change point, fresh held-out views, K=32/320/3200,
D=1/4/8, Q=16 and one local insertion. Implementable roles receive no entity
ID, key, latent coordinate, class/family, path, scoring target or privileged
routing.

The future role order is frozen:

1. `learned_discrete_address_index_v1`: learned encoder -> 16-bit discrete key
   -> four-probe bounded index -> at most eight verifier candidates -> at most
   32 bounded fallback candidates.
2. `source_identical_dense_scan_v1`: the same learned encoder and verifier with
   full dense access.
3. `source_identical_frozen_encoder_index_v1`: the same bounded index with the
   encoder frozen.
4. `source_identical_shuffled_representation_index_v1`: the same bounded index
   with the representation shuffled.
5. `raw_nearest_neighbour_scan_v1`: classical raw-space full scan.
6. `local_dense_transition_gru_v1`: local 32-unit dense GRU, no external memory,
   pretrained weights or model API.
7. `privileged_exact_entity_key_v1`: evaluator-private exact-key control,
   excluded from implementable Pareto evidence.

Roles 1-4 must share encoder source, widths 24/32/16, initialization, data order,
outputs, verifier, update, constants and accounting outside the registered
intervention. Other frozen constants are bucket capacity 8, 32 Adam epochs,
batch 64, learning rate 0.001, state limit 64 MiB, accuracy margin 0.02,
maximum K-cost slope 0.30 and R1/R4/R16/R256/R4096. Acquisition, encoding, fit,
routing/index, verifier, fallback, query, local update, state and bytes touched
must all be charged. Fallback may not grow with K and insertion may not globally
refit the encoder.

## Local learner infrastructure

The dependency is pinned to `torch==2.6.0` from the explicit official cu124
index. Installed runtime: torch 2.6.0+cu124, CUDA 12.4, NVIDIA RTX 4070, driver
551.78. CPU and CUDA deterministic development fits pass. The shared local
module only supplies deterministic device selection, parameter bytes and
explicit MLP/GRU operation accounting; it contains no pretrained loader,
network client, model API or framework layer. Candidate subprocesses retain
network denial and now receive deterministic CuBLAS workspace configuration.

## Validation and immutable digests

- Focused semantic/Torch tests: 12 PASS.
- Full pytest: 581 PASS, including existing atomic complete/timeout/crash/
  budget-failure/missing-metric supervisor E2E tests.
- All three mandatory control source audits and semantic tests: PASS.
- Largest-scale raw-scan real smoke: K=3200, D=8, status complete, accuracy 1.0,
  K-linear query cost preserved as the discriminating baseline.
- Evaluator digest: `e01c9361294c6f8eea2c1d29644a7dc6a3fa3b60037131e107ee269c053890e6`.
- Candidate bundle digest: `12b9dbd2981190dce5c2a9928300523f0e9dff23119e984c75526fed894a00a1`.
- Manifest digest: `b2a19b33f1031891d42905f9d325325e2f9c6ec37dfb7f5d5ff370966ea1d423`.
- Preflight certificate digest: `af877b93a54566c6b061bfd622040926905ad7f34d80e0d98bfe7bbbfff9357d`.
- Integrity: PASS, 753 protected files. Doctor: PASS.

## Only permitted next experiment

In the next separate wake, preregister (but do not create now)
`research/plans/EXP-20260901-0052.json` as one quick revision/test of HYP-0012.
It must use the seven frozen roles above, K=32/320/3200, D=1/4/8, Q=16, one
runner-random seed, the frozen local Torch encoder and all costs/reuse horizons.
Success requires quality within 0.02 of source-identical dense scan, meaningful
advantage over frozen and shuffled representations, confusable-view robustness,
full K-cost slope below 0.30, bounded fallback, local insertion without global
refit, and no Pareto domination by raw NN or the dense GRU. A negative ends this
exact rule without tuning. A positive authorizes only an unchanged three-seed
screen with an adversarial or disjoint corpus; it cannot promote.
