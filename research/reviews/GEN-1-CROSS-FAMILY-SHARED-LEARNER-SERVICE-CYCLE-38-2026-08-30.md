# Cross-family shared learner — service cycle 38

## Scope

This cycle responds to the explicit user direction to stop building one-off benchmark algorithms and test one unchanged local learner across several existing world families. It is service/design only: no scored candidate, scoring seed or immutable experiment plan is created. The active harness supports only one homogeneous benchmark and cannot yet record the required transfer boundary, so scoring before a protected contract migration would be scientifically invalid.

## Existing families selected

The future cohort reuses four existing generators; it does not invent a fifth toy world:

1. `context_specific_probabilistic_circuit_v1` — hidden conditional independence and calibrated probabilistic inference.
2. `action_conditioned_predictive_equivalence_v1` — history compression, forecasting and action-conditioned predictive state.
3. `nonlinear_local_state_transfer_v1` — reusable local transition representation, recurrent composition and state repair.
4. `behavioral_conjugacy_library_transfer_v1` — representation-invariant operator alignment and program composition.

All four randomize observable labels or coordinates around reusable latent structure, but test distinct capabilities. Worlds produced from fixed development seeds are training worlds. Worlds produced only from runner-realized scoring seeds are unseen test worlds. No scoring seed, test target, hidden state, selector, descriptor kind, primitive role or regime identity may enter the candidate input.

## One unchanged learner contract

The tested candidate will be one source module and one parameter/state update rule across all four families. The evaluator may convert public observations into a single frozen family-neutral episode format, but it may not pass family names, native dataclass names, oracle fields or hand-derived roles. The format must use the same structural markers, token budget, output protocol and accounting in every family. The candidate may learn from values and relations in the episodes; it may not dispatch on family, import benchmark modules, contain per-family constants or receive separately tuned hyperparameters.

Slow/shared parameters are fit once on the pooled training worlds and frozen before any test world is opened. Each unseen test world may expose only its preregistered support observations; any local state update is charged. No gradient, threshold, representation dimension or stopping rule may change after a test query or result is observed.

The smallest credible candidate is a shared permutation-equivariant predictive encoder with one local state learner and one generic structured-output head. The precise mechanism must be preregistered after the evaluator is frozen; this service cycle does not implement it.

## Mandatory comparisons

The implementable specialist suite is the principal null. It sums, rather than averages away, the fit, state, update, query and acquisition costs of separate family-specific models:

- probabilistic circuit: `contextual_chow_liu`, `empirical_joint_table`, `empirical_autoregressive_table`; ordinary `chow_liu_tree` is retained with its prior timeout risk;
- predictive state: `cssr_state_reconstructor`, `spectral_psr_state`, `empirical_bisimulation_state`;
- local dynamics: `exact_finite_state_propagation` plus the strongest learned sparse control;
- behavioral transfer: `relational_graph_mdl_library` plus primitive enumeration.

Native oracles are reported separately and never enter the implementable Pareto front. Additional shared controls must include an unchanged empirical joint model, unchanged autoregressive model, random/frozen representation ablation and a no-cross-family version of the same learner trained independently per family. This isolates representation transfer from model capacity and pooling more data.

## Frozen train/test and seed policy

- Training worlds: public development seeds from the budget tier, expanded by fixed family-specific salts inside the frozen evaluator.
- Test worlds: runner-random scoring seeds only, realized after plan validation, source audit and integrity verification.
- Quick: one runner-random seed, used only to kill an implementation or reveal a large signal; it cannot promote.
- Screen: at least three runner-random seeds if and only if quick survives.
- Any collision between a derived training seed and a scoring seed, any test-world access during meta-fit, any post-result tuning, or any family-specific branch in the shared learner invalidates the run before interpretation.

## Required metrics and full boundary

Primary capability axes are unseen-world transfer accuracy and the minimum mean accuracy over the four families. A candidate that succeeds in three families and fails one does not pass. Family-native calibrated loss remains mandatory for probabilistic queries, while exact native task correctness is used elsewhere.

Cost includes raw observations acquired, canonical encoding, pooled meta-fit, test-world support fit, every local update, every query, state bytes, peak fit memory, bytes touched and declared R1/R4/R16 workloads. The specialist suite pays all four models and all four states. The shared learner pays pooled meta-fit once but may not hide test adaptation or serialization work.

Success requires every family mean at least `0.90` in quick, overall transfer at least `0.95`, no family below the strongest matched shared-control by more than `0.02`, and membership on the implementable Pareto frontier when transfer, minimum-family accuracy, full R16 workload, state and acquisition/meta-fit cost are included. One seed only authorizes a screen.

The hypothesis is null if the shared learner is dominated by the specialist suite or by the no-cross-family ablation, if its gain comes only from pooled sample count, or if any family requires a manual adapter that exposes its ontology. A crash falsifies only the implementation.

## Infrastructure gap and service decision

The current plan schema has one benchmark name and no machine-readable cross-family split or invalidation policy. The result aggregation has no `world_family`, `transfer_accuracy`, `minimum_family_accuracy`, `data_acquisition_ops` or `meta_fit_ops`; Pareto analysis therefore cannot enforce the stated success rule. The active evaluator also exposes family-specific candidate APIs.

This cycle may extend the protected schemas, aggregation and protocol with those generic fields, add regression tests and move the new cohort to `maintenance`. It must not implement the candidate, create an immutable scored plan or run scoring. After tests and manifest freeze, the next cycle must build and audit the family-neutral evaluator from the four existing generators. Only after the evaluator digest is frozen may EXP-0041 be preregistered; only after that plan exists may the shared candidate and baseline wrappers be implemented.

## Exact next discriminating experiment

`EXP-20260830-0041` is reserved conceptually, not yet registered. It will be a `quick` cross-family screen under `cross_family_shared_representation_v1`, with one runner-random scoring seed, K=`8/32`, D=`1/4/6`, Q=`8`, the frozen train/test policy above and the mandatory shared/specialist/oracle controls. The decisive observation is whether one unchanged learner remains above the per-family gates and non-dominated after all four families and all full-system costs are combined.
