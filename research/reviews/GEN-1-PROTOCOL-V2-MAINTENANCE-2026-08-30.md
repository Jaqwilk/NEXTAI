# GEN-1 — protocol v2 maintenance, 2026-08-30

## Scope

User-authorized maintenance after the eight-hour portfolio audit. This was not an experiment: no candidate was scored, no completed plan/result/analysis was edited, and no new empirical claim was created. `PAUSE` was installed before maintenance and the concurrent task stopped. EXP-20260830-0036 remains byte-for-byte preregistered and has one append-only invalidation event; it has no result.

## Objective observations

- Durable history contains 36 plans, 35 results and 35 analyses. State reports 35 completed experiments; there is no active or pending plan.
- Before repair, config pointed to `behavioral_conjugacy_library_transfer_v1` while the manifest still committed `latent_entity_binding_retrieval_v1`; `doctor` failed and EXP-0036 exposed the known development/scoring seed `1103`.
- The repository had 184 candidate adapters, many delegating to top-level core modules, while the prior AST audit inspected only the adapter file.
- Configured cadence, replication, seed-CV, promotion and cooldown rules were mostly prose/TOML without executable gates. `STOP` and `PAUSE` were warnings rather than blockers.
- Historical quick cohorts commonly estimated K slope from only two K values, with no point count or regression uncertainty. Oracle candidates could occupy the same Pareto frontier as implementable candidates, and pairwise dominance silently skipped missing axes.
- The modern direct-competitor ledger lacked Mamba, BLT, Titans and Product-Key Memory. Four checked primary records, `SRC-0093` through `SRC-0096`, were appended; the ledger now contains 96 sources, 95 primary.

## Implemented protocol changes

- Hard gates now block `doctor`, plan creation and scoring on `STOP/PAUSE`, active lock, incomplete lifecycle, due reviews, another pending plan, retired benchmark, legacy exposed score seed or cooldown.
- Plans can be invalidated only by an append-only event. Result-bearing plans cannot be invalidated, and an invalidated plan cannot produce a valid lifecycle.
- New plans preregister explicit metric directions, a runner-random seed method/count/range and the evaluator digest. Exact score seeds are realized only after plan validation, integrity verification and transitive candidate audit, then persisted in the result matrix.
- The manifest covers 305 files and publishes separate evaluator and candidate-bundle digests. Candidate-only implementation can be frozen after preregistration while preserving the evaluator commitment; an evaluator change forces invalidation and a new plan. Previous manifests are archived by content hash.
- Candidate audit recursively traverses local imports, hashes all dependencies and rejects evaluator/benchmark/ledger/runner access. The retired active benchmark now imports a data-only `entity_binding_contract` rather than the candidate core.
- Aggregates include fit ops/peak bytes, input ops, comparisons, bytes touched, R1/R4/R16 workload where supplied, minimum cell accuracy, seed count/CV and scaling regression metadata. Fewer than three scale points remain screening-only.
- Pareto uses only preregistered axes measured for every eligible row. Oracle controls are listed separately and can never support promotion. `promising` and `promoted` transitions enforce replicated screen/deep evidence, per-cell capability, seed stability, integrity, analysis, checked primary prior art and implementable non-dominance.
- The report was regenerated under these rules; for EXP-0035 the implementable frontier is `paired_stability_index`, while `oracle_identity_index` is shown only as a lower bound.
- The actual two-hour Codex heartbeat prompt was updated so a gate/integrity failure ends the wake instead of authorizing autonomous protocol repair.

## Verification

- `uv run pytest`: 166 passed.
- Transitive audit: all 184 shipped candidates passed; a fixture proves a forbidden import hidden in a local dependency is detected.
- Gate dry run: attempting to run EXP-0036 was rejected before mutation by PAUSE, retired benchmark, append-only invalidation, legacy fixed seed and cooldown.
- `uv run nextai integrity verify`: 305/305 protected files match; evaluator SHA-256 `1a60f8763ae02470b7f5b3948be02d587c36d4fa1f0f303b5e69fccae341273e`; candidate bundle SHA-256 `80e879da153c4430b2a16518707a5612a9a886fb857028b40db30da0ab2d7877`.
- No experiment budget was consumed. No dependency was added. The host policy rejected `git add`, so an initial Git commit could not be created; repository artifacts and append-only ledgers remain the available history layer.

## Interpretation and confidence

Protocol v2 closes the specific process failures found in the audit and makes accidental continuation in the old configuration impossible. Confidence is `0.99` for the tested software gates and artifact consistency, `0.95` that fixed-score-seed leakage and oracle-front contamination are removed for new v2 results, and only `0.70` that the local cooperative-process boundary prevents all evaluator leakage. It is not an OS sandbox, and Codex can still inspect local benchmark generators; strong scientific claims still require an evaluator it cannot read.

This maintenance improves evidence quality, not the empirical outlook of any architecture. The portfolio still has no replicated learned end-to-end advantage, no promoted hypothesis and no evidence for an LLM successor.

## Decision

`keep` the research program, `discard` the old operational configuration, and hold new scoring until a clean protocol-v2 cohort is prepared. Generation is now `1`, phase `consolidation`, and the last completed benchmark is `retired`.

## Exact next discriminating experiment

Prepare `behavioral_conjugacy_library_transfer_v2` as a new evaluator/contract cohort before any candidate implementation. It must make primitive identities and state encodings independently opaque, use paid target probes, include primitive enumeration, exact semantic graph/MDL, hierarchical Bayesian and product-key/retrieval controls, and treat oracle correspondence/library as lower bounds. Freeze the evaluator digest; preregister a child of invalidated EXP-0036 with runner-random quick seeds and primary full-system axes; only then implement candidate code under `candidates/`, re-freeze the unchanged-evaluator bundle and score once after cooldown. A null or dominated result returns HYP-0002 to dormant without tuning; a positive quick permits only a multi-seed adversarial screen, not promotion.
