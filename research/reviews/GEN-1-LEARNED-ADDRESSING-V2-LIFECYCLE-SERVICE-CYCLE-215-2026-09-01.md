# Learned addressing v2 prospective lifecycle service — cycle 215

## OBSERVATION

Start gates passed with no STOP, PAUSE, active lock, pending plan or integrity
error. `EXP-20260901-0052` preregistered the frozen v2 sizes and budgets but did
not state every required algorithmic rule, so it was append-only invalidated
before candidate code or seed realization. Its fully specified child
`EXP-20260901-0053` then exposed a protected lifecycle contradiction: the
frozen regression required all four prospective candidate files to remain
absent, although the protocol requires those files to be implemented only after
preregistration. It too was invalidated before code, seed or scoring.

The single service change replaces that unconditional absence assertion with
one future-safe invariant: either all four role wrappers are absent, or all four
exist and import the same `learned_addressing_v1` core. Partial bundles and a
wrong-core wrapper fail a hand-checkable temporary-directory fixture. No
candidate, world, target, metric, direction, cost, threshold or control changed.

## INTERPRETATION

This was an infrastructure lifecycle defect, not evidence for or against
HYP-0012. Preserving both invalid plans prevents an underspecified or
post-plan-digest-invalid experiment from entering the scientific record. The
corrected fixture now permits the intended preregister-then-implement sequence
while still enforcing source identity.

## CONFIDENCE

Confidence is 1.00 that neither invalid plan realized a scoring seed or result.
Confidence is above 0.999 that the new fixture rejects absent/present mixtures
and independently implemented wrappers. HYP-0012 confidence remains 0.86.

## DECISION

Maintenance complete. Keep `latent_entity_binding_retrieval_v2` active. Do not
score in cycle 215 and do not add another design-only wake unless integrity
fails.

## VALIDATION

- Focused lifecycle and semantic tests: PASS.
- Full pytest: 582 PASS.
- Semantic control gate: PASS for raw NN, local dense GRU and privileged key.
- Evaluator digest: `ed0c9083cf224bafb6bdd75d2a5ce496f7f084b264efc239517b2b9a43189795`.
- Candidate bundle digest: `4732e1031c3f414a59bb68737a4e7d75087a31267436f856642a10eec2f2b9b6`.
- Manifest digest: `332e2f1eb3838fbc5c1a15f3735a54fcfb6c83a6bcae4fbb313a5b214ec24ed2`.
- Preflight digest: `ffd275c1177c1a5a90652fd6904fdb7326cfd258732f72010cab5411bfaa0581`.
- Integrity: PASS over 753 protected files. Doctor: PASS.

## NEXT DISCRIMINATING EXPERIMENT

Cycle 216 must create `research/plans/EXP-20260901-0054.json` as a child of
EXP-0053, copying its fully specified encoder loss, fixed batch order, shuffled
pair intervention, median bit thresholds, four probes, bucket retention,
verifier threshold, bounded fallback, local update and prospective break-even
definition while committing the new evaluator digest. Only after registration
may the four wrappers and one shared core be implemented. Run exactly one quick
through the audited harness. A valid negative ends the exact rule without
tuning; a positive only authorizes unchanged three-seed replication.
