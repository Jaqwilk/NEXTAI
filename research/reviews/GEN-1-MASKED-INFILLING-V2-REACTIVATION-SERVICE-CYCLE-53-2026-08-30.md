# Masked infilling v2 — protected reactivation service cycle 53

## Scope

This is the service-only wake selected by the mandatory cycle-52 portfolio and literature review. No immutable experiment plan, scoring seed, runner candidate process, scored result or candidate implementation was created. The only protocol mutation was changing the active `benchmark_version` from `cross_family_relation_fragment_transfer_v4` to the already existing and previously repaired `heldout_parallel_masked_infilling_v2`.

## Exact semantic preservation

The current files were compared with immutable archive `research/manifests/heldout_parallel_masked_infilling_v2-protocol-v2-b86188bf0719.json` (file SHA-256 `537b109e575bd4f1976e2f4b298b09f1da31f10737b3e58fb4de01174c03b499`). These nineteen masked-cohort paths retained identical content hashes:

- `heldout_parallel_masked_infilling_v1.py` and its v2 wrapper;
- `masked_refinement_contract.py`;
- iterative and forced-one-pass learners;
- uniform, empirical-unigram, PPM-D, CTW, dense autoregressive, exact bidirectional Markov, parallel Markov BP and privileged oracle candidates and their shared cores;
- `tests/test_parallel_masked_infilling.py` and `tests/test_baseline_semantics.py`.

`config/baseline_semantics.json` and its verifier differ from the old archive only because the subsequent service history added cross-family cohorts and stronger validity handling. The registered masked baseline IDs, versions, specifications, implementation hashes, test nodes and test hashes remain unchanged.

The frozen corpus remains `nextai_disjoint_masked_corpus_sha256_v1`: 48 whole files, 35 train / 4 validation / 9 test, 305,106 bytes, no exact duplicate hash, no path overlap with EXP-0044, maximum cross-role normalized-line Jaccard `0.2258` and containment `0.4375`. Span lengths remain `8/32/128`, context 64 bytes and refinement rounds are supplied by the unchanged quick D grid `1/4/6`.

## Mandatory baseline semantics

- PPM is `ppm_d_byte_order5_v1`: maximum order 5, PPM-D distinct-symbol escape, longest-suffix backoff through uniform order -1, full exclusion, fixed prior-byte context during root-to-depth training updates, frozen trained counts during left-to-right inference.
- CTW is `ctw_multinomial_byte_depth2_v1`: 256 runner-permuted symbols, depth 2, symmetric Dirichlet-1/2 KT estimator at every node, exact `0.5 * local KT + 0.5 * child-product` recursion, root-to-leaf counts and bottom-up weight finalization, frozen inference tree.
- The intentional first-order Markov impostor continues to fail both PPM and CTW conformance.
- The runner must verify eight required semantic baseline records and execute every registered conformance node before scoring-seed realization.

## Frozen integrity

- benchmark: `heldout_parallel_masked_infilling_v2`;
- evaluator SHA-256: `fab675150f7f4d5af8ff3433ab10e08743fe55a77c0444a42eff037b9506a3f0`;
- candidate bundle SHA-256: `32a251727a844ae433751aa0cf7aba34a3f4b2789b7fc2afa318496969547514`;
- manifest SHA-256: `24c6ed602452742e0b77de1593565c0f23839525b1df702ffe71c24a988096d5`;
- protected files: 425;
- prior active v4 manifest archive: `research/manifests/cross_family_relation_fragment_transfer_v4-protocol-v2-3f34edba46f3.json`, SHA-256 `2a3083101694995a5a2d9766f59e82ec097aecb07258631da49992055db1e792`.

Twenty-five focused corpus/protocol/semantic tests passed, including the deliberate false-baseline rejection. The full 233-test suite, report generation, integrity verification and doctor passed. Eight semantic baselines were verified. Disk free space was `72.58 GiB`.

## Decision and exact next experiment

The corrected cohort is ready for a scientifically valid quick. HYP-0017 remains `proposed` at confidence `0.16`; infrastructure reactivation is not positive evidence.

In the next wake, preregister `EXP-20260830-0053` before any candidate change or scoring. Use K=`8/32`, D=`1/4/6`, Q=`8`, spans=`8/32/128` and exactly one runner-random seed. Candidates are `iterative_masked_learner`, `one_pass_masked_learner`, `uniform_masked_byte`, `empirical_unigram_masked_byte`, `left_to_right_ppm_masked_byte`, `context_tree_weighting_masked_byte`, `dense_autoregressive_masked_byte`, `bidirectional_markov_masked_byte`, `parallel_markov_bp_masked_byte` and `oracle_conditional_masked_byte`. Declare mean and worst-span conditional bits per byte, exact-span accuracy, critical path, total/R16 work, resident/peak state and bytes touched with explicit directions. Quick can only discard the mechanism or authorize a three-seed new-corpus screen; it cannot promote.
