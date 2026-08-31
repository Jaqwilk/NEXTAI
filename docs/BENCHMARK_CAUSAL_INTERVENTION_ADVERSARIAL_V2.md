# Causal intervention adversarial v2

This screen replaces the complete XOR chain with an eight-layer branched target
path, mixed XOR/AND/OR/XNOR gates, two K distractor mechanisms per knowledge unit,
five-percent measurement noise, and incomplete intervention coverage. Training uses
96 fully observed environments with labeled multi-node interventions; every query is
a new three-intervention composition.

The robust learner selects mechanisms by intervention-filtered error and abstains
when the best and second-best candidates are separated by less than the 0.05 noise rate. Clone-root
distractors make some structures deliberately non-identifiable. The noninvariant
ablation scores directly intervened nodes as ordinary data. Known topological order,
a four-parent candidate pool, full root context, and a fixed Boolean gate library are
strong side information and must be charged as confounds.

Local and dense candidates share one learned model. Local execution visits only
ancestors not cut by interventions; dense execution scans every learned mechanism.
The oracle receives the true model. This visible synthetic screen tests robustness,
calibration, and irrelevant-K query scaling—not novelty, latent causal discovery,
language reasoning, or an LLM successor.
