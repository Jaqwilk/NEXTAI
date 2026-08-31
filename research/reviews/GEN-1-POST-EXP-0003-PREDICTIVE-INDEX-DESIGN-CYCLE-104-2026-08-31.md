# GEN-1 — post-EXP-0003 predictive-index design review, cycle 104

## Scope

This was one bounded review-only cycle after valid negative `EXP-20260831-0003`. It created no hypothesis, experiment plan, candidate implementation, scoring seed, runner invocation, result, dependency, external model/API, benchmark, schema or protected evaluator change. `heldout_three_family_continuous_transfer_v2` remains active and unchanged. The currently staged protected history from EXP-0003 was inspected rather than overwritten.

## Objective evidence

The three valid v2 quicks test three materially different forms of parameter sharing under the same frozen worlds and causal assignments.

| experiment | changed mechanism | transferable observation | decisive failure |
|---|---|---|---|
| EXP-20260831-0001 | coordinate-aligned masked spectral dynamics | none robust | catastrophic quality and persistence dominance |
| EXP-20260831-0002 | channel-exchangeable bounded residual around persistence | shared beat independent in all six family/K cells | cross-family-only lost in both mechanical families and worst-family quality fell below persistence |
| EXP-20260831-0003 | support-calibrated convex prior over persistence/ridge/RLS | four of six shared cells were positive | both DS08a shared cells and all six cross-family cells failed; persistence was much better and cheaper |

These results support a narrow conclusion: same-family observations can regularize a small stable learner, but direct dynamics parameters or algorithm weights have not transferred across the three families. They do not justify another rank, residual, shrinkage, ridge, mixture-temperature or support-blend variant. None of the three results has more than one scoring seed, no candidate is accuracy-gated Pareto eligible, and no scaling claim is supported.

Earlier portfolio evidence removes several superficially different escapes. Recurrent state, dictionary readout and relation fragments had zero worst-family capability in the old heterogeneous cohort; learned online updates lost to LMS by orders of magnitude in cost; sequence hierarchy lost to CTW; grammar-library transfer collapsed into SEQUITUR/Re-Pair/adaptor-grammar prior art; operator-equation completion had a real K=32 signal but zero minimum-combination accuracy and 26.1x exact-MDL meta-fit. The current three-family worlds also do not contain one evaluator-supplied common state/operator algebra.

## Candidate direction comparison

| direction | reason to consider | strongest null | review decision |
|---|---|---|---|
| another shared continuous dynamics parameterization | active v2 already exposes the required causal assignments | persistence, ridge/RLS, autoregressive and three consecutive negatives | reject as outcome-informed family tuning |
| richer learned test-time update | directly targets local adaptation | LMS/RLS/Kalman; EXP-0043 already showed cost and identifiability failure | reject until a real prequential boundary exists; v2 does not reveal targets after queries |
| cross-file grammar or hierarchical compressor | raw observations and local updates are natural | CTW, PPM-D, LZ, SEQUITUR/Re-Pair | reject; prior design gate showed no distinct calibrated mechanism |
| predictive-equivalence index over anonymous transition windows | changes representation acquisition rather than dynamics parameters; can reuse v2 worlds and hidden outputs | exact raw-window nearest neighbour/local linear prediction, random projection hashing, persistence and ARX | select for one semantic/service gate only |

## Selected causal principle

The selected principle is `self_supervised_predictive_equivalence_index`, not yet a hypothesis.

Training transitions are anonymous numeric history/future-public windows. A learner may use training-world targets to learn a bounded code whose buckets minimize future-target dispersion while remaining balanced. Each bucket stores only a compact local transition operator and sufficient statistics. A held-out support prefix may insert or revise bucket statistics locally; it may not refit the global code. Querying computes one code and reads one capped bucket, so charged query work is structurally independent of the number of dormant training windows. The same source, code width, bucket cap, local operator, update law and constants must serve shared, independent, cross-family-only and support-only assignments.

This tests one hard missing factor from HYP-0001: whether a useful index key can be acquired from raw predictive evidence without supplied positive-pair identity. Indexed access itself is classical and receives no novelty credit. CPC (`SRC-0077`) is prior art for future-predictive representation learning and Indyk–Motwani ANN (`SRC-0080`) is prior art for sublinear indexed retrieval. A positive could support only the narrow learned-binding claim.

## Required discriminator and controls

The present v2 cohort is sufficient in data, split, tensor contract, loss and causal assignments, and it already accepts three knowledge scales `K=4/6/9`. It is not sufficient in controls: it has no source-identical raw-window nearest-neighbour/local-linear index or random-projection hash. Without them, a score cannot distinguish learned predictive binding from ordinary nonparametric retrieval or hashing.

Before any hypothesis or plan, one protected service-only successor may therefore change only candidate/control registration and semantic fixtures while preserving all v2 worlds, splits, tensors, normalization, metrics, directions, budgets and success semantics. It must add:

1. an exact raw-window nearest-neighbour plus local-linear operator control;
2. a random-projection hash with the identical bucket cap, state limit and local operator;
3. a semantic fixture where two observation windows are close in raw distance but have different futures, while two farther windows share the same future operator;
4. relabeling, world-order and channel-permutation fixtures;
5. exact accounting for representation fit, index construction, bucket probes, collision resolution, local support inserts, bytes, resident/peak state and R1/R4/R16 work;
6. a pre-seed assertion that candidate code never reads family names, native types, paths, semantic channel names or test outputs.

If adding these controls changes the evaluator digest, create `heldout_three_family_continuous_transfer_v3` as a prospective comparison cohort. Do not edit or reinterpret v1/v2 history. No new schema or data is justified.

## Prospective kill and success signatures

All numerical thresholds, code width, bucket cap, collision policy and minimum meaningful effects must be selected from development-only training worlds and frozen before hypothesis creation. A future quick must use one runner-random seed and `K=4/6/9`, and cannot promote.

Kill the direction before scoring if the semantic fixture does not separate predictive binding from raw/random indexing, if capped lookup cannot be audited, or if v2 data/metrics must change. Kill it after one valid quick if any of the following occurs:

- learned indexing fails to exceed both raw and random source-identical controls by the frozen meaningful margin in every family and K;
- shared-versus-independent or cross-family-only-versus-support-only transfer fails in any family/K cell;
- worst-family quality falls outside a development-frozen tolerance of persistence;
- query work or bytes touched increase with K despite a fixed bucket cap;
- support insertion triggers global refitting;
- a simpler implementable control dominates at matched quality and full cost.

A one-seed conjunctive positive permits only an unchanged three-seed replication. Even a replicated positive would establish learned predictive binding on these visible continuous worlds, not an LLM successor or a general scaling law.

## Decision and confidence

`select_design_gate_only` for `self_supervised_predictive_equivalence_index`. Confidence is `0.97` that direct parameter-sharing variants should stop, `0.90` that raw/random indexed controls are necessary to isolate the new causal factor, and only `0.10` that a learned predictive index will survive those controls and persistence. No HYP-0027 is created in this cycle.

## Exact next discriminating cycle

First obtain a local commit for the already verified staged EXP-0003 history; the host currently rejects `git commit` before execution under `AskForApproval=Never`, and protected uncommitted candidate/manifest changes prohibit scoring. Once the commit boundary exists, perform exactly one protected service-only cycle with no hypothesis, plan, seed or scoring: add the two source-identical indexed controls and semantic fixtures, preserve the v2 data and metrics, activate v3 only if full pytest, preflight certificate, integrity and doctor pass. Only a later wake may preregister one HYP-0027 quick at K=`4/6/9`.
