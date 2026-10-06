# HAR01: first independent replication — failed preparation

Decision: **INCONCLUSIVE; scientific execution stopped.** This is a technical conformance failure. There are no new HAR measurements, effect sizes or confidence intervals. The earlier HAR screen's DISCARD decision remains unchanged; this failed preparation neither confirms nor overturns it.

## Frozen authority and implementation

Human authority permitted preparation up to1200s inside the existing6000s first HAR independent-replication stage, including pre-EXP work. The other6 registrations/41000s stay protected. Plan `research/plans/HAR01-INDEPENDENT-REPLICATION-V1.json` was committed before implementation/data at b2b1cb8; SHA256 `d5567973e85b444d95ac13a70db9fe24b87c0ab3b672932e8322862c336ad12a`. Full tested source was frozen at f8911b9, with29 exact file bindings verified equal in root and independent clone.

The prospective cohort was T6–10/D21–25, five paired source/target units, three scales K16/32/64, updates0/1/4 and nominal/adverse views. The nine arms,4096 alignment pairs,2048/1024 dense steps, source states, models, mathematical transformations, metrics, calibration and decision thresholds were preserved against the parent. Source fitting was prohibited. The implementation added a versioned cohort/intake binding, isolated wrapper around the original HAR suite, scoped cost ownership and failure accounting, readiness/controller bindings, an unchanged-analysis adapter, and synthetic contract tests. These changes are **not fully validated**.

## Sole clone validation and failure

Exactly one bounded pytest invocation ran with `-q -x` and clone/src package provenance. JUnit records50 cases: **49PASS/1FAIL** —26 budget passes,23 intake passes and one intake failure. The analysis, integration, original HAR, authority and process-supervision groups were not reached. The preliminary driver receipt's `conformance_cases=0` means its success-only XML-parsing branch did not execute; the preserved XML and subsequent STOP receipt supply the actual50-case count.

The failing node was `tests/test_har01_replication_intake.py::test_selected_zip_rows_only_are_converted_and_labels_stay_closed`. Dynamic `spec_from_file_location('har01_replication_intake', path)` leaves `__package__` empty. Consequently `scripts/acquire_har01_replication.py:12` executes `from acquire_har01 import data_archive`; dynamic loading does not add `scripts` to the import path. This raised **ModuleNotFoundError** before the selected-row synthetic intake ran. This failure does not demonstrate a defect in native archive contents or in the model's learning/transfer logic. A normal direct-script invocation has a different import-path context, but that route was not executed after failure.

The process receipt also records wrapper return124, root return1, reason `lingering_descendants`, exit active-process count1 and descendant PID6844. The sole job lasted13.032867s and sampled peak tree RSS487190528bytes. A later read-only PID query at approximately15:15Z found no such process. This later absence does not erase the failed exit receipt or identify the lingering process's cause. No conformance rescue, import fix, test retry or native continuation was attempted.

## Costs and deadlines

| Item | Charged seconds | Meaning |
|---|---:|---|
| Preregistration/implementation/clone preparation |1200|Full conservative frozen preparation cap, includes failed test and administration.|
| Failure preservation/archive/report/publication |1200|Full conservative second auxiliary envelope; **no experiment-controller job**.|
| Scientific workers / supervised fit |0|No native intake, readiness, EXP or fit.|
| Total stage charge |2400/6000|Unused3600 remains associated with the failed stage, without release or retry authority.|

The frozen policy explicitly allocates auxiliary2400 as prep1200 plus controller/archive/report1200. The latter was reserved and charged under the exact bound ID solely for required failure preservation and reporting. These are conservative time charges, not measured fit time, money or energy. No old cost, failure or wallet was reset. Final B usage is **1/12 registrations and27369.55024020007/72000s**; remaining44630.44975979993s covers the untouched other6/41000s plus3600 unused current-stage seconds and30.44975979993s original unprotected remainder. Seven protected future registrations remain in the ledger because this stage registered no EXP.

The preparation driver stopped at15:12:51Z, before its15:16:00Z deadline. The formal administrative STOP receipt was written at15:16:05Z: **5s late**. This lateness is disclosed; no claim of perfect preparation-clock conformance is made. Administration from15:16:00Z, including those5s, is included in the separate archive/report charge and must end by15:36:00Z; the full stage deadline remains16:36:00Z. The completion receipt records observed administration through its creation and the prepaid remaining envelope.

The first archive/report helper stopped at an administrative assertion because it compared the aggregate historical wallet with a B-only number. The durable B charge had already been written correctly. Its unchanged source and error are preserved; the bookkeeping continuation reads the B-specific field and does not repeat the archive, charge, tests or scientific execution.

## Preserved evidence and uncertainty

All failed source bytes, preregistrations, stdout/stderr, JUnit XML, job and stop receipts, original AGENTS history and the append-only event prefix are in `research/results/HAR01-REPLICATION-PREPARATION-FAILURE-V1.zip`. Every archived file was checked byte-for-byte by SHA256 after decompression; archive SHA256 `834a85db94ad02ea63f92ed0c5085c8a1cff9b42affbf009996fcd6e7e810171`. Frozen source hashes were compared in both repositories without re-executing tests. Fresh NPZ, acquisition manifest, readiness receipt and controller-start marker are absent in both repositories. Current HARv2 configuration stays maintenance; the study is terminal and scoring=false.

Synthetic passes support only the particular budget/intake bindings exercised. They cannot establish conformance of the unrun groups or native feasibility. Ranking, source identity, retained/updated answers and UNKNOWN are all **unmeasured** here. Economic qualification is also unmeasured; fit0 is not a scientific efficiency result.

## Unperformed scope and next prospective boundary

The remaining tests, fresh intake, integrity/preflight/readiness,45-role/810-trial experiment and all scientific estimates were not performed. The broader transfer/prototype goal remains ACTIVE/INCOMPLETE. If continuation is separately authorized, first freeze a narrow import-loading conformance correction and an exit-accounting diagnosis against the preserved failed version, before any execution or new content; keep models/gates/source states unchanged and debit every cost from an explicit existing allocation. This report does not authorize a retry, use of the unconsumed replication registration slot, use of the other protected budgets, or opening other future HAR/ASM data.

Machine accounting and immutable bindings: `research/laboratory/HAR01-REPLICATION-FAILURE-COMPLETION-V1.receipt.json`. Earlier `PREPARATION-COMPLETION` and `STOP` receipts remain unchanged.

Publication byte-preservation addendum: Git initially normalized CRLF in the STOP receipt, JUnit XML and stdout. Their exact canonical bytes were restored from the lossless archive and these three paths now use -text attributes. Frozen scientific source bytes and event/receipt bindings remain unchanged. Evidence: research/laboratory/HAR01-REPLICATION-BYTE-PRESERVATION-V1.receipt.json; no further tests or scientific execution, within the same charged archive/report envelope.
