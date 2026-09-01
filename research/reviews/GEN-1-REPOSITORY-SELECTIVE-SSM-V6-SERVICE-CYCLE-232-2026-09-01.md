# Repository selective state-space v6 service migration — cycle 232

## Scope

This was the second and final consecutive no-scoring G1 cycle after the valid
negative `EXP-20260901-0060`. It created no hypothesis, experiment plan,
candidate, scoring seed or scientific result. It activated one role-only
successor over the already frozen real repository corpus. All completed plans,
results, analyses and manifests remain append-only.

## Selection and deduplication

The selected causal question is narrower than “test another recurrent model”:
does observation-learned, input-dependent retention add useful long-context
state beyond the same diagonal recurrence with fixed selection? The third role
disables recurrence while preserving the remaining source and constants.

This does not reopen the exact width-16 orthogonal reservoir rejected by
`EXP-20260901-0009`; that model had a frozen, input-independent transition and
lost every K/D cell to its recurrence-disabled ablation. It also does not patch
the heterogeneous shared recurrent decoder rejected by
`EXP-20260830-0048`, whose four native interfaces introduced an output-binding
confound. V6 exposes one anonymous-byte interface and makes input selectivity
the only prospective main-versus-fixed causal difference.

Mamba and S4 already establish selective/structured state-space sequence
operators (`SRC-0093`, `SRC-0114`). V6 therefore claims no architectural
novelty and no removal of autoregressive output dependence. It is a cheap test
of whether the selective retention principle provides useful quality per full
cost in this local boundary. A positive would remain screening evidence only.

## Frozen boundary

`heldout_repository_sequence_compression_v6` re-exports the v5 evaluator. The
43 file hashes and roles, anonymous bytes, predict-before-reveal ordering,
K=`8/20/32` KiB, D=`4/16/64`, eight queries per cell, quality/cost/state axes,
R1/R4/R16 workloads and six classical controls are unchanged. Only three
prospective role names, their one shared implementation identity and the
source-identical intervention contract were added.

The future main, fixed-selection and recurrence-disabled wrappers must resolve
to `selective_diagonal_state_space_byte_core_v1`. They must share embedding,
state width, diagonal dynamics, readout, initialization, chronological fit,
context, input, update, output, numerical constants and accounting. The next
immutable plan—not this service cycle—must freeze all numerical choices before
candidate implementation or seed realization.

## Why the existing cohort is sufficient

The real corpus already supplies three knowledge and context scales, cold and
worst-file loss, bounded online reveal updates, state and byte traffic, and
fully charged repeated workloads. A useful selective-state signal must improve
long-context D64 quality over both source-identical ablations and the strongest
complete implementable control while retaining fixed-width state and query
work independent of K. PPM-D, CTW, LZ and dense autoregression prevent an
ordinary context model from being mistaken for a new scaling principle.

No new benchmark or metric is needed. Failure against the fixed-selection role
would reject input selectivity; failure against the recurrence-disabled role
would reject useful retained state; domination by a classical compressor would
reject the full-cost claim even if either paired contrast is positive.

## Validation and activation

The v6 schema rejects historical role substitution and requires the one-core
identity. Regression fixtures confirm that v5 roles retain their original
semantics under a non-active cohort. All `617` tests passed. The six semantic
baseline gates, including reference PPM-D and recursive CTW checks, passed on
real files. Integrity passed for `791` protected files with evaluator digest
`fc399c0927fc12172d0bd13a1b48007a28ee3ea5046bc6575c69b41ea7f7ea49`;
preflight certificate
`57926888c192efa11109654af34d9e637882d77dc3520c34499e05c505f6d4e4`
and doctor both passed.

## Exact next discriminating experiment

Cycle 233 must create `HYP-0058` and preregister
`EXP-20260901-0061` before implementation. The plan must freeze one stable
diagonal recurrence, state/embedding width, input-selection parameterization,
fit schedule, optimizer, initialization, clipping and exact operation/byte
accounting. It then implements one core plus the three wrappers, passes
history-dependence, fixed-selection, recurrence-disabled memorylessness,
predict-before-reveal, byte-relabeling and full-cost fixtures, and runs exactly
one runner-random quick through the audited harness.

Success requires a preregistered meaningful bpb improvement in every K/D cell
over both causal ablations and the strongest complete implementable control,
with an explicit D64 benefit, bounded state, K-independent fixed-D query work
and implementable Pareto non-dominance. A valid negative closes the exact rule
without width, gate, optimizer or schedule tuning. A positive quick can only
authorize unchanged three-seed replication.
