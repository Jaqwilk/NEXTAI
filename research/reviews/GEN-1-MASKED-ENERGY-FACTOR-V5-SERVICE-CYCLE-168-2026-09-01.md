# Cycle 168 — masked energy-factor v5 protected service migration

## Scope

This was exactly one protected service-only cycle. It created no hypothesis,
experiment plan, runner-random seed, candidate implementation or scored result.
The completed `EXP-20260901-0024` and all earlier plans, results, analyses and
manifests remain immutable.

## Objective observations

- `heldout_parallel_masked_infilling_v5` directly re-exports the v4 `run_suite`;
  v4 directly re-exports v3. The evaluator execution path is therefore identical.
- V5 preserves all 48 file hashes and roles, whole-file split, random byte
  relabeling, masks, spans `8/32/128`, K=`8/32`, rounds=`1/4/6`, Q=`8`, immutable
  snapshots, metrics, cost formulas, state budget, Pareto axes and eight controls.
- The only scientific contract change is prospective: the three Born-MPS role
  identifiers are replaced by a learned sparse energy-factor graph, its
  source-identical one-sweep intervention and its source-identical frozen-factor
  intervention.
- No module exists for any of the three v5 roles. The plan schema requires all
  three exact identifiers and rejects substitution with a historical v4 role.
- A small frozen contract fixture has two masked variables between unequal
  observed endpoints. Independent boundary completion produces `(0,0,1,1)`,
  while the overlapping middle factor makes `(0,0,0,1)` lower energy. The
  fixture also checks nonincreasing accepted energy, equality-energy invariance
  under byte relabeling, absence of a target field and factor-by-iteration cost.
- Historical v1-v4 regression tests remain valid independently of the active
  cohort. Focused tests, all 455 repository tests and the eight registered
  semantic baseline gates passed.
- A development-only, non-scored real-file smoke ran every frozen control at
  K=8, one refinement round and one case per span. All eight returned complete
  rows for all three spans. This did not execute an experimental role.
- Integrity verified 625 protected files. The preflight certificate digest is
  `e5d48688c8505d0628fd12ee160a3d0a9c993e91de7b4886817b3d3bc43c84ea`.
  Doctor passed with eight semantic baselines and zero pending plans.

## Interpretation and uncertainty

The existing benchmark can discriminate this direction without another toy or
schema: long masked spans and immutable parallel rounds test distributed
constraint relaxation, while exact bidirectional Markov and parallel Markov-BP
are strong implementable controls. This migration is infrastructure readiness,
not evidence that learned energy factors work. The main uncertainty is whether
a preregistered sparse learned factorization can improve conditional loss or
exact-span completion rather than merely reproduce finite-order Markov inference.

Confidence that the migration is role-only and preserves historical evaluator
semantics: high. Confidence in the unimplemented mechanism: low (`HYP-0007`
remains dormant at its prior confidence until a valid scout exists).

## Decision and next discriminating experiment

Decision: activate v5 for exactly one later scout. Keep all scientific evidence
and confidence unchanged. The next wake must revive `HYP-0007` explicitly and
preregister one immutable quick before implementing the three source-identical
roles. Freeze graph construction, sparsity, factors, initialization, learning
and relaxation constants plus the semantic-test digests before runner seed
realization. Score one runner-random seed over the full K/round/span matrix
against all eight controls. Require causal improvement over both ablations,
meaningful loss/exact-span gains, monotone-energy and equivariance conformance,
bounded critical depth/state, explicit full cost and implementable Pareto
non-dominance. A valid negative ends this exact energy-factor rule without
tuning; one positive seed only authorizes unchanged replication.

Integrity: PASS. Budget: service-only, no scoring. Experiment ID and immutable
plan path: none by design.
