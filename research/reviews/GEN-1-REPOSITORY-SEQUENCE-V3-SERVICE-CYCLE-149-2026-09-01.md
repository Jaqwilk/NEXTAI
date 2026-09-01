# GEN-1 — repository sequence v3 causal-role service, cycle 149

## Scope

This was exactly one protected service-only migration from repository
compression v2 to v3. It created no hypothesis, plan, candidate, scoring seed,
result or evidence and did not invoke the runner. It is no-scoring cycle `1/3`
after EXP-20260901-0007; the next wake must score the reservoir scout unless a
real pre-seed gate fails.

## OBSERVATION

The v2 evaluator could numerically execute arbitrary byte candidates, but its
machine-readable plan contract still named the three completed Forward-Forward
roles and their reverse-credit invalidation rule. A reservoir plan under that
contract would not machine-identify its actual causal ablations.

V3 re-exports the v2 evaluator and preserves all 43 file hashes and roles,
367,255 acquisition bytes, K=`8/20/32`, D=`4/16/64`, eight segments per cell,
predict-then-reveal execution, metrics, cost formulas, state limit, seed policy,
Pareto axes and the six semantic controls. It changes only prospective plan
semantics to three `causal_roles`: an orthogonal recurrent reservoir, the same
model with recurrence disabled, and the same recurrent model with readout
learning disabled. Historical v1/v2 artifacts remain immutable.

The regression fixture validates both old v2 `credit_assignment_roles` and new
v3 `causal_roles`, and proves the static corpus contract is identical. All 393
tests and six semantic baseline tests passed. Integrity covered 563 files;
preflight and doctor passed. No reservoir implementation exists yet.

## INTERPRETATION

This migration removes a semantic ambiguity rather than creating a new task.
It lets the next immutable plan isolate whether temporal recurrence adds useful
predictive state beyond the identical random feature/readout system, while a
frozen readout checks that any gain is learned rather than supplied by random
dynamics. The unchanged PPM-D, CTW and LZ controls retain the strong classical
null.

## CONFIDENCE

Confidence is `0.99` that v3 preserves v2 numerical evaluation because its
benchmark module directly re-exports v2 and the static contracts compare equal.
Confidence is only `0.12` that the prospective small reservoir will beat its
source-identical ablations at meaningful bpb and avoid classical dominance.

## DECISION

`activate_v3_for_one_orthogonal_reservoir_scout`. No confidence or hypothesis
status changes in this service cycle. Do not add another audit-only wake.

## EXACT NEXT DISCRIMINATING EXPERIMENT

Create one low-confidence hypothesis and immutable quick plan before candidate
implementation. Freeze one source-identical width-16 tanh system: QR-orthogonal
recurrent matrix, recurrent scale `0.9` for main/frozen-readout and `0.0` for
the no-recurrence ablation, normal byte embedding scale `0.25`, zero-initialized
bias-plus-state 256-way readout, one chronological training epoch and online
multinomial SGD learning rate `0.05`. The frozen-readout role performs no
readout update. All roles share initialization, byte order, state transition,
query rule and test-slot lifecycle except those two preregistered interventions.

Use the existing development-only `0.1671047931063159` bpb threshold without a
grid search. Run one runner-random seed over every K/D cell against all six
controls. Continue only if the recurrent role improves mean, cold and
worst-file bpb over both source-identical ablations by at least the threshold in
every cell, remains finite, keeps query work independent of K, and is not
Pareto-dominated after full cost. A negative ends this exact rule without
changing width, scale, embedding or learning rate; a positive authorizes only
unchanged multi-seed replication.
