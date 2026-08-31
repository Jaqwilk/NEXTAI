# GEN-1 — protected `.gitignore` re-freeze, cycle 103

## Scope

This was one protected service-only cycle. It created no hypothesis, experiment plan, scoring seed, candidate, runner scoring call, result, evidence update or confidence change. The user required large benchmark payloads to remain local through `.gitignore` and authorized protected changes to be explained before scoring.

## Defect and diagnosis

Commit `361e75f63e560861a7d7878ef1af5b7e6a392524` intentionally added seven ignore rules for local archive, extracted, ZIP, HDF5, NumPy and MATLAB benchmark payloads. The worktree was clean, but the active manifest still committed the prior `.gitignore` SHA-256 `432e9fb606b4726f9d871b28e99d2d2e8034014e15da96d35cd3b3ea7eaa1a95`; doctor therefore stopped the wake before preregistration or scoring. The new file SHA-256 is `4769ec975e1cdfa456ef9a8ae3e39d34a0d004a5e2c680dfe6ab3a3e6256872a`.

The commit changed no evaluator implementation, runner, schema, baseline registry, candidate implementation, benchmark world, split, metric, budget or scientific result. The evaluator digest changed mechanically because `.gitignore` is classified as a protected non-candidate file by the existing integrity implementation.

## Minimal correction

The service scope was frozen before mutation in `research/checks/gitignore_protected_refreeze_v1.json`. `nextai integrity freeze --overwrite` archived the previous manifest without editing it and re-froze the same active `heldout_three_family_continuous_transfer_v2` contract. The preflight certificate was regenerated through the existing repository function. No benchmark or scientific semantics were changed.

- archived manifest: `research/manifests/heldout_three_family_continuous_transfer_v2-protocol-v2-5d65692a3b01.json`, SHA-256 `616f61b836ad4ce3e8ba2b308836b6cd798c9e8f0e022474f2b26cebbbe81fd6`;
- active manifest SHA-256: `28565361560c93a76cdfaa25b13e1fda91cc8b9bc131526bfe159d28a795364a`;
- evaluator digest: `a27bf2308e5f514c77e9d1b9a87fce850e93d097a4cc0ab8a2a0b6de24d9d7d2`;
- candidate bundle digest unchanged: `6d89cd44f610e40d1ec4d9b6a04b5751086520a3dcc4c094176b8db04a99a283`;
- preflight certificate content digest: `c4d392fd782d52f931cf59d0651c6e74a3f3dd51499fdc4ea74a883e83735c75`;
- preflight certificate file SHA-256: `15f60337f4743d0bfda518cd7e86bd465d27bf66bdabddacb7364fb379dc2aab`.

## Verification and decision

The full suite passed with 319 tests. Integrity passed for all 494 protected files and doctor passed with zero pending plans. The research report was regenerated. Keep the protected re-freeze and permit the next wake to prepare the already specified development-only meaningful-effect thresholds before preregistering one algorithmic-prior mixture quick. This cycle performed no scoring.
