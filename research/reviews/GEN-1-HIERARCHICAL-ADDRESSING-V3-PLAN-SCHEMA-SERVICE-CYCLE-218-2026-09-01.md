# Hierarchical addressing v3 plan-schema service — cycle 218

## OBSERVATION

All start gates passed. The first `plan new` attempt for EXP-0055 failed in
JSON Schema validation before a plan file, registry entry, runner seed,
candidate or score existed. The active v3 generator emitted the frozen
hierarchical fields, while `experiment_plan.schema.json` still required the
flat v2 key/probe/bucket object.

The schema now accepts two disjoint addressing objects. The v2 branch retains
its exact fields, roles and three controls. The v3 branch requires recursive
tree construction, split/tie rules, beam four, 64 visited nodes, squared
distance verification, zero fallback, path-only insertion, four hierarchical
roles and four controls. A mixed v2/v3 object fails.

No hypothesis, immutable experiment plan, registry entry, scoring seed, main
candidate, result, confidence or scientific evidence changed.

## INTERPRETATION

This was an executable-contract defect, not evidence about hierarchical
routing. Correcting the protected schema in a service-only wake preserves the
rule that implementation and seed realization may follow only a valid
immutable preregistration.

## DECISION

Keep `latent_entity_binding_retrieval_v3` active with the corrected pre-seed
schema. Reserve EXP-0055 for the next wake; do not reinterpret EXP-0054 or v2.

## VALIDATION

- Historical EXP-0054 v2 plan validates.
- A prospective pure v3 object validates.
- A mixed flat-role/hierarchical-protocol object is rejected.
- Focused v2/v3/protocol tests: 31 PASS.
- Full pytest after final manifest and certificate: 593 PASS.
- Integrity: 762 protected files PASS.
- Evaluator: `a30135accad58a76883fd0f5415902558d1e30501e130ac09ba95c89ec394f88`.
- Preflight: `57ce90b7e5041bf0c89486b9b0132034725584017760b156b88f728622268a31`.
- Doctor: PASS; pending plans: zero.

## NEXT DISCRIMINATING EXPERIMENT

Cycle 219 must preregister EXP-20260901-0055 with the eight frozen v3 roles and
the exact pair loss, data order, node-local median tree, four-entry frontier,
64-node cap, zero fallback, path-only insert and prospective matched-quality
break-even already stated in the rejected command. Only after registration may
the four wrappers and one shared core be implemented and one quick scored.
