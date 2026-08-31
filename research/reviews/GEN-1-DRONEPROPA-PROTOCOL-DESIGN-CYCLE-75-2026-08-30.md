# GEN-1 — DronePropA protocol and identifiability gate, cycle 75

## Outcome

The proposed `heldout_dronepropa_factor_recombination_v1` protocol is **rejected before implementation**. This cycle created no hypothesis, experiment ID, plan, seed, candidate, evaluator migration or predictive score. The active `heldout_mechanism_recombination_v3` benchmark remains unchanged.

The real-data easy-router ceiling was frozen at `0.35` before execution. Leave-one-trajectory-out accuracy was `0.0972` from length, `0.1111` from session time, `0.3472` from amplitude, `0.25` from normalized histograms and `0.3611` from their combination, against chance `0.1111`. Because `0.3611 > 0.35`, the rule rejects. The excess is only one correctly routed file out of 72, so practical confidence is moderate, but moving the ceiling after observing the result would invalidate the gate.

## Audited interface and data handling

The proposed observable interface contained only `QDrone_data` motor-command rows 47, 49, 51 and 53 plus gyroscope/accelerometer rows 27–32, at 1 kHz. Time row 1 was validation-only. The four defective ESC-monitor channels 48, 50, 52 and 54 were excluded uniformly. After that exclusion all audited matrices were finite and every time axis was strictly increasing with the expected step. No filename, fault/severity, speed, trajectory, airframe, repetition, timestamp, reference path, position, height, battery or flight mode would reach an implementable learner.

The one known file `F0_SV0_SP1_t3_D1_R1.mat` retains its incomplete zlib trailer as diagnostic history. Its decompressed inner `miMATRIX` boundary is exact and the earlier archive CRC, raw SHA-256 and numeric-payload hashes remain verified; the source was not rewritten.

The existing 4.44 GB archive and 4.54 GB extraction were reused in place. Nothing was downloaded or copied again.

## Exact whole-flight split

The anonymous manifest is `research/checks/dronepropa_anonymous_split_v1.jsonl`, SHA-256 `8381cc9d8e245059cf6ce49a5ba988bb50a588a14de445e73cb72709fdaffed0`. It exposes anonymous content-derived paths, lengths, bytes, role and hashes, not original factor names.

- Train: 64 files — five connected faulty pairs (`F1_SV1`, `F1_SV2`, `F2_SV1`, `F2_SV3`, `F3_SV2`) over t1/t2/t3/t5 plus healthy D1 controls.
- Validation: 8 whole files from `F3_SV3`.
- Test: 24 whole files from the unseen anti-diagonal pairs `F1_SV3`, `F2_SV2`, `F3_SV1`.
- OOD diagnostic only: 8 healthy D2/D3 files.
- Reserved adversarial: all 26 t4 files.

No file or history/target window crosses roles. Healthy D2/D3 data cannot count as fault-transfer evidence.

## Proposed learner and evaluation, not implemented

If an independent future gate ever clears the corpus, the minimal learner would be one unchanged `shared_operator_subspace_arx`: fit per-training-file one-step ridge ARX operators from 32-sample ten-channel histories, learn one rank-12 SVD basis of flattened operators, then fit only basis coefficients from 32 charged adaptation anchors on each anonymous held-out file. One-step evaluation is teacher-forced. Ten- and 50-step evaluation is recursive open-loop; future motor commands are supplied identically to every controlled-dynamics model while future sensor targets remain hidden.

Metrics would include mean and worst-flight/channel NRMSE at 1/10/50 steps, conditional log loss where defined, worst held-out pair, rollout finite/stability rate, transfer gain over source-identical independent and no-sharing controls, oracle-gap closure, and full acquisition/preprocessing/fit/adaptation/query/state/bytes-touched cost at R1/R4/R16.

Mandatory future controls are persistence, pooled ridge ARX, RLS ARX, nearest operator template, source-identical independent ARX, no-sharing pooled ARX, empirical Gaussian joint, contextual Gaussian Chow–Liu, a fully charged privileged condition specialist and a privileged condition oracle. Before any scoring, each must have an exact versioned specification, implementation path/hash, conformance-test path/hash and a passing hand-checkable fixture. A name is never semantic evidence.

## Synthetic identifiability and interpretation

The synthetic fixture passed: one shared rank-2 subspace reconstructed all three unseen factor pairs with maximum absolute error `1.42e-14`; exact-table coverage, nearest-template exact recovery and easy-router exact recovery were all zero. Thus the proposed mechanism is identifiable in principle, but the real corpus fails the separately frozen anti-routing condition.

Confidence is `0.97` that the gate was executed faithfully and `0.65` that the small excess routing signal is practically meaningful. The scientific decision is `reject_before_implementation`; no quality or transfer claim exists.

## Exact next discriminating step

In a later design-only wake, preregister an independent sensitivity audit before seeing its output: nested leave-one-trajectory-and-speed-out routing, a permutation confidence interval and an exact candidate-visible feature audit. Do not migrate the evaluator, create HYP-0023/EXP-0058, implement a learner or score unless that independent gate passes.
