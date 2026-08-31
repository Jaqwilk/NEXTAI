# Metrics and accounting

## System boundary

For a candidate query, count every required component:

```text
input encoding
+ routing / retrieval / index reads
+ active reasoning or relaxation
+ memory movement
+ decoding / output interface
+ mandatory cache or state maintenance
= end-to-end inference cost
```

Report one-time training, index construction and continual update costs separately. If a deployment requires frequent updates, also report an amortized total-cost scenario.

Codex research effort is tracked as R&D overhead and must never be inserted into a candidate's inference path.

## Capability vector

- task accuracy;
- compositional held-out accuracy;
- OOD size/depth accuracy;
- continual-learning retention;
- new-fact acquisition accuracy;
- transfer across task families;
- calibration where probabilistic answers exist;
- planning or algorithmic success as appropriate.

## Cost vector

- exact primitive operations when instrumentable;
- estimated FLOPs with the formula and assumptions;
- wall-clock p50/p95 latency;
- maximum resident state and peak process RSS;
- serialized model/index size;
- active state/parameter count;
- bytes read or moved when measurable;
- raw input/encoding operations and comparisons;
- fit operations and peak fit memory;
- update operations and latency;
- training/search nodes, steps and total time.
- repeated-use totals such as R1/R4/R16 workload.

Do not use estimated FLOPs and measured FLOPs interchangeably. Do not compare latency across different hardware, load or numerical kernels as an architecture law.

## Scaling slopes

For cost `C`, knowledge size `K` and reasoning depth `D`, the harness estimates log-log slopes:

```text
s_K = d log(C) / d log(K) at a fixed preregistered D grid
s_D = d log(C) / d log(D) at a fixed preregistered K grid
```

Interpretation anchors, not universal thresholds:

- `s_K ≈ 0`: bounded/simple queries do not touch more state as irrelevant K grows;
- `s_K ≈ 1`: linear scan-like behavior;
- `s_K ≈ 2`: dense pairwise/matrix-like behavior;
- `s_D ≈ 1`: work proportional to reasoning depth;
- `s_D < 1`: possible compiled/jump behavior, which must pay memory/update cost somewhere;
- `s_D > 1`: search, branching or repeated global work.

The aggregate averages across the other axis and is a screening estimator. Fewer than three distinct axis values produces only `*_slope_screening`; the inferential slope remains null. With at least three points the result records point count, regression standard error and R². A promoted result still needs a broader range, uncertainty and a specification that controls interactions.

## Experience compilation

Measure cold and warm queries separately:

```text
warm_op_ratio = mean_warm_query_ops / mean_query_ops
```

A low ratio is useful only if:

- warm accuracy is unchanged;
- cache size is reported;
- the query distribution has realistic reuse;
- update invalidation cost and correctness are reported;
- preprocessing/warm-up cost is not omitted.

## Continual learning

At minimum:

- correctness on newly inserted knowledge;
- retention on unaffected old queries;
- changed-edge consistency;
- update operations/latency;
- affected state bytes;
- any replay or retraining cost.

An append-only fact benchmark is not sufficient to establish general continual learning; later versions must include conflicting updates and global consistency constraints.

## Pareto analysis

Rows are compared only within the same benchmark version and budget. A row dominates another if it is no worse on every declared, jointly observed axis and strictly better on at least one. Missing values never disappear opportunistically from a pairwise comparison. Before entering the research frontier, an implementable row must pass the configured minimum accuracy and integrity gates.

Oracle candidates are not implementations: they form a separate lower-bound list and cannot dominate the implementable research frontier or support promotion. Random controls remain capability-gated.

No automatic scalar combines capability and cost. A later application may introduce explicit utility weights, but those weights become part of the preregistered decision context.
