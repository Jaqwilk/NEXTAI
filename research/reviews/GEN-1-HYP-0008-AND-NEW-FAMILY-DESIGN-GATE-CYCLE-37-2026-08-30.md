# Generation 1 design gate: partially observed predictive state and a new circuit family

## Scope

This was a review/design-only cycle after EXP-0038 and protocol maintenance. No benchmark, candidate, plan, seed policy or scored result was created. The question was whether the proposed `partially_observed_predictive_state_v1` would add discriminating evidence beyond EXP-0030 while satisfying HYP-0008's reactivation conditions: high-dimensional raw observations, unknown memory length, sparse non-exhaustive exploration and strong CSSR, spectral PSR and empirical-bisimulation controls.

## Existing evidence

- EXP-0016 showed exact multi-seed causal-state recovery only under a clean, constructionally identifiable intervention apparatus; the learned route was not globally Pareto-optimal.
- EXP-0020 removed clean exhaustive coverage and the factorized learner fell to `0.0417` accuracy while the dense learner reached only `0.5625`; a broken oracle-representation control prevented clean attribution.
- EXP-0030 removed latent labels and learned predictive quotients from action-observation histories. CSSR, spectral PSR, empirical bisimulation, contrastive state and information bottleneck were all exact, but CSSR dominated information bottleneck, spectral PSR dominated contrastive state, and the recurrent encoder failed capability at `3733x` CSSR workload.
- HYP-0008 is therefore dormant at confidence `0.22`; a new test must change the information structure, not merely add raw dimensions or a larger recurrent encoder.

## Primary-source constraints

- SRC-0097 establishes that a finite POMDP has a compact linear PSR, but this is an existence result; it does not make core-test discovery or exploration free.
- SRC-0098 makes CSSR a variable-memory control: it reconstructs predictive causal states from discrete sequences under its data/structural assumptions.
- SRC-0099 already demonstrates statistically consistent spectral PSR learning and planning from high-dimensional vision-like trajectories. High-dimensional observations alone therefore do not isolate a neural advantage.
- SRC-0100 shows that RPSP uses spectral/two-stage regression as consistent initialization and then refines the same recurrent filter with gradient optimization. Calling RPSP “learned” and spectral PSR “classical” does not create independent mechanisms unless the experiment isolates the effect of task-level refinement.
- SRC-0101 shows that non-uniform action coverage biases conditional spectral estimates and supplies denoising/structural corrections. A deliberately naive spectral baseline would be invalid.

## Identifiability gate

The proposed small local cohort has no clean discriminating regime:

1. If training trajectories excite every action-conditioned test needed to distinguish predictive states, coverage-aware spectral PSR and variable-memory CSSR have a principled route to the same sufficient state. A gradient-refined RPSP then starts from that state and tests optimization/constant factors, not a new representational principle.
2. If the distinguishing action sequences have zero support, two latent mechanisms can induce the same training distribution and different held-out intervention outcomes. No learner can identify the answer without an added prior; scoring one preferred architecture would reward an undisclosed ontology.
3. If support is merely low, the causal factor becomes estimator/sample efficiency. A fair test requires multiple sampling budgets and seeds plus calibrated uncertainty, not the quick K=`8/32` architecture screen proposed here.
4. Adding nonlinear high-dimensional emissions does not solve this separation. Either a feature map/clustering step preserves the sufficient observable statistics and must be charged for every control, or it destroys information and changes identifiability.
5. End-task reward refinement could distinguish RPSP from spectral initialization, but it simultaneously changes representation, policy optimization and exploration. That interaction requires a larger predeclared study and is not the cheapest falsification of dormant HYP-0008.

## Decision on HYP-0008

Reject `partially_observed_predictive_state_v1` before implementation. It would most likely repeat EXP-0030 under richer cosmetics or create an unidentifiable sparse-coverage task. HYP-0008 remains `dormant` at confidence `0.22`; no source file, benchmark, candidate or plan is warranted. Reactivation now requires an external task or dataset with naturally occurring continuous partial observability, logged coverage diagnostics and an end-task distinction that cannot be reduced to spectral initialization.

## Portfolio challenge

The 12-family portfolio has repeatedly tested retrieval, program induction, adaptive recurrence, VSA, cellular rules, energy relaxation, causal/predictive state, learned VMs, modular routing, compilation and active acquisition. Most local generators expose a small exact algebra that a classical solver recovers. Continuing to add noisy encoders around those algebras selects for another predictable null.

Primary sources SRC-0102 through SRC-0104 identify an untested architectural principle: learn the distribution directly in a smooth/decomposable probabilistic circuit so that many marginals and conditionals are exact feed-forward computations rather than autoregressive sampling or repeated generic inference. This is established prior art, not project novelty, but it is materially different from every current family.

## New hypothesis selected for a future design gate

Create HYP-0013, `learned_tractable_probabilistic_circuits`, initially `proposed` at confidence `0.30`. Its first design gate must answer whether a hidden context-specific factorization can be learned from samples and retain exact held-out conditional inference while full fit, circuit size, update work and bytes touched beat an empirical full table, autoregressive chain, Chow–Liu tree, generic variable elimination and fixed-region SPN. Oracle circuit is a separate lower bound.

Do not construct a benchmark around a hand-supplied SPN and call linear inference a discovery. The positive signature requires learned structure, nontrivial held-out evidence masks, calibrated conditional answers and favorable end-to-end scaling with variables. If the compact circuit is supplied, if circuit size grows exponentially, or if a classical tree/factor compilation matches it, the family returns dormant after one quick.

## Exact next action

Perform one design-only gate for `context_specific_probabilistic_circuit_v1`: specify an identifiable distribution family with hidden context-specific independence, derive analytic oracle marginals, verify that no target label or factorization leaks into samples, and preregister required accuracy/calibration and circuit-size metrics. Only after that gate passes may a later cycle implement and freeze an evaluator. No scored experiment is authorized by this review alone.
