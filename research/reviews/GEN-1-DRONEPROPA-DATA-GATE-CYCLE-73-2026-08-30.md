# GEN-1 — DronePropA data and transfer gate, cycle 73

## Scope

This was one primary-source, no-download audit. It created no protected migration, hypothesis, experiment plan, candidate, scoring seed, runner invocation, score, result, dependency, external model/API, or benchmark mutation. The active `heldout_mechanism_recombination_v3` cohort remains unchanged.

Acceptance required explicit rights and a stable version; one common input/output contract; at least three whole held-out conditions with a genuine factor-recombination split; enough inputs and outputs for predictive system identification; and a feasible route to content-deduplication and matched controls before any scoring.

## Observation

### Rights, version and acquisition boundary

Mendeley Data version 1 has DOI `10.17632/ftdyxrr3c5.1`, was published on 2024-12-17, and is licensed CC BY 4.0. The official project page reports a 4.13 GB download. The versioned DOI gives a stable release identity, but the public HTML and DataCite record expose no per-file digest or file inventory; the Mendeley file API returned `401` without credentials. Therefore this cycle did not claim content identity and did not download the archive. A later acquisition cycle must compute the archive digest, extracted-file digests and exact inventory locally before any evaluator is frozen.

### Exact experimental factorial

The primary data article accounts for all 130 `.mat` files as five trajectories with 26 flights each. For the main drone, every trajectory contains all `3 fault types × 3 severity levels × 2 speeds = 18` faulty conditions plus healthy flights at both speeds repeated three times. Two additional drones contribute one healthy maximum-speed flight per trajectory. The filename grammar exposes fault, severity, speed, trajectory, drone and repetition.

This supports at least three whole held-out fault-type/severity combinations while leaving every fault type, severity, speed and trajectory represented in training. Candidate inputs must not include filenames or condition IDs. Split construction must group before sampling by physical file and condition, hash-deduplicate first, and prevent temporal windows from one flight crossing boundaries.

### Predictive interface

Every record uses the same documented schema. It includes position, velocity, orientation, two IMUs, thrust references, four motor and four ESC commands, battery signals, range and flight mode at 1 kHz. This is sufficient to define a common input-conditioned next-state forecasting interface without a hand-written cross-dataset ontology.

### Limits on the claim

All nine faulty-propeller combinations were flown only on drone 1. Drones 2 and 3 are healthy-only. Consequently this corpus can test recombination across defect type, severity, speed and trajectory on one closed-loop platform; it cannot establish defect transfer across airframes. The indoor trajectories were scripted, the controller remains inside the system boundary, and the paper says the artificial faults did not significantly affect normal flight performance. A condition classifier could therefore exploit controller response, trajectory or session artifacts rather than reusable dynamics.

Required negative controls are: a condition router from observable summaries; healthy-only training; independent per-condition models; trajectory-only and speed-only predictors; shuffled condition groupings; and classical ARX/state-space/nonlinear autoregressive baselines at matched acquisition, fit, update, query, memory and horizon-scaled cost. Success must occur on entire unseen factor combinations, not random windows, and must survive an airframe-confound limitation in the interpretation.

## Interpretation and uncertainty

DronePropA passes the source-level gate for a bounded acquisition audit. It is the first audited real cohort in this search with explicit redistribution rights, a versioned DOI, a fully stated 130-flight factorial and a uniform actuator/state interface. It does not yet pass the evaluator gate because file-level hashes, exact extracted inventory, duplicate content, sample lengths, missing values and schema equality have not been measured.

Confidence is `1.00` in the published rights, DOI version and stated factorial; `0.98` in the documented common schema; `0.95` that a legitimate held-out condition-recombination split exists in principle; and only `0.55` that the signals contain enough condition-dependent predictive dynamics to defeat routing and simple per-condition controls. The last uncertainty is empirical and must not be resolved by inspecting test outcomes while designing the split.

## Decision

`pass-for-bounded-acquisition-audit-only` for `dronepropa_factor_recombination_transfer`.

Passed gates:

- CC BY 4.0 rights and DOI-pinned version 1;
- exact published accounting of 130 flights;
- uniform 1 kHz actuator/state schema;
- complete fault-type × severity × speed × trajectory grid on the main drone;
- at least three possible whole held-out factor combinations;
- 4.13 GB compressed size fits current free disk for a controlled acquisition.

Still blocked before hypothesis, migration or scoring:

1. no publicly exposed per-file digest or inventory;
2. no local verification of 130 unique files, schema equality, durations, missingness or duplicate windows;
3. all faulty conditions come from one drone;
4. closed-loop, scripted-flight routing and session confounds are unmeasured;
5. the exact preregistered train/test grouping and matched full-cost baselines do not yet exist.

Do not register HYP-0023, create EXP-0058, freeze a new evaluator, realize a seed, implement a learner or score from source descriptions alone.

## Exact next discriminating step

In the next wake, run one service/data-acquisition cycle only: download exactly Mendeley version 1 into a verified temporary acquisition directory; record the archive URL, byte count and SHA-256; safely list and extract it; compute every file SHA-256; verify exactly 130 unique `.mat` flights, the filename factorial, sample lengths, shared fields, missing/non-finite values and duplicate whole files or overlapping sequences; estimate retained storage; then delete only the verified compressed temporary artifact if the extracted immutable source copy and manifest are complete. Do not create a hypothesis, plan, seed, protected evaluator migration or scoring run. Reject the corpus if the identity, inventory, schema, uniqueness or bounded storage gate fails; otherwise design the protected evaluator in a later wake under the user's standing migration authorization.
