# GEN-1 — three-family predictive-index v3 service cycle 105

## Scope

This was exactly one protected service-only cycle. It created no hypothesis, experiment plan,
scoring seed, scored candidate, result or confidence update and did not invoke `nextai run`.
The existing three real families, splits, anonymous tensors, normalization, metrics, directions,
budgets, causal gains and Pareto semantics are unchanged. Historical v1/v2 artifacts remain
append-only. The active prospective cohort is `heldout_three_family_continuous_transfer_v3`.

## Service defect resolved

The cycle-104 design review found that v2 could not distinguish a learned predictive-equivalence
key from ordinary bounded retrieval. It lacked two matched controls. V3 adds an exact raw-window
nearest-prototype control and a random-projection hash control. Both use exactly 32 buckets,
eight stored samples per bucket, the same masked affine ridge operator (`lambda=0.001`), the same
touched-bucket-only support update and the same 64 MiB state limit. Their query path reads a
fixed-size index, so dormant training-window count cannot increase query work or bytes touched.

## Semantic evidence

The frozen fixture has observations `0.0`, `0.1`, `2.0`, future-operator identities
`1`, `-1`, `1`, and query `0.06`. Exact raw proximity selects observation 1, while the two
predictively equivalent observations are 0 and 2. It therefore separates the proposed learned
binding from raw nearest-neighbour retrieval before any learned candidate exists.

Reference tests verify the exact raw-distance key, exact five-bit random hash, common bucket cap
and local operator, slot relabeling, training-world order invariance, consistent channel
permutation equivariance, local support insertion without global-model mutation, fixed query work
as K changes, source audit, absence of private routing tokens and real-file finite execution on
DS08a, DronePropA and continuous-event worlds. All nine mandatory v3 baselines passed their
registered semantic tests. The full suite collected 330 tests and passed.

## Frozen integrity

- evaluator SHA-256: `d8c0e482498d087f072959d3de7ee680af25c0e2f346c99f79a0865aa1614aa9`
- candidate-bundle SHA-256: `9c0200578f484919ee15f066e4ab88dc7656b2fcfe4ed0b2ff09a8dffb16eec5`
- manifest-file SHA-256: `8eedb1a37883af769cddf2889c4d48ed67f71f80c71064130e6a498492367ed9`
- preflight certificate: `d160c774ef7dc2fc5cf3a0541d05d70fdfe4c641f6cdd229681c0bd6aa31f26c`
- semantic gate: `research/checks/three_family_predictive_index_controls_v1.json`
- semantic-gate SHA-256: `1705ee4c06a0610b3ffdad6d0140a6fea438f592c7017cbeb23b1d952b190afe`

## Decision

`keep` the v3 infrastructure. This is not evidence for predictive indexing and gives no novelty,
capability, transfer or scaling credit. Classical indexed access remains the null explanation.

## Exact next discriminating experiment

In the next wake only, use development-role training worlds to freeze the smallest meaningful
advantage over both new index controls and persistence, then create HYP-0027 and preregister
`EXP-20260831-0004` quick on unchanged v3 at K=`4/6/9`, one runner-random seed and all four
source-identical causal assignments. Only after immutable preregistration may the smallest learned
predictive-equivalence code be implemented. Kill before scoring if it cannot solve the frozen
future-equivalence fixture with capped lookup and local-only support updates. A valid one-seed
positive may authorize only unchanged three-seed replication; a negative ends this exact direction
without tuning code width, bucket cap, local operator or thresholds.

