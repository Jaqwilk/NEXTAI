# Operator-algebra v3 protected migration design — cycle 65

## Scope

This was one design/service-only cycle after the cycle-64 transition audit. It created no experiment plan, candidate implementation, scoring seed, runner invocation, result, dependency, external model/API or protected-file mutation. The active `heldout_mechanism_recombination_v2` evaluator and all EXP-0056 artifacts remain unchanged.

The intended next experiment was EXP-0057 for HYP-0022. The preregistration gate stopped before plan creation because the frozen v2 contract still names the discarded HYP-0021 implementation and ablations.

## Exact blocking conflict

`config/research.toml` fixes:

- `shared_candidate = "shared_latent_mechanism_library"`;
- `independent_ablation = "independent_latent_mechanism_library"`;
- `no_cross_mechanism_ablation = "no_cross_mechanism_factorizer"`.

`schemas/experiment_plan.schema.json` independently requires those same three identifiers and requires all eight EXP-0056 candidates in every mechanism-recombination plan. `nextai plan new` copies the config values into the immutable plan. Therefore a nominal HYP-0022 plan created now would machine-declare the HYP-0021 pair-selection learner as its shared candidate. Adding `operator_algebra_completion` to the candidate list would not repair the causal contract.

Reusing the old identifiers by replacing their implementations was rejected. It would obscure candidate identity, overwrite the live source of negative candidates, and make the source-identical HYP-0022 ablations impossible to distinguish from historical HYP-0021 semantics. Editing a generated plan after registration is also forbidden.

## Minimal protected migration

A scientifically valid comparison needs a new cohort `heldout_mechanism_recombination_v3`. The evaluator task, generator, source seed, state conjugation, train/held-out compositions, K/D/Q grid, targets, metrics, state limit and five registered classical/oracle baselines remain byte-for-byte and semantically identical to v2. Only the future candidate contract changes.

The authorized service wake would make the following minimal protected changes, without candidate implementation or scoring:

1. Add a delegating benchmark module whose sole version change is `BENCHMARK_VERSION = "heldout_mechanism_recombination_v3"`.
2. Change active config to v3 and set:
   - shared: `operator_algebra_completion`;
   - independent: `operator_algebra_independent`;
   - no-relations: `operator_algebra_no_relations`.
3. Make the plan schema version-aware rather than weakening it globally:
   - v2 plans continue to require the three historical HYP-0021 IDs and eight historical candidates;
   - v3 plans require the three HYP-0022 IDs plus the unchanged classical baselines;
   - every existing immutable plan must still validate unchanged.
4. Add schema/config tests proving that a v2 plan cannot masquerade as v3, a v3 plan cannot name the HYP-0021 shared learner, and both historical EXP-0056 and a future-plan fixture validate.
5. Reuse the existing semantic baseline registry unchanged because the five mandatory baselines and their implementations do not change.
6. Freeze a new manifest, archive the v2 manifest, run the full suite, report, integrity and doctor, and record the v3 evaluator digest.

No `operator_algebra_*` module or semantic candidate fixture is created during migration. Those belong after immutable EXP-0057 preregistration, so the tested implementation cannot precede its plan.

## Scientific invariants retained

- EXP-0056 and HYP-0021 remain immutable negative history.
- The evaluator does not become easier and no score is compared across changed task semantics; v3 is a new cohort only because the candidate/plan contract changes.
- Runner-random seed realization still occurs only after plan, integrity, source audit and baseline conformance.
- Classical baselines, full cost axes, `0.95` overall and `0.90` minimum-combination thresholds remain unchanged.
- No global cooldown, dependency, external model or API is added.

## Decision

`maintenance-required-before-preregistration`. Do not create EXP-0057 under v2. The migration is protected because it changes config, the experiment-plan schema, benchmark version and manifest. The standing autonomous objective does not override the explicit-approval rule for protected evaluator/protocol migration.

No confidence change is warranted: this is infrastructure, not evidence. HYP-0022 remains `proposed` at `0.14`.

## Exact next step

After explicit user approval for `heldout_mechanism_recombination_v3`, perform exactly one protected service-only migration implementing the six items above. Do not create a plan, candidate, seed or score in that wake. Only the following wake may preregister EXP-0057 and then implement/test the three `operator_algebra_*` candidates against the frozen v3 digest.
