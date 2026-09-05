# PC-01-FINAL-PREP-V1 — selected v2 to measured v3, no training

Cycle 291. Immutable plan: research/plans/PC-01-FINAL-PREP-V1.json.
Plan SHA-256: a6e38d7c0afda28ef6e899f09ee0f7055ac0079236ce99ba05e0ff868e8a041f.
The user approved the proposed contract/adapter preparation only. This is a
service cycle, not a registered EXP, model attempt or final-series freeze.
The fixed service deadline is 2026-09-05 16:52:59 UTC, maximum 45 minutes.

## OBSERVATION

Startup doctor and the previous metadata/history validator passed. No STOP,
PAUSE or active experiment lock was present. All 877 previously protected files
were verified and copied into research/laboratory/archive/PC-01-METADATA-CYCLE-290
before edits. Their manifest is research/manifests/PC-01-FINAL-PREP-BEFORE.json.

The exact selected development result remains EXP-20260905-0002, v2, seed 1103,
5000 updates, best dev 2.1919434488637624 bpb. It is not a final replica. Its
missing historical GPU metadata remains missing; no score or artifact was repaired.

Implemented two bounded compatibility changes:

- A read-only transition verifier binds the exact immutable v2 plan/result,
  candidate/audit, recipe, original design, metadata repair receipt and trusted
  source hashes to the current v3 evaluator. It checks that pc01.py outside
  series_decision has an unchanged AST. Actual future series freeze must still
  pass the ordinary authorization, maintenance, certificate, integrity and lock
  gates, and must record both evaluator identities. Changed target evaluation
  after freeze is rejected; v2 numbers are never pooled as final measurements.
- The pure series gate accepts mandatory v3 GPU metadata and validates every
  pair without stripping it. The authenticated gate still binds measurements to
  immutable worker artifacts and all registered outcomes. Legacy v1/v2 schema
  files and quality rules are unchanged. Missing, malformed or mismatched
  metadata, failures, omissions and duplicate seeds cannot yield a positive.

The candidate, worker, runner, telemetry and GPU helper are byte-identical to
the plan's source constraints. No dataset or checkpoint was used by the new
tests. The v3 end-to-end lifecycle uses synthetic process fixtures; policy
activation and selected-source identity are isolated in that fixture, while
the exact real selection bridge is separately checked read-only. This does
not establish production final execution or model replication.

Validation:

- Targeted new tests: 26 passed, 0 failures/errors/skips, 2.821 seconds.
  Report: research/laboratory/PC-01-FINAL-PREP-TARGETED-V1.xml.
- Full regression: 912 passed, 0 failures/errors/skips, 127.011 seconds.
  Report: research/laboratory/PC-01-FINAL-PREP-CONFORMANCE-V6.xml.
  It also exercised the existing read-only GPU metadata probe, without a model.
- New execution conformance certificate: PC-01-EXECUTION-CERTIFICATE-V6.
- Doctor PASS; current integrity 881 files. Historical 348 non-ledger artifacts
  and ledger prefixes verified, previous receipts and complete archives intact.
- Production dev/final registration, actual series freeze and replay remain
  denied; plan registry unchanged. No production final-series artifact exists.
- git diff --check passed. No push, merge, scheduling, download or installation.

Current evaluator SHA-256:
5d298d79cfd398d56c54d95ba457ecfe54cba000dafc38e6759e8e5f2832a08f.
Selected v2 evaluator SHA-256:
bbb174b5f8bab4717c483a4b152e27bdbf5cebc803a37d3aa1b5a88ae1233773.
The validated manifest is research/manifests/PC-01-FINAL-PREP-VALIDATED.json.

## INTERPRETATION

The two known compatibility blockers are addressed without changing the
scientific question or rescuing the development outcome. The preparation
establishes software conformance only. It adds no evidence of learning,
economic advantage, transfer, scaling or superiority over dense LLMs.

## CONFIDENCE AND UNCERTAINTY

High confidence in the exercised local selection/metadata/ledger failure paths
and unchanged thresholds; bounded by synthetic fixtures and this Windows setup.
No actual final replica has run. Runtime success, three-seed learning stability,
and all final quality thresholds remain unverified. Three seeds will quantify
seed variation conditional on one visible corpus, not corpus generalization.
GPU snapshots remain point observations, not continuous energy measurement.

## DECISION

KEEP the prepared contract and adapter; return to PC-01-DECISION. No architecture
promotion, third development attempt or automatic final execution. The rules
files now identify this narrow preparation and its stop-for-decision boundary;
original restart and closed budgets remain immutable.

## INTEGRITY AND BUDGET

101 scientific results and exactly two dev attempts remain. Cumulative fit charge
is unchanged at 1500.4259332000001 / 7200 seconds, including the failed first
attempt's conservative 1200-second charge. Remaining fit capacity is
5699.5740668 seconds. The prospective three-replica reservation is 3600 seconds;
capacity does not grant permission. Benchmark remains v3 / maintenance and
laboratory remains preparation_only, scoring false. Service elapsed time and
free disk at closure are recorded in the hash-linked receipt. No history reset.

## NEXT DISCRIMINATING EXPERIMENT

After a separate explicit user authorization, record a narrowly scoped final
activation (no further dev), validate/freeze its own current evaluator and
certificate, then freeze the actual series using this transition contract.
Execute exactly three fresh pc01_byte_gpt_v1 replicas through the audited runner,
one per bounded cycle, distinct runner-generated seeds, unchanged recipe and
5000 updates, <=1200 fit / <=1800 worker seconds each. Never resume dev best.pt.
Run fresh train-only baselines and frozen controls under v3 for every replica.

Report every outcome. Positive learning requires each trained loss <=3.5 bpb,
each frozen-minus-trained contrast >=1 bpb, and the lower paired 95% t interval
(df=2) strictly >0, with every control and metadata requirement satisfied.
The unigram contrast >=0.1 is secondary. A valid negative closes this tested
version; a crash/integrity failure is inconclusive, not family falsification.
No replacement seeds, omitted outcomes, holdout-guided tuning or automatic retry.
There is no authorization to perform that experiment in this preparation cycle.
