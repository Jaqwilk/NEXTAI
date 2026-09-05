# PC-01-POSTRUN-TELEMETRY-MAINTENANCE-V1

Authority:
`research/laboratory/PC-01-POSTRUN-TELEMETRY-MAINTENANCE-20260905-V1.json`.
Immutable no-scoring plan:
`research/plans/PC-01-POSTRUN-TELEMETRY-MAINTENANCE-V1.json`, file SHA-256
`aeae17450dbd4e1b30e09d133013e5f33db6e761608044049618a81b30be02d1`.
The plan and authorization were committed and pushed as `4e2632a` before the
prospective V2 source was implemented or tested.

## OBSERVATION

The prospective source
`research/laboratory/versions/PC-01-TELEMETRY-V2/pc01_telemetry.py`, SHA-256
`fe116cd65ff93e6234ca326ba6e51508345a25f588ce07a27de91b50a86b54ed`,
adds one read-side classification: `FileNotFoundError` returns `None` for the
existing bounded parent-side unavailable-gap policy. Its writer function is
AST-identical to frozen V1.

The dedicated report, SHA-256
`d4baf947724a31959cc2e97727ae22e644071dd328a3ba43116f556db555a2fa`,
passed all eight controls: exact valid reads; transient absence; recovery after
absence; the one-second persistent-absence boundary; malformed JSON and schema
rejection; registered Windows sharing-error handling; and rejection of an
unrelated permission error.

Three independent subprocess-reader stress repetitions each completed 2000
atomic writes. They recorded 10913, 10548 and 10297 coherent monotonic reads in
10.658, 10.580 and 10.624 seconds. Writer retries were 146, 138 and 136. No
reader crashed and no temporary file remained. The hashes of all three final
PC-01 results and the authenticated `positive_control_pass` decision were
revalidated unchanged.

The separately preserved full regression ran 927 tests in 129.021 seconds and
reported one failure, zero errors and zero skips. The failure was again
`test_concurrent_reader_and_two_thousand_device_writes`, this time repetition
1, because the unchanged frozen V1 reader propagated `FileNotFoundError`.
Its report SHA-256 is
`7dfbd16b6ebaad34fef2e5a91303289f5573dbb447386fc668447ea873d90c1f`.

## INTERPRETATION

The causal V2 change is sufficient for the dedicated reproduction: it preserves
coherent samples, writer behavior and fail-closed validation while tolerating
the observed transient path absence. The repeated failure of V1 independently
confirms that the cycle-294 observation was not a one-off test artifact.

The maintenance stage nevertheless fails its preregistered all-regression-green
condition. V2 is a validated prospective artifact, not the active frozen PC-01
runtime. Integrating it or changing which version the live regression exercises
would require a separate provenance-aware lifecycle migration; doing that after
seeing this result would exceed this plan.

## CONFIDENCE

High confidence that V2 handles the specific reproduced exception and that V1
does not. Confidence is supported by deterministic fault injection plus 6000
real atomic writes and more than 31000 valid concurrent reads. This does not
prove all filesystem behaviors on other Windows versions or network filesystems.

## ALTERNATIVE EXPLANATIONS

Antivirus, filesystem load or Windows replacement semantics may affect the
frequency of the missing-path window, but they do not explain away the exact
uncaught exception. A fixture startup race is unlikely: every reader starts only
after an initial sample exists and the parent waits for its ready signal. The
V2 success cannot be attributed to changing the writer because its function AST
is identical. A future passing V1 rerun would only demonstrate intermittency.

## DECISION

INCONCLUSIVE for repository-wide maintenance completion; KEEP V2 as a validated
prospective repair. Do not mark the full suite green, mutate frozen V1, rerun
PC-01 training, change the series verdict, or begin WT-01 scoring.

## INTEGRITY AND BUDGET

No model execution, scoring, final-data access, dependency installation,
download, schedule change or budget reset occurred. Frozen V1 remains SHA-256
`4b998b96132011b3f8359cfcce9cd315bca4d474432c40907a4ba6b7f75ad209`.
The three final result hashes and all completed plans/results remain unchanged.
The stage stayed within its 45-minute service window.

## NEXT DISCRIMINATING EXPERIMENT

Request a new, bounded no-training lifecycle migration. Before changing an
active source or test, bind the completed V7 bundle to its exact Git/archive
bytes and prove historical series verification no longer depends on today's
path contents. Then integrate the already tested V2 reader under a new execution
identity, retain a deterministic historical V1 failure fixture, run the V2
concurrency controls and require a genuinely zero-failure full regression.
Only a passed migration may clear the infrastructure caveat and allow WT-01
contract preparation; it does not authorize WT-01 scoring.
