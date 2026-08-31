# GEN-1 — non-axis identity-acquisition feasibility, cycle 133

## Scope

This was one preregistered no-scoring audit for dormant HYP-0001. It created no
hypothesis, experiment plan, scoring seed, candidate, benchmark, schema or
protected-file change and did not call `nextai run`. No data array was loaded;
WT test files 8–9, DronePropA test/privileged roles and every test target were
untouched.

The immutable diagnostic is
`research/checks/nonaxis_identity_acquisition_feasibility_preregistered_v1.json`
(SHA-256
`991f825655857c9c215092b73053b4fd9a577f92daeb361cc56a29c9db225a31`).

## OBSERVATION

DronePropA exposes `FlightExamples(slot, features, targets)`. The evaluator
constructs features and targets from identical anchors, validates row alignment
and retains an explicit stable flight slot. The two matrices are an ARX
feature-to-next-state training relation, not two unlabeled views of one entity.

WT exposes fit observations as `WTEpisode(history, control, target)`. History
and target occupy one immutable object and are adjacent intervals around an
evaluator-known intervention. Development queries and reveals additionally
share an evaluator-issued slot for the entire file. This is a prequential
forecasting relation, not latent identity acquisition.

Both contracts therefore failed the required natural-view, identity-absence and
task-distinction gates before numerical interpretation. Non-axis identity
variation cannot be defined without first inventing an entity ontology. Exact
clustering, record linkage, ANN and oracle identity controls are consequently
not well-defined. A cyclic shift would merely destroy supervised temporal
alignment; it would not remove a naturally occurring identity relation.

## INTERPRETATION

The missing factor from EXP-0035 is not an untried learner. It is the
observational contract itself. Current real-data cohorts hand over temporal
pairing and grouping while exposing no independent persistent-entity views.
Manufacturing labels from slots, containers, rows or adjacency would repeat the
positive-pair ontology that made analytic paired-stability hashing decisive in
EXP-0035.

## CONFIDENCE AND LIMITATIONS

Confidence is `0.995` that the frozen candidate interfaces fail the registered
contract: the result follows directly from immutable dataclasses, constructors
and validation. Confidence is `0.85` that the raw archives contain no other
scientifically useful identity relation. Raw arrays were intentionally not
searched for a post-hoc ontology, and a future independently motivated dataset
could expose naturally repeated views.

This audit is not scientific evidence and changes neither HYP-0001 confidence
nor its dormant status.

## DECISION

`no_nonaxis_identity_acquisition_contract`. Keep HYP-0001 dormant. Do not tune
`latent_entity_binding_retrieval_v1`, reinterpret temporal prediction as entity
binding, or create a new benchmark merely to rescue the family.

## Exact next discriminating cycle

Run one no-scoring primary-literature and portfolio review after the five
consecutive feasibility failures in cycles 129–133. Select at most one genuinely
different principle only if an existing frozen cohort can test a qualitative
signature at three scales against matched classical controls. Otherwise record
that no scored experiment is currently justified and specify the minimal
missing observational contract without creating it.
