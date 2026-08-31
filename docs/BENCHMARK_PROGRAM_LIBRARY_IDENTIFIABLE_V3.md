# Program library identifiable v3

This corrective cohort keeps the v2 program generator, training corpus, candidates,
seeds, and operation accounting unchanged. Each task now provides 30 distinct
input-output examples from the 31-element domain and holds out the remaining input.

Every DSL program is a permutation. Two permutations that agree on 30 inputs must
also agree on the last output, so a solver matching the examples has an identifiable
test answer. This removes the v2 behavioral ambiguity without changing the learned
fragment or search procedure.

The setup is deliberately synthetic and unusually informative. A positive result
validates the diagnostic and this test apparatus; it does not establish a general
successor architecture or justify further program-library tuning.
