# Cycle 199: disjoint-source corpus v12 service migration

## Scope

This was exactly one protected service-only cycle. It created no hypothesis,
experiment ID, immutable plan, runner-random seed, candidate implementation,
result or score. EXP-20260901-0041 and every v8-v11 artifact remain immutable.
HYP-0050 remains `uncertain` at confidence `0.60`.

## Corpus finding and correction

The v11 loader supplied 8,192 training bytes for K=8 but only 8,226 for the
declared K=32 cell. V12 does not reinterpret that valid v11 quick; it corrects
the replication cohort prospectively. Its frozen registry contains 102 train,
7 validation and 3 reserved test files with zero path or SHA-256 overlap with
the historical v8-v11 corpus. All twelve evaluated role modules and their
shared pushdown implementation are excluded from the new corpus.

After tokenization, v12 supplies 8,192/32,709 whole shallow-trace training
bytes and 1,023/4,096 validation bytes at K=8/32. The disclosed 59-byte K=32
shortfall avoids splitting or duplicating a trace. Reserved tests provide
55/17/10 immutable cases at depths 3/4/5. The corpus registry SHA-256 is
`7e002e170cd237b063cf79c4e83418f09a1fd664b32fc918f92a403dcc19673b`.

## Minimal evaluator change

The versioned evaluator replaces only `_load_corpus` and the resulting
training/test material. It reuses v9 closure-chain selection and v11 `_run_case`
query routing. The representation, depth ceiling, byte permutation, targets,
K/D/Q contract, metrics, directions, state boundary, cost formulas and
thresholds are unchanged. Direct old/new manifest comparison confirms that all
twelve EXP-0041 role-module hashes are identical; no candidate file changed.

## Verification and activation

The first maintenance full-suite run had the single expected stale-preflight
failure. After the maintenance freeze it passed, then v12 was activated and
frozen again. Final verification:

- focused v12/stack/routing tests: 20 passed;
- full pytest: 546 passed;
- semantic baseline nodes: 15 passed;
- exact registry path/size/hash and historical-overlap gate: PASS;
- effective-byte and depth-count regression: PASS;
- evaluator SHA-256: `bf0e4c57b3830177c296eb80eaaa4d9cc12f0935a0ddc8a76563ace3c59187f5`;
- candidate bundle SHA-256: `26fe3d5c07e27752477668c2722827e7984987bee77d7d1fe3b2c904069b3f12`;
- preflight certificate: `72364f96b1c6bd06b39098feb7189fdd20592589d6c1bf60d51dcf081ecdf537`;
- integrity: 715 protected files, PASS;
- doctor: PASS.

The candidate-bundle digest changes only because the semantic registry is part
of that digest and now admits v12; the candidate directory is unchanged. The
final v11 manifest and intermediate v12-maintenance manifest are preserved
append-only. No `nextai run` command was invoked.

## Decision and exact next experiment

Decision: activate v12 and keep HYP-0050 unchanged. The next wake must
preregister one unchanged three-runner-seed screen replication on v12 with the
same twelve roles, K=`8/32`, D=`3/4/5`, Q=`8`, algorithm constants, thresholds
and invalidation rules as EXP-0041. No tuning is permitted. A negative result
discards this exact learned-pushdown direction; a replicated positive may only
authorize a later adversarial verification and cannot itself promote.
