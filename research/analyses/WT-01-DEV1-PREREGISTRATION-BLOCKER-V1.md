# WT-01-DEV-1 preregistration blocker

## Experiment and immutable plan

- Experiment ID: `EXP-20260905-0006`
- Immutable plan: `research/plans/EXP-20260905-0006.json`
- Registered canonical plan SHA-256: `d20dc0b70255bee2fefab87c9fd32c87f308e19f7fc20478085131504e17b6a7`
- Terminal status: append-only invalidated before seed realization

## OBSERVATION

The prospective WT-01 integration passed 949/949 tests, integrity over 907
protected files and doctor before plan creation. Creating the first post-PC-01
plan correctly appended one record to `research/plan_registry.jsonl`. The next
doctor call failed in `pc01_closure.closure`: the historical closure lists that
append-only registry under `current_immutable_evidence` and compares the current
whole-file SHA-256 with the terminal PC-01 snapshot. A valid append therefore
appears as mutation of historical evidence.

No `experiment_scoring_started` event exists for this experiment. No scoring
seed was realized, no candidate worker started, no WT data array was loaded, and
files 8-9 were not opened. The plan was invalidated at 2026-09-05T21:01:07Z.

## INTERPRETATION

This is a lifecycle/ledger contract defect, not evidence for or against the WT
mechanism. The immutable historical prefix should remain byte-identical while
well-formed later JSONL records are allowed to append. Altering the closure code
after preregistration would change the frozen evaluator digest, so executing the
registered plan would violate evaluator immutability.

## CONFIDENCE

High. The failure is deterministic, occurs before seed realization, names the
exact file, and follows directly from the whole-file hash comparison in
`src/nextai_autoresearch/pc01_closure.py`.

## DECISION

Invalidate `EXP-20260905-0006`; do not score, tune, retry or register a
replacement under the consumed one-registration authority. Return the benchmark
to maintenance and request a separate user decision.

## INTEGRITY AND BUDGET

- Scoring runs: 0/1
- Runner-random seeds realized: 0/1
- Development arrays loaded: no
- Files 8-9 opened: no
- Candidate workers started: 0
- Development compute attempt used: 0
- Experiment registrations used: 1/1

## NEXT DISCRIMINATING ACTION

Under a separate explicit authority, make one no-scoring correction that treats
`research/plan_registry.jsonl` as an append-only prefix: authenticate the entire
PC-01 historical prefix from Git, parse and validate every later JSONL record,
and reject any changed/deleted/reordered historical byte. Add positive append and
negative prefix-mutation tests, run full regression, freeze a new evaluator and
preflight certificate, then stop again. A further explicit replacement-run grant
is required because this authority allowed only one registration.
