# Scope

This required six-experiment cadence review follows the completed EXP-0036
scout. It changes no result, hypothesis decision, benchmark, candidate or
confidence. It compares the tested exact-search ordering principle with three
primary sources and does not start a second experiment.

# Primary prior art

He, Daume and Eisner (2014, SRC-0200) learn adaptive branch-and-bound node
ordering by imitation over problem families. Khalil et al. (2016, SRC-0201)
learn a cheap ranking surrogate for expensive strong-branching variable
selection and explicitly expose the trade between tree size and work per node.
Gasse et al. (2019, SRC-0202) learn a graph branching policy that transfers from
smaller training instances to larger instances while retaining the exact
branch-and-bound substrate.

These papers establish learned ordering and branching as prior art. EXP-0036
does not support a novelty claim. Its narrower discriminator is whether one
anonymous priority learner beats source-identical support-only and frozen
orders, plus exhaustive MDL, after charging acquisition, fit, state and
R1/R4/R16 query work.

# Relation to EXP-0036

The positive qualitative observation is consistent with prior work: learned
ordering reduced the exact solver's cold node visits and preserved the optimum.
The negative system result is also compatible with the literature's central
cost trade-off: acquisition and fitting outweighed the saved queries at every
declared horizon versus the frozen source-identical solver. The result therefore
falsifies only the preregistered add-one frequency and unique-correct priority
rule on this cohort; it does not falsify learned branching in general.

# Decision

Keep the admissible complete branch-and-bound solver as classical diagnostic
infrastructure. Do not tune or replicate HYP-0047. Do not credit learned search
ordering as a new principle. Any future learned-search proposal would need a
fundamentally different, preregistered mechanism and must demonstrate transfer
and full-cost amortization against source-identical exact controls.

# Exact next step

Cycle 187 remains a minimal no-scoring aggregation-completeness service cycle:
carry every declared plan-primary metric into complete summaries and reject
summary incompleteness before Pareto computation, without recomputing EXP-0036.
Cycle 188 must score a fundamentally different breadth mechanism on an existing
frozen cohort.
