# PC-01 telemetry persistence repair — cycle 288, no training

Immutable maintenance plan: research/plans/PC-01-TELEMETRY-REPAIR-V1.json.
Prospective diagnostic addition: PC-01-TELEMETRY-REPAIR-V1-READ-ADDENDUM.json.
User authorized the local repair and concurrent read/write tests only.

## OBSERVATION

Startup doctor passed at cycle 287 with 100 results, no pending plan and 861
protected files. The complete previous protected source set (861 files,
3299974 bytes) and evaluator manifest were archived before changes. Free space
after archival was 110763241472 bytes. No installation or download was needed.

A real Windows reader handle sharing read/write but not delete reproduced the
legacy atomic replacement denial. This establishes a concrete sufficient
mechanism, not the identity of the process responsible for the production crash.
REPRODUCTION-V1.xml preserves that expected failure assertion; its single test
passed. The xunit2 property-format warning was retained; later reports use xunit1.

Initial writer-only validation: 14 passed, 3 failed. All three stress readers
encountered PermissionError errno 13 opening the replaced device.json. Preserve
PC-01-TELEMETRY-TEST-1.xml and the writer-only source archive; this is not a
successful repair report. The read-side addendum was recorded before extending
the implementation. Subsequent TEST-2: 17 passed; TEST-3: 105 scoped tests passed.

Final full suite: 834 passed, zero failures/errors/skips, in
research/laboratory/PC-01-TELEMETRY-CONFORMANCE-V3.xml. Final stress properties:

| Run | Successful writes | Coherent reads | Writer retries | Seconds |
|---:|---:|---:|---:|---:|
| 1 | 2000 | 10196 | 121 | 10.3677881 |
| 2 | 2000 | 9851 | 115 | 10.1248677 |
| 3 | 2000 | 10114 | 130 | 10.3398099 |

All 6000 writes completed; 30161 reads passed JSON validity, coherent paired
fields and monotonic counter checks. Final counters and absence of abandoned
writer temporary files were checked. Each stress case remained below its
preregistered 30-second bound. These timings characterize fixtures on this
machine, not inference speed or algorithmic complexity.

Real lock tests cover successful recovery from transient denial and failure
under persistent denial. Deterministic tests cover exact retry budget/error
classification, invalid JSON/types and STOP/PAUSE while retrying. Real subprocess
tests verify fit timeout, CUDA-limit termination, worker failure on persistent
write denial, parent failure after persistent read denial, STOP during read
contention, and resolution of the last read before accepting worker exit.
The full suite retains independent worker-wall/RSS/payload/disk controls.

Production changes are PC-01-specific: the worker calls write_device_sample;
the supervisor uses a nonblocking read and records contention/gap diagnostics.
Generic atomic_write_json, every candidate source, data, model initialization,
optimizer, 5000 updates, thresholds and 1200/1800 s budgets are unchanged.
The retained SuiteSparse configuration assertion now reflects maintenance;
its baseline mathematics and implementation are unchanged.

The new history validator checks append-only prefixes instead of requiring an
entire ledger to stay unchanged. It verifies 348 immutable nonledger artifacts,
all historical ledger prefixes, the 861-file archive and every artifact linked
by the cycle-287 receipt, including its failed result and checkpoint. Original
validators, their failure annotation and completed analyses remain unchanged.

Maintenance evaluator SHA-256:
c6865a2443b011943a7ce3a5aad3ba03a594569596a55894528e37cfa88e6d6d.
Execution conformance certificate V3 verifies against this source/test set.
Doctor and integrity pass, now with 868 protected files. This is a maintenance
revision, not a newly activated scoring cohort; a future scored comparison must
receive its new version/identity and prospective authority before registration.

## INTERPRETATION

Bounded recovery addresses the reproduced file-sharing mechanism on both sides.
Short Windows access conflicts no longer necessarily abort the worker/parent;
persistent failures still terminate. The correction does not justify changing
the model or reclassifying EXP-20260905-0001 as a complete learning result.

## CONFIDENCE

High within the tested Windows contention scenarios. The original lock owner
remains unknown. Passing finite stress tests does not guarantee all filesystem,
antivirus, hardware or OS failure modes, nor completion of a future model fit.

## ALTERNATIVE EXPLANATIONS

The crash could have involved another reader or an access restriction not
represented by these fixtures. Permanent permission/I/O errors must remain
visible. Atomic replacement OS latency itself has no hard real-time bound.

The writer retries recognized WinError 5/32/33 for at most one second. The parent
never sleeps inside a failed read: it continues STOP, fit/worker, RSS and storage
checks and fails after one second of continuous read unavailability. CUDA
telemetry has a one-second unavailability threshold plus polling/scheduling
overhead; independent worker allocator caps/checks remain in place. No claim of OS-isolated or
perfectly continuous memory enforcement is made. Retry waits stay inside the
existing measured worker/fit time, and recoveries are recorded in worker logs.

## DECISION

Keep the tested telemetry repair in maintenance. No PC-01 model training, new
EXP registration, final evaluation, architecture promotion, publishing or
schedule change was performed. Historical counts stay at 100 results, one
consumed dev attempt and 1200/7200 charged fit seconds. No old service budget
was reset. Close this single service cycle within its self-imposed 45-minute
limit and return to the user decision gate.

## NEXT DISCRIMINATING EXPERIMENT

If separately authorized: validate a new scored cohort identity/authority and
preregister exactly one fresh dev attempt from initialization with the identical
model, data, seed 1103, 5000-update recipe and 1200/1800 s caps. Test whether the
entire recipe plus end controls now completes. Do not resume the partial
checkpoint, automatically retry, expose final data or tune learning thresholds.
