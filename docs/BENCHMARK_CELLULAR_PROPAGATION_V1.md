# Cellular propagation v1

This quick cohort isolates update scheduling. The synchronous and event-driven
candidates learn the same three-weight local AND rule from the complete four-case
truth table. Tasks propagate activation through two short lanes embedded in a dense
K×K dormant grid. One broken lane must be tolerated; two aligned breaks must block
the signal.

`mean_cell_updates` counts swept cells for synchronous execution and expanded
frontier cells for event/BFS execution. Query operations also charge neighbor reads
and learned-rule evaluation. `state_bytes` is a proxy that includes eight bytes per
dense input cell plus candidate and peak work state.

The oracle event queue bounds rule-learning overhead. Sparse BFS tests whether any
gain is simply standard traversal of the active causal region. This visible toy
benchmark can validate or reject the scheduling signature only; it cannot establish
self-organization, language reasoning, or an LLM successor.
