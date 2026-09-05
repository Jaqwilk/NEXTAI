# PC-01 final post-run validation addendum

Cycle 294. This addendum preserves a validation issue discovered only after the
third and last authorized PC-01 final result and its authenticated aggregate
decision had been produced. It does not alter any plan, result, seed, metric,
source commitment or series decision.

## OBSERVATION

The full post-run suite executed 927 tests in 129.030 seconds. It reported zero
errors and one failure:
`tests/test_pc01_telemetry.py::test_concurrent_reader_and_two_thousand_device_writes[2]`.
The first two repetitions completed 2000 writes each and recorded 10799 and
10626 coherent reads. In the third repetition the independent reader exited
after `read_device_sample()` propagated `FileNotFoundError` while opening the
atomically replaced `device.json` path.

The immutable failure report is
`research/laboratory/PC-01-FINAL-3-POSTRUN-REGRESSION-V1.xml`, SHA-256
`551d26210e363bd35274995a26eb4d1de307d20fe1272340bb7da39dbe66b327`.
The production reader returns `None` for the already registered transient
Windows permission/share conflict but does not classify transient path absence.
The writer uses a same-directory temporary file followed by `os.replace`.

The completed EXP-20260905-0005 run itself did not hit this exception. It
recorded four recovered permission/share conflicts, a maximum unavailable gap
of 0.0615611 seconds, complete resource telemetry, all ten controls and a valid
result. The authenticated three-result gate had already returned
`positive_control_pass` before the regression failure was observed.

## INTERPRETATION

This is a real, low-frequency Windows concurrency defect in the frozen PC-01
telemetry publication/read path, not evidence against the observed learning
contrast. It creates a possible false crash during a future concurrent run; it
does not silently improve a metric or explain the three successful final
results. Because the telemetry module hash is committed by the completed final
series, editing it now would break provenance rather than repair that series.

## CONFIDENCE

High confidence in the failure classification: the traceback identifies the
exact uncaught exception and source line, and two adjacent stress repetitions
passed under the same invocation. Moderate confidence that transient target
absence is the complete Windows mechanism; a separate maintenance cycle should
reproduce and bound it before changing production behavior.

## ALTERNATIVE EXPLANATIONS

Temporary-directory cleanup is unlikely because the parent was still performing
writes and had not left the test. External filesystem or antivirus activity may
change the frequency, but does not make an uncaught transient absence acceptable.
A passing rerun would demonstrate intermittency only and would not erase this
failure. The failure does not show corrupt JSON, non-monotonic samples, an
unresolved gap in any scored result or candidate access to final data.

## DECISION

Preserve the failed report and retain the narrow authenticated PC-01 decision as
`positive_control_pass`. Mark post-run infrastructure validation as NOT fully
green. Do not rerun training, replace a seed, edit a completed result, or mutate
the frozen series source in place.

## INTEGRITY AND BUDGET

No additional model execution, scoring, final-data access, dependency install,
source edit or budget reset occurred. The completed PC-01 charge remains
2394.270825300002 / 7200 seconds. This addendum is new append-only evidence and
the failed XML remains tracked.

## NEXT DISCRIMINATING EXPERIMENT

Stop at PC-01-DECISION. Before WT-01 preparation, request explicit authority for
one bounded no-training maintenance cycle that preregisters the transient path-
absence behavior, tests concurrent read/write recovery and persistent absence,
versions the telemetry source instead of rewriting the completed series, and
re-runs the full regression suite. No WT-01 scoring or PC-01 retry follows
automatically.
