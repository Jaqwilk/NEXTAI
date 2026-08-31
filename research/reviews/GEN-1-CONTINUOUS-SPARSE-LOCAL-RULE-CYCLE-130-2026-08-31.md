# GEN-1 — continuous sparse local-rule feasibility, cycle 130

## Scope

This was one preregistered, no-scoring development diagnostic. It created no
hypothesis, experiment plan, scoring seed, candidate, benchmark, schema or
protected-file change and did not call `nextai run`. WT test files 8–9 and all
three-family test targets were not read. The frozen diagnostic is
`research/checks/continuous_sparse_local_rule_feasibility_preregistered_v1.json`.

## OBSERVATION

The WT diagnostic used 1,728 fit-only teacher-forced transitions and 288
transitions in each development file. The learned rule selected one anonymous
parent and one fixed basis per output from fit data, then refit only
`intercept + control + self + selected basis`. It was exactly equivariant under
a second consistent channel permutation (maximum prediction difference `0`).

The local rule obtained NRMSE `0.679209` on development file 6 and `0.644210`
on file 7. Its relative gains over dense VAR, sparse one-parent VAR, a static
correlation tree and a fixed random graph ranged from only `0.006733` to
`0.020905`. The preregistered minimum was `0.05` against every control on both
files. Exact output-parent-basis selection agreed for 5 of 10 channels between
fit files 0–2 and 3–5, exactly meeting but not exceeding the `0.50` stability
floor.

The three-family v7 contract can apply a generic graph estimator separately to
each world and charge it at K=`4/6/9`. It cannot define one shared graph across
families without using candidate-visible native-width masks: the input/output
widths are 18/14, 10/6 and 32/1, with no registered common node identity.

## INTERPRETATION

WT has a small nonlinear local predictive effect, but the effect is already an
explicit sparse basis regression and is far below the frozen meaningful floor.
Calling its selected parent an emergent graph would rename sparse feature
selection rather than isolate a new computational principle. The perfect
permutation fixture proves clean mechanics, not scientific distinctness.

V7 provides heterogeneous worlds but no ontology-free graph correspondence.
Separate per-world graphs test a source-identical estimator; shared coordinate
transfer would instead exploit the same family/native-width router rejected in
cycle 129. This fails HYP-0006's revival condition before implementation.

## CONFIDENCE AND LIMITATIONS

Confidence is high (`0.96`) that the preregistered gate failed: all eight
control-by-file gains are below 5%, and the cross-family contract defect is
structural. This does not prove that nonlinear sparse dynamics never help. The
diagnostic is one fixed low-order basis family on two development files, so it
cannot falsify arbitrary graph neural dynamics; it does show that richer search
is not justified by the existing signal and would be post-result model search.

This service diagnostic is not scientific evidence and changes no hypothesis
confidence.

## DECISION

`no_distinct_sparse_local_rule_contract`. Keep HYP-0006 dormant. Do not create
a candidate, hypothesis, plan, benchmark or schema and do not tune the basis,
ridge, edge count or thresholds. Preserve the small positive association as a
classical sparse nonlinear-regression control.

## Exact next discriminating cycle

Run one no-scoring `adaptive_halt_certificate_gap_feasibility` audit over
existing sequential contracts. Before reviving HYP-0004, require a
candidate-visible uncertainty statistic that predicts when more computation is
needed while a calibrated transition-residual or convergence certificate does
not. The gate must use at least three registered depths/scales, prevent target
leakage, compare fixed depth, residual/convergence certificates and learned
halting at matched transition semantics, and charge halt queries, state and
full workload. If the uncertainty statistic is reducible to the classical
certificate or no frozen contract exposes the distinction, record
`no_adaptive_halt_certificate_gap_contract` and create no hypothesis or plan.
