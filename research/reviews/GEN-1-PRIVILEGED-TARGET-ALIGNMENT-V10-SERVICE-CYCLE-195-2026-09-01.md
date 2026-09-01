# Cycle 195: privileged-target alignment v10 service migration

## Scope

This was exactly one protected service-only cycle. It created no hypothesis,
experiment plan, runner-random seed, candidate learner, result or score. The
immutable EXP-20260901-0039 plan, result, analysis and privileged-control crash
were not edited or recomputed. HYP-0050 remains `uncertain` at confidence 0.35.

## Confirmed defect

The historical `oracle_conditional_masked_byte` v1 adapter assumed one
contiguous centered span and indexed the private target as
`target[position - start]`. V9 instead masks all matching closers in a nesting
chain and supplies the target tuple in `masked_positions` order. Noncontiguous
positions therefore produced an out-of-range index before a trial existed.
This is an adapter defect in one mandatory privileged control, not evidence for
or against the learned pushdown mechanism.

## Minimal correction

`heldout_parallel_masked_infilling_v10` reuses v9 `run_suite` byte-for-byte and
changes no corpus, split, trace, target, permutation, K/depth/query cell,
metric, direction, cost, state boundary, learned role or implementable control.
It replaces only the failed control with the separately registered
`privileged_conditional_masked_byte_v2`. The new adapter maps target bytes using
`zip(public.masked_positions, target)`, rejects unequal lengths and rejects a
declared position that is not masked. Its distinct ID preserves the historical
v1 implementation and semantic hash. Its `privileged_` name excludes it from
the implementable Pareto frontier.

The hand-checkable regression maps noncontiguous positions `(1, 3, 6)` to
distinct target bytes `(31, 47, 59)` in tuple order. A deliberately short
target tuple raises before probabilities are returned. The transitive source
audit passed, and all thirteen mandatory semantic baseline nodes passed.

## Verification and activation

The first full maintenance test correctly rejected the stale v9 preflight
certificate while the other 536 tests passed. After freezing the maintenance
manifest and certificate, all 537 tests, integrity and doctor passed. Only then
was v10 marked active, frozen again, and rechecked on the final active state:

- pytest: 537 passed;
- evaluator SHA-256: `655e8713fb8a7264f11dc99b80f34d644e71d930b812feda504c2787291c8ad0`;
- candidate bundle SHA-256: `29651402fb8609c4699afea1dc5a596cdb7ebc2a8dc082d80a0d58c954003b14`;
- preflight certificate: `4df3dc5e8485e592f82cd9f8231f89debb09b05247aab44475b26abe7b25a44c`;
- integrity: 711 protected files, PASS;
- doctor: PASS.

The final v9 manifest and intermediate v10-maintenance manifest are preserved
append-only. No scoring command was invoked.

## Decision and exact next experiment

Decision: activate v10 and keep HYP-0050 unchanged. Cycle 196 must preregister
EXP-20260901-0040 as one unchanged one-seed `quick` on v10 with the exact
learned pushdown, depth-two finite-state and frozen-transition implementations
from EXP-0039, the same K=`8/32`, D=`3/4/5`, Q=`8`, thresholds, costs and eight
implementable controls, and the corrected mandatory privileged support control.
No candidate constant or algorithm may change. A complete negative stops this
exact rule; a complete positive can only authorize an unchanged three-seed
adversarial replication in a later wake and cannot promote.
