# GEN-1 — N-CMAPSS DS02 source gate, cycle 88

## Scope

This was one metadata-only source and design gate. It created no hypothesis, EXP-0060 plan, seed, candidate, runner invocation, score, result, evaluator mutation or confidence update. It downloaded no dataset bytes. The active v6 cohort and immutable history remain unchanged.

## Observation

### Authoritative artifact, rights and identity

NASA's official Prognostics Data Repository lists `Turbofan Engine Degradation Simulation-2` as dataset 17 and links directly to the PCoE S3 archive. A metadata-only HEAD request returned HTTP 200, `Content-Length: 15760443389`, `Content-Type: application/zip`, `Last-Modified: Sun, 18 Sep 2022 03:42:06 GMT`, and multipart ETag `bc0e65c8560b05cec3f88f964c32c403-918`. The ETag is not accepted as a content digest and NASA publishes no SHA-256 on that page.

The primary data descriptor explicitly declares `Dataset License: CC0 1.0`. It describes synthetic run-to-failure trajectories under real flight profiles and a common record contract. This resolves the rights ambiguity that rejected classic C-MAPSS. Exact artifact identity still requires one local SHA-256 after acquisition.

At the gate, drive C had 68,236,333,056 free bytes. Downloading the 15.76 GB archive leaves about 52.48 GB before extracting one member. A later acquisition is allowed only if it streams one official archive, extracts only DS02, creates no duplicate full archive and preserves at least 40 GiB free; otherwise it must stop and remove only an incomplete temporary download.

### Split and scientific boundary

DS02 contains six development engines (2, 5, 10, 16, 18 and 20) and three held-out test engines (11, 14 and 15). All share scenario descriptors, measured sensors, virtual sensors and health parameters. A conservative candidate boundary exposes only chronology, `W` scenario descriptors and `X_s` measured sensors. Unit identity, split membership, paths, fault class, health parameters `theta`, RUL/health targets and archive metadata remain evaluator-only. Virtual sensors are excluded initially because they are simulator-derived and are unnecessary to establish the minimal real-sensor contract.

This is a valid unseen-engine transfer split, but not an unseen fault-combination split: development already includes both HPT-only and HPT+LPT engines, while all official test engines are HPT+LPT. Any future claim must therefore say unseen engine/trajectory transfer, not discovery of a novel fault combination. Repartitioning three HPT-only engines against combined-fault engines would confound fault support with unit identity and discard the official test protocol, so it is not authorized here.

### Required post-acquisition negative controls

The source-only gate cannot measure observable routing. Before any protected evaluator migration, a later service wake must use the frozen DS02 bytes to test whether a simple classifier can identify unit or official split from a fixed early healthy prefix using only candidate-visible fields. It must also compare zero-adaptation, per-engine adaptation and shuffled-training-world controls. A high router score, target leakage, hash mismatch, schema drift or inability to keep the storage guard rejects the cohort before planning or scoring.

## Interpretation and uncertainty

N-CMAPSS DS02 passes provenance, explicit-license, official-endpoint, size, common-schema and whole-engine holdout gates. It is materially stronger than classic C-MAPSS for a local real-data transfer test. It does not yet pass cryptographic identity, real-file schema, leakage or routing gates because those require the bytes. Confidence is `0.99` in the official endpoint and response metadata, `1.00` in the descriptor's CC0 declaration and published 6/3 split, `0.97` that a bounded single-copy acquisition fits the current disk guard, and only `0.70` that the candidate-visible early trajectories will defeat a simple engine/split router.

## Decision

`authorize_bounded_acquisition_only`. This is not permission to activate a cohort, preregister EXP-0060, realize a seed or score anything. No protected file changes in this cycle.

## Exact next discriminating step

Next wake: perform one service-only acquisition gate. Stream the exact NASA dataset-17 archive to a temporary same-volume path, require the published byte length, compute SHA-256, atomically retain one archive, list members, extract only DS02, hash the extracted member, verify the primary-paper 6/3 units and field groups, and run leakage/router/no-adaptation audits. Enforce at least 40 GiB free after retained artifacts. Stop before evaluator migration; a separate later wake may propose a protected cohort only if every real-file gate passes.
