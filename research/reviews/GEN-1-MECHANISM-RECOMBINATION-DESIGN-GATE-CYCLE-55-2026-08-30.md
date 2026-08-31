# GEN-1 — held-out mechanism recombination design gate, cycle 55

## Scope

This was one design/service-only cycle after the cycle-54 identifiability rejection. No evaluator, candidate implementation, immutable experiment plan, scoring seed, runner process, scored result, external model/API or dependency was created. The active benchmark and protected manifest were not changed.

The cycle tested whether a narrow, honest recombination question can reuse three existing NEXTAI mechanisms while removing family-shape routing and complete-example shortcuts.

## Common mechanism contract

Three existing deterministic mechanisms are used:

- one 12-symbol transformation table from `behavioral_conjugacy_library_transfer_v1`;
- one action-conditioned transition/outcome function from `action_conditioned_predictive_equivalence_v1`;
- one local transition function from `nonlinear_local_state_transfer_v1`.

One fixed numeric normalization converts each source behavior to a function on twelve symbols. The same Feistel lift converts every function to a permutation on 144 states. Ordered composition is ordinary function composition. A single seed-derived permutation conjugates all module maps, so public state IDs are opaque while algebraic composition is preserved.

This is not a claim that the raw four-family representations share a latent ontology. The evaluator-specific extraction is privileged data generation; implementable candidates receive only anonymous state-to-state examples with identical shapes. The scientific claim is deliberately restricted to discovering and reusing opaque mechanisms after a common behavioral interface exists.

## Factorial coverage and holdout

Training contains the three singleton mechanisms and eight ordered pairs: `AA, AB, AC, BA, BB, BC, CA, CC`. The ordered pair `CB` is held out. Every constituent and both order positions occur in training, but the exact ordered test combination does not. Three equal 48-example partitions cover every training composition map. Test support has 48 examples and queries use a disjoint 48-state subset.

All worlds expose the same state alphabet, input/output arity, support size and query size. Module names, source families, native objects, extraction paths and the composition graph are evaluator-only.

## Development gate results

The deterministic audit `research/audits/mechanism_recombination_gate_v1.py` has SHA-256 `d9d95bb75e93d41ff6cc558cd581f09c9623522c0b94b76fb429eaee432afd9b`. It ran twice identically on fixed seeds `1103, 2207, 3301, 4409, 5519, 6607, 7717, 8821`.

- train/test combination overlap: `0/8`;
- shape-only classification: `0.090909`, exactly the `1/11` training-composition chance level and below chance plus `0.10`;
- behaviorally distinct maps: `12/12` on every seed;
- maximum unigram accuracy: `0.020833`;
- maximum order-1 through order-5 Markov accuracy: `0.104167`;
- maximum complete-map nearest-template accuracy: `0.25`;
- module-composition oracle accuracy: `1.0` on all eight seeds;
- the 48 support pairs uniquely selected the held-out `CB` composition on all eight seeds.

The gate is local visible development evidence, not scored evidence and not a positive result for a future learned candidate.

## Remaining risks

- The common interface is supplied by the evaluator. A future result supports reusable opaque mechanism induction, not spontaneous discovery of a shared representation from raw heterogeneous worlds.
- The exact MDL module-library control may solve the task more cheaply and Pareto-dominate any learned factorizer. It is mandatory, not an oracle.
- The Feistel lift and 144-state alphabet may make finite structure search easy. This is useful as a falsification screen but cannot support an LLM-successor claim.
- Fixed development seeds and visible audit code require runner-random state relabeling, support partitions and a disjoint scoring-seed path in the frozen evaluator.
- Shape balance must be tested from actual frozen public dataclasses, not inferred from this prototype.

## Decision

`keep` the narrow mechanism-recombination question and create HYP-0021 at low confidence. The design gate proves that the question is mechanically distinguishable from the named simple shortcuts. It does not authorize a plan or scoring yet.

## Exact next discriminating step

Use the next wake as one protected service-only cycle to implement and freeze `heldout_mechanism_recombination_v1`, not a candidate. The frozen evaluator must reproduce the eight-seed gate, derive scoring worlds only after runner seed realization, use runner-random 144-state conjugation and partitions, expose identical public shapes, enforce zero combination overlap and register the exact MDL module library, order-5 Markov, unigram, nearest-template, source-identical independent/no-sharing ablations and privileged graph oracle as mandatory future controls. Add schema requirements for overall and minimum-combination accuracy plus acquisition, structure search/meta-fit, support fit, query/update, bytes, resident/peak state and R16 work. If actual public serialization reintroduces shape leakage or any simple control becomes exact, do not freeze.
