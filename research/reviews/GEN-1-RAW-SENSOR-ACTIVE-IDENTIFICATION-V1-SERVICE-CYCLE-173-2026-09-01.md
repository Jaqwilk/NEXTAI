# Raw-sensor active-identification v1 service migration — cycle 173

## Scope

This was exactly one protected service-only migration. It created no hypothesis,
experiment plan, scoring seed, candidate under test, score, evidence change or
confidence change. It is the second consecutive no-scoring cycle; therefore the
next wake is a mandatory scored scout rather than another audit or migration.

## What was frozen

The new cohort exposes only anonymous continuous sensor values through a charged,
single-use probe session. Three fixed meta-training worlds are distinct from each
runner-random scoring world. Each unseen world independently permutes labels and
sensors and flips sensor signs. The evaluator uses three hypothesis-set sizes
(8, 32 and 128), three probe budgets (4, 8 and 16), 48 sensors, three support
observations per class and fixed noise 0.20.

The cohort is explicitly synthetic screening evidence. It cannot support a
promotion, a real-world robustness claim, a general-intelligence claim or an LLM
successor claim. A positive one-seed result can only authorize unchanged
replication later.

## Identifiability and controls

The development-only seed was read solely for pre-score feasibility. It produced:

- no-probe class prior: accuracy 0.0417;
- full observation nearest prototype: 1.0000;
- random probes: 0.8220;
- fixed support-Fisher order: 0.8837;
- adaptive Gaussian information gain: 0.9227;
- adaptive support-kernel information gain: 0.9288;
- privileged hidden-target control: 1.0000 with zero probes.

Thus the task is identifiable, the low-budget cells do not saturate, and strong
fixed and adaptive implementable controls leave a narrow but nonzero region for a
learned transfer mechanism to discriminate. The target labels, latent code,
sensor-generating weights, unprobed values and test transform remain evaluator
private.

Seven semantic baseline records bind exact implementation and conformance-test
hashes. Tests verify the probe boundary, deterministic held-out transforms,
budget compliance, adaptive second-probe conditioning, privileged-input
separation and the fact that only the source-identical shared and frozen roles
may receive meta worlds. Classical controls are not charged for training data
they cannot use.

## Cost and integrity

The final schema and aggregation include mean probe count. Pareto axes come from
the benchmark contract and include quality, acquisition, fit/meta-fit, query,
state, peak memory, bytes touched and R1/R4/R16 workload. The previous repository
compression manifest was archived append-only. The active manifest freezes 647
files with evaluator digest
`6afec026a44ce21ccec32213578a4b171507709e083b7a6c1ed756266204e00b`.
The preflight certificate digest is
`969eec5dc1429c1d4fcbc1935cae351aa40497756baa21b69312a174c7869fce`.

All 472 tests passed. All seven semantic baseline gates passed. Integrity verify
and doctor passed after the final freeze.

## Decision and exact next experiment

Decision: activate `heldout_raw_sensor_active_identification_v1` for exactly one
mandatory quick scout in cycle 174. The next wake must create HYP-0042 and
preregister immutable EXP-20260901-0030 before implementing the candidate or
realizing a seed.

The single tested causal factor will be a meta-learned residual-distance
calibration used by an adaptive probe policy. The shared, support-only and frozen
roles must use one source and identical constants, support order, query schedule
and output rule; they differ only in the preregistered calibration-learning
source or frozen calibration. The plan must freeze the distance basis, regularizer,
stopping rule, meaningful effect threshold, success/null/negative rules and
runner-random seed policy before implementation. It must compare all three roles
with the seven controls above over the full 3x3 matrix and charge the complete
end-to-end boundary.

One seed cannot promote. A positive scout may only authorize an unchanged
three-seed replication. Null or negative evidence ends this exact mechanism
without tuning its basis, ridge, thresholds or probe rule.
