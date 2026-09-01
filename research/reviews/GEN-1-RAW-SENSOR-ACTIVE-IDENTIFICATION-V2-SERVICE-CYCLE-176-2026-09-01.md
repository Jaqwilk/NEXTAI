# Raw-sensor active-identification v2 service migration — cycle 176

## Scope

This was exactly one protected service-only migration. It created no hypothesis,
experiment plan, candidate under test, scoring seed, score, evidence or
confidence change. It is the second consecutive no-scoring cycle after valid
EXP-20260901-0030. Cycle 177 is therefore a mandatory scored scout and may not
be replaced by another audit or migration.

## Minimal versioned change

`heldout_raw_sensor_active_identification_v2` is a thin wrapper over the frozen
v1 evaluator. It preserves the nonlinear world generator, fixed meta-worlds,
runner-random held-out transform, anonymous support, charged single-use probe
boundary, K=`8/32/128`, budgets=`4/8/16`, 32 queries per cell, 48 sensors,
three support repetitions, noise 0.20, metrics, directions, full-cost formulas,
state limit, seed policy, Pareto axes and all seven semantic controls.

The migration changes only the prospective causal role identifiers:

- `shared_posterior_partition_decision_dag_v1` receives meta worlds;
- `source_identical_support_only_partition_dag_v1` receives held-out support;
- `source_identical_frozen_partition_dag_v1` uses a frozen policy.

All three are bound prospectively to
`posterior_partition_decision_dag_core_v1`. The v2 evaluator rejects a mixed
historical/new role contract before delegating to v1. The actual candidate core
does not exist yet: implementing it before preregistration would violate the
protocol. The next immutable plan must first freeze the split objective, DAG
growth, leaf prediction, tie rule, stopping rule and every numerical constant.

## Historical preservation

The v1 benchmark, raw probe contract, seven-control implementation and v1
semantic-test hashes are byte-identical between the archived v1 and active v2
manifests. EXP-20260901-0030 and every earlier plan, result, analysis and
candidate remain untouched and cohort-separated.

The previous manifest is archived at
`research/manifests/heldout_raw_sensor_active_identification_v1-protocol-v2-2ed646328dc0.json`
with file SHA-256
`3439514a861ae7534f4f5dfc1819d41ca5374c7c5c9553b22cf1dc5dc80b1db6`.

## Verification

The prospective CLI plan path emits the fixed 3x3 matrix and a schema-valid,
coherent v2 role contract. Tests prove preservation of the v1 task constants,
one shared prospective implementation ID, exactly three allowed policy sources,
correct meta-world routing and rejection of a mixed v1/v2 contract.

All 476 tests passed. All seven baseline conformance nodes passed. The new
manifest freezes 653 files with evaluator digest
`0296fd1872dcdd6a4f5835c2d6d905d0c1b02e2ca9f27c81e56dffc890900e52`.
The preflight certificate digest is
`fe9efbe411a1c42cc7af3fc5cbcfe4c8901f9d297a377de0b79bf41b3f81f163`.
Integrity and doctor pass.

## Decision and exact next experiment

Decision: activate v2 for exactly one mandatory quick scout. Infrastructure is
not evidence and creates no HYP-0043 confidence.

Cycle 177 must create HYP-0043 and preregister immutable
EXP-20260901-0031 before writing the candidate core or realizing a seed. The
single changed mechanism is compilation of posterior class partitions into a
reusable adaptive decision DAG learned across meta worlds. Shared, support-only
and frozen roles must use one source, constants, support order, charged probe
interface, traversal and output rule, differing only in the preregistered policy
source. The full unchanged 3x3 matrix must compare both causal ablations and all
seven controls with complete acquisition, fit, query, probe, state, bytes and
R1/R4/R16 accounting.

The plan must define a meaningful aggregate and minimum-cell accuracy margin
against matched-budget Gaussian and kernel controls; observe-all remains a
capability ceiling rather than an impossible matched-probe success threshold.
One seed cannot promote. A positive result may only authorize unchanged
replication. A null or negative ends this exact decision-DAG construction
without split, depth, leaf or stopping-rule tuning.
