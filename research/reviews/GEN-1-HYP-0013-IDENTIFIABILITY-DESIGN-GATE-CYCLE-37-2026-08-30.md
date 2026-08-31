# HYP-0013 identifiability design gate: context-specific probabilistic circuits

## Status and scope

Design-only cycle. No evaluator, candidate, immutable plan, scoring seed or scored result was created. This gate asks whether a compact local benchmark can test learned tractable probabilistic circuits without supplying the target circuit or making exact conditional inference impossible from samples.

## Proposed distribution family

For knowledge size K=`8/32`, each world has K opaque binary payload variables and one opaque binary context selector. A runner-seeded permutation hides which observed coordinate is the selector and removes positional pair identities.

- The selector C is uniform.
- Conditional on C=`0`, payload variables form independent correlated pairs `(0,1),(2,3),...`.
- Conditional on C=`1`, they form the shifted matching `(1,2),(3,4),...,(K-1,0)`.
- Within a pair, the first bit is uniform and the second equals it with probability `0.9`; pair factors are independent conditional on C.
- Training contains `64K` complete joint samples and no query answers, target marginals, selector label, pairing label or circuit nodes.
- The coordinate permutation, sample order and query masks change with the runner-realized scoring seed.

The true distribution is a smooth/selective decomposable circuit: a root sum over the two selector values followed by products over disjoint pair factors. This deliberately favors the architectural family, so a learned contextual-tree control that can recover the same representation is mandatory.

## Identifiability proof and development check

The selector is not identifiable by marginal correlation: exact enumeration at K=8 gives mutual information `I(C; Xi)=0` for every payload variable. It is identifiable by conditional factorization.

For a proposed selector S and each value s, compute all pairwise conditional mutual informations among the remaining K variables. Select a maximum-weight disjoint pairing and define residual as total pairwise information outside that pairing. Under the true selector, conditional independence across true pairs makes the population residual exactly zero. Under a payload variable used as false selector, the unobserved mixture of the two shifted matchings leaves incompatible dependencies that no single perfect matching captures.

Exact enumeration at K=8 produced:

- true selector residuals `0/0`;
- false-selector residuals at least `0.387530553743` and normally `0.469813432248`;
- normalized total mass `1.0`;
- marginal selector/payload mutual information numerically `0` for all eight payloads.

The unscored development seed `1103`, using only raw samples and a random coordinate permutation, recovered the true selector:

- K=8, N=512: true residual `0.107120`, runner-up `0.783246`;
- K=32, N=2048: true residual `0.402891`, runner-up `2.885468`.

This is a design sanity check, not scoring evidence and not a seed search. The temporary enumerator was removed after recording these invariants.

## Exact oracle and query protocol

For partial evidence e, each context component has evidence likelihood equal to the product of the one- or two-variable marginal of every pair factor. If C is unobserved, sum the two component likelihoods with prior `0.5`; if observed, retain only that component. For an unobserved target Xt:

`P(Xt=1 | e) = P(e, Xt=1) / P(e)`.

This gives an analytic oracle without enumerating `2^K` assignments. Scored candidates receive only training samples and queries.

- D=`1/4/6` is the number of observed evidence variables.
- Cold queries include both selector-observed and selector-hidden masks.
- Near queries always hide the selector and choose evidence spanning dependencies from both matchings, preventing a single-context shortcut.
- Accuracy is the fraction of conditional probabilities within absolute error `0.05`; also report mean absolute probability error, conditional log loss and calibration error.
- A local update supplies a small new raw-sample batch after one pair parameter changes from `0.1` to `0.25`; measure updated conditional accuracy, unrelated-context retention, update operations and whether unrelated circuit structure is rebuilt.

## Required candidates

1. `uniform_conditional` — leakage/random negative control.
2. `empirical_joint_table` — assignment table with exact lookup when covered, exposing exponential state/sample dependence.
3. `empirical_autoregressive_table` — fully charged chain-rule estimator with learned conditional tables.
4. `chow_liu_tree` — strongest single-tree pairwise structure learner.
5. `pairwise_factor_elimination` — learned pairwise factor graph with generic variable elimination and charged intermediate work.
6. `contextual_chow_liu` — searches every selector and learns one matching/tree per value; strongest classical control and likely null explanation.
7. `fixed_region_spn` — same circuit operations with a seed-independent wrong region graph.
8. `learned_decomposable_spn` — generic independence/instance-split learner; the HYP-0013 candidate.
9. `oracle_context_spn` — privileged selector, matchings and parameters; separate lower bound only.

All candidates must charge raw sample reading, pair/dependence estimation, structure search, parameter fit, persistent tables/circuit nodes, query evaluation, bytes touched and local updates. A supplied factorization, uncharged compilation or enumeration hidden in preprocessing invalidates the cohort.

## Metrics and decision contract

Primary axes:

- maximize: `accuracy`, `near_equivalent_accuracy`, `continual_retention`;
- minimize: `conditional_probability_mae`, `conditional_log_loss`, `mean_query_ops`, `fit_ops`, `state_bytes`, `circuit_nodes`, `update_ops`, `workload_ops_r16`.

K has only two values in quick, so any K slope is explicitly screening-only. D has three points and may use the registered regression diagnostics. Latency remains secondary to operation counts.

Positive/retain only if learned SPN reaches every-cell accuracy at least `0.95`, calibrated near queries and retention, and is on the implementable full-system Pareto frontier against `contextual_chow_liu` and pairwise elimination. Quick cannot promote.

Null if contextual Chow–Liu recovers the same circuit/capability with equal-or-lower full workload, showing that the apparent PC benefit is a classical conditional-tree decomposition. Negative if the learned SPN misses calibration/near queries, grows superlinearly in circuit size without compensating capability, or depends on leaked selector/pair metadata.

## Confounds

- The generator is exactly representable by a small PC and therefore tests best-case discoverability, not open-world universality.
- The selector has a unique conditional-independence signature by construction. Real data may have several nearly equivalent decompositions.
- Full joint samples avoid missing-data structure learning; queries, not training records, are partially observed.
- A contextual tree is itself a tractable circuit. Classical dominance would reject a distinct learner but still retain probabilistic compilation as established prior art.
- K=`8/32` cannot establish polynomial versus exponential asymptotics. It can only expose immediate state/work trends and gross table blow-up.
- Conditional-probability tolerance must not replace calibration metrics; a candidate cannot pass by always predicting a coarse majority.

## Decision

`pass design gate`, with HYP-0013 confidence unchanged at `0.30`. The family is identifiable without marginal label leakage, the oracle is analytic, the strongest alternative is explicit, and the negative/null outcomes are informative. Move HYP-0013 from `proposed` to `testing`, but do not claim evidence for the hypothesis.

## Exact next action

In the next bounded cycle, implement only the evaluator/contracts/tests for `context_specific_probabilistic_circuit_v1`, add the four new probability/circuit metrics to the protected schemas/config, run the old suite plus evaluator invariants, and freeze the evaluator digest before creating a plan. Candidate code must still wait until after immutable preregistration. Do not score in the evaluator-construction cycle.
