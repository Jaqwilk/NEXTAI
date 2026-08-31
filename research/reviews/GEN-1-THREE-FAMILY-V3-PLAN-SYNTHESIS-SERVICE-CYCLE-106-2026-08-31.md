# GEN-1 — three-family v3 plan-synthesis service cycle 106

## Scope

This was exactly one protected service-only cycle. It created no hypothesis, experiment plan,
scoring seed, scored candidate, result, evidence or confidence update and did not invoke
`nextai run`. The active cohort remains `heldout_three_family_continuous_transfer_v3`.

## Defect and minimal correction

The pre-plan audit found that `nextai plan new` attached the universal capability/full-cost
Pareto axes and the two causal promotion gates only when the active benchmark name ended in
`_v2`. The v3 experiment-plan schema requires those same fields, so an otherwise valid v3 plan
could not be registered. The correction changes the one version predicate to cover v2 and v3.
It does not change worlds, splits, tensors, normalization, candidates, metrics, directions,
budgets, seed policy, evaluator execution or result aggregation.

A new no-write regression invokes the real v3 plan generator with all four predictive-index
roles, nine frozen controls and all declared metrics. It validates the generated document against
the active schema and asserts that `pareto_capability_metrics` and
`causal_promotion_gates` are present. The focused test and full 331-test suite passed.

## Development-only preregistration input

The already-started development-role noise-floor computation was preserved but is not scientific
evidence. It uses only fixed training-role seeds 1103/2207/3301, K=4/6/9 and a deterministic
bootstrap null; it explicitly forbids EXP-0001/0002/0003 results, scoring seeds and v3 test worlds.
It freezes a minimum NRMSE effect of `0.03806855146519833` and worst-family accuracy tolerance
of `0.008823017208322348`. Artifact SHA-256 is
`6e6da320c92b39a1f427f1a0c19c7ae69c42e239c0df56d25c52679d500d7fab`; script SHA-256 is
`a31eecf656954d1a005e581c733d44cde36a8a3c706436ffdda5dc06f347b5e1`.

## Frozen integrity

- evaluator SHA-256: `6d721631f70dd384b0cd66c6b193df1a7f33842cde64332bac6c6efa925fa4d6`
- candidate-bundle SHA-256: `9c0200578f484919ee15f066e4ab88dc7656b2fcfe4ed0b2ff09a8dffb16eec5`
- manifest-file SHA-256: `c341b89b146cc0e3d7aacf91a72571ebe0d7c6c19b981961959c48cf4579b243`
- preflight certificate: `1c859f615eeef7ef27a20874f4aab9367b6c14217b510de65690ecdc97b0624f`
- protected files: 500

The evaluator digest changed only because protected plan-generation code, its regression test and
the frozen development inputs were added. Candidate-bundle digest and scientific evaluator
semantics are unchanged. The previous v3 manifest is archived append-only.

## Decision

`keep` the corrected v3 infrastructure. This maintenance result provides no evidence for a
predictive-equivalence learner and authorizes no promotion.

## Exact next discriminating experiment

In the next wake, create HYP-0027 and preregister `EXP-20260831-0004` quick on the unchanged v3
evaluator at K=4/6/9 with one runner-random scoring seed. Only after immutable preregistration may
the smallest five-bit family-blind predictive-equivalence index be implemented under identical
shared, independent, cross-family-only and support-only source/hyperparameters. Compare it against
the exact raw-window, random-hash, persistence and all other frozen controls. Require every
family/K improvement over each matched index control and persistence, both causal contrasts, the
worst-family tolerance, stable rollout, bounded local updates, K-independent capped lookup and
full-cost Pareto non-dominance. One seed may only discard or authorize unchanged three-seed
replication; a negative ends this exact design without tuning.
