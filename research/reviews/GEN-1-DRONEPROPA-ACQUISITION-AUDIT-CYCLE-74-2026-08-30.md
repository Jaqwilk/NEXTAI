# GEN-1 — DronePropA acquisition audit, cycle 74

## Scope

This was one service/data-acquisition cycle. It downloaded and audited exactly Mendeley Data version 1. It created no hypothesis, experiment plan, scoring seed, candidate, protected evaluator migration, runner call, score, result, dependency, external model/API or cooldown. The active `heldout_mechanism_recombination_v3` evaluator remains unchanged.

## Observation

### Immutable acquisition

The stable public endpoint returned a ZIP of 4,438,911,840 bytes with SHA-256 `a7255dc4393a2314ba2a684beb3684106dbb6de23ba141eaa0529bd21ba3d825`. Its 131 entries contain 130 MATLAB v5 files and one author-generated file list. There are no absolute paths or parent traversal entries. Extracted size is 4,537,694,153 bytes, leaving 63.71 GiB free after retaining both archive and extracted source.

The generated per-file manifest is `research/data/dronepropa_v1/files.jsonl`, SHA-256 `76a27c66b38b634cbee362a8a2af250b02b2a1dea44eb9328d1d731472b24f53`. It records raw-file and numeric-payload hashes, dimensions and non-finite counts for every flight. All 130 raw SHA-256 values and all corresponding numeric payloads are unique.

### Inventory and factorial

The actual filenames exactly equal both the author-provided list and the preregistered factorial:

- 90 faulty flights: `3 fault types × 3 severities × 2 speeds × 5 trajectories`;
- 30 healthy drone-1 flights: `2 speeds × 5 trajectories × 3 repetitions`;
- 10 healthy reference flights: `2 additional drones × 5 trajectories × maximum speed`.

Nothing is missing or extra. Every trajectory has 26 files. All files share exactly three double matrices with row schemas `56/37/21`, and the three matrices within every file have identical sample counts. Flight lengths range from 49,689 to 99,660 samples; total length is 10,058,196 samples.

### Uniqueness and leakage screen

There are no duplicate whole files or duplicate numeric matrices. A content screen hashed 19,445 exact `QDrone_data` windows of 1,024 samples at stride 512 and found no repeated window within or across files. This does not prove the absence of approximate trajectory/session similarity, so a future condition-router negative control remains mandatory.

### Data defects

There are 255,381 non-finite values: 255,373 NaNs and eight positive infinities in 22 files. Every one is confined to `QDrone_data` rows 48, 50, 52 and 54, the four documented ESC-monitor channels. Every other `QDrone_data` row and all `commander_data` and `stabilizer_data` values are finite. A future evaluator must exclude these four channels uniformly before constructing any split; it may use the adjacent finite motor-command rows 47, 49, 51 and 53. Raw data must remain unchanged.

One healthy file, `F0_SV0_SP1_t3_D1_R1.mat`, contains one zlib member without a complete trailer. Its decompressed bytes nevertheless form exactly one complete MATLAB `miMATRIX`: the declared inner byte count equals the decompressed payload. The enclosing ZIP CRC, raw-file SHA-256 and numeric-payload hashes preserve its identity. The tolerant condition is explicit in the audit manifest and cannot silently become evidence of corruption handling by a learner.

## Interpretation and uncertainty

The acquired release passes the inventory, stable-identity, schema, factorial, whole-file uniqueness and bounded-storage gates. The non-finite values are a channel-local acquisition defect rather than missing trajectories, and can be excluded with one uniform pre-outcome rule. The incomplete zlib trailer is a serialization defect whose matrix payload is structurally complete.

Confidence is `1.00` in the byte hashes, counts, filename factorial, dimensions and exact-window screen; `0.99` that excluding the four ESC-monitor rows produces a finite common interface; and `0.55` that unseen fault combinations will contain reusable predictive structure rather than controller/session signatures. The last question requires a frozen evaluator and scored controls; it was not answered here.

## Decision

`pass-for-protected-evaluator-design-only` for `heldout_dronepropa_factor_recombination_v1`.

The corpus is not scientific evidence and is not yet approved for scoring. No HYP-0023 or EXP-0058 exists. The future evaluator must freeze, before signal inspection beyond quality auditing:

1. uniform exclusion of `QDrone_data` rows 48, 50, 52 and 54;
2. candidate-visible actuator/state fields with no filename, fault, severity, trajectory, speed, drone or repetition tags;
3. whole-file grouped train/test worlds and no cross-boundary windows;
4. at least three held-out fault-type/severity combinations while each constituent type and severity remains in training;
5. a condition-router control, healthy-only ablation, source-identical independent-per-condition learner and shuffled-condition negative control;
6. matched ARX/state-space, nonlinear autoregressive, empirical-joint/contextual and oracle controls where semantically applicable;
7. acquisition, preprocessing, fit, meta-fit, update, query, bytes, memory and declared-horizon workload costs;
8. an explicit limitation that faulty-airframe transfer is untested because only drone 1 has faults.

## Exact next discriminating step

In the next wake, perform one no-scoring protocol-design cycle for `heldout_dronepropa_factor_recombination_v1`. Freeze the exact observable channel indices, normalization fit boundary, forecast horizons, grouped held-out factor combinations, development-only files, invalidation rules, routing and causal ablations, full-cost axes and baseline semantics in an immutable design review. Do not inspect predictive scores, create an experiment plan, realize a seed or modify the protected evaluator. Only a later separately bounded service wake may implement and freeze that evaluator under the user's standing authorization.
