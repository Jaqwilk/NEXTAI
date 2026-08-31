# GEN-1 — natural-corpus shared-density design gate, cycle 62

## Scope

This was one design/audit-only cycle after the cycle-61 cross-family identifiability rejection. It created no hypothesis, experiment plan, candidate, scoring seed, runner invocation, result, dependency, external model/API or protected evaluator change. The active `heldout_mechanism_recombination_v2` cohort remains unchanged.

The audited proposal was to reuse the two existing immutable whole-file corpora and ask whether documentation, implementation and test files could form three anonymous natural domains for one common predictive-density learner spanning next-byte compression and masked conditional prediction.

## Corpus reconstruction and separation

Both frozen corpora remain exactly reconstructable from the current workspace. All `43/43` compression entries and `48/48` masked-infilling entries exist and match their registered byte lengths and SHA-256 digests. The corpora have zero path overlap and zero expected-hash overlap.

The combined `91` files yield three path-defined evaluator-only domains:

- documentation: `14` files (`11` train, `2` validation, `1` test);
- implementation: `57` files across both corpora (`41` train, `7` validation, `9` test);
- tests: `20` files (`16` train, `0` validation, `4` test).

There are enough files for three names, but the support is strongly imbalanced and the documentation test boundary contains only one file. Creating a new split could improve balance only by changing protected roles and therefore would be a new cohort, not reuse of the historical evidence.

Cross-domain duplicate leakage is not the limiting defect. Exact paths and hashes are disjoint. After removing blank and shorter-than-eight-byte lines, maximum cross-domain line Jaccard is `0.026549`; maximum containment is `0.075`. The strongest pair for Jaccard shares only three lines.

## Domain-router gate

A length-free content profile was computed for every file: its normalized 256-byte histogram. Leave-one-file-out nearest-centroid classification used Hellinger distance and no path, extension, role, length or file name. It classified all `91/91` files correctly. Per-domain recall was `1.0` for documentation, implementation and tests; balanced accuracy was `1.0` against chance `0.333333`.

Thus equalizing file length or hiding paths cannot remove domain identity. Syntax alone provides a perfect implicit router. A pooled learner may implement three specialists internally without demonstrating a transferable representation. This is natural domain structure rather than duplicate leakage, but it defeats the preregistered claim that success must be distinguishable from hidden domain routing.

## Query-boundary gate

The existing tasks do not expose one source-identical query contract. Compression uses `ByteContext(slot, history)` and chronological predict-then-reveal updates. Masked infilling uses `MaskedQuery(slot, snapshot, masked_positions, round_index, maximum_rounds)`, predicts multiple interior positions and never receives truth. Attribute presence, arity and mask geometry identify the task perfectly before any content is inspected.

A generic conditional-density API could encode both as observed positions plus target positions, but constructing it would be a new protected evaluator. Next-byte targets would remain suffix masks while infilling targets remain interior spans, so query geometry would still be a task tag unless the scientific question changed. Actual CTW, PPM and autoregressive controls also require different conditionalization semantics across the two tasks. Reusing their names without new semantic fixtures would repeat the invalid-control defect repaired after EXP-0047.

## Decision

`reject-before-migration` for a combined next-byte/masked multi-task cohort over the current corpora. The failure is not insufficient files or duplicate contamination; it is perfect observable domain/task identification plus incompatible update boundaries. Do not create EXP-0057, do not merge the two evaluator APIs, and do not treat file categories as evidence of shared latent representation.

This result does not say pooled models cannot be useful on mixed natural corpora. It says this proposed experiment cannot distinguish reusable representation from implicit routing while also preserving the existing task semantics.

## Exact next discriminating step

Use the next wake for one literature/design-only cycle with no scoring. Evaluate a genuinely different real-data principle: an explicit cross-file byte grammar library learned once from anonymous whole files and queried only through the existing chronological next-byte density boundary. This is not a continuation of HYP-0016's validation-weighted context mixture; the candidate mechanism must induce reusable nonterminal productions and expose a derivation trace. Compare it with a source-identical no-cross-file grammar ablation, actual Sequitur/Re-Pair or equivalent grammar controls, PPM-D, CTW, LZ and dense autoregressive prediction under full acquisition, grammar search, fit, query, update, bytes, state and R16 costs.

Before creating HYP-0022 or changing protected infrastructure, the design gate must establish from primary literature that the proposed operation differs from classical grammar compression, specify a semantic fixture where reusable nonterminals transfer to an unseen file without complete-example retrieval, and show how online next-byte probabilities are derived without future-byte access. If the learned rule collapses to Sequitur/Re-Pair, cannot produce calibrated probabilities, or requires file/domain labels, reject it without an evaluator. A valid protected migration would still require explicit user approval in a later wake.
