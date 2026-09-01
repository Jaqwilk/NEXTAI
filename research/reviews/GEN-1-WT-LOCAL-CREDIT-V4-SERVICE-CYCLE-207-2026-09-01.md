# WT local-credit v4 protected service cycle — cycle 207

## Scope and decision

The active whole-I/O v4 cohort cannot observe a continuous prediction error or
a post-artifact reveal, so it cannot discriminate temporal credit assignment.
This user-authorized protected cycle therefore activates only a prospective
role version, `heldout_wt_changepoints_prequential_v4`. It creates no
hypothesis, experiment ID, plan, candidate implementation, scoring seed, or
scientific result. No candidate was executed.

This is consecutive no-scoring cycle 2 of the maximum 3. Cycle 208 must
preregister, implement, and score one quick unless a genuine integrity failure
appears.

## Preserved scientific boundary

V4 imports and delegates to the frozen v3 evaluator. It preserves:

- all ten immutable real WT CSV files and their hashes;
- whole-file train/development/test split 0–5 / 6–7 / 8–9;
- train-only normalization and runner-random anonymous channel permutation;
- predict → atomic immutable artifact → reveal ordering;
- K 18/36/54, horizons 16/32/96, Q=18 and runner-random seed policy;
- every quality, stability, cost, state and R1/R4/R16 metric and direction;
- the frozen 0.1325268421060828 meaningful NRMSE effect;
- all ten v3 controls: persistence, pooled mean, control-level bank, LMS, RLS,
  transition bank, bounded replay, ridge FIR, spectral PSR and finite-sample
  discretized CSSR.

A real-file regression ran `wt_persistence_v1` through both v3 and v4 at the
same development seed and confirmed identical deterministic trial outputs,
artifact hashes, quality, state and operation accounting. Only hardware/load-
dependent latency and allocator peak values were excluded from byte equality.
The v3 module remained byte-identical at SHA-256
`225f28d33a3865e1e6cad63870a56d809428de60c21deda3eb0df37100918563`.

## Prospective causal roles

V4 freezes four identifiers that must later resolve to the single prospective
implementation `wt_local_credit_trace_core_v1`:

1. `wt_error_triggered_eligibility_trace_v1` — aligned, error-gated trace;
2. `wt_source_identical_frozen_eligibility_trace_v1` — zero/frozen trace;
3. `wt_source_identical_shuffled_eligibility_trace_v1` — temporally shuffled
   credit with the same public data and trace magnitudes;
4. `wt_source_identical_dense_eligibility_trace_v1` — aligned credit without
   sparse error gating.

All roles must share features, initialization, fit order, prediction, rollout,
update code, constants, output and accounting except those interventions.
Candidate modules are intentionally absent. The next immutable plan must freeze
the feature map, trace recursion and cap, decay, error threshold, learning rate,
shuffle policy, clipping, tie behavior and exact operation/byte accounting
before any implementation or scoring output.

This is distinct from falsified WT predictive-state EXP-0024: that experiment
changed the train-time temporal projection and used the same one-step NLMS
readout update in every causal role. V4 instead holds the representation path
fixed and tests whether post-artifact temporal credit alignment and sparse
error-gated updates add held-out capability. LMS/RLS, transition-bank and replay
controls remain mandatory so a positive cannot be attributed to generic online
adaptation or stored examples.

## Verification

- focused WT contract/regression suite: 31 PASS;
- registered semantic baselines: 10 records and 13 conformance nodes PASS;
- full pytest: 559 collected, PASS;
- protected manifest: 726 files, integrity PASS;
- evaluator SHA-256:
  `938f36b972fcf0a91180fa7abe656a3f65ff356b816c0804fd150bb0006a9eda`;
- candidate-bundle SHA-256:
  `4f2d95cd8e14223a771a94f737ea083ee5a1bdee689b216b38530b0b31258684`;
- preflight certificate:
  `3a1501be44fe5e05d38c67fe4481b4a562b5689bceae132ab8eee5e3ab29f7bb`;
- doctor: PASS;
- scoring performed: false.

The previous whole-I/O v4 manifest is preserved at
`research/manifests/program_induction_from_whole_io_v4-protocol-v2-9924b17b8135.json`.

## Exact next discriminating experiment

Cycle 208 must preregister one low-confidence one-seed breadth quick on v4,
before implementing the four roles. The main must beat all three source-
identical causal ablations and the strongest complete implementable control by
the frozen 0.1325268421060828 aggregate NRMSE margin; the positive direction
must also hold at H32 and H96 with no worst-file or worst-transition regression,
stable rollout 1, slot-local updates, bounded state, three-scale accounting and
implementable Pareto non-dominance. The plan must additionally require fewer
update operations/bytes than dense credit in every K/H cell. One positive seed
can authorize only unchanged three-seed replication. A valid negative ends the
exact trace/gate rule without threshold, decay, feature or learning-rate tuning.
