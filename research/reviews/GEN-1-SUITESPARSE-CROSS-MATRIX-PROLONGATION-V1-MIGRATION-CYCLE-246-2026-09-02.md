# OBSERVATION

Cycle 246 is one protected service-only migration. It created no formal
hypothesis, immutable experiment plan, learned candidate, runner-random seed or
score. Completed plans, results and analyses were not edited. The historical
RID evaluator and its `K_CONTRACT_FAIL_OTHER` outcome remain available; only
tests that had deliberately required the impossible certification were changed
to assert the preserved K decision and scoring hard-stop.

The new cohort is
`heldout_suitesparse_cross_matrix_prolongation_v1`. It freezes twelve source
matrices and three disjoint targets with exact payload hashes. The candidate
boundary contains only CSR `shape`, `indptr`, `indices` and numeric `data`.
Group, name, application kind, pair identity, geometry, PDE label, path and
hand-written near-nullspace never enter a candidate object.

# FROZEN CAUSAL CONTRACT

Four roles map to exactly one future implementation:
`shared_anonymous_prolongation_v1`, `independent_anonymous_prolongation_v1`,
`cross_family_only_anonymous_prolongation_v1` and
`support_only_anonymous_prolongation_v1`. They may differ only in the source
matrix tuple selected by the evaluator. Shared receives all twelve sources;
support-only and independent receive the paired source; cross-family-only
receives the other eleven sources. This intentionally makes the two required
contrasts strict tests of foreign-source information rather than model or
constant changes.

Five mandatory controls are semantically registered and hashed:

1. per-target standard PyAMG smoothed aggregation;
2. per-target adaptive smoothed aggregation with one candidate and five
   candidate iterations;
3. frozen standard-SA source hierarchy with only the fine solve matrix changed;
4. fixed source P/R with target Galerkin operators and smoothers rebuilt;
5. unpreconditioned SciPy CG.

All use `rtol=1e-7`, `atol=0` and `maxiter=2000`. A finite completed solve
above the residual threshold remains a low-quality scientific outcome. The
known complete recycling failures on `fv2 -> fv3` are preserved and explicitly
checked; they are not converted into timeouts or missing rows.

# ACCOUNTING AND DECISION RULES

The frozen trial contract records residual, solver iterations, acquisition,
fit, hierarchy construction/update, estimated sparse operations, bytes touched,
resident/peak hierarchy state and R1/R4/R16 workloads. Wall time remains
diagnostic. Universal Pareto axes exclude the intervention-specific
shared-versus-independent and cross-family-only-versus-support-only gains; those
remain promotion gates. A rebuild/reuse admission choice cannot be credited to
the learner.

The three held-out dimensions `9801`, `10605` and `81920` are the three
prospective scale points. One runner-random quick may kill the exact future
rule, but cannot promote it.

# VERIFICATION

- semantic baseline gate: PASS for all five controls;
- exact split/hash, anonymous boundary and source-identity fixtures: PASS;
- real-file standard-SA smoke: PASS at the frozen residual;
- full test suite: `668 passed`;
- integrity: PASS, 815 protected files;
- evaluator SHA-256:
  `c132847d99aea7f693045e29dd27b5e71ea3ee630c994d10ace27ad369ab7ece`;
- candidate bundle SHA-256:
  `bc7969114d6b4ded2774048e9533c5da02f12811abb6cd5fc67225576a49bdbb`;
- preflight certificate:
  `726cf953acd3c126417a82d6100607c09fd590ecb0c8e00ef3ea5e2206267f97`;
- doctor: PASS;
- free disk after migration: `96,236,277,760` bytes, above the 10 GiB floor.

# INTERPRETATION

The apparatus now measures the already selected causal question rather than
inventing a benchmark before a mechanism. It can distinguish trivial scaling
reuse, useful but slower reuse, failed reuse and strong per-target rebuilds.
Passing the migration does not increase confidence in learned prolongation; it
only removes the infrastructure and classical-control ambiguity that prevented
a valid quick.

# UNCERTAINTY

There is one held-out transition per slot, so any quick remains screening
evidence. PyAMG is a strong maintained implementation but not every published
preconditioner update. Operation counts are explicit estimator-boundary counts,
not hardware-independent FLOP proofs. The future learner interface is frozen,
but its numerical rule and constants must still be preregistered before its
implementation.

# CONFIDENCE

Confidence is `0.995` in split and payload integrity, `0.99` in semantic
identity of the five controls, and `0.96` that this cohort can falsify the
strict cross-matrix transfer thesis without crediting classical reuse.

# DECISION

`ACTIVATE_HELDOUT_SUITESPARSE_CROSS_MATRIX_PROLONGATION_V1`.

Experiment ID: none. Immutable plan path: none. Scientific evidence and the G1
qualifying count are unchanged.

# NEXT DISCRIMINATING EXPERIMENT

In a separate wake, prospectively define one minimal local anonymous
prolongation rule, prove its numerical constants and causal identity are not a
post-result variant of known learned AMG, create one HYP and one immutable quick
plan containing all four source-identical roles and five controls, then
implement only that frozen rule. Execute exactly one runner-random quick through
the audited harness. A valid negative closes the exact rule without tuning; a
positive can only authorize unchanged replication.
