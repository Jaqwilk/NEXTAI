# GEN-1 — NanoDrone data and transfer gate, cycle 71

## Scope

This was one primary-source and repository-metadata audit. It created no dataset download, protected migration, hypothesis, experiment plan, candidate, scoring seed, runner invocation, score, result, dependency, external model/API, or benchmark mutation. The active `heldout_mechanism_recombination_v3` cohort remains unchanged.

Acceptance required explicit data rights adequate for local vendoring, immutable or pin-able artifacts, independent training and unseen test trajectories, fixed leakage-free chronology, one unchanged multivariate input-conditioned predictor, no trajectory labels, a routing/adaptation negative control, and evidence relevant to shared representation rather than only ordinary interpolation.

## Observation

### Authoritative correction and artifact inventory

The cycle-70 next-step text anticipated nine training and three test trajectories. The authoritative repository instead contains twelve training CSV files—four runs each of `Chirp`, `Random`, and `Square`—and three `Melon` test CSV files. This review records the correction append-only; it does not alter cycle 70.

The repository and paper agree on the native contract: four motor angular velocities are inputs and a thirteen-dimensional full state is the output. The benchmark is sampled at 100 Hz and scores open-loop prediction through 50 steps. `Melon` is excluded from training and all three runs are held out, so the split is materially stronger than an arbitrary suffix of one trace.

Git commits and blobs can be pinned after acquisition, and the CSV files are individually addressable. No authoritative release manifest or published content digest was found in the audited material. More importantly, the repository root contains no `LICENSE` or `COPYING` file and the README provides no SPDX identifier or explicit dataset license. The paper calls the data and code open-source, but that descriptive phrase is not a license grant with defined rights and conditions.

### What transfer this benchmark can identify

The fixed split tests extrapolation from three excitation/trajectory classes to a fourth class on the same physical nano-drone and measurement pipeline. With trajectory names removed, the learner can still see motor inputs and state histories, which are scientifically legitimate causal inputs rather than forbidden source tags. A no-adaptation ablation and a classifier over initial context could quantify whether test-time behavior depends on recognizing the maneuver distribution.

However, every file comes from one platform, sensor stack and state representation. There is no held-out vehicle, payload, battery regime, aerodynamic configuration, coordinate convention, or output ontology. A successful learner would establish multi-trajectory dynamics generalization within one system. It would not answer whether one shared learner discovers a representation transferable across multiple worlds or beats separate benchmark-specific probabilistic models. Calling this the requested multi-world test would broaden the evidence after seeing the data design.

## Interpretation and uncertainty

The split is usable for a future auxiliary real-data control if the authors publish explicit terms, but it is not sufficient as the next main HYP-0023 cohort. Confidence is `0.99` that the authoritative count is 12 train and 3 test files, `0.98` that the repository currently lacks an explicit root/data license, and `0.95` that this design only identifies maneuver-level transfer within one system. A license could exist outside the audited repository or be added later; that uncertainty does not permit assuming rights now.

## Decision

`reject-before-download` for `nanodrone_shared_world_representation`.

The candidate passes provenance, stable repository identity, native-contract, disjoint-trajectory and leakage-design gates. It fails:

1. explicit data-license and redistribution-rights gate;
2. published artifact-digest gate;
3. multi-world representation identifiability, because only maneuver type changes while system and ontology remain fixed.

Do not register HYP-0023, create EXP-0058, download/vendor the repository, realize a seed, implement a learner, or migrate the protected evaluator from this proposal.

## Exact next discriminating step

In the next wake, perform one no-download source-resolution gate for `NanoBench` (Ullah and Baca, 2026). Locate its authoritative repository or archive and verify an explicit dataset license, version/digest, exact train/validation/test trajectory lists, vehicle/session diversity, battery/payload/speed-regime coverage, and whether the system-identification subset supports a predeclared leave-regime-or-session-out test with identical observable fields. Require at least three independently held-out worlds and a negative control that separates shared adaptation from trajectory classification. Do not treat its three different tasks as three worlds if their targets or observables differ. If provenance or rights fail, reject it before download and pivot to a DOI-backed repository with an explicit CC/ODC license.
