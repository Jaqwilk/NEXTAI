# PC-01-GPU-METADATA-V1 — scoped NVIDIA metadata repair, no training

Immutable maintenance plan: research/plans/PC-01-GPU-METADATA-V1.json.
Plan file SHA-256: f0d14d68e266a9701ab6aaa66638e1375618eb59d2acae284c915830de69ed8e.
Cycle 290. User approval: "okej kontynuuj" after the proposed no-training
metadata repair. Agent-imposed service cap: 45 minutes, deadline
2026-09-05 16:29:39 UTC. This is not a new EXP or a new development attempt.

## OBSERVATION

Startup doctor passed. Neither STOP/PAUSE nor a live run lock was present.
The previous completed development result EXP-20260905-0002 and its analysis,
checkpoint and completion receipt remain byte-identical. That result's in-run
GPU metadata remains null; this repair does not reconstruct or refill it.

Two real paired, read-only probes were run in fresh subprocesses using the
same sanitized environment as the research worker. No candidate, corpus or
training was used by these probes. Both original queries failed with exit 255,
"Failed to initialize NVML: Unknown Error". Both repaired queries completed:

| Probe UTC | Driver | SM / memory MHz | GPU utilization | Memory used MiB | Repaired query elapsed s |
|---|---|---:|---:|---:|---:|
| 15:54:38 | 551.78 | 210 / 405 | 31% | 695 | 0.0374303 |
| 15:57:49 | 551.78 | 210 / 405 | 27% | 1029 | 0.0414463 |

Both identify NVIDIA GeForce RTX 4070, GPU index 0, UUID
GPU-53e40ab4-0b69-c994-91af-620aca6a9153. These are current diagnostic snapshots,
not the clocks or load of the earlier model run and not a throughput benchmark.
Raw original/repaired stdout, exit codes, timestamps, executable and environment
policy are retained in JUnit properties in PC-01-GPU-METADATA-TEST-1.xml and
PC-01-GPU-METADATA-CONFORMANCE-V5.xml. Only two of the maximum three permitted
paired real probes were used. No third probe or new training was needed.

The repair reads the 64-bit Windows ProgramFilesDir registry value and passes
it as ProgramW6432 only in an environment copy for the nvidia-smi child.
It does not change os.environ, the global sanitized environment policy, the
candidate's environment, credentials, PATH, model, optimizer or data access.
src/nextai_autoresearch/runner.py is unchanged from the pre-stage archive.

The new trusted helper has a five-second subprocess timeout, explicit missing-
executable/registry/NVML/timeout/malformed-output evidence, and strict parsing
for exactly one GPU, its identity/driver, positive clocks, utilization 0..100%,
and nonnegative memory. Null/incomplete probes are not accepted. Timestamp and
raw-query consistency, ordered snapshots and unchanged GPU identity are checked.

Prospective v3 worker integration saves a required before-fit snapshot before
importing the model or requesting fit. A failed probe writes its error artifact
and rejects execution without training. A second required snapshot follows timing.
The v3 parent validates both snapshots and their separately persisted artifacts;
missing/inconsistent post-fit metadata becomes an inconclusive result rather
than an accepted measurement. Synthetic tests cover these paths without a
production model run. Snapshots are outside individual timed inference callbacks
but within the supervised worker wall-clock boundary.

Legacy v1/v2 plans, results and replica schemas remain unchanged. Only explicit
v3 measurement validation requires the new field. The actual completed v2
record still passes its historical validator. New cohort identity
pc01_byte_lm_learning_measurement_v3 is frozen in MAINTENANCE, not activated.
Model/data/quality thresholds and the 5000-update recipe remain unchanged.

Validation reports are all preserved:

- Targeted metadata, prior-authority and version tests: 60 passed.
- Additional targeted metadata tests, excluding a redundant real probe: 34 passed.
- Full conformance: 886 passed, zero failures/errors/skips, 131.050 s.
- Execution certificate: PC-01-EXECUTION-CERTIFICATE-V5.json.
- History proof and doctor: PASS; all 877 current protected files verified.
- Real-root dev, final, legacy, final-series freeze and replay gates: denied;
  the registration ledger remained unchanged.

The full regression uses isolated numerical/lifecycle fixtures and existing
benchmark tests; it is not a new scored research experiment. No PC-01 model
training, checkpoint resume, final data evaluation, dependency installation,
network acquisition, GitHub publishing or schedule change was performed.

