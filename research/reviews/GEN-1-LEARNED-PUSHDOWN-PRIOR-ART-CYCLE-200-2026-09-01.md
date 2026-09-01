# Learned pushdown prior-art review — cycle 200

This cadence-required review closes the same bounded cycle that scored
EXP-20260901-0042. It is analysis of the completed evidence, not a second
hypothesis, plan, seed, benchmark, candidate, or scored experiment.

## Question

Does EXP-0042 expose a new computational principle, or a rigorous instance of
an established stack/grammar-induction mechanism?

## Primary-source findings

Alur and Madhusudan's visibly pushdown automata already formalize exactly the
relevant execution principle: input roles determine push, pop, or internal
transitions, so a finite controller plus stack transfers across nesting depth
(SRC-0203). Stack-augmented recurrent networks were already trained from
sequence examples to operate expandable memory (SRC-0204). Deeper-than-train
Dyck closure prediction is also an established diagnostic; explicit stack
models can approach perfect accuracy while ordinary recurrent networks remain
unreliable (SRC-0205, SRC-0206).

The literature also warns that a closing-bracket metric can overstate grammar
understanding when a model fails exact sequence completion (SRC-0207). NEXTAI's
whole masked closure, zero-bit criterion, finite-state and frozen ablations,
three runner-random seeds, disjoint whole-file source corpus, full operation
accounting, and implementable Pareto test are therefore useful controls, but
they do not create a new automaton class. Recent V-Star work further shows
that observation-driven inference of visibly pushdown structure is itself an
active grammatical-inference topic (SRC-0208).

## Relation to EXP-0042

The replicated observation is real and narrower than a novelty claim. The
unchanged learner inferred anonymous call/return/internal roles from bounded
traces and executed exact closures at unseen depths in every registered cell.
Both source-identical ablations failed, and no implementable control matched
quality. This establishes a robust NEXTAI signature for learned discrete
external memory under the frozen v12 contract.

It does not establish a successor-to-LLM principle, natural-language utility,
novel stack computation, or favorable scaling against dense autoregressive
models. The main role also pays more declared R16 work than Re-Pair, PPM and
CTW; it is Pareto-nondominated only because those cheaper controls are much
less accurate.

## Decision

Keep HYP-0050 `uncertain` at confidence 0.80. Do not mark it `promising` or
`promoted`, and do not tune or combine it. The evidence raises confidence in
the narrow learn-and-execute claim, while the prior-art review sharply lowers
confidence that the mechanism itself is novel.

One final adversarial discrimination is justified: preserve the anonymous
seven-symbol interface but introduce frozen, recoverable stack corruption that
cannot be solved by copying the visible top-of-stack trajectory. This directly
tests whether the induced roles support robust state repair rather than only a
clean visibly-pushdown alias. Because v12 contains valid balanced traces only,
the next wake must be one minimal service-only v13 cohort migration; the wake
after that must score the unchanged learner and controls. A valid negative
makes this exact family dormant. A positive remains screening evidence and
authorizes no promotion without an independent non-synthetic corpus.
