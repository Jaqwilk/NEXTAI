# GEN-1 — heldout mechanism recombination v1 service cycle 56

## Scope

This was one protected service-only cycle authorized by the standing autonomous objective and the HYP-0021 design decision. No candidate implementation, immutable experiment plan, scoring seed, runner candidate process or scored result was created. No external model/API, dependency or cooldown was added.

## Frozen question and boundary

`heldout_mechanism_recombination_v1` tests whether one learner can induce reusable opaque mechanisms from singleton and ordered-pair training worlds and apply them to the unseen ordered `CB` composition. It does not claim to discover a common ontology from raw heterogeneous worlds.

The evaluator reuses three existing deterministic sources: a behavioral-program transformation table, an action-conditioned predictive transition/outcome function and a nonlinear local-dynamics rule. One frozen numeric normalization and one common Feistel lift map each source onto 144 states. Runner-random scoring seeds apply one global state conjugation, anonymous world shuffle and support/query partitions after runner integrity, candidate-source and registered-baseline checks.

Training compositions are `A/B/C/AA/AB/AC/BA/BB/BC/CA/CC`; `CB` is absent. Every constituent and both order positions appear in training. Public candidates receive only equal-shaped state-to-state pairs. Module/source names, native objects, extraction paths, targets and the composition graph remain evaluator-only.

K is the public support size (`8/32` in quick), D is repeated application depth (`1/4/6`) and Q is the disjoint query count (`8`). Training provides three anonymous worlds per registered composition. Test support and queries are disjoint.

## Protected gates

Six focused cohort/protocol tests and nine existing protocol-v2 tests passed. On five fixed, non-scoring development relabelings at both K values (ten cells):

- actual serialized public training profiles had one identical shape;
- train/held-out composition overlap was zero;
- 48-support and K=`8/32` checks uniquely selected `CB`;
- unigram accuracy ranged `0.0–0.125`;
- the input-conditioned transition-mode upper bound for order-1 through order-5 Markov ranged `0.0–0.25`;
- complete-map nearest-template ranged `0.0–0.375`;
- the privileged module-composition oracle and unique-match count were exactly `1.0` in every cell.

The complete 239-test suite passed before freeze. Future plans are schema-required to include shared, source-identical independent and no-cross-mechanism learners; unigram, order-5 Markov, nearest-template and exact MDL controls; and the privileged graph oracle. The runner now recognizes `mechanism_recombination_protocol` and will reject scoring before seed realization unless every classical control has a semantic registry record, implementation/test hashes and a passing conformance node.

## Full accounting

Future plans must maximize held-out accuracy and minimum-combination accuracy and minimize acquisition, fit, meta-fit/structure search, query, update, resident/peak state, bytes touched, total work and R16 work. The state cap is `4,194,304` bytes and horizons are `1/4/16`. A one-seed quick cannot promote.

## Frozen integrity

- benchmark: `heldout_mechanism_recombination_v1`;
- evaluator SHA-256: `7f6f397484d2313cf61e21fde7df6e26b5f06a6758195c98234274fca81ba89b`;
- candidate bundle SHA-256: `32a251727a844ae433751aa0cf7aba34a3f4b2789b7fc2afa318496969547514`;
- manifest file SHA-256: `455accd44023d13731850a3e090cd5d1e2a96353074d2366f9d3a89b3b4899aa`;
- protected files: 428;
- prior manifest archive: `research/manifests/heldout_parallel_masked_infilling_v2-protocol-v2-79c18b30d131.json`;
- prior archive file SHA-256: `24c6ed602452742e0b77de1593565c0f23839525b1df702ffe71c24a988096d5`.

## Decision and exact next experiment

The evaluator is ready for preregistration, but infrastructure is not evidence and HYP-0021 confidence remains `0.18`. In the next wake, preregister EXP-20260830-0054 quick before implementing any candidate or semantic registry record. Use K=`8/32`, D=`1/4/6`, Q=`8` and one runner-random seed. Include exactly `shared_latent_mechanism_library`, `independent_latent_mechanism_library`, `no_cross_mechanism_factorizer`, `unigram_recombination`, `markov5_recombination`, `nearest_template_recombination`, `exact_mdl_module_library` and `oracle_composition_graph`, with every schema-required quality and full-cost axis. Then implement the smallest shared core and controls, register their semantic hashes/tests, re-freeze only the candidate bundle while preserving the evaluator digest, run all gates and execute exactly one scored quick. A one-seed positive can authorize only a three-seed adversarial screen.
