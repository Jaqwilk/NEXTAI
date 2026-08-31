# GEN-1 — real system-identification data gate, cycle 70

## Scope

This was one literature/data-audit cycle with no dataset download, protected migration, hypothesis, experiment plan, candidate, seed, runner invocation, score, result, dependency, external model/API, or benchmark mutation. The active `heldout_mechanism_recombination_v3` cohort remains unchanged.

The proposed cohort was Silverbox, DaISy 96-006 hair dryer, and DaISy 96-009 flexible robot arm. Acceptance required authoritative provenance, explicit redistribution terms, stable hashable artifacts, enough disjoint chronology for train/validation/test, no target leakage, one unchanged anonymous `(past inputs, past outputs, future inputs) -> future outputs` learner contract, and a predeclared negative control showing dataset routing cannot explain transfer.

## Observations

### Native contract

All three records are naturally input/output dynamical systems. Silverbox records excitation and measured response of an electronic Duffing oscillator; the hair dryer records heater voltage and air temperature; the robot arm records reaction torque and acceleration. The same causal forecasting contract can therefore be stated without hand-written state alignment or benchmark-specific target semantics.

This is a necessary but insufficient commonality. The measurement units, excitation processes, trace lengths and physical time scales remain dataset-specific observable content. Removing a dataset-name field would not make the source latent.

### Provenance, files and rights

- Silverbox has an authoritative benchmark page and download, and the official loader documents designated train/validation and test records. The benchmark page does not state dataset redistribution terms or publish a content digest. Its download is not identified by a content-addressed URL.
- DaISy is maintained by KU Leuven STADIUS, describes the database as publicly accessible, supplies direct gzip links, and requests citation. Its submission page requires clearance from confidentiality agreements. None of the audited official pages grants a redistribution license or supplies a digest for these two files.
- The loader repository's software license cannot be treated as a license for independently contributed underlying measurements.

Public download access and a citation request are evidence of intended research use, not sufficient evidence that NEXTAI may vendor and freeze copies. Because this cycle prohibited downloads, it also did not compute local content hashes.

### Chronology and transfer identifiability

- The hair-dryer description contains one 1000-sample two-column trace and no official split.
- The robot-arm description contains one 1024-sample two-column trace and no official split.
- Silverbox has official separated records, but the other two systems do not provide independently sampled training and unseen-world trajectories in the audited material.

A chronological prefix/suffix split could test within-trace forecasting, but it would be an evaluator-authored split of one realization. It cannot establish transfer to an unseen system variant. With one trace per DaISy system, family-level adaptation, dataset identity and transfer are not separately identifiable.

The source is also expected to be readily routable from lossless observations: sample count, amplitude/range, excitation spectrum, units expressed numerically, autocorrelation and noise characteristics differ by physical system. A shared parameter container could therefore implement three implicit specialists while satisfying a source-identical API. No evidence in this cohort can force or verify a shared transferable representation rather than routing.

## Gate decision

`reject-before-download` for `real_system_identification_shared_transfer` on this exact three-dataset cohort.

The cohort passes authoritative provenance and the native-contract check, but fails four mandatory gates:

1. explicit redistribution rights are absent from the audited official pages;
2. authoritative content digests are absent;
3. two members provide only one short trace and no official train/test worlds;
4. dataset identity remains an observable shortcut, so transfer cannot be separated from routing.

Do not register HYP-0023, create EXP-0058, download/vendor files, compute a seed, implement a learner, or migrate an evaluator from this proposal. This rejection is about cohort adequacy, not a falsification of system-identification learning.

## Exact next discriminating step

In the next wake, perform one no-download primary-source gate on the official nonlinear-benchmarks `NanoDrone` cohort as a deliberately narrower but identifiable real-transfer test. Require: explicit dataset rights or written terms adequate for local vendoring; authoritative stable files or published digests; the documented nine training and three held-out trajectories; fixed chronological/trajectory splits; one unchanged multivariate input-conditioned predictor; no trajectory or flight-name tags; a source-router/adaptation-ablation control; and complete acquisition, fit, query, update, memory/state and horizon-scaled cost accounting. Register no hypothesis or experiment unless every gate passes. If licensing remains unspecified, reject without download and audit a repository with an explicit data license rather than weakening the legal gate.
