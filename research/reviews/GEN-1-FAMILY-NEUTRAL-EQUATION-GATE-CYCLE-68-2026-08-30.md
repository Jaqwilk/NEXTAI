# GEN-1 — family-neutral observable-equation gate, cycle 68

## Scope

This was one design/audit-only cycle after valid EXP-0057. It created no hypothesis, experiment plan, candidate, scoring seed, runner invocation, result, dependency, external model/API, or protected change. The active `heldout_mechanism_recombination_v3` cohort and all immutable history remain unchanged.

The audited proposal was one unchanged observable-equation learner across the four existing v4 families: context-specific probabilistic circuits, action-conditioned predictive equivalence, nonlinear local state transfer, and behavioral program composition. The acceptance gate required a lossless family-neutral equation pattern shared by every selected family and a negative shape/router classifier no better than chance plus 0.10.

## Negative routing control

The audit used only fixed training seeds `1103/2207/3301`, K=`8/32`, and D=`1/4/6`; no runner-random scoring state was realized. A family-blind profile contained lossless support length, counts of the seven structural markers, the multiset of query lengths, and the multiset of target lengths. Leave-one-training-seed-out nearest-profile classification was exact in every cell: `12/12` for each of six K×D cells and `72/72` overall, versus four-family chance `0.25`.

Target arity alone distinguishes most cases: probabilistic targets have length `1` at every depth; predictive targets have lengths `2/5/7`; local targets remain length `3`; program targets have lengths `1/4/6`. At D=1 probabilistic and program both have arity one, but the lossless support/query structure still separates them exactly. Any three-family subset therefore retains a deterministic observable router.

## Positive equation fixture

The existing lossless structural encoder and the already frozen anonymous relation parser were applied without family labels or native types. Across both K values, all three depths, three fixed seeds, and four examples per world:

- probabilistic: `0/36` target components were pointers to public atoms;
- predictive: `168/168` components were pointers and `36/36` examples were fully pointer-valued;
- local: `108/108` components were pointers and `36/36` examples were fully pointer-valued;
- program: `132/132` components were pointers and `36/36` examples were fully pointer-valued.

The exact lossless `(anonymous query-relation graph, target-component kinds)` pattern intersection was zero for every one of the four possible three-family subsets and for all four families together. The source audit agrees with that mechanical result: the four builders sample independent mechanisms and do not contain a repeated evaluator-hidden factor or factorial factor/rendering split.

Consequently no shared positive fixture exists in the current public data. Abstracting scalar probabilities, action-conditioned rollouts, grid-state triples, and executable programs into one common operator would require a hand-authored semantic ontology or evaluator-supplied state space. Keeping the encoding lossless preserves the router; erasing the distinguishing structure is lossy and changes the tasks.

## Interpretation

This rejects the proposed evaluator/question pairing, not universal representation learning. EXP-0057 showed that observable equation closure can transfer when a common state/operator algebra genuinely exists. These four families do not contain such a common algebra before evaluator intervention, so another v5 wrapper would confound representation learning with hidden routing exactly as cycles 54 and 61 warned.

## Decision

`reject-before-hypothesis` for `family_neutral_observable_equation_transfer`. Do not register HYP-0023, do not create EXP-0058, do not implement a translator/learner, and do not migrate the protected evaluator. The standing migration authorization does not override a failed scientific gate.

## Exact next discriminating step

Use the next wake for one no-scoring temporal-interface gate over three different existing families: `action_conditioned_predictive_equivalence_v1`, `continuous_event_predictive_state_v1`, and `nonstationary_online_update_battery_v1`. Test whether their native chronological observations admit one lossless anonymous `(history, action/intervention, next observation)` event contract without task tags, type dispatch, padding-based routing, or hand-aligned state meanings. Run a leave-one-seed-out shape/content router and require chance plus 0.10; identify a repeated predictive-state equation under independently relabeled observations; and require a fixture separating shared state induction from independent CSSR/spectral-PSR/Kalman/autoregressive fitting. Register HYP-0023 only if every gate passes. Otherwise reject this temporal set before migration and pivot away from synthetic shared-representation benchmarks.
