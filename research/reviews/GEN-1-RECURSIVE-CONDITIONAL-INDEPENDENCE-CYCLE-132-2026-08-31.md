# GEN-1 — recursive conditional-independence feasibility, cycle 132

## Scope

This was one preregistered no-scoring audit. It created no hypothesis,
experiment plan, scoring seed, candidate, benchmark, schema or protected-file
change and did not call `nextai run`. It used WT files 0–5 for fit and 6–7 for
development; WT files 8–9 and all three-family test targets were not read.

The immutable diagnostic is
`research/checks/recursive_conditional_independence_feasibility_preregistered_v1.json`
(SHA-256
`bce9a832d7b496306f0e1158ba074559f60b4ad569d265a4929b823f18371b9e`).

## OBSERVATION

The diagnostic represented every WT episode by ten anonymous response changes
and sorted its four public control values. Depth 0 fitted one Gaussian
Chow–Liu tree, depth 1 fitted one tree to each lower/upper control branch, and
depth 2 fitted one tree to every control level.

Depth 1 had overall development NLL `-0.5958438` per coordinate. Depth 2
worsened it to `-0.5259527`, a relative regression of `11.73%`. Regressions
were present independently in both development files: `12.10%` in file 6 and
`11.29%` in file 7. Thus the extra recursive split did not improve held-out
density fit.

The four leaf trees shared two root edges. The lower and upper branches had
four and two additional within-branch shared edges. However, the root/lower/
upper hierarchy Jaccards between fit files 0–2 and 3–5 were `1.0`, `0.3333`
and `0.0`; their mean `0.4444` missed the frozen `0.50` stability threshold.

Contract inspection was independently decisive. The WT construction is
exactly a four-component conditional Chow–Liu mixture selected by observed
control, equivalently a small decision tree. In v7 the three candidate-visible
scopes are 18→14, 10→6 and 32→1; a common circuit scope would require the
prohibited native-width masks.

## INTERPRETATION

The first control split captures a real broad density difference, but the
second split overfits 54 fit episodes rather than exposing stable recursive
independence. Shared edge names do not establish shareable probabilistic
factors because conditional parameters can still differ by leaf.

More fundamentally, nesting the four contexts does not create a mechanism
beyond the classical controls. A flat mixture with parameter sharing or a
decision diagram can encode the same partition. The exact collapse observed in
EXP-0040 therefore remains unresolved rather than repaired.

## CONFIDENCE AND LIMITATIONS

Confidence is high (`0.98`) that the preregistered gate failed: the numerical
gain and stability gates both failed, and the representational equivalence is
structural. The sample is small and a different naturally hierarchical dataset
could favor recursive circuits, but selecting another split, signature or
regularizer now would be post-diagnostic search.

This service diagnostic is not scientific evidence and changes no hypothesis
confidence.

## DECISION

`no_recursive_pc_structure_contract`. Keep HYP-0013 dormant. Do not tune the
number of contexts, tree learner, variance floor or structure-sharing rule, and
do not create a new circuit benchmark merely to rescue the family.

## Exact next discriminating cycle

Run one no-scoring `nonaxis_identity_acquisition_feasibility` audit for the
highest-confidence dormant architectural family, HYP-0001. Inspect only
candidate-visible DronePropA train/validation support and WT fit/development
streams. Require naturally available paired views without stable entity IDs,
paths or semantic labels; a pair-breaking/identity-shuffle negative control;
non-axis-aligned or nonlinear variation; and exact clustering, record-linkage
and ANN controls. If temporal adjacency or tensor slots already supply identity,
or no pair signal survives the negative controls, record
`no_nonaxis_identity_acquisition_contract` and create no hypothesis or plan.
