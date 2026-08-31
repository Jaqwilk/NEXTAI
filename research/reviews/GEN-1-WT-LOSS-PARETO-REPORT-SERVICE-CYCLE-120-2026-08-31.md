# GEN-1 — WT loss-cohort Pareto report repair, cycle 120

## Scope

This was one protected service-only cycle. It created no hypothesis, experiment plan, scoring seed, candidate, scored result, evidence update or confidence change. Immutable plan, result and analysis files for EXP-20260831-0006 were not modified.

## Defect and correction

The audited runner already exempted registered loss cohorts from the generic `accuracy >= 0.95` capability gate, but the generated report applied that gate to every cohort. Consequently, the correct immutable four-member Pareto frontier in EXP-20260831-0006 rendered with blank markers.

The smallest durable repair adds the same two registered loss-cohort prefixes directly to the reporter eligibility check. Runner semantics, benchmark contracts, metric formulas, axes and completed results remain unchanged. A regression loads the immutable EXP-20260831-0006 result and requires the report to mark exactly `wt_candidate_under_test`, `wt_persistence_v1`, `wt_pooled_mean_v1` and `wt_control_level_bank_v1`.

An attempted shared-helper refactor was rejected by the full suite because historical repository-compression corpus hashes intentionally include `pareto.py`. The final patch restores that file and the runner byte-for-byte, keeping the correction local to `report.py`. Automatic manifest archives from the protected re-freezes are retained append-only: `research/manifests/heldout_wt_changepoints_prequential_v1-protocol-v2-24669d553bf8.json` is the pre-service manifest, `research/manifests/heldout_wt_changepoints_prequential_v1-protocol-v2-1f6169330927.json` records the rejected intermediate protected state, and `research/manifests/heldout_wt_changepoints_prequential_v1-protocol-v2-08e8c05230b9.json` records the state before the final negative regression was added.

## Verification and decision

- focused report and historical corpus tests: PASS;
- full pytest: 360 PASS;
- generated report: exactly the four immutable EXP-0006 Pareto members marked `yes`;
- integrity: PASS, 523 protected files;
- doctor: PASS, zero pending plans;
- active manifest SHA-256: `86c8af290f486ceee716b1183e73b7b1aea3e0d6406318f5efdfa3b3a4e4c643`;
- evaluator digest: `e2249a64b9c0a5b477cd2652cdae23af6f142c8744b70efca7b94615ee854012`;
- preflight certificate content digest: `bb95bdefcddcbc86477bd6751f989f5f9bec5e42be1d67becdbc141bee02fc4a`;
- preflight certificate file SHA-256: `d52e057bc24debe21cc65e29032b004f25dc51f581a26d583f2ee0b12dd6e603`.

Keep the presentation repair. In the next wake, preregister one unchanged three-seed screen replication of `wt_candidate_under_test` on `heldout_wt_changepoints_prequential_v1` against all eight frozen controls. Require the frozen NRMSE effect `0.1325268421060828` on every seed and every K-by-H96 cell, no degradation of worst-file or worst-transition NRMSE, complete stability, implementable Pareto non-dominance and report seed variability. Do not tune the learner after observing replication outcomes.
