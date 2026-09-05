# NEXTAI laboratory cycle — protocol v3

This is the operational contract. Read AGENTS.md first. The active work queue is
research/LAB_PLAN.md and research/laboratory/restart.json. Historical analyses,
hypothesis next_experiment fields and events are evidence, not the current queue.
Preparing this repository does not start or change an app schedule.
`nextai lab status` resolves the current action from validated append-only
`lab_milestone_progress` completions; restart.json retains the initial contract.
Do not repeat PC-01-CONTRACT after its completion. If status reports
user_decision_required, stop: unused minutes do not authorize a third service
cycle, and a doctor PASS does not override the completed milestone's cap.
The user authorized exactly one extra no-training service cycle on 2026-09-05:
research/laboratory/PC-01-EXTENSION-20260905-V1.json. Its deadline is binding;
the original 2/2 history stays intact. Completion is a separate append-only
lab_extension_completed event, not a reset or a new scientific experiment.

The subsequent user approval "zatwierdzam etap" authorizes prospective activation
and ONE dev attempt, recorded in PC-01-ACTIVATION-20260905-V1.json. It is not a
reset of the closed service accounting. `nextai lab status` uses this hash-bound
overlay; restart.json remains the immutable original preparation state.
Only pc01_byte_gpt_v1 / dev / seed 1103 may be registered once, after evaluator
freeze and conformance certification. Implement the candidate after registration.
Fit <=1200 s and worker <=1800 s; preserve timeout/crash, no automatic retry.
No final-series freeze/access or architecture promotion is authorized. Review
the single outcome before another attempt. Maintenance/STOP/integrity still apply.

After EXP-20260905-0001 crashed on device telemetry, the user authorized one
no-training repair stage: research/plans/PC-01-TELEMETRY-REPAIR-V1.json.
The read-side addendum records the concurrent-read failure discovered in synthetic
stress tests. Keep benchmark_status=maintenance and scoring disabled. Preserve
the consumed dev attempt, old evaluator/source archive and 1200 s charge.
Validate the scoped I/O repair, including persistent errors and STOP/deadlines;
the agent-imposed service bound is 45 minutes, with no old-budget reset.
The new prefix-aware history validator supersedes the pre-registration-only
check for this maintenance stage without editing that historical script.
Completion returns to PC-01-DECISION; it does not authorize training or final data.

## 1. Start safely

Read the complete required startup set in AGENTS.md. Run:

```powershell
uv run nextai doctor
uv run nextai lab status
```

Inspect Git changes, STOP, PAUSE and research/run.lock. A stop file, live lock,
schema/integrity/lifecycle error stops the cycle. Explicitly authorized maintenance
may repair a gate, without scoring, and must append a maintenance event.
Do not discard another task's changes. A pending experiment must be completed or
append-only invalidated before creating another one. Check available disk space
and bound installed/extracted footprint before every installation or download;
at least 10 GiB must remain. Preserve dependency locks and acquisition receipts.

## 2. Read the current milestone, not the old search backlog

LAB-RESTART-20260904-V1 starts with the positive-control design milestone PC-01.
The old eight-result G1-POST-EXP-0059-V1 window is historical, not restarted.
Cycle 228 completed CAL-20260901-0001: do not rerun it, overwrite it or count it
as candidate evidence. PC-01 is a new learning/measurement calibration with a
new contract, task, recipe and result identity, not a replay of that diagnostic.

One wake performs one bounded deliverable or resumes the one in progress.
The first package is reproducibility + positive controls + WT causal isolation,
followed by a decision. No language prototype, new architecture search, paid
service, external model/API, publication or deployment is implicit in preparation.

## 3. Service and development are explicit work, not scoring

When benchmark_status is maintenance or the effective laboratory authority is preparation_only:
do not create/run an EXP plan. Produce only the next named preparation artifact.
For PC-01, select a licensed local corpus and an established small-transformer
recipe; freeze data units, split, training budget, controls, thresholds, timing
scenarios and instrumentation tests before candidate implementation/training.
Record primary sources, size/space checks and what remains unknown. Do not claim
positive-control success from unit tests or from the old 0.68-second fit.

Each milestone has a fixed maximum number of service cycles and development
attempts in LAB_PLAN.md. Append lab_milestone_progress to research/events.jsonl
with milestone_id, attempt, artifact paths/hashes, observed checks, next action
and cumulative budget. At the cap, stop and report ready, failed or blocked;
do not rename the milestone to get more attempts. No forced score after two
service cycles; no unbounded literature-only loop.

## 4. Open a scored cohort only after its contract exists

Do not reactivate the retained SuiteSparse cohort to escape maintenance.
A new benchmark/cohort must name one of: mechanism, economics, transfer.
Its frozen contract must specify per-task useful-quality thresholds, required
controls and failure policies, metrics/directions, hardware/scenario, full-cost
boundary, seed policy, independent data units, development cap, final selection,
uncertainty analysis and invalidation rules. No automatic global 0.95 threshold
for loss tasks. Implement and test the claim-specific gates before activation;
the legacy promotion CLI alone does not establish a protocol-v3 claim.

Freeze a new evaluator and semantic-baseline certificate before registration.
Use nextai plan new to register the immutable experiment and evaluator digest.
Then implement the tested change under candidates/, using only preregistered
development data/attempts. Re-freeze candidate changes only if the evaluator is
unchanged. Invalid plans are append-only invalidated, not edited. Final recipes
and source hashes must be frozen before any final holdout result is visible.
Do not use current filenames as proof of historical implementation identity:
nextai provenance checks hashes from the immutable result against local/Git bytes.

## 5. Run and interpret one experiment

Only the audited nextai run --plan research/plans/EXP-....json route may create
scored evidence. Source audit and integrity precede runner-random seed realization.
No bypass runner, deleted failure or hidden training/preprocessing is allowed.
A single seed screens only. A replicated claim requires at least three seeds
and independent data units appropriate to the question, not just permutations
of the same trace. Keep all timing samples, failed cells and resource overruns.

For each analysis keep these exact top-level sections:

OBSERVATION
INTERPRETATION
CONFIDENCE
ALTERNATIVE EXPLANATIONS
DECISION
NEXT DISCRIMINATING EXPERIMENT

Separate learning, economic advantage and transfer. Report narrower positives
even when the full economic contract fails. Do not promote them into architecture
success. Conversely, a bad control invalidates that comparison, not all learning.
Record adverse results, exact scope and the next discriminating question.
Never rescue-tune on a final test. Use a new question and fresh test set.

## 6. Close durably

Append events and, only when warranted, hypothesis updates. Preserve all old
probabilities and completed artifacts. A belief shift is not a reward target.
Refresh nextai report (content provenance, not file timestamps). Run doctor and
pytest, record exact results and any unverified platform. Update state without
resetting the 99 historical results or old cycle counter; service work is not
a new scientific result. At most one scored experiment per wake.
Report milestone/experiment ID, immutable contract/plan, observations, confidence,
decision, budget/integrity and exact next action. End this cycle.

Review cadences still apply to completed experiments. A milestone review may be
earlier. Schedule behavior remains best-effort; no catch-up or overlapping runs.
