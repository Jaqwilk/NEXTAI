# Parallel masked infilling — service cycle 43

## Scope

This is a protected service-only cycle for HYP-0017 after the valid negative EXP-0046. No candidate implementation, immutable experiment plan, scoring seed, runner call or scored result is created. The purpose is to decide whether simultaneous masked refinement has an auditable signature distinct from another sequential decoder or a classical finite-order smoother.

## Frozen disjoint corpus

`nextai_disjoint_masked_corpus_sha256_v1` contains 48 existing Python benchmark/test files and 305,106 bytes: 35 train, 4 validation and 9 test files. Every row records its whole-file byte length and SHA-256 in the evaluator. No path occurs in the 43-file EXP-0044 corpus, and all 48 hashes are unique.

Cross-role near-duplicate analysis over normalized nontrivial lines found maximum Jaccard `0.2258` and maximum containment `0.4375`, caused by shared benchmark boilerplate. This is disclosed rather than silently filtered. The split remains local and visible screening evidence; it cannot support an independent holdout claim.

The runner-realized seed generates one permutation of all 256 byte values and applies it consistently to selected training, validation and test bytes. It also chooses anonymous slots, test-file order and mask offsets. Paths, roles, offsets, original byte identities and uncorrupted target spans are evaluator-only.

## Identifiability gate

An exact lookup using four public bytes on each side covered `65.42%` of eligible test positions and correctly predicted `98.84%` of covered positions, for `64.67%` overall single-byte accuracy. It therefore supplies a strong classical null but does not exactly determine all individual bytes, much less complete 8/32/128-byte spans. The task is probabilistically identifiable through conditional bits per byte, while exact-span accuracy remains a deliberately hard secondary metric.

The benchmark would have been rejected if this fixed context solved every target, if all models were effectively uniform, or if a public query needed target metadata. None of those rejection conditions occurred.

## Auditable simultaneous-round semantics

A public `MaskedQuery` contains only an anonymous slot, one immutable corrupted snapshot, the positions still masked, and current/maximum round indices. One call returns a 256-way distribution for every currently masked position. The evaluator validates the entire batch before changing the snapshot, so no distribution within a round can observe another prediction from that round.

Between rounds the evaluator ranks predictions by confidence and fills `ceil(remaining / rounds_left)` positions with the candidate's own argmax values. Truth is used only for evaluator-side loss/accuracy and is never revealed to an implementable candidate. The one-pass ablation is forcibly evaluated in exactly one round even in D=4/6 cells.

Span lengths `8/32/128` are independent of registered rounds `1/4/6`, ensuring `L > R`. Reported critical path adds candidate-declared internal sequential depth and logarithmic confidence-selection/reveal depth. Total work separately charges every returned position-probability, normalization/validation, confidence ordering and reveal. Source audit remains necessary because no Python interface can mechanically prove that candidate internals contain no hidden sequential loop; such a loop invalidates rather than scores the candidate.

## Mandatory comparisons and boundary

The future cohort requires uniform and unigram sanity controls, left-to-right PPM, context-tree weighting, a small dense autoregressive model, exact finite-order bidirectional Markov inference, parallel fixed Markov belief propagation, the same masked learner in forced one-pass and iterative modes, and a privileged conditional oracle. Missing PPM, CTW, dense AR, bidirectional Markov or parallel BP makes the plan schema invalid.

Primary quality must include mean and worst-span conditional bits per byte plus exact-span accuracy. Cost includes corpus verification, byte relabeling, train/validation allocation, corruption, fit/meta-selection, every position-round distribution, confidence sort/reveal, bytes touched, resident/peak state, critical path and R1/R4/R16 workloads. The generic `0.95` top-1 filter is disabled only for this loss cohort; Pareto selection uses its registered loss/quality axes instead.

Quick success must beat every implementable control by a preregistered bits-per-byte margin, strictly improve over the one-pass ablation, avoid a worst-span collapse, keep critical depth bounded as span length grows, and remain implementably non-dominated. One runner seed can only discard or authorize a three-seed new-corpus screen.

## Service decision and next experiment

The identifiability, leakage and simultaneity gates pass for a screening evaluator. Freeze `heldout_parallel_masked_infilling_v1` now, with no candidates present. HYP-0017 remains `proposed` at confidence `0.16`; evaluator construction is not positive evidence.

Next wake: preregister `EXP-20260830-0047` quick with K=`8/32`, D=`1/4/6`, Q=`8`, spans `8/32/128`, one runner-random seed and primary axes mean/worst-span bits per byte, exact-span accuracy, critical path, R16 work and state. Only after immutable registration implement the smallest shared masked learner and all mandatory controls. Do not tune corpus, spans, contexts, reveal fraction or control orders after any scoring output.
