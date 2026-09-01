# Sparse set-memory v5 protected service activation — cycle 222

## Scope

This is exactly one protected service-only migration authorized by the user's
standing approval and the cycle-221 portfolio correction. It creates no
hypothesis, immutable experiment plan, candidate implementation, scoring seed,
runner invocation or scientific result. Completed v1-v4 plans, results,
analyses, evaluators and role implementations remain unchanged.

## Protected change

`cross_family_sparse_set_memory_v5` is a thin import-only wrapper over
`cross_family_shared_representation_v2`. The v5 `_training`, `_run_cell` and
`run_suite` objects are the same Python objects as v2; v3 and v4 still resolve
to those objects as well. Consequently v5 reuses the same four frozen world
generators, lossless anonymous public serialization, fixed training seeds,
runner-random disjoint test worlds, K=`8/32`, D=`1/4/6`, Q=`8`, targets,
metrics, directions, update events, costs, state boundary and controls.

The only new scientific contract is the disjoint future causal-role tuple:

1. `shared_sparse_set_memory_v1`;
2. `independent_sparse_set_memory_v1`;
3. `source_identical_dense_set_attention_v1`;
4. `source_identical_frozen_sparse_router_v1`.

All four map to future implementation `sparse_set_memory_core_v1`. The schema
freezes width 32, 32 memory slots, top-k 4, one attention head, 24 Adam epochs,
batch size 32, learning rate 0.001 and squared-Euclidean routing. The roles may
differ only in pooled versus independent fit, sparse versus dense slot access,
or learned versus frozen routing keys. A v5 plan containing a v3/v4 role,
fragment field, incomplete role list or changed constant is rejected.

The future candidate source is intentionally absent. The protected lifecycle
test accepts either all five files absent before preregistration or all four
wrappers plus one common core present afterward; a partial bundle fails.

## Regression and leakage evidence

The protected test records and checks the pre-migration SHA-256 of the v1-v4
evaluator wrappers and the v3/v4 shared/independent role wrappers. All eight
match exactly. It also constructs all four v5 public test worlds and confirms
that none has a family field, while privileged native worlds retain evaluator-
only family labels. Two dataclasses with different field names and identical
values serialize identically, proving field names are not present in the
candidate view.

The four registered specialist controls passed their semantic pre-seed tests.
Focused v5 tests passed `6` with one intentional preimplementation skip. The
full suite passed `599` with the same one intentional skip.

## Frozen integrity

- active benchmark: `cross_family_sparse_set_memory_v5`;
- protected files: `769`;
- evaluator digest:
  `e4687fa8412a0dca72c0bc776032d8d077e66f3d08cac5405435e64e560a5b50`;
- unchanged candidate-bundle digest:
  `cf3ee0106678325c826c2567ae9cf36424335a9f875b1a12211a04174373a2e8`;
- manifest file SHA-256:
  `ce66febde66a832a793a45d870022540cfa3edf3a3cf2259b7705734a8404c11`;
- preflight certificate:
  `4b48c8f4e9e0ef0a49c47624987c2fefabab84c354524ff01fbfa26574ff97d0`;
- prior manifest archive:
  `research/manifests/latent_entity_binding_retrieval_v3-protocol-v2-b4394fa11049.json`,
  file SHA-256
  `b49b12d67df37a69cd7854be2be3940e6658a5ecffc11046ddd55db440e2e1e7`.

Integrity verify and doctor pass. The active manifest has no prospective v5
candidate files because implementation before preregistration is forbidden.

## Decision and exact next experiment

**Decision: activate v5 and require scoring next wake.** This is consecutive
no-scoring cycle 2 after scored cycle 220; another design-only wake is not
permitted unless a new integrity failure appears.

Cycle 223 must create one new hypothesis, preregister expected
EXP-20260901-0057 with exactly the eight frozen roles and constants above,
then implement the smallest common core and four wrappers. It must run the
transitive candidate audit, the candidate semantic/permutation fixture, all
four baseline gates, full pytest, renewed candidate-bundle manifest and
preflight, then score exactly one quick through the audited runner.

The preregistered success conjunction is overall accuracy at least 0.95,
minimum-family accuracy at least 0.90, shared-minus-independent gain at least
0.05 on both, learned sparse better than frozen sparse routing, quality within
0.02 of dense source-identical attention, top-k access and bytes below dense,
full R16 cost no worse than dense, complete stability and implementable Pareto
non-dominance. A valid negative closes the exact rule without tuning. One
positive seed authorizes only unchanged three-seed replication and cannot
promote.
