# Cycle 201: recoverable push-chain v13 service migration

## Scope

This was exactly one protected service-only cycle. It created no hypothesis,
experiment ID, immutable experiment plan, runner-random seed, candidate change,
result or score. EXP-20260901-0042 and every v12 artifact remain immutable.
HYP-0050 remains `uncertain` at confidence `0.80`.

## Frozen adversarial contract

V13 reuses the immutable v12 corpus, whole-file roles, shallow training bytes,
training-depth ceiling, depths `3/4/5`, K=`8/32`, Q=`8`, anonymous byte
permutation, twelve candidate implementations, metrics, directions, state
budget and full-cost formulas. It changes only the evaluator-private test
transformation.

For the first chain reaching exact depth D, v13 leaves the outermost push
visible and simultaneously masks the remaining D-1 pushes. Their matching
returns remain visible. A trace is eligible only when at least one missing push
has a different type from the visible outer push. Therefore repeating or
closing the visible top cannot recover the entire target, while the intact
return chain makes every missing push mechanically recoverable under the same
anonymous grammar learned from training.

The hand-checkable trace `([{}])` becomes `(??}])`, with target `[{` and
visible return suffix `}]`. Reversing that suffix and applying the learned
return-to-push pairing recovers `[{`; repeating the visible `(` does not.
Single-type `((()))` is rejected as copyable. The frozen v12 test corpus
contains 32, 9 and 10 eligible traces at depths 3, 4 and 5 respectively, so
every registered cell has genuine cases without synthesizing new data.

No candidate was executed on a v13 case during this service cycle. The new
cases therefore remain unseen by candidate scoring until a later immutable
plan is registered and the audited runner realizes its seeds.

## Historical and implementation integrity

The final v12 manifest is archived at
`research/manifests/heldout_parallel_masked_infilling_v12-protocol-v2-cded85614f7f.json`
with file SHA-256
`ed0fefec5573b6a9383437b2a780d551ab3a018f95dce0bf078df8f362aedce4`.
Direct comparison with the v13 manifest proves identical hashes for all twelve
role modules and the shared learned-pushdown core. Existing v8-v12 evaluators,
plans, results, analyses and reports were not changed or reinterpreted.

## Verification and activation

- focused stack, routing and masked-contract tests: 42 passed;
- full pytest: 552 passed;
- mandatory semantic baseline nodes: 15 passed;
- literal recoverability, copy-alias rejection and real-corpus availability:
  PASS;
- evaluator SHA-256:
  `0ca80f3cb683e34d50aadc01a05c14864555223a0581319d3d75a0ee3a12bc71`;
- candidate bundle SHA-256:
  `40b5c47c1ad01624ac2e0eed371ca4b83a69d48cc2fe9e225d15f03a7448ed28`;
- preflight certificate:
  `4a72094c8881045ac72a401ee27a83465e7e878ad7f54ee37e35231bf4cdf261`;
- integrity: 717 protected files, PASS;
- doctor: PASS.

The candidate-bundle digest changes only because the semantic registry is part
of that bundle and now admits v13. No candidate source changed. No `nextai run`
command was invoked.

## Decision and exact next experiment

Decision: activate `heldout_parallel_masked_infilling_v13` and keep HYP-0050
unchanged. The next wake must preregister expected EXP-20260901-0043 as one
three-runner-seed adversarial screen using the unchanged twelve roles,
K=`8/32`, D=`3/4/5` and Q=`8`. Success requires exact-span accuracy `1.0` in
every cell, at least `0.25` exact-span advantage and lower bits than both
source-identical ablations and the strongest complete implementable control,
all mandatory controls complete, the existing state budget, and implementable
Pareto non-dominance. The screen cannot promote. A valid negative makes this
exact family dormant without tuning; a positive remains narrow screening
evidence pending an independent non-synthetic corpus.
