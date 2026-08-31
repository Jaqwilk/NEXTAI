# GEN-1 — observable auxiliary identifiability audit, cycle 129

## Scope

This was exactly one no-scoring, development-only audit. It created no
hypothesis, experiment plan, scoring seed, candidate, benchmark, schema or
protected evaluator change. It did not call `nextai run`. Three-family scoring
targets and WT test files 8–9 were not read.

The diagnostic was frozen before outcomes in
`research/checks/observable_auxiliary_identifiability_audit_preregistered_v1.json`
(SHA-256
`6b25b5525149a15bbcd1f12da3789add4e575835c10798e474edadcf944f07b7`).
The complete result is
`research/checks/observable_auxiliary_identifiability_audit_v1.json`
(SHA-256
`4aa55faaf5d6c0d1a29859cf7308d69c058f9f9653546b4bfb368293210dcfc5`).

## OBSERVATION

The three-family v7 interface has one common padded container but three
different candidate-visible validity signatures:

| Family | support/history width | target/output width | future-public width |
| --- | ---: | ---: | ---: |
| N-CMAPSS DS08a | 18 | 14 | 4 |
| DronePropA | 10 | 6 | 4 |
| continuous-event | 32 | 1 | 32 |

Thus masks identify the family exactly. World slots, support-pair order, row
index, world boundary and public numeric coordinates are also visible, but none
has one verified latent meaning across the three generators. DS08a segment time,
DronePropA flight time and synthetic-event time are merely placed in equal row
positions. The four DS08a public coordinates, four motor controls and 32
synthetic-event coordinates are not registered interventions on one shared
latent system.

WT exposes a stronger candidate-visible auxiliary: one mechanically unique
normalized scalar control with four values in all six fit files and both
development files. The preregistered response signature used 54 fit episodes
and 18 development episodes. Its four centered control centroids had the maximum
possible rank three, so the auxiliary does modulate the response.

The modulation did not pass the frozen discriminators. Nearest fit-centroid
development accuracy was `0.4444444444`; the mean of 256 shuffled-label controls
was `0.2469618056`, but their preregistered 95th percentile was
`0.5555555556`. The observed margin over that bound was therefore
`-0.1111111111`, not the required `+0.25`. After subtracting the control
centroid, absolute cross-channel correlation had mean `0.2764192012`, p90
`0.8512682971` and maximum `0.9939739779`, far above the frozen `0.15`/`0.25`
conditional-dependence limits.

Both cohorts already support three scales and full-cost accounting. This
infrastructure fact cannot rescue the failed identifiability conditions.

## INTERPRETATION

WT contains a real intervention useful for prediction, but a predictive
association is not an identified transferable representation. The observed
rank says control changes response means; it does not establish conditionally
independent latent components, support independence or a shared-factor pairing
model. Strong residual coupling and failure against the pair-breaking control
make the proposed nonlinear-ICA route unjustified even within this diagnostic.

V7 fails earlier. Its apparently common signals are either syntax—row order and
world boundaries—or forbidden routing information—mask/native width and slot
ranges. Applying one encoder to those fields would be source-identical code, but
not evidence of a shared latent mechanism. It would let a model infer which
benchmark family it is processing and then regularize separately, the exact
confound isolated by EXP-0008 and EXP-0009.

The audit therefore supports the portfolio interpretation that additional
representation assumptions must be measured, not silently embedded. It does not
prove that causal representations are impossible on all future data.

## THEOREM MAPPING

- SRC-0165 fails because no varying latent factor is known to be shared by each
  v7 pair across families; a WT apparatus identity is constant rather than the
  required learned varying factor account.
- SRC-0166 fails because v7 lacks one common auxiliary and WT retains strong
  conditional dependence after conditioning on its public control.
- SRC-0167 fails because WT's intervened `load_in` is already observed and no
  hidden latent/support geometry is mapped to the theorem; v7 public coordinates
  are not registered interventions with common targets.
- SRC-0168 fails because native-width masks are padding metadata and family
  routers, while file/world groups group samples rather than observational
  variables under the paper's mixing assumption.

## CONFIDENCE AND LIMITATIONS

Confidence is high (`0.97`) that neither frozen contract currently supports the
preregistered auxiliary-identifiability claim. The decisive facts are contractual
for v7 and all five frozen WT numerical gates are explicit. Uncertainty remains
about other feature maps and future datasets, but selecting one after these
outcomes would be post-diagnostic tuning. With only 18 WT development episodes,
the shuffled-control percentile is coarse; that uncertainty weakens a positive
claim and cannot turn the observed negative margin into a pass.

This service diagnostic changes no hypothesis confidence and is not scientific
scoring evidence.

## DECISION

`no_observable_auxiliary_identifiability_contract`.

Do not create HYP-0030 and do not implement or tune an auxiliary-variable,
paired-disentanglement, intervention-canonicalization or grouped-observation
learner on v7 or WT. Preserve the audit and negative controls as append-only
design history.

## Exact next discriminating cycle

Use one no-scoring `continuous_sparse_local_rule_feasibility` gate to evaluate a
radically different principle already named by HYP-0006's revival condition:
learn a sparse continuous local transition graph from observations and update
only affected node state, without transferring a canonical coordinate system.

Audit the existing WT and three-family contracts without reading held-out
targets or changing protected files. Retain the direction only if all of the
following can be specified before a hypothesis:

1. one permutation-equivariant graph-induction and node-update rule, with no
   family labels, channel names, native types, paths or supplied adjacency;
2. a causal contrast against a source-identical dense transition rule and a
   fixed random graph, plus persistence, RLS/VAR, Chow–Liu and event/transition
   controls where applicable;
3. a development-only fixture where useful sparse edges cannot be reproduced by
   marginal variance, native-width routing or a static Chow–Liu tree;
4. quality matched before cost comparison, with active edges, query/update
   operations, bytes, state and R1/R4/R16 charged at at least three scales;
5. local post-reveal updates touching only the learned Markov blanket, and an
   H96 or rollout-depth test that does not require full retraining;
6. no new benchmark or schema unless the frozen contracts are proven unable to
   express the discriminator and a later protected service cycle is separately
   authorized.

If the learned rule collapses to sparse VAR, Granger selection, Chow–Liu,
event simulation or benchmark-specific routing, record
`no_distinct_sparse_local_rule_contract` and keep HYP-0006 dormant. Only a full
pass may authorize creation of one low-confidence hypothesis in a later wake.