## INTERPRETATION

The paired evidence supports the diagnosed NVML environment dependency on this
Windows installation and the narrowly scoped repair. The executable completeness
gap is closed for prospective v3 individual runs. Retain the repair rather than
repeating the successful v2 development training solely to obtain metadata.

This is apparatus conformance, not new evidence for learning, inference-cost
superiority, transfer or a promoted architecture. The earlier v2 learning result
remains useful dev evidence with its documented environmental limitation.

## CONFIDENCE

High confidence for the tested Windows/RTX 4070 setup, based on two paired real
probes and positive/negative fixture tests. No population reliability interval
or cross-platform claim follows from two observations on one machine. Linux
runtime behavior was not tested. Multi-GPU configurations deliberately fail
closed rather than guessing which device was measured.

The two snapshots do not continuously trace clocks/load during training or
inference and do not measure energy. The five-second subprocess timeout is not
a kernel-level hard real-time bound on OS scheduling/process startup. No missing
historical measurement can be recovered retrospectively by these current reads.

## ALTERNATIVE EXPLANATIONS

Ordinary environment variables, driver installation details or future NVML
versions may change the failure mechanism. The repair does not prove that every
NVML failure is caused by this registry/environment dependency. Explicit error
artifacts and fail-closed checks therefore remain necessary. Varying live load
and memory in the two probes are observations, not treatment effects.

## DECISION

KEEP the scoped repair and v3 completeness controls. Finish this authorized
maintenance stage and return to PC-01-DECISION. Do not run a third dev or final
replica, unlock scoring, or certify PC-01's final learning criterion here.
The final-series transition is still a separate, explicit decision and contract.

## INTEGRITY AND BUDGET

All 872 pre-change protected files were archived and verified under
research/laboratory/archive/PC-01-DEV-CYCLE-289. Its manifest is
research/manifests/PC-01-GPU-METADATA-BEFORE.json, SHA-256
1671535a2d03a4d7bd3467ab241b4d2f9ceb0bb25898ce193d559bc75e40a118.
348 older immutable non-ledger artifacts and historical ledger prefixes remain
verified; both dev attempts and their recorded worker artifacts are preserved.
The previous dev completion receipt and every artifact it binds remain exact.
Candidate sources, global runner environment, telemetry helper and legacy schema
bytes are unchanged. The broader candidate-bundle hash changed only through
the retained-baseline test's current-cohort/status assertion, not model code.

New evaluator SHA-256:
687c0a7534808d7158213e9d9594ea936eea03d6366061c10b3d7e0dcc452e69.
Current integrity: 877 files. Completed results remain 101; dev attempts remain 2.
Cumulative PC-01 fit charge remains exactly 1500.4259332000001 / 7200 s.
Remaining design capacity 5699.5740668 s is not authorization to spend it.
Original 2/2 service accounting, closed 1/1 extension, G1/CAL, hypotheses and
BELIEFS are not reset or reinterpreted. No plans/results/logs were deleted.
The completion receipt records this stage's actual duration and final disk check.

## NEXT DISCRIMINATING EXPERIMENT

After explicit approval, prepare a bounded final-series transition contract
selecting the unchanged candidate/recipe audited in EXP-20260905-0002, while
using the newly certified v3 metadata evaluator and fresh per-run baselines.
Bind both evaluator identities, immutable selected dev result/source/recipe,
the exact measurement-only changes, and three fresh runner-generated final seeds.
No additional dev training is scientifically required by this metadata fix.

Two concrete compatibility tasks remain before any final registration:
(1) freeze_series currently copies the selected dev's old evaluator digest,
whereas verify_series requires the current evaluator; this needs a narrowly
authorized, hash-bound v2-to-v3 selection transition, not a blanket exception;
(2) the pure final series_decision still uses the legacy strict replica schema,
so a version-aware v3 series adapter must require the new metadata without
weakening legacy validation or dropping metadata before a claim decision.
These are recorded prerequisites, not implemented bypasses or approved scoring.

After this contract/adapter is frozen and tested, the discriminating study is
three unchanged final replicas, one per bounded cycle, each at most 1200 s fit
and 1800 s worker, with a 3600 s total fit reservation for that series. Retain
every failure and all three outcomes; no holdout-guided tuning or replacement
replicas. This tests replicated local positive-control learning, not independent
corpus transfer or end-to-end economic advantage. WT remains downstream.
