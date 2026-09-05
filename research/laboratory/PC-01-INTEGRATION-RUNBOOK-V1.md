# PC-01 execution integration: prospective operating notes

Cycle 286 is the single user-authorized extension of the original 2/2 service
budget. It implements and checks execution infrastructure only. It does not
authorize training, activate a cohort, create an EXP or demonstrate learning.
The frozen design remains research/plans/PC-01-CONTRACT-V1.json.

## Prepared execution boundary

`nextai plan new --pc01-phase dev --candidates <name> --question <question>`
registers a diagnostic plan only when the normal STOP, lifecycle, integrity,
active-cohort and laboratory authorization gates permit it. It does not require
a fictitious hypothesis, legacy K/D matrix or five-seed deep configuration.
Dev always uses 1103. The model factory may be implemented only AFTER that plan
is registered; source audit precedes execution and any final random seed.

The sole execution entry is `nextai run --plan research/plans/EXP-....json`.
The normal runner dispatches `pc01_diagnostic_plan` into a locked supervisor.
The worker validates its registered runtime before importing torch or loading
data. Candidate gets configuration and input token tensors, never target labels,
split buffers, corpus paths or final results. This is audited local Python,
not a blind holdout or OS security sandbox.

Candidate exports `Candidate(model_config=...)`, a torch.nn.Module with the
conventional nanoGPT names: transformer.wte/wpe/drop/h/ln_f, lm_head, and each
block's ln_1/ln_2, attn.c_attn/c_proj, mlp.c_fc/c_proj/gelu/dropout. Each attention
block exposes n_head=6 and attn_dropout/resid_dropout. Exact parameter names,
shapes, tied embeddings, 13 LayerNorms (epsilon 1e-5, no bias), 19 dropout modules
(0.2), six exact GELUs, six heads and 10,818,432 FP32 trainable parameters are
checked. Forward receives BxT integer tokens and returns BxTx256 logits using
causal SDPA; no candidate optimizer, sampling or checkpoint selection is allowed.
The evaluator initializes weights, owns the pinned AdamW schedule and all 5000
updates, complete dev curves, checkpoint choice, controls and measured scenarios.

## Attempts, failures and final series

Plans remain in the ordinary immutable plan registry. Phase attempt indices
cannot reset, duplicate or exceed three. Invalidated preregistrations consume
the phase registration cap conservatively; they never disappear from selection.
The append-only pc01_attempts.jsonl records a hash-linked runtime BEFORE launch.
Starts count even if the parent dies. A finished receipt binds the immutable
result and measured/reserved fit charge; all worker artifacts remain hash-linked.
Malformed output becomes inconclusive, with raw malformed bytes retained by hash.

An interrupted parent without a finished receipt reserves 1200 seconds and
blocks continuation. It needs an explicit recovery review of retained process,
runtime and supervisor evidence; never rerun the ID, delete a lock blindly,
invent missing elapsed time, mark a lost worker successful or omit the attempt.

After development has ended, explicit selection uses
`nextai lab pc01-freeze-series --selected-dev EXP-...`. The freeze commits all
development plans and attempts, selected source bundle, evaluator, data, recipe
and the complete three-replicate policy before final access. Each final plan is
registered separately with `--pc01-phase final --pc01-series` pointing to the
canonical series file. Each final run receives one distinct runner-random seed
in [10000,2147483647]. No development or source tuning follows the series freeze.
`nextai lab pc01-series-status` authenticates all three registered attempts and
only then applies the existing scoped learning gate. Crashes/missing attempts
are inconclusive, not a reason to select another successful subset.

## Resource and measurement limits

The parent grants fit only after starting its clock: 1200 seconds including
dev evaluation/checkpoints; 1800 seconds for the entire worker. It polls at
50 ms for STOP/PAUSE, wall time, process-tree RSS, device telemetry, global
PC-01 data/checkpoints (2 GiB) and disk reserve (10 GiB). PyTorch's allocator is
also capped at 10 GiB; peak allocated/reserved values are checked. These are
sampled stop-on-exceed controls, not kernel-enforced RSS quotas. Brief overshoot
is retained and charged, never clipped away to manufacture budget compliance.
Foreign GPU allocators and malicious native code are not OS-sandboxed.

Unknown failures reserve the full fit allowance; measured overshoot is charged
when larger. The series checks the total 7200-second budget including final runs.
The frozen recipe may still exceed the resource budget: that is inconclusive,
not evidence against transformers. No feasibility result exists before a run.

The result stores supervisor costs, source provenance and hashes of raw worker
outputs. Environment, attention profiler events, raw timing repeats, curves and
cost-boundary notes are separate retained worker artifacts. Matmul MAC/FLOP
estimates are labeled estimates and omit normalization/activation/optimizer/copy
operations; full measured worker time includes those operations. Acquisition
and service costs refer to prior receipts, never an assumed zero. Missing exact
acquisition wall time remains unknown. No energy/economic/transfer claim follows.

## Certification and activation review

Conformance consists of isolated registered-plan/ledger/real-subprocess fixtures,
positive and intentionally broken measurement records, legal scalar baselines,
meta-device model-layout checks, plus the prior real-CUDA attention control.
The synthetic process fixture does not train, import the candidate or execute the
full torch recipe. The real model's 5000-update run is intentionally unexecuted.
Conformance confidence must not be presented as empirical positive learning.

The certificate commits required source/test files, a passing unskipped XML
report, and the current evaluator; it is registered append-only. A new evaluator
needs a new versioned certificate, never overwriting the old certificate. The
former harness sources and exact evaluator manifest are archived, and the new
history validator checks them without redefining old completed assertions.

Before any actual EXP, a separate user decision must authorize the initial dev
run and a prospective activation contract replacing preparation-only authority.
Keep the historical restart/design documents unchanged; do not merely change
maintenance to active. Activate the new PC-01 identity (never old SuiteSparse),
validate the activation gates, archive/freeze its evaluator, issue its matching
semantic/conformance certificate, then register dev and implement the candidate.
This activation-policy transition is not performed or certified by this service
cycle. The current laboratory must remain blocked for training and scoring.

Diagnostic result envelopes have no candidate/Pareto rows and cannot promote an
architecture. Future EXP results remain in the historical result count, while
service cycles remain outside it. The 99 pre-restart results are unchanged.
