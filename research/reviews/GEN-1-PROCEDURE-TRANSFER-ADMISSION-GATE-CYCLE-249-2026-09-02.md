# GEN-1 procedure-transfer admission gate — cycle 249

## Scope

This is the second bounded no-scoring SEARCH MODE cycle after
`EXP-20260902-0001`. It audits only existing frozen cohort contracts. It
creates no hypothesis, experiment, plan, candidate, seed, score, benchmark,
evaluator, runner, schema or manifest change. The active SuiteSparse cohort
and all completed artifacts remain unchanged.

## Natural-interface audit

| Existing cohort | Candidate-visible interaction | Natural chronological target reveal? | Admission result |
|---|---|---:|---|
| `heldout_three_family_continuous_transfer_v7` | batch `fit`; per-world supervised support `adapt`; trajectory `predict` | no | fails: support adaptation is not a post-query update stream |
| `heldout_wt_changepoints_prequential_v5` | `fit`; trajectory query; target reveal; `update` | yes | passes locally |
| `heldout_repository_sequence_compression_v6` | `fit`; byte context query; realized byte; `update` | yes | passes locally |
| `heldout_parallel_masked_infilling_v12` | `fit`; offline masked queries; evaluator-only targets | no | fails: hidden targets are never revealed to the learner |
| `heldout_suitesparse_cross_matrix_prolongation_v1` | whole anonymous CSR matrix; build prolongation; external CG solve | no | fails: there is no prediction-target update stream |
| `cross_family_sparse_set_memory_v5` | evaluator-packed token query and one revealed target | yes, but synthesized | fails: its common interface is a hand-written serialization of native typed records |

Only the wind-turbine and repository-compression cohorts naturally expose the
same abstract order `query -> reveal -> update`. Their public values still have
incompatible semantics: a continuous multichannel trajectory versus a
256-category byte distribution. A third qualitatively different natural
family is absent. Manufacturing one common loss, gradient, coordinate adapter
or tokenization would move representation work into the evaluator and import
the forbidden ontology.

The role registries also cannot be reused as aliases. WT v5 is frozen to the
particle-proposal mechanism, repository v6 to the selective state-space
mechanism, and SuiteSparse v1 to the closed prolongation mechanism. Scoring a
new procedure under one of those names would violate source identity and
historical semantics; adding a role would require a protected new cohort.

## Causal and classical-control gate

A full learned update function remains causally broader than NEXTAI's previous
learned rates, gates, proposal weights, retention values and local label
tables. That distinction is insufficient for admission. On the two natural
online contracts, an anonymous source-identical rule must also emit objects of
different mathematical type. A generic coordinate-wise update would reduce
to the already tested learned-rate/LMS/RLS family; a richer adapter would be
domain-specific representation code. PPM-D and CTW are mandatory controls for
bytes, while posterior means, persistence, Kalman/control banks and fixed
adaptive estimators are the relevant continuous controls. There is no single
matched classical envelope or disabled ablation that preserves identical
semantics across three families.

## Prospective full-cost crossover

The local evidence makes a crossover claim implausible before implementation:

- On continuous transfer, the shared learned update law in
  `EXP-20260831-0009` consumed about `9.810e9` R16 operations versus about
  `9.692e9` for persistence, while its mean NRMSE improvement over persistence
  was below the frozen meaningful-effect threshold and cross-family-only lost
  to support-only.
- On WT, `EXP-20260901-0060` retained the desired local/K-independent
  signature but was worse than the posterior mean and control-level bank and
  was Pareto-dominated after acquisition, fit, query and update cost.
- On repository compression, `EXP-20260901-0062` spent about `9.907e8` fit
  operations and reached `4.679687` bits/byte; PPM-D reached `3.350801` and CTW
  `4.365597` at much lower declared R16 work.
- The procedure-discovery contradiction reviewed in cycle 248 required tens
  of thousands of accelerator core-hours and relied on an RL field ontology.

No existing cohort supplies a prospective reuse count large enough to recover
discovery cost while also demonstrating useful quality unavailable to its
classical control. A cheap compiled deployment does not erase meta-fit and
data-acquisition cost.

## Observation, interpretation and uncertainty

**Observation.** Two existing cohorts have a natural online reveal/update
contract; four other relevant cohorts do not, or obtain it through an
evaluator-authored serialization. Frozen roles are mechanism-specific. The
available scored analogues have no useful full-cost advantage.

**Interpretation.** The proposed common procedure cannot presently be tested
without either reducing it to an old adaptive estimator or introducing the
very domain adapters and semantic alignment that the hypothesis forbids. This
is a contract-level rejection, not evidence that transferable procedures are
impossible in principle.

- Confidence `0.99` that no three existing frozen families expose the required
  natural source-identical interface.
- Confidence `0.97` that reusing current role IDs would reinterpret protected
  historical semantics.
- Confidence `0.93` that no prospective full-cost crossover is supported by
  current local evidence.
- Confidence `0.88` that a generic coordinate optimizer would duplicate
  learned-rate/LMS/RLS tests rather than test procedure-semantic transfer.

## Decision

`ABANDON_META_DISCOVERED_UPDATE_PROCEDURE_NEIGHBORHOOD`.

The admission gate fails. Do not create a benchmark, protected migration,
hypothesis, plan or quick for this neighborhood. Preserve cycle 248 as a
useful literature contradiction and this cycle as the audit that prevents an
invalid implementation.

## Exact next discriminating action

Cycle 250 remains SEARCH MODE and must broaden outside parameter,
representation and update-procedure transfer. Audit primary literature and
NEXTAI history for **interface-free operation-vocabulary acquisition**: a
learner must derive a small executable operation or certificate directly from
raw observations, with externally checkable consequences and no evaluator DSL,
family labels or semantic adapters. AlphaDev, AlphaTensor, CLRS-style traces,
learned optimizers, active sensing, exact guidance and compiled dictionaries
are mandatory duplicate controls. If no natural existing corpus and
prospective full-cost crossover exist, reject the neighborhood without a new
benchmark or scored alias.

Experiment ID: `none`. Immutable plan path: `none`. Scoring seed: `none`.
