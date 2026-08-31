# GEN-1 — N-CMAPSS DS02 semantic gate, cycle 90

## Scope

This was one service/design-only real-file audit. It created no hypothesis, EXP-0060 plan, seed, candidate, runner invocation, score, result, evaluator mutation, dependency installation or confidence update. The active v6 cohort and immutable scientific history remain unchanged.

## Observation

### Reader and exact schema

The apparent HDF5-reader blocker was resolved without installing a dependency. An already installed VTK runtime contains a namespaced native HDF5 library. One 296-line read-only `ctypes` audit bridge binds only file, dataset, dataspace, datatype and read operations. The library SHA-256 is `f9152376c0d8fde2703531888e1c21cbc088c6e531a74e544a7b8e139cf83df3`; the bridge SHA-256 is `c8c3d3b6856e5439817c3e7d0e724d49e2730349352260eb3e57710c4006e7a3`.

The exact DS02 file contains 5,263,447 development rows and 1,253,743 test rows. Each row aligns across four scenario descriptors `W`, 14 measured sensors `X_s`, 14 virtual sensors `X_v`, ten private health parameters `T`, a one-column integer target `Y`, and four auxiliary values. `A_var` identifies the auxiliaries as `unit`, `cycle`, `Fc` and `hs`. The unit split exactly matches the primary descriptor: development 2/5/10/16/18/20 and test 11/14/15.

### Append-only preregistration correction

Gate v1 required 8192 adaptation plus 4096 query transitions at stride 32. It stopped before writing or displaying any semantic result because unit 14 supplies only 4897 valid sampled transitions. The v1 specification remains preserved with status `invalid_pre_result_insufficient_unit14_transitions`. Before seeing any router or metric result, v2 changed only the control sizes to 2048 adaptation and 2048 query; all features, thresholds and invalidation rules remained identical.

### Leakage, routing and adaptation controls

The frozen leakage audit found no exact match between any candidate-visible `W+X_s` column and evaluator-only `Fc`, `hs`, `T` or `Y`. Maximum absolute correlation was `0.683037`, below the `0.999999` rejection threshold.

The split itself is nevertheless observable. Every development engine belongs to flight class 3, while test engines 11/14/15 belong to classes 3/1/2 respectively. Using only the first 4096 candidate-visible `W+X_s` rows per engine, their column means and standard deviations, and leave-one-engine-out nearest class centroids, the frozen router classified 8 of 9 engines correctly: accuracy `0.888889` versus the preregistered majority ceiling `0.666667`. No unit ID, flight-class label, health parameter, target or path was provided to the router.

The diagnostic one-step controls also show no adaptation challenge under the frozen sample: persistence NRMSE `0.029882`, development-pooled ridge without test adaptation `0.027948`, and per-engine prefix adaptation `0.029191`. Pooled no-adaptation is slightly better than explicit test-engine adaptation. These are design diagnostics, not scientific scores or hypothesis evidence.

## Interpretation and confidence

DS02's official split cannot identify the intended claim. A learner can infer split membership from public early trajectories because flight classes 1 and 2 occur only in test, and a simple pooled no-adaptation model already matches or beats per-engine adaptation. A positive result could therefore reflect source/split routing or ordinary pooled dynamics rather than a portable representation. Removing flight classes 1 and 2 leaves only one test engine, which is insufficient; moving them into training leaves no same-class held-out engine. This is a structural data-support problem, not an implementation issue.

Confidence is `0.99` in rejection of this exact cohort: the router exceeds its frozen ceiling by two correct engines, the class support is directly confirmed from the evaluator-only auxiliary column, and no threshold was changed after the result. This does not reject N-CMAPSS generally or shared representation learning.

## Decision

`reject_before_evaluator_observable_split_router`. Preserve the acquired bytes and both gate specifications/results as diagnostic history. Do not activate DS02, create EXP-0060, realize a seed or tune a router threshold.

## Exact next discriminating step

Next wake: perform one metadata-only design gate over the broader N-CMAPSS archive before extracting another member. Require at least two development and two held-out whole engines in every included flight class, common candidate-visible `W+X_s` schema, no fault/source label, and a preregistered source/split router ceiling at majority chance. If the published subset composition cannot support that factorial separation, reject N-CMAPSS broadly before further extraction; otherwise authorize only the minimum members needed for a later real-file router gate.
