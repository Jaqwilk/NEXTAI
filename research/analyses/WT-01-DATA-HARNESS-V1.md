# WT-01 data/harness service-cycle analysis

Date: 2026-09-05  
Authority: `WT-01-DATA-HARNESS-20260905-V1`  
Plan: `research/plans/WT-01-DATA-HARNESS-V1.json`  
Scientific experiment: none

## OBSERVATION

- There are zero fresh same-protocol physical WT recordings. The existing ten
  `wt_changepoints_v1` files are all visible historical material: 0-5 fit, 6-7
  development and 8-9 diagnostic. The three old runner permutations do not add
  physical replication.
- The exact historical candidate bytes from Git commit `4952515` and SHA-256
  `4471f2a...` produced bit-identical synthetic fit state, predictions,
  post-reveal RLS state, operation counts, bytes and state size to R1-U1-C1.
- The separately expressed affine controlled VAR(2)/ARX control matched the
  historical residual representation within the frozen absolute and relative
  tolerance `1e-12` (observed synthetic maximum difference about `1.6e-14`).
- All eight R×U×C wrappers directly inherit one core and realize every Boolean
  cell exactly once. Tests also establish R0 one-step-and-hold behavior, U0 zero
  update work/state change, slot isolation, and fail-closed nonfinite C0 rollout.
- The maintenance evaluator records per-file/horizon NRMSE, first-16 error area,
  samples-13-to-16 recovery, divergence/stability, operations, bytes, state and
  R1/R4/R16 workloads. It labels files 8-9 as visible diagnostics.
- Full regression V1 preserved one failure: a historical lifecycle test still
  expected a review stop after service cycle 1. The test was updated only to
  recognize the separately authorized hash-bound cycle 2. Full regression V2:
  945 tests, 0 failures, 0 errors, 0 skips. Targeted: 11/11 passed.
- No real WT arrays were loaded, no archive was downloaded, no model was trained,
  no score or EXP was produced, and no development attempt was consumed.

## INTERPRETATION

The apparatus is now capable of asking which of recurrence, online RLS and
clipping explains the old visible quality gap without changing fit semantics or
mistaking the same computation for architectural novelty. The explicit VAR(2)/
ARX equivalence removes a naming ambiguity: a later positive factorial contrast
would be evidence about operations inside this classical controlled forecaster,
not evidence for a new architecture by itself.

The harness does not solve the data problem. With two already observed physical
diagnostic files, any later result is descriptive mechanism revalidation only.
It cannot establish independent replication, a hidden-holdout result, transfer
or end-to-end economic dominance.

## CONFIDENCE

High confidence in source equivalence, factor wiring, leakage boundary and
maintenance gating because they are hash-bound and directly tested. Moderate
confidence that the planned contrast will be informative on these historical
files. No confidence increase is assigned to replication or transfer because no
new physical data or cross-operation data was observed.

## DECISION

`diagnostic_harness_ready_user_review_required`. Stop at `WT-01-DEV-1`. Do not
activate scoring or read the visible development arrays without a separate,
prospective user authorization.

## NEXT DISCRIMINATING EXPERIMENT

If separately authorized, run at most one visible-development WT-01 attempt with
the frozen nine roles and matrix. Evaluate the primary contrast
`NRMSE(R0,U1,C1)-NRMSE(R1,U1,C1)` against `0.03343253453162794`, require it to be
positive on both development files, preserve every cell/divergence and stop for
review before files 8-9. This would test causal attribution only; it would still
not be replication or transfer.
