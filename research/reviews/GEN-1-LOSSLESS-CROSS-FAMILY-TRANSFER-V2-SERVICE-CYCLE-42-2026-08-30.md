# Lossless cross-family transfer v2 — service cycle 42

## Scope and decision

This user-authorized protected service cycle changes the research direction back to the central transfer question, but does not repeat EXP-0041/0042. No immutable plan, candidate implementation, scoring seed, runner call or scored result is created. The completed v1 cohort remains immutable.

The v1 interface was not neutral in information: at K=32 the probabilistic support serialized to 139,270 integers and was deterministically reduced to 65,536, while predictive, local and program supports were 19,716, 3,330 and 1,956 and were preserved. EXP-0042 therefore validly rejects its pooled SVD/pointer learner, but it does not cleanly test whether a shared learner can use a lossless common observation boundary.

## Existing families and unseen-world split

Version 2 reuses exactly four frozen generators and creates no new toy family:

1. `context_specific_probabilistic_circuit_v1`: conditional probabilistic inference;
2. `action_conditioned_predictive_equivalence_v1`: predictive-state compression and action choice;
3. `nonlinear_local_state_transfer_v1`: local dynamics and recurrent composition;
4. `behavioral_conjugacy_library_transfer_v1`: representation-invariant program composition.

Training worlds use fixed seeds 1103, 2207 and 3301. Test worlds and their observable relabelings derive only from runner-realized scoring seeds after plan validation, evaluator integrity and candidate-source audit. The evaluator rejects collisions across every family-derived seed. The learner receives anonymous slots, complete public supports and queries; it never receives family names, class/field names, native types, hidden roles, paths, oracle objects or test targets during fit.

## One unchanged local learner

The planned `shared_multiverse_local_learner` is one source-identical, bounded-state learner across all cells. Its preregistered causal factor will be a shared local relation representation learned from structural-token co-occurrence and reused by one generic prediction/update rule. It may form representations from values and containment/equality relations present in the lossless stream, but it may not dispatch on family, slot, native type, token position template or a hand-written ontology. One representation dimension, update law, state cap and stopping rule apply everywhere.

The evaluator implements only the information boundary, not this candidate. Candidate code is deliberately deferred until after EXP-0045 is preregistered. This prevents the architecture from being fitted to development outputs during harness construction.

The essential causal ablation is `independent_multiverse_local_learner`: identical source and total family ensemble, but no parameters shared across families. Shared success must exceed this ablation, not merely exploit four times as many pooled examples.

## Common representation and leakage controls

The v2 encoder recursively preserves all public dataclass values, mappings, sequences, booleans, integers, floats and nulls with syntax-only container/scalar markers. It performs no truncation, subsampling, hashing, family normalization or name/type encoding. The same function handles every family.

Metamorphic tests before scoring must verify: losslessness above the old 65,536-token limit; invariance to dataclass and field renaming; anonymous public test slots; exact train/test seed disjointness; and rejection of family labels or privileged objects by implementable candidates. Any family-specific source branch, test-result access during fit, post-score tuning, oracle-derived feature or evaluator digest change invalidates the cohort.

## Matched comparisons

Mandatory shared controls are `shared_contextual_chow_liu_v2`, `shared_empirical_joint_v2` and `shared_autoregressive_v2`. They receive the same lossless anonymous interface, data and state limit. The independent learner ablation isolates actual cross-family sharing.

The fully charged specialist controls are contextual Chow–Liu, empirical joint and autoregressive suites fit through their native public views. Their acquisition, fits, resident states, queries and updates are summed over all four components. `oracle_cross_family_suite_v2` is a privileged attainable bound and is excluded from the implementable Pareto frontier. This directly includes the strongest EXP-0042 controls requested by the user.

## Full cost boundary and success rule

Every comparison receives the same K/D/Q matrix and wall/RSS limits. Report acquisition and lossless serialization operations, pooled or specialist fit, support fit, every query and update, mean bytes touched, fit peak, resident/peak state and workloads R1/R4/R16. Latency remains a noisy implementation measurement; operation counts are estimates where candidates cannot expose exact hardware work.

Quick success requires overall unseen-world transfer at least 0.95, every family mean at least 0.90, at least 0.05 absolute overall and minimum-family advantage over the independent ablation, and no implementable Pareto dominance by a shared probabilistic control or fully charged specialist suite on quality, R16 work, acquisition/meta-fit and state. A one-seed success authorizes only a three-seed adversarial screen. It cannot promote.

Failure of capability or dominance discards the tested learner implementation without another decoder patch. A crash rejects only implementation. Leakage, information truncation, seed collision, family dispatch, missing mandatory controls or state-budget breach invalidates the cohort.

## Service outcome and exact next experiment

The new benchmark is `cross_family_shared_representation_v2`; its contract, evaluator, schema commitments, CLI plan mapping and focused tests are frozen before any candidate exists. The previous benchmark and all negative results remain preserved in archived manifests and the append-only ledger. No global cooldown is present: the only cadence restriction is one scored experiment per wake plus real quick/screen/deep budgets.

Next wake: preregister `EXP-20260830-0045` quick for HYP-0018 with K=8/32, D=1/4/6, Q=8 and one runner-random seed. Only after immutable registration implement the smallest shared local-relation learner and the exact mandatory controls, run metamorphic/source audits and tests, then score solely through `uv run nextai run --plan research/plans/EXP-20260830-0045.json`. The decisive observation is whether sharing learned representation improves every unseen family and remains non-dominated after the full R16 boundary.
