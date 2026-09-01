# Cycle 202: v13 scientific-protocol documentation service

## Scope and defect

This was exactly one protected service-only cycle. Required reading before the
planned EXP-0043 found that `heldout_parallel_masked_infilling_v13` was frozen
in its evaluator, config, manifest, service review and check but lacked a
dedicated prospective section in protected `docs/SCIENTIFIC_PROTOCOL.md`.
Scoring on that incomplete central contract would have weakened preregistration,
so no hypothesis, experiment ID, plan, runner-random seed, candidate execution,
result or score was created.

## Minimal correction

The protocol now records the already frozen v13 semantics: reuse of all v12
data and training boundaries, simultaneous masking of the D-1 inner pushes,
intact matching returns, multi-opener eligibility, the literal `([{}])`
recoverability fixture, rejection of copyable `((()))`, real-case counts,
unchanged roles and full-cost boundary, activation gates, quantitative success
criteria and the terminal negative decision. No evaluator, case, corpus,
candidate, baseline, metric, direction, cost formula, threshold, budget or
scientific evidence changed.

The v13 evaluator file remains byte-identical at SHA-256
`01f99a548613fce50c9c3f2e5f0614d2a45b32cfcbc4b5c20390013c34ce9c63`.
The intermediate v13 manifest is preserved append-only at
`research/manifests/heldout_parallel_masked_infilling_v13-protocol-v2-0ae13993d737.json`
with file SHA-256
`228915ca02c963231a4929421788a521654235c5a6d0b604fac8d2df8aecf99d`.

## Verification

- focused stack/masked tests: 42 passed;
- full pytest: 552 passed;
- mandatory semantic baseline nodes: 15 passed;
- evaluator code hash unchanged: PASS;
- protected protocol SHA-256:
  `98032d1cf45299f76c2d96c2604fa7a568938406159d6812b1463ae86b9b68eb`;
- evaluator digest after documentation refreeze:
  `971660f67df708fde694cda2191714ddcbda377efbb843a16036e68678991d3a`;
- candidate bundle unchanged:
  `40b5c47c1ad01624ac2e0eed371ca4b83a69d48cc2fe9e225d15f03a7448ed28`;
- preflight certificate:
  `b44fb4150b681317813edf78d4021d5647c44cc12ab48d2ab45dd2e6131d7356`;
- integrity: 717 protected files, PASS;
- doctor: PASS.

## Decision and next experiment

Decision: keep v13 active and HYP-0050 unchanged at `uncertain`, confidence
`0.80`. This is the second consecutive no-scoring wake after EXP-0042. Cycle
203 must preregister expected EXP-20260901-0043 and score exactly one unchanged
three-runner-seed adversarial screen on v13 with all twelve roles, K=`8/32`,
D=`3/4/5` and Q=`8`. No further no-scoring design or audit cycle is allowed
unless an actual integrity failure appears. A valid negative makes the exact
family dormant without tuning; a positive remains non-promotable narrow
screening evidence.
