# Masked Born-MPS v4 service review — cycle 159

## Scope

This was one protected service-only migration. It created no hypothesis, experiment plan,
candidate implementation or scoring seed, and performed no scoring. It counts as the first
consecutive no-scoring cycle under the breadth-mode limit of three; the next wake must run one
cheap scout rather than another review or migration unless integrity is actually broken.

## Portfolio correction

The cycle-158 proposal for surprise-gated local predictive plasticity was rejected before new
scientific state was created. HYP-0031 and EXP-20260901-0004 had already tested the same
event-sparse local-update principle: update work and state scaling were attractive, but the
candidate regressed worst-file NRMSE beyond the frozen tolerance. Reopening that direction would
be post-result tuning, not breadth. An operator dictionary was also rejected as a recurrence of
GNG/ART/PSR-style routing and state discovery. A sequential probabilistic MPS alone is not treated
as new because finite-dimensional sequence models overlap weighted-automaton/OOM/PSR semantics.

The retained discriminating property is narrower: exact conditional masked inference with a
learned fixed-rank Born uniform MPS, comparing a tree contraction with a source-identical
sequential contraction. Miller, Rabusseau and Terilla (SRC-0197) provide direct prior art for
parallel u-MPS evaluation and conditional generation; Thon and Jaeger (SRC-0198) delimit the
novelty claim; Tang, Khoo and Ying (SRC-0199) identify initialization/training failure as a strong
alternative that must be frozen before scoring.

## Protected change

`heldout_parallel_masked_infilling_v4` re-exports the complete v3 evaluator. It preserves the 48
hashed files and roles, random byte relabeling, masks, span lengths, K=`8/32`, rounds=`1/4/6`, eight
queries per cell, immutable snapshots, metrics, costs, state boundary, Pareto axes and all eight
semantic controls. Only the three prospective causal role identifiers and their machine-readable
source-identity contract changed:

- `parallel_born_mps_masked_byte`;
- `source_identical_sequential_born_mps_masked_byte`;
- `source_identical_frozen_born_mps_masked_byte`.

The roles must share representation, rank, initialization, train examples/order, update count,
normalization and output probabilities. Only contraction schedule and tensor learning may differ.
The evaluator helper now reads the historical one-pass role optionally; v1-v3 schemas still
require it, while v4 forbids silently applying that historical intervention. Regression fixtures
show the old cohorts retain their contract.

## Validation and decision

All 416 tests passed, including PPM/CTW semantic fixtures and v1-v4 masked regressions. Integrity
verified 588 protected files, the eight required baselines passed, preflight certificate digest is
`e286ceabc8cba0f0ecff7a2b78113070dc718b4c70d5eccea59970f8dd12946f`, and doctor passed.
Scientific evidence and confidence did not change.

Decision: activate v4 solely to permit one cheap, low-confidence scout next wake. That immutable
plan must freeze tensor rank, representation, initialization, normalization, fit/update rule and
all constants before implementation. It must score the three source-identical roles and all eight
controls through the audited runner with exactly one runner-random seed. A valid negative ends the
exact rule without tuning; a positive can authorize unchanged replication only, never promotion.
