# Cycle 204 service review: verified-incumbent whole-I/O v4

## Scope and observation

This was one protected service-only cycle. It created no hypothesis, experiment
plan, candidate implementation, scoring seed or scored result. The initial
raw-sensor v2 direction was rejected before modification because
EXP-20260901-0031 already tested and falsified that exact posterior-partition
DAG. Repeating it would not add information.

`program_induction_from_whole_io_v4` reuses the frozen v3 program class, noisy
whole-I/O support, held-out programs, matrix, five controls, metrics and full
cost boundary. The only new scientific contract is prospective: three roles
must resolve to `verified_incumbent_program_vm_core_v1`, share the exact solver,
objective, bound, ties, verifier, fallback and fixed branch order, and differ
only in the meta/support/frozen source of an initial incumbent. No such
candidate was implemented or executed in this cycle.

## Regression and semantic gates

The v4 wrapper delegates all existing control trials to v3. A deterministic
regression confirms equality of every non-timing field. Contract tests reject a
historical branch-order role or a second implementation. The prospective v4
plan schema requires all three v4 roles, the single implementation identifier
and the frozen comparison matrix.

The semantic gate initially exposed pre-existing registry debt: all five
whole-I/O controls still referenced hash `4b55bc...` for their conformance file,
while current HEAD and the immutable v12 corpus both contain the unchanged
6138-byte file at `38088e...`. The test file was not changed in this cycle. Only
the stale registry hashes were aligned, after which all five controls and four
hand-checkable nodes passed. Historical result and corpus files were not edited.

## Decision and uncertainty

Decision: activate the role-only v4 cohort. This is infrastructure, not evidence
that an incumbent learner works. The key uncertainty is empirical: a verified
proposal may rarely be the optimum or may cost more to acquire than it saves in
exact fallback search.

This is no-scoring cycle 1 of at most 3 after scored cycle 203. The next wake
must preregister HYP-0051 and exactly one one-seed breadth quick (expected
EXP-20260901-0045) on v4. The implementation must be fixed before output,
verify/reject every proposal, retain fixed branch order and exact fallback, and
charge proposal, verification and all visited nodes. Exactness in every cell is
mandatory; selection additionally requires lower cold-search work than both
source-identical ablations and complete MDL with no full-cost Pareto dominance.
One positive seed can only authorize unchanged replication. A negative quick
ends this exact incumbent rule without tuning.
