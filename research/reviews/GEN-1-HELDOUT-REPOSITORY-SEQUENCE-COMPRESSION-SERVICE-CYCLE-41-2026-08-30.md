# Held-out repository sequence compression: evaluator service gate

## Scope and decision before implementation

This is a protected, no-scoring service cycle after `EXP-20260830-0043`. It may create a hypothesis and freeze an evaluator, but it must not create an experiment plan, candidate implementation, scoring seed, or result. The next scientific cycle may preregister `EXP-20260830-0044` only if every gate below passes. No global cooldown exists or is introduced.

The discriminating question is whether a bounded, hierarchical sequence learner can reuse motifs learned from whole training files to improve prequential byte probabilities on whole held-out files, rather than solve another synthetic generator. A win against only uniform, unigram, or fixed n-gram is uninformative.

## Immutable corpus and leakage boundary

- Corpus source: existing local UTF-8 Markdown and Python source files only; no downloads, research plans/results/logs, candidate adapters, benchmark evaluators, caches, generated artifacts, or files changed by this service cycle.
- Eligibility was fixed before evaluator implementation: top-level `AGENTS.md`, `program.md`, `README.md`, `docs/*.md`, and top-level `src/nextai_autoresearch/*.py`; at least 1,500 bytes; explicit infrastructure exclusions are frozen in the evaluator.
- Role is derived once from the pre-implementation file SHA-256: first hash byte modulo 10 gives train 0–6, validation 7, test 8–9. Exact role, length, path, and SHA-256 are embedded in protected evaluator source.
- Frozen inventory: 43 files / 367,083 bytes: train 33 / 296,514 bytes, validation 5 / 28,171 bytes, test 5 / 42,398 bytes. Exact duplicate hashes: 0. Maximum cross-role containment of nonblank lines of at least 20 characters: 0.1538; maximum cross-role line Jaccard: 0.0647. This is not a semantic-deduplication guarantee and must be reported as a limitation.
- Every corpus hash and byte length is checked before a trial. Any mismatch invalidates the cohort. Splits are whole-file; no fragment of a test file enters fit or validation.
- A non-oracle candidate receives only anonymous byte tuples supplied by the evaluator. It cannot read the filesystem, paths, roles, hashes, file names, extensions, test offsets, future bytes, or another test slot's state.

## Frozen public contract

- `knowledge_size` means an offline training budget in KiB. Bytes are allocated deterministically and round-robin across train files. A separate validation allowance of `min(4096, knowledge_size * 128)` bytes is supplied only for preregistered fit-time selection.
- `reasoning_depth` is the maximum raw byte-history length supplied with each query. No tokenization, AST, ontology, path label, or benchmark-specific feature is supplied.
- For every held-out file, the runner seed selects one contiguous segment after enough context. Segment length is `queries_per_cell * 128` target bytes. A fresh anonymous slot is used per file.
- Evaluation is strictly predict-then-reveal: query a 256-way byte distribution, score the true byte, then call `update` for that slot. Slow/shared fit state must remain frozen during test; update may change only bounded slot-local state.
- Probabilities must be finite, nonnegative, and have positive mass. The evaluator normalizes them and floors the scored probability at `2^-52`; malformed outputs fail the candidate.
- A privileged oracle, if used, is reported outside the implementable Pareto front and may receive the current test file. No implementable candidate receives that envelope.

## Metrics and full-system boundary

Primary capability is mean held-out `bits_per_byte`; secondary gates are `worst_file_bits_per_byte`, first-128-byte `cold_bits_per_byte`, and top-1 byte `accuracy`. Lower is better for all bit metrics. Uniform coding is 8 bits/byte.

Every trial reports and Pareto analysis may charge:

- acquisition: all bytes read for corpus hash verification, train/validation selection, and held-out segment construction;
- offline fit and any validation/meta-selection operations;
- every probability query and every revealed-byte update;
- mean bytes touched, resident state and peak state;
- full workloads at R1, R4, and R16: acquisition + fit/meta-fit + updates + repeated query work. State is a separate Pareto axis.

Wall time is diagnostic only. Operation counts are implementation-reported estimates and must be labeled as such.

## Required controls and outcome policy

The first quick must compare one unchanged hierarchical learner with uniform byte, empirical unigram, variable-order PPM, context-tree weighting, LZ-style dictionary prediction, and a small dense autoregressive control. An empirical full-file test oracle is privileged and cannot establish implementable success. Existing `SRC-0054`, `SRC-0108`, and `SRC-0109` make dictionary parsing, PPM, and CTW mandatory nulls.

Screening success requires all of the following on unseen files: lower mean and worst-file bits/byte than every implementable baseline by at least 0.05 bits/byte; lower cold bits/byte than the strongest baseline; no benchmark-specific branch or manual ontology; and implementable Pareto non-dominance when acquisition, fit/meta-fit, query, update, R16 workload, and state are charged. One scoring seed can only justify `replicate`, never promotion.

The result is negative if PPM, CTW, LZ, or the small autoregressive control matches or dominates the hierarchical learner, if improvement appears only after local test updates while cold transfer does not improve, or if the state/cost advantage disappears at R16. It is inconclusive if a required baseline fails, corpus integrity changes, any split leakage is found, or the evaluator cannot enforce the public boundary.

## Seed and invalidation policy for the next cycle

The immutable plan must use `runner_random_v1`; the scoring seed is unavailable during candidate implementation. It selects only anonymous test slots and segment offsets, never the frozen train/validation/test roles. Any candidate tuning after observing scoring output invalidates the plan.

Additional invalidation conditions: corpus hash or length mismatch; test bytes, paths, file labels, offsets, future bytes, or privileged metadata reaching an implementable candidate; shared test-state mutation across slots; post-score parameter changes; missing PPM/CTW/LZ/autoregressive control; state-budget breach; evaluator digest change; or bypassing `uv run nextai run --plan`.

## Known limits

This is a small, visible, single-repository screening corpus, not evidence of language understanding or a successor to LLMs. File style and shared project boilerplate can create residual train/test similarity. Strong claims require a larger immutable multi-repository holdout that the research agent cannot inspect and replication across at least the configured seed count.

