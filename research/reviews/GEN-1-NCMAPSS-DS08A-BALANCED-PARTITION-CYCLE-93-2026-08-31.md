# GEN-1 — N-CMAPSS DS08a balanced partition, cycle 93

## Scope

This was one metadata-only design cycle. It created no hypothesis, experiment plan, seed, candidate, runner call, score, predictive result, evaluator migration or dependency. The active v6 cohort remains unchanged.

## Observation

Across the verified DS08a file, each flight class has exactly five whole engines. Therefore a disjoint 9/6 partition with exactly three training and two holdout engines per class exists, despite the official split failing that balance.

The frozen selection rule uses only evaluator-private unit, flight class and official source role. Among the 1,000 class-balanced partitions it minimizes the absolute difference in the proportion of official-development engines between roles; lexicographic training-unit order breaks ties. It never inspects trajectory length, `W`, `X_s`, `T`, `Y`, health state, router output or predictive output.

The resolved training units are 1, 2, 3, 4, 5, 10, 11, 12 and 13. Holdout units are 6, 7, 8, 9, 14 and 15. Every class contributes 3/2 units, there is no unit overlap, training mixes five official-development and four official-test units, and holdout mixes four official-development and two official-test units.

## Interpretation and uncertainty

This repairs the class-count defect without combining different N-CMAPSS subsets, reusing an engine across roles or selecting on model performance. It does not yet prove a valid evaluator: public prefixes may still reveal the custom role, private fields may leak, or pooled no-adaptation prediction may already solve the task.

Confidence is `1.00` that the partition is deterministic, class-balanced and whole-unit disjoint. Confidence that it will pass the still-unseen semantic gate is intentionally unassigned.

## Decision

`authorize_partition_for_semantic_gate_only`. Preserve the rejected official split and this new contract as separate history. Do not activate an evaluator, create EXP-0060, realize a seed or score anything.

## Exact next discriminating step

In one separate service-only wake, verify the source and partition hashes, then run a preregistered candidate-visible fixed-prefix train/holdout router, exact and near-exact private-field leakage checks, and finite persistence, pooled-no-adaptation and prefix-adaptation controls. Reject immediately on any failure. Only a full pass may authorize a later protected evaluator design.
