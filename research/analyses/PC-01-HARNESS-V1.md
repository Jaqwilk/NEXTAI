# PC-01-HARNESS-V1 — cycle 285, resumed and closed

## OBSERVATION

This is the second PC-01 service cycle, started 2026-09-04 23:43:51 UTC,
interrupted during the full regression run, and resumed 2026-09-05 09:11 UTC.
It is not a third cycle. The initial full-run terminal result was unavailable
after interruption, so it was not reported as a pass or used as a certificate.

The six entries in pytest's lastfailed cache referred to test names no longer
present in the current source. Explicitly requesting those names produced six
collection errors and ran zero tests. It did not reproduce six current test
failures. The zero-test XML and the exact cache names are retained in the receipt.
No cache deletion, test removal, threshold adjustment or candidate change was
used to obtain a passing regression.

The full current suite was then rerun: **748 passed, zero failed/errors/skips**;
pytest reported 76.42 s. Its durable XML is
`research/laboratory/PC-01-HARNESS-REGRESSION-RESUME-2.xml`.
The new PC-01 file contains 59 tests, including a real CUDA causal-attention
fixture, not model training or a real-system performance ranking. Earlier targeted
runs passed 79 tests including the 20 restart tests. One earlier boundary-test
fixture failed because its temporary evaluator module was absent; the fixture
was corrected to test an actually resolvable forbidden import. No scored result
was involved. A rejected multi-file patch made no changes and was reapplied with
one operation per file.

Implemented: exact split verification; development-only data view; float64 bpb
with complete tail/target counting; dev-only checkpoint selection; causality,
learning-off and precision controls; timing callback boundaries with reference
CPU outputs and separate batch scenarios; cooperative resource checks; a strict
replica schema and three-record claim gate; verified append-only queue progress;
and a candidate import boundary excluding the private PC-01 evaluator.

Doctor passed with 847 protected files, 516 historical candidate audits, 427
sources, 59 hypotheses, 99 completed EXP results and no pending EXP. The history
validator confirmed 341 immutable artifacts and the append-only ledger prefixes.
The exact former evaluator manifest is preserved in
`research/manifests/PC-01-HARNESS-BEFORE-a0c945af93aa.json`.
The new maintenance evaluator digest is
`7c41acf72f99df1613481de0168ade2018b7114b3fc25af5916803343cf7b7e7`.
The candidate bundle is unchanged:
`8d31045c9742fceaafeb88ec468702e358591ecc0616490855d21a30d767085e`.
The maintenance preflight certificate was archived/rebuilt for these harness
bytes. It is NOT an executable-PC-01 or successful-learning certificate.

## INTERPRETATION

The measurement primitives are tested; an end-to-end runnable cohort is not.
`research/laboratory/PC-01-HARNESS-V1.json` records the partial scope and four
specific missing components:

1. PC-01 EXP plan/CLI/worker adapter and audited candidate interface, with the
   intended development versus final seed policy and no fictitious K/D axes.
2. Authoritative series provenance and attempt accounting from registered plans,
   runner receipts and failures, rather than trusting supplied metric records.
3. Parent-supervised fit deadlines and real resource/storage accounting through
   failures; cooperative checks alone cannot stop a stuck kernel or callback.
4. Integrated positive/negative worker conformance tests, output provenance and
   exclusion of calibration diagnostics from architecture rankings, followed by
   freezing the executable cohort and its own semantic certificate.

The current pure claim gate explicitly reports runner_authenticity_checked=false.
Synthetic passing records do not prove scientific success. The selected
SuiteSparse cohort remains in maintenance, restart scoring authorization remains
false, and no PC-01 model implementation, training or final-quality evaluation
was started. Existing regression fixtures are not new scientific experiments.

## CONFIDENCE

High in the recorded primitive/regression checks and preserved historical bytes.
No empirical PC-01 learning or end-to-end execution evidence exists. Neither the
CUDA fixture nor the schema proves that the 5000-update recipe fits its budget.

## ALTERNATIVE EXPLANATIONS

The disappeared cache names explain the six initial alarms but cannot reconstruct
the interrupted terminal output. The fresh full-suite result is the evidence for
current regression status. Callback tests do not establish actual model forward
execution, authoritative seed history or complete fit-time supervision. A local
inspectable final interval remains different from a genuinely inaccessible holdout.

## DECISION

KEEP the measurement primitives. Readiness is INCONCLUSIVE/BLOCKED on the four
integration requirements, not on a failed neural family or a scientific negative.
Cycle count is now 2/2. Conservatively reserve the full 60-minute allowance for
this interrupted/resumed cycle, making 120/120 minutes accounted together with
the first design cycle. This is a budget reservation, NOT a measured 120 minutes
of active work; the overnight interruption is not treated as active tool work.
PC-01 training remains 0 minutes, development attempts 0/3, final replicas 0/3.
The cycle-count cap independently prohibits an automatic third service cycle.

No schedule, model API, package installation, data download, branch merge,
GitHub push or deployment was performed. Old G1, CAL, BELIEFS, hypotheses,
completed plans and results remain unchanged. The older contract validator still
asserts the old live-manifest hash by design; use validate_pc01_harness.py to
verify the exact archived manifest after the legitimate maintenance freeze.

## NEXT DISCRIMINATING EXPERIMENT

First obtain a user decision on one explicitly bounded additional service cycle
for the four integration gaps; do not silently reset the two-cycle limit or
proceed directly to training. If authorized, implement the audited execution path
and complete its conformance checks without changing the frozen learning recipe,
quality thresholds or final data. Only once the cohort is ready, preregister the
first dev experiment with seed 1103, then implement the candidate and execute
through `nextai run --plan`, with no final-test access. Failure to finish the extra
service budget would require another concrete blocker report, not endless setup.
