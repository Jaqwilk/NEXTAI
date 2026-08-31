# GEN-1 — cross-file grammar-library design gate, cycle 63

## Scope

This was one literature/design-only cycle after the cycle-62 natural-corpus rejection. It created no hypothesis, experiment plan, candidate, scoring seed, runner invocation, result, dependency, external model/API or protected evaluator change. The active `heldout_mechanism_recombination_v2` cohort remains unchanged.

The audited proposal was an anonymous cross-file byte grammar library: induce reusable nonterminals from training files, retain one shared library, then use it unchanged for chronological next-byte prediction in an unseen file. The intended novelty was transfer through reusable hierarchical productions rather than benchmark-specific rules or complete-example retrieval.

## Primary prior-art boundary

The proposed operation is already occupied by several strong classical families.

- SEQUITUR incrementally replaces repeated phrases with recursively reusable grammar rules, enforces digram uniqueness and rule utility, and runs in linear time and space.
- Re-Pair greedily replaces the most frequent adjacent pair and builds a straight-line grammar/dictionary for the complete input.
- Kieffer and Yang formalize grammar transforms whose deterministic grammar uniquely represents the source string and prove universal coding results for finite-state sources under stated restrictions.
- Their sequential follow-up constructs irreducible grammars incrementally and combines the transform with arithmetic coding, so adding chronological operation is not by itself a new mechanism.
- Adaptor grammars supply a genuinely probabilistic cached-subtree mechanism through PCFGs and Pitman-Yor adaptors, but require a declared base grammar and general posterior inference. On raw bytes, a hand-written base grammar can carry the ontology; an unrestricted base grammar leaves a large ambiguous structure-search problem whose acquisition, inference and state costs must be charged.

Consequently, “learn reusable nonterminals across files” is not a distinct scientific hypothesis. It becomes distinct only after specifying a probability model, legal update rule and transfer signature that a source-identical sequential grammar code, Re-Pair/SEQUITUR dictionary, PPM-D, CTW and LZ cannot reproduce.

## Manual semantic discriminator

Consider anonymous training strings `abxabxabx` and `abyabyaby`, followed by an unseen test string beginning `abzabz...`. A shared-library learner can name `ab` as a reusable nonterminal, but so can SEQUITUR, Re-Pair and ordinary dictionary compressors. Replacing the strings with nested repetitions or holding out a recombination of two phrases does not fix the problem: straight-line grammar transforms recover the same repeated substrings, while a supplied production topology would be a hand-written ontology.

The prediction boundary creates a second, independent gate. For target position `t`, a legal predictor may inspect only training files and the revealed prefix `x[:t]`.

1. A batch grammar `G(x[0:n])` derived from the complete test file leaks future bytes and is invalid.
2. A prefix-only code-length construction can evaluate every byte `a` by transforming `x[:t] + a` and normalizing `2**(-delta_length(a))`. This is legal, but requires up to 256 grammar transforms per query, is exactly a universal-code baseline rather than a new learner, and must charge all transforms.
3. An incremental grammar dictionary such as SEQUITUR does not by itself define calibrated next-byte probabilities. Attaching symbol/rule probabilities creates a separate probabilistic model that must specify normalization, rule selection, escape behavior and update order.
4. An adaptor grammar can define probabilities, but without a learned and evaluator-hidden base grammar the test either embeds the solution in the grammar or reduces to generic Bayesian grammar induction. That is established prior art and is not a small isolated intervention.

Thus the proposed fixture cannot distinguish the intended learner from classical grammar induction. The failure occurs before implementation and is not evidence that hierarchical structure is useless.

## Decision

`reject-before-hypothesis`. Do not create HYP-0022, an evaluator migration or EXP-0057 for the cross-file grammar-library proposal. The current description collapses into existing grammar/dictionary compression controls, and its only immediate route to next-byte probabilities is either future-byte leakage, a costly universal-code construction, or a new probabilistic grammar whose ontology and inference semantics are unspecified.

Confidence in this design rejection is `0.93`. Uncertainty remains about whether a future learned stochastic grammar with an ontology-free base prior and tractable exact filtering could show transfer; that is a materially different hypothesis and would require its own prior-art and identifiability gate.

## Exact next discriminating step

Use the next wake for an early generation-transition audit with no scoring. Reconstruct all valid protocol-v2 cohorts and compute, per cohort, the strongest implementable baseline accuracy, oracle gap, best candidate gap, minimum subgroup/family accuracy, full-cost dominance and whether public observations identify the task or family. The audit must separate architecture failures from benchmark ceilings and routing leakage. Start generation 2 only if it identifies a frozen or safely versionable task with all four properties: a nontrivial implementable-baseline gap, hidden OOD structure, no supplied ontology/task label and an exact end-to-end cost boundary. Otherwise record that the current benchmark portfolio cannot discriminate a successor principle and design a new evaluator only after explicit protected-migration approval.
