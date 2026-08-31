# GEN-1 — WT v1 reactivation, service cycle 144

## Scope

This was exactly one protected service-only cycle. It created no hypothesis,
experiment plan, scoring seed or scored result and changed no scientific
evidence or confidence. It reactivated the already frozen
`heldout_wt_changepoints_prequential_v1` cohort after valid EXP-20260901-0003
closed operator compilation.

## Preserved contract

The evaluator, public contract and both WT test files are byte-identical to the
historical WT manifests. The data manifest remains
`3d91f9b82644a9e9d0092a0baec0c012ed6b790f8331bdbb3b044cb0cbd5091e`;
all ten CSV hashes passed. Whole files 0–5 remain train-only, 6–7 development,
and 8–9 test. K=18/36/54, H=16/32/96, the query–artifact–reveal–update boundary,
normalization, metric formulas/directions, 16 MiB state limit, budgets and all
eight semantic controls are unchanged. Historical plans, results, analyses and
manifests were not edited.

The first full suite exposed a cross-cohort test defect before any plan, seed or
scoring: the operator-v4 plan-generator test silently loaded whichever benchmark
was globally active, so it tried to validate operator roles under the WT schema.
The minimal repair gives that test an explicit operator-v5 configuration. It
changes no runtime evaluator path. Seven corresponding conformance registry
hashes were updated to the new test-file digest; all semantic nodes still run.

## Verification

All 383 tests passed after the repair. The WT semantic suite has 20 focused
tests, doctor executes eight mandatory semantic baselines, integrity verifies
553 protected files and doctor passes. The active evaluator digest is
`adccdf4e88676cc164865a6673e12e20f8771b9953a98179ff0680e2153d8aa8`,
manifest SHA-256 is
`c81bdc1c0fb7e8afbff8d22b0a51f832af79542c4dcb3061546290dce3ea789c`,
and preflight certificate digest is
`734cf0850490295560eb3152931167666cb712a722b085909c4ded4de6b44002`.

## Decision and exact next experiment

Decision: activate WT v1 for one quick breadth scout in the next wake. This is
not a revival of HYP-0028: the new candidate may not use its affine recurrent
residual transition, ridge/RLS fit, correction bound or parameter tuning.

Preregister a new low-confidence hypothesis before implementation. The tested
mechanism is one source-identical event-sparse local-plasticity circuit: signed
change events in the public history activate a fixed anonymous population;
prediction is emitted from active units, and after reveal only synapses incident
to active units may update. No replayed trajectory, nearest template, global
gradient, least-squares solve, slow recurrent transition, family/channel names
or manual ontology is allowed. Channel permutation must commute with event
creation, prediction and update.

Run one runner-random quick through `wt_candidate_under_test` at all K/H cells
against all eight frozen controls. Freeze the event rule and learning constant
from train-only scale statistics before candidate implementation. Success
requires stable finite rollouts, NRMSE and worst-file/transition no worse than
the strongest complete control by the frozen meaningful effect
`0.1325268421060828`, strictly smaller update operations and bytes touched than
both LMS and RLS in every K, K-independent query work, and implementable Pareto
non-dominance. A negative ends the exact circuit without threshold, width or
learning-rate tuning; a positive one-seed scout only selects unchanged
replication.
