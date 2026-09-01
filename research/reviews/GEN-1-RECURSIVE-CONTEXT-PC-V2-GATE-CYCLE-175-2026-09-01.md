# Recursive-context probabilistic-circuit v2 gate — cycle 175

## Scope

This was exactly one service-only identifiability gate after the valid negative
EXP-20260901-0030. It created no hypothesis, experiment plan, scoring seed,
candidate under test, score or confidence change. It did not modify the active
evaluator, manifest, runner, schemas, baseline registry or configuration. The
active cohort remains `heldout_raw_sensor_active_identification_v1`.

This is the first consecutive no-scoring cycle after cycle 174. It is permitted
by the breadth cadence, but it does not authorize a chain of reviews. At most one
small role-only migration may follow; cycle 177 must score a cheap scout.

## What EXP-0040 actually established

EXP-20260830-0040 showed that complete binary samples were sufficient to recover
one hidden selector followed by context-specific pair matchings. It did not show
a distinct learned probabilistic-circuit mechanism: `learned_decomposable_spn`
and `contextual_chow_liu` executed the same selector-and-matching search and were
numerically identical, while the learned label paid additional work.

The current implementations cannot be carried forward under stronger names:

- `contextual_chow_liu` searches one binary selector and then disjoint pair
  matchings. It is not a generic mixture of Chow–Liu trees.
- `pairwise_factor_elimination` learns degree-one pair factors and enumerates
  their components. It is not generic variable elimination.
- there is no registered tensor-train or ordered-decision-diagram control for
  this cohort;
- there is no versioned privileged recursive-circuit control with reference
  semantics.

Names are not algorithmic evidence. Reusing these controls would recreate the
control-semantics defect that invalidated EXP-0047.

## Identifiability result

The proposed `heldout_recursive_context_probabilistic_circuit_v2` fails before
protected migration. Observational samples from a finite positive distribution
do not identify a unique recursive circuit. The same distribution can be
represented as a flat sum of point products, an ordered decision diagram, or a
factor graph evaluated by variable elimination. Circuit node count also changes
with variable ordering, common-subgraph sharing and compiler conventions.

Consequently, a synthetic generator authored directly as a two-level recursive
sum-product circuit would privilege the target representation. A smaller circuit
on that generator would not distinguish learned structural discovery from
alignment with the generator and compiler. Adding several new control compilers
would make this a substantial benchmark-engineering project rather than the
smallest experiment capable of resolving a mechanism.

This does not falsify probabilistic circuits as a family. It rejects this exact
benchmark proposal because the claimed mechanism and its null are not separable
under the proposed observational boundary.

## Decision

Decision: reject `heldout_recursive_context_probabilistic_circuit_v2` before
migration. Do not create HYP-0043 or EXP-20260901-0031 for this direction, do not
implement a recursive-PC candidate, and do not substitute simplified controls.
The rejection is methodological infrastructure history, not scientific evidence
against the architectural family.

## Exact next discriminating cycle

Cycle 176 may perform exactly one minimal protected migration of the existing
raw-sensor active-identification contract to v2. It must preserve the anonymous
world generator, train/test separation, three scales, probe budgets, metrics,
cost boundary and all seven frozen controls. Its only scientific-purpose change
is to register three source-identical roles for a fundamentally different
mechanism: a learned posterior-partition decision DAG, a support-only DAG and a
frozen DAG. Fixtures must prove identical inference code and constants, charged
probe-only access, and that roles differ only in the allowed source of the
compiled partition policy.

The migration must remain small and score nothing. Cycle 177 is then mandatory:
preregister and run exactly one runner-random quick scout comparing the compiled
decision DAG with the seven existing controls and its two ablations. The scout
cannot promote. A null or negative result ends that exact DAG construction
without tuning; a positive result may only authorize unchanged replication.
