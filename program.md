# NEXTAI laboratory cycle — protocol v3

## Current REVIEW-01 decision state (2026-09-06)

The user authorized one preparation-only REVIEW-01 cycle, capped at 60 minutes,
under `research/laboratory/REVIEW-01-20260906-V1.json`. The bounded plan is
`research/plans/REVIEW-01-V1.json`; the completed review and proposed next
contract are `research/analyses/REVIEW-01-V1.md` and
`research/plans/MUC-01-PROPOSED-CONTRACT-V1.json`. This proposal does not grant
implementation, training, downloads, EXP registration, scoring, WT files 8-9,
WT replication or schedule changes. After validation and Git synchronization,
stop at REVIEW-01-DECISION and request an explicit decision before any next step.

## Current WT-01 terminal decision state (2026-09-06)

The user explicitly authorized the bounded append-only lifecycle correction,
one new evaluator/preflight freeze and exactly one replacement WT-01-DEV-1
registration/run in `research/laboratory/WT-01-LIFECYCLE-REPLACEMENT-20260906-V1.json`.
The lifecycle correction and re-freeze passed, and `EXP-20260906-0001` consumed
the one replacement registration, seed and run. It completed all 162 trials on
visible-development files 6-7; files 8-9 were not opened. The primary recurrence
contrast was 0.1627937252458549 versus the frozen 0.03343253453162794 threshold,
positive on each file. The numerically equivalent VAR(2)/ARX control matched
within 3.552713678800501e-15, so preserve only a narrow classical-mechanism
attribution. Current action is WT-01-DECISION. Do not score, retry, tune, open
files 8-9, register another plan/seed, or claim replication, transfer, economic
advantage, novelty or promotion. Synchronize GitHub `master` and `main`.

## Historical WT-01 decision state (2026-09-05)

The user approved exactly one WT-01-DEV-1 registration in
`research/laboratory/WT-01-DEV1-20260905-V1.json`; follow the prospective
integration plan `research/plans/WT-01-DEV1-ACTIVATION-V1.json`. The integration
passed 949/949 tests and was frozen, but the one registration
`EXP-20260905-0006` exposed a pre-seed lifecycle blocker and was append-only
invalidated. The historical PC-01 closure requires the entire append-only
`research/plan_registry.jsonl` to retain its old terminal hash, so any legitimate
new registration makes doctor fail. No scoring seed was realized and no WT array
was opened. The required separate authority was granted on 2026-09-06 as recorded
above; this does not rewrite or replenish the original registration.

All eight R×U×C roles share one core. R is recursive self-feeding, U is post-reveal
slot-local RLS, and C is origin-relative clipping at +/-4. The separately named
control is the same affine rule written as controlled VAR(2)/ARX. The primary
contrast is NRMSE(R0,U1,C1)-NRMSE(R1,U1,C1); its causal-attribution threshold is
0.03343253453162794, exactly 10% of the already observed historical quality gap.
This threshold can only explain that old positive; it is not a general quality
gate. `wt_walks_v1` remains deferred as a different-operation adversarial source.
Synthetic equivalence and the prior full regression passed. Preserve the
invalidated preregistration and blocker receipt, synchronize GitHub `master` and
`main`, and do not score. Files 8-9, downloads, retries, a second plan/seed and
tuning remain forbidden.

## Historical final-series authorization (2026-09-05)

The user explicitly approved PC-01-FINAL-ACTIVATION-20260905-V1: exactly three
fresh v3 final replicas of the unchanged pc01_byte_gpt_v1, selected dev
EXP-20260905-0002, one experiment per bounded cycle, <=1200 s fit / <=1800 s
worker each. The hash-bound authority supersedes only the completed preparation
waiting state. Freeze/certify before final access; no new dev, tuning, resume,
replacement seed, automatic retry or architecture promotion. A crash/invalid
final stops for review; all three valid outcomes precede the aggregate decision.
Preserve the original restart, prior receipts and cumulative 7200-second cap.

The user also authorized committing and pushing verified project changes to
the existing GitHub origin. Preserve history; use non-force fast-forward pushes.
Keep large data/checkpoints local, publish scientific records and their hashes,
and preserve archived bytes. This does not authorize schedule changes or deployment.
Older stage-specific prohibitions below describe their historical scopes.

## Current preparation overlay

Follow `research/plans/PC-01-FINAL-PREP-V1.json` and laboratory status. This is
only the v2-to-v3 selection bridge and synthetic final-series validation, with
no training or final access. After completion or its fixed deadline, stop at
PC-01-DECISION. Do not freeze a production series or infer activation from tests.

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

The later explicit approval "zatweirdam" is recorded separately in
research/laboratory/PC-01-DEV2-20260905-V1.json. Current action: PC-01-DEV-2,
ONE additional dev after new v2 cohort freeze/certification/preregistration.
Retain the failed v1 attempt and its 1200 s charge. No candidate/recipe tuning,
resume, final-series freeze/access, or third attempt. Start from initialization;
5000 updates and all controls, fit <=1200 s, worker <=1800 s. A terminal result
or invalidation consumes this permission and returns to the decision review.

After completion of dev 2, "okej kontynuuj" authorizes the no-training plan
research/plans/PC-01-GPU-METADATA-V1.json (agent-imposed cap 45 minutes).
Current action PC-01-GPU-METADATA: repair the trusted NVIDIA metadata subprocess
and enforce completeness prospectively in v3. V3 remains maintenance; historical
v1/v2 records retain their original validators. Never refill missing in-run
metadata in a completed result. Completion/expiry returns to PC-01-DECISION,
with no third dev, final freeze/access, training, schedule or publishing authority.

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
