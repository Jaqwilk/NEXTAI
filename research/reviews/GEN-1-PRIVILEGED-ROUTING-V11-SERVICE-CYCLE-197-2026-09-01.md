# Cycle 197: privileged-query routing v11 service migration

## Scope

This was exactly one protected service-only cycle. It created no hypothesis,
experiment plan, runner-random seed, candidate learner, result or score.
EXP-20260901-0040 and every historical plan, result, analysis and crash remain
immutable. HYP-0050 remains `uncertain` at confidence `0.35`.

## Confirmed defect

V10 correctly versioned the target-alignment adapter but re-exported the v9
runner. The historical `_run_case` wrapped private targets only for the exact
name `oracle_conditional_masked_byte`; therefore the new registered ID received
a public `MaskedQuery` and crashed before producing a trial. The earlier unit
fixture called the control directly and did not test this evaluator boundary.

## Minimal correction

`heldout_parallel_masked_infilling_v11` delegates every existing role directly
to the unchanged v9 `run_suite`. Only
`privileged_conditional_masked_byte_v2` uses a versioned cell adapter, which
reuses the historical `_run_case` scoring/accounting implementation while
explicitly selecting its `PrivilegedMaskedQuery` branch. No corpus, split,
trace, target, permutation, matrix, metric, direction, cost, threshold, learner,
ablation, implementable control or candidate constant changed.

The semantic gate now includes four checks for the v2 control: ordered
noncontiguous target mapping, alignment rejection, a real `([{}])` closure-chain
through `_run_case`, and a one-cell immutable real-file `run_suite` smoke. The
last two cover the exact boundary missed by v10. A regression monkeypatch proves
that every other role is delegated to the historical v9 entry point unchanged.

## Verification and activation

The first full maintenance run had exactly one expected failure: the stale v10
preflight certificate. After freezing the maintenance manifest and certificate,
the full suite passed. V11 was then marked active, frozen again, and verified:

- focused routing/stack tests: 15 passed;
- full pytest: 541 passed;
- semantic baseline nodes: 15 passed;
- benchmark-boundary audit: PASS;
- transitive v2 control audit: PASS;
- evaluator SHA-256: `1bf1d8b95aab825e236d646811e46e55c67c51978e805956b8cc3196f57c5f88`;
- candidate bundle SHA-256: `d3fea2fead3b255e4872352c2aa81cb8f3096f9adcd39b557e9f578e3d106244`;
- preflight certificate: `6fe573fda34dc02436a1ccf19a8188c7f4d6009153b8a5bfb2c26f3220b99e89`;
- integrity: 712 protected files, PASS;
- doctor: PASS.

The final v10 manifest and intermediate v11-maintenance manifest are preserved
append-only. No runner command was invoked.

## Decision and exact next experiment

Decision: activate v11 and keep HYP-0050 unchanged. The next wake must
preregister expected `EXP-20260901-0041` as one unchanged one-seed quick on v11
with the exact EXP-0039/0040 learner, ablations, K=`8/32`, D=`3/4/5`, Q=`8`,
thresholds and all nine controls. No algorithm or constant may change. A
complete negative ends this exact rule. A complete positive still cannot
promote; it may only authorize an unchanged three-seed adversarial new-corpus
replication in a later wake.
