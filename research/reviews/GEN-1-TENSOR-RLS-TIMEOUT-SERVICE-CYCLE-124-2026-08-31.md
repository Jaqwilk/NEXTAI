# GEN-1 — tensor RLS timeout repair, service cycle 124

## Scope

This was exactly one service-only cycle. It created no hypothesis, experiment
plan or scoring seed, ran no scored benchmark and changed no scientific result,
evidence, confidence, metric, split, budget or completed artifact. Immutable
EXP-20260831-0008, including its mandatory-control timeout, remains unchanged.

## Diagnosis and minimal repair

The frozen tensor RLS baseline performed the same 33-by-33 covariance update
separately for every output channel, even when channels had byte-identical row
visibility masks. Because every public test support adaptation refits the model,
this redundant matrix trajectory accumulated until the EXP-0008 worker reached
the unchanged 180-second quick limit.

The repair groups only output channels with exactly identical complete visibility
masks. Each group runs one covariance trajectory with initial covariance `1000 I`
and the original ordered predict, gain, error, weight and covariance recurrence.
Individual weight columns retain the original scalar dot and update order. The
ridge, row order, masks, predictions and charged operation counts are unchanged.

A randomized mixed-mask regression requires `np.array_equal` between the grouped
implementation and an embedded copy of the original scalar recurrence. The old
scalar reference test remains unchanged. Synthetic K9 one-adaptation time fell
from `0.1205474` to `0.0323984` seconds, a measured 3.72-fold reduction; wall
time is diagnostic only and is not reported as algorithmic cost.

## Supervisor smoke and preserved failures

The existing audited supervisor ran a deterministic, synthetic-only workload
covering K=4/6/9, three representative input/output widths and 128 public support
adaptations per family. No holdout, research plan or scoring seed was used.

The first workload completed its computation in `49.7803` seconds but the
temporary diagnostic row omitted `mean_warm_query_ops`, so aggregation crashed.
This diagnostic failure is preserved at
`research/checks/tensor_rls_timeout_supervisor_outcome_v1.json` (SHA-256
`62aab7b7ddeb19973c38a6b966823de0a5ad00c088c2b3a2bd71f2072049bf2a`).
After adding only required diagnostic fields, the same workload completed 9/9
profiles in `52.5378` seconds with peak RSS `55,345,152` bytes and no termination
reason. Its outcome is
`research/checks/tensor_rls_timeout_supervisor_outcome_v2.json` (SHA-256
`70fd92252515a6f3ee1ebebe0750df96a27bec5cfac7db974ab49b34fd7e59ac`).
The temporary benchmark and text worker artifacts were removed; diagnostic logs
and both durable outcomes were retained.

## Verification and decision

- grouped-versus-original mixed-mask weights: bit-exact PASS;
- original scalar RLS reference: PASS;
- semantic baseline gate: PASS, 9 controls and 11 conformance nodes;
- full pytest: PASS;
- integrity: PASS, 530 protected files;
- evaluator digest remains
  `3e219128c0a00030c60529e1f2549f834b1dc395f78425d2d7e2652c9d61ac5c`;
- preflight content digest:
  `bdc2491e76a22b15a11090a5ae1532e3daae3efca745258b582df479b5fd474a`;
- active manifest file SHA-256:
  `b8b1681d493896219372b5635083a3491cb05df1418a0dedf049d84bac3cee39`;
- preflight file SHA-256:
  `320c03ccf8773060eb602bb73958d1afbd794786bf8c8371997d7c80c245480c`.

Decision: keep the bit-exact runtime repair. Do not rerun EXP-0008 and do not
alter its negative decision; HYP-0028 remains dormant.

## Exact next cycle

Cycle 125 should be a mechanism-selection review with no scoring. Synthesize the
last ten completed experiments, explicitly separate concrete repairable failures
from repeated fundamental transfer failures, and select one genuinely different
principle whose cheapest test uses an existing frozen cohort. The selected test
must target at least one qualitative signature—sublinear full query cost at
matched quality, generalization beyond trained depth, bounded local update, or
decreasing inference cost with experience—at three scales and against the
strongest classical controls. Do not revive bounded residual, predictive-index,
low-rank, spectral, convex-prior or benchmark-specific families, and do not score
until a later immutable plan freezes its causal contrast and meaningful effect.
