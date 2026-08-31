# Codex-native architecture

## Control flow

```text
Codex scheduled wakeup in this chat
             |
             v
   AGENTS.md + program.md
             |
             v
 hard gates -> doctor -> observe ledger -> select one question
             |
             v
 immutable preregistration + blinded seed policy
             |
             v
 candidate dependency graph -> transitive AST audit -> runner seed reveal
                                              |
                                              v
                                    sanitized child process
                                      | timeout / RSS monitor
                                      v
                         protected benchmark + oracle
                                      |
                                      v
                         append-only result + TSV
                                      |
                                      v
                  Codex scientific analysis and update
```

There is deliberately no API client or separate model. Codex supplies open-ended scientific judgment; the local package supplies deterministic bookkeeping and measurement.

## State machine

```text
PROPOSED -> PLANNED -> RUNNING -> COMPLETE -> ANALYZED
                 \-> INVALID / CRASH / TIMEOUT

hypothesis:
proposed -> testing -> uncertain -> promising -> promoted
                    \-> dormant / falsified
```

Plans do not change status in place because that would mutate preregistration. `plan_status_events.jsonl` records append-only invalidation; runtime state and results record the remaining transitions. Hypothesis revisions are new JSONL events.

## Trust boundaries

### Codex policy boundary

`AGENTS.md` and `program.md` constrain research behavior across scheduled runs. They are procedural controls, not an OS security boundary.

### Harness integrity boundary

`research/eval_manifest.json` stores SHA-256 hashes of the whole harness/candidate Python tree, tests, schemas, lockfile, configuration and scientific contract. It publishes separate evaluator and candidate-bundle digests. A v2 plan commits the evaluator digest before candidate implementation; a candidate-only re-freeze preserves that commitment, while an evaluator change forces invalidation. `doctor` and `run` verify the bundle before and after scoring. Overwrite first archives the old manifest by content hash.

### Candidate process boundary

Candidate code is:

- restricted to one conventional module interface;
- recursively checked across local imports for allowlisted imports, forbidden builtins and evaluator-boundary access;
- launched in a child process with a sanitized environment;
- monitored for wall time and process-tree RSS;
- logged without flooding Codex context.

This catches common mistakes and discourages leakage. On this Windows host it is **not** a hardened sandbox. Docker is not installed, and process isolation alone cannot stop malicious code. The threat model assumes a cooperative Codex following repository rules. Untrusted third-party candidates require Windows Sandbox, a VM or a container runtime.

## Durable files

- `research/state.json`: one small mutable pointer to current progress;
- `research/hypothesis_events.jsonl`: append-only belief revisions;
- `research/plan_registry.jsonl`: immutable plan hashes;
- `research/plan_status_events.jsonl`: append-only invalidations;
- `research/plans/*.json`: preregistrations;
- `research/results/*.json`: raw trials and aggregates;
- `research/experiments.tsv`: compact append-only index;
- `research/analyses/*.md`: Codex interpretation;
- `research/reviews/*.md`: periodic portfolio reflection;
- `research/sources.jsonl`: checked prior art.

Git provides a second history layer. Failed candidate code may be retained as a commit or source artifact; it is never erased from the scientific ledger.

## Concurrency

An atomic `research/run.lock` prevents overlapping scored runs. `STOP/PAUSE`, pending-plan, analysis/report completeness and review cadence are hard gates. A stale lock is archived rather than silently deleted.

## Benchmark versioning

Thirty-five completed v1 experiments and their manifests remain immutable historical cohorts. The last completed cohort, `latent_entity_binding_retrieval_v1`, is now `retired`. Its shared evaluator data types were separated into `entity_binding_contract.py`; the active benchmark boundary may not import candidate `*_core` modules.

There is intentionally no active scoring cohort during protocol-v2 consolidation. A new benchmark must be identifiable, use contract-only evaluator interfaces, establish public development checks, preregister runner-random scoring seeds, rerun strong implementable baselines and oracle lower bounds, and freeze a new manifest before scoring.
