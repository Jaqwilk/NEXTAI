# GEN-1 — masked v3 matrix-wiring service cycle 152

## Scope

This was exactly one minimal protected service cycle before HYP-0034. It
created no hypothesis, plan, candidate, scoring seed or result and did not call
the runner. It is consecutive no-scoring cycle `2/3`; the next wake must
preregister and score the predictive-code scout unless a genuine integrity
failure blocks seed realization.

## Observed pre-seed defect

The active v3 data/evaluator contract was sound, but `nextai plan new` still
inherited the global quick matrix K=`8/32`, D=`[1]`, Q=`128`. The common plan
schema requires at least two reasoning depths, so the generated document could
not validate. More importantly, D=`1` makes the iterative candidate and its
forced-one-pass ablation execute exactly one round and therefore cannot test the
registered causal question. No plan was attempted or registered and no seed was
realized.

## Minimal repair

The existing `[masked_refinement]` configuration now records
K=`8/32`, refinement rounds=`1/4/6` and Q=`8`. The plan generator copies those
three fields only for `heldout_parallel_masked_infilling_v3`. The v3 schema
locks the exact matrix, and a plan-synthesis regression exercises the real CLI
path without writing a plan or realizing a seed. All other benchmark matrices,
the masked evaluator, corpus, masks, metrics, baseline implementations and
historical artifacts are unchanged.

## Decision and exact next experiment

Decision: `repair_matrix_wiring_then_score_next_wake`. In the next wake create
HYP-0034 and one immutable quick plan before candidate implementation. Use the
three already frozen source-identical roles and all eight controls over every
K/round/span cell. Run exactly one runner-random seed after audit, semantic
baseline, preflight, integrity and doctor PASS. A valid negative ends the exact
16-position, 32-unit, top-4, LR=0.025 code without tuning.
