# GEN-1 — N-CMAPSS DS02 acquisition gate, cycle 89

## Scope

This was one service-only acquisition cycle. It created no hypothesis, EXP-0060 plan, seed, candidate, runner invocation, score, result, evaluator mutation or confidence update. The active v6 cohort and immutable scientific history remain unchanged.

## Observation

### Exact acquisition and storage

The official NASA dataset-17 response was downloaded once to a same-volume partial path. Its exact length is `15,760,443,389` bytes and its local SHA-256 is `d1271732485dc1ed354e8c7d950edc196aa78ec48d78f38f2d9681dc82fb61c2`. The ZIP central directory contains one nested `data_set.zip`, with uncompressed length `15,814,385,805` bytes and CRC32 `fe845723`.

Materializing the nested ZIP would have temporarily violated the preregistered 40 GiB free-space guard at the initial free-space level. Instead, the nested member was exposed through Python's standard-library seekable ZIP stream. Its complete central directory was read without saving it, and only `data_set/N-CMAPSS_DS02-006.h5` was extracted. No other dataset member or duplicate nested archive was created.

The DS02 HDF5 file has exact length `2,450,472,504` bytes, archive CRC32 `e85c00fc`, and local SHA-256 `47971a68b239ecb756833218a95d68ded6eb7e63ee84e86671c8b188de1ca765`. Extraction verified CRC while streaming and atomically renamed both files only after length and digest checks. Free space after acquisition was `142,406,799,360` bytes, above the 40 GiB guard.

### Real-file evidence and remaining gate

The DS02 file begins with the exact HDF5 signature `894844460d0a1a0a`. A raw read-only name scan finds the expected physical records `W_dev/test/var`, `X_s_dev/test/var`, `X_v_dev/test/var`, `T_dev/test/var`, `Y_dev/test`, and `A_dev/test/var`. This proves that the acquired member is an HDF5 container with the expected top-level contract; it does not prove shapes, dtypes, unit values or leakage properties.

No HDF5 reader is installed in the project environment, system Python, bundled workspace Python or local binaries: `h5py`, PyTables, `h5dump`, `h5ls` and an HDF5 DLL are absent. The repository rule forbids installing a dependency autonomously. Implementing a partial HDF5 parser would be a larger, fragile framework and could silently misread chunking, filters or metadata. Therefore the exact 6/3 unit audit, field separation, target leakage check, early-prefix engine/split router and zero-adaptation comparison were not run.

## Interpretation and confidence

The acquisition itself is complete and reproducible with confidence `1.00`: authoritative URL, byte length, both archive identities, CRC and local SHA-256 agree with the observed bytes. Scientific suitability remains unresolved, not failed. The missing reader is an infrastructure boundary discovered before evaluator construction or scoring, so it invalidates no scientific result.

## Decision

`maintenance_blocked_before_evaluator`. Preserve the acquired archive and DS02 file. Do not activate a cohort, create EXP-0060, realize a seed or use raw string evidence as a substitute for the semantic audits.

## Exact next discriminating step

After explicit dependency approval, one later service-only wake may add only `h5py` as the local HDF5 reader, freeze its version, and run exact real-file schema, development/test unit, candidate-visible/evaluator-only leakage, early-prefix router and no-adaptation audits. That wake must still perform no cohort migration and no scoring. Only a subsequent protected wake may migrate an evaluator if every audit passes.
