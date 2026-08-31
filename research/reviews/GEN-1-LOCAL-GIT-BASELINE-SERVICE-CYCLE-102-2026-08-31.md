# Local Git baseline service cycle 102

## Scope

This was one maintenance-only cycle after `EXP-20260831-0002`. It created no hypothesis, experiment plan, scoring seed, candidate mutation, runner scoring call, result, evidence transition, benchmark version or schema. No remote was configured, and no push or publication was performed.

## Observation

`git rev-parse --verify HEAD` failed because the repository had no commit object. This directly explains why completed plans and results recorded `git_commit` as `null`; their environment capture was correct rather than defective.

The initial untracked snapshot set contained locally acquired benchmark payloads larger than 20 GiB, including ZIP, HDF5, NumPy and MATLAB data. The protected `.gitignore` could not be changed without invalidating the evaluator manifest, so it was restored byte-for-byte to SHA-256 `432e9fb606b4726f9d871b28e99d2d2e8034014e15da96d35cd3b3ea7eaa1a95`. Equivalent local-only exclusions were added under `.git/info/exclude` for `research/data/**/*.zip`, `*.h5`, `*.npy` and `*.mat`; existing archive and extracted-directory exclusions remain.

After exclusions, the proposed local baseline contains 884 files totaling 14.65 MiB, with no file larger than 5 MiB. It includes source, configuration, schemas, dependency lock, protected manifests, acquisition metadata, plans, results, analyses, reviews and append-only ledgers. Credential-like filename and assignment scans found no candidate secret file. Runtime environments, caches, logs, locks and local dataset payloads remain excluded.

## Verification

Before staging, the full 319-test suite passed. Integrity verified all 494 protected files with evaluator SHA-256 `b035558e9ac636952c975f2e708032e55eedb1741de46c57cf96a754e93c2107` and candidate-bundle SHA-256 `6d89cd44f610e40d1ec4d9b6a04b5751086520a3dcc4c094176b8db04a99a283`. The preflight certificate remained `d6c8b6ba63341495fdc78d505c1e5ccedb5d402bf9a2876151f4f15aa2f0ca99`.

The maintenance transaction creates the first local Git commit from the reviewed staged set. The authoritative commit identifier is the resulting repository `HEAD`. A post-commit test, integrity, doctor and clean-status verification are required before this cycle is considered complete.

## Decision

Create the local baseline snapshot. Do not publish or configure a remote. Preserve large local datasets in place but outside Git. Future plans can now record a non-null Git commit and distinguish pre-snapshot historical work from subsequent changes.

## Exact next scientific discriminator

On the next scientific wake, remain on `heldout_three_family_continuous_transfer_v2`. Before preregistration, use only the fixed development fixtures to estimate and freeze a minimum meaningful transfer effect above deterministic and finite-support noise. Then preregister one quick test of a source-identical support-calibrated convex algorithmic-prior mixture over existing generic local predictors. The same mixture learner and hyperparameters must be used for shared, independent, cross-family-only and support-only assignments. Success requires every-family gains above the frozen effect threshold, no worst-family regression against persistence, full stability and implementable Pareto non-dominance. A one-seed positive may only authorize unchanged three-seed replication; a negative discards the exact mixture without tuning.
