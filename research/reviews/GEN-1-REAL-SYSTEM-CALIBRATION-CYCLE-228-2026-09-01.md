# One-time real-system calibration — cycle 228

## Scope and validity

This is systems calibration `CAL-20260901-0001`, not an experiment and not
hypothesis evidence. The exact task, models, constants, measurement definitions
and invalidation rules were frozen in
`research/checks/real_system_calibration_v1_preregistered.json`, SHA-256
`d2004bc548a2253dcd1072cf9641b1369d9ce1dff9edd786f23a52095a384829`,
before the implementation was written and before validation or test metrics
were observed. No runner-random seed, EXP plan, candidate evidence, confidence
change, Pareto promotion or G1 counter update was made.

The calibration used all 102/7/3 frozen train/validation/test files from the
v12 real repository registry (699,426/117,023/55,389 bytes). Next-byte examples
never cross file boundaries. The common test comprises all 55,197 positions
after a 64-byte prefix; validation is the first fixed 8,192 eligible positions
and was reported without changing any choice. Corpus acquisition read 871,838
bytes in 0.06648 seconds.

## Observation

All five required methods completed on local PyTorch 2.6.0+cu124, CUDA 12.4
and one NVIDIA GeForce RTX 4070.

| model | test bits/byte ↓ | top-1 ↑ | fit s | query s | bytes/s | cold/warm µs per byte | update | state bytes | peak CUDA bytes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PPM-D order 5 | 2.1678 | 0.5576 | 0.7367 | 1.7175 | 32,139 | 27.33 / 28.20 | 16.0 µs | 3,113,912 | 0 |
| CTW depth 2 | 2.8315 | 0.4485 | 0.5497 | 4.8855 | 11,298 | 68.25 / 68.13 | 7.868 ms | 1,907,048 | 0 |
| dense AR order 5 | 3.9134 | 0.2608 | 1.1962 | 5.0664 | 10,895 | 85.48 / 87.26 | 20.6 µs | 1,312,584 | 0 |
| bounded local retrieval | 6.4413 | 0.4701 | 0.1363 | 5.0677 | 10,892 | 138.14 / 137.80 | 9.3 µs | 9,037,508 | 0 |
| small dense Transformer | 4.6247 | 0.2235 | 0.6801 | 0.4803 | 114,931 | 7.79 / 7.99 | 3.952 ms | 1,248,880 | 82,967,040 |

The append-only accounting correction adds common acquisition to the measured
read-only workloads. R1/R4/R16 seconds are respectively: PPM-D
2.521/7.673/28.282; CTW 5.502/20.158/78.784; dense AR
6.329/21.528/82.324; retrieval 5.270/20.473/81.286; Transformer
1.227/2.668/8.431. The Transformer moved 32,962,280/119,069,600/463,498,880
host-device bytes at R1/R4/R16; CPU models made no host-device transfer, which
does not mean they made no host-memory traffic.

The GPU Transformer executed an estimated 291.2 billion query work units in
0.480 seconds, while PPM-D executed 98.9 million declared work units in 1.717
seconds. These units are not semantically identical operations, but the
roughly four-order-of-magnitude difference in measured rate proves that raw
cross-backend operation counts cannot be converted to hardware time by one
constant.

## Uncertainty and measurement limits

- This is one machine, one process, one fixed context/batch configuration and
  one timing run. Latency is noisy; exact differences should not be generalized
  to other hardware or software stacks.
- “Cold” means the first synchronized post-fit test batch, as preregistered.
  Fit already initialized the device, so it is not process-start or driver-cold
  latency. Near-equal cold/warm values cannot support a startup-cost claim.
- Peak CUDA allocation is model-specific. Peak host RSS is absolute process
  RSS and the models were measured sequentially, so later values include the
  resident runtime and earlier allocations. RSS is therefore a safety ceiling,
  not a clean per-model memory comparison. Resident state estimates are the
  usable model-specific memory measure in this run.
- The CPU paths did not instrument host bytes touched. Their zero transfer
  values mean only that no CPU↔GPU transfer occurred.
- No method was tuned to match PPM-D quality after observing the result. The
  Transformer speed advantage is therefore not a matched-quality advantage.

## Interpretation

PPM-D is the strongest quality control on this frozen real corpus. The small
Transformer processes bytes about 3.6 times faster than PPM-D during the full
test and has the lowest R1/R4/R16 wall time, but it loses 2.457 bits/byte and
33.4 percentage points of top-1 accuracy. It cannot be called more efficient
at matched useful quality. Bounded retrieval attains 47.0% top-1 accuracy but
its KT-smoothed distribution has 6.44 bits/byte, illustrating why accuracy
alone would overstate its predictive quality.

The main durable lesson is accounting-related: algorithmic work estimates are
useful only within a stable implementation boundary. Across CPU dictionary
logic, NumPy tables and batched CUDA kernels, actual throughput, transfer,
state and quality must remain explicit. HYP-0012 receives no evidence or
confidence update from this calibration.

## Confidence

High confidence that the recorded artifact faithfully measures this exact
frozen run and that no compared learned system matched PPM-D quality. Medium
confidence in the relative warm throughput ordering on this machine. Low
confidence in extrapolation to other batch sizes, hardware or matched-quality
models, and no scientific confidence update for any NEXTAI mechanism.

## Decision

Keep the calibration as a systems guardrail. Do not promote, replicate, tune or
enter it into `G1-POST-EXP-0059-V1`; the counter remains 0/8. Future experiments
must report hardware measurements as secondary diagnostics while retaining
matched-quality algorithmic accounting as the scientific boundary.

## Next discriminating experiment

No currently active frozen cohort admits a genuinely new mechanism: the v5
whole-I/O roles encode the closed certified-pattern rule. Cycle 229 must not
reuse that rule or manufacture an EXP-0060 alias. It must perform one minimal
protected role-only migration over the unchanged real WT prequential data for
a source-identical **learned particle-proposal predictive state**. This is not
another surprise gate: valid EXP-0029 already closed conditional transition
refresh, and its code, threshold and update rule may not be reused.

The future main role uses a fixed bounded particle population and learns one
family-blind proposal from training observations; a source-identical bootstrap-
proposal ablation isolates proposal learning, and a source-identical
deterministic posterior-mean ablation isolates population uncertainty. Existing
persistence, RLS/Kalman, nonlinear RLS, change-point bank, replay and frozen
prequential controls remain mandatory. The unchanged evaluator already exposes
three channel scales, unseen files/regime transitions, predict-then-reveal
updates, recovery, retention and full cost, so no new data, metric or schema is
justified. The contract must freeze particle count, proposal, weights,
resampling, initialization and ties; forbid channel names and hidden regimes;
and charge acquisition, fit, every particle propagation/weight/resample,
query, update, state, bytes and R1/R4/R16 workloads. Cycle 230 must then
preregister and execute exactly one cheap scout. Success requires a frozen
development margin over every source-identical ablation and the strongest
complete classical control in overall, worst-file and worst-transition NRMSE,
stable H96 rollout, local update without refit and implementable Pareto
non-dominance. A negative closes the exact particle-proposal mechanism without
particle-count, proposal or resampling tuning.
