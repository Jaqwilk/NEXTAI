# Microbial adaptive-prediction and conditioning monitor — cycle 276

## Scope and prospective boundary

This SEARCH MODE cycle created no hypothesis, experiment plan, scoring seed,
candidate, benchmark or score and changed no protected apparatus. The admission
contract was frozen in
`research/checks/microbial_adaptive_prediction_conditioning_monitor_cycle_276.json`
before new sources were inspected, at source cutoff `SRC-0364`.

The gate required more than an organism responding better after prior exposure.
A qualifying source had to isolate natural within-lifetime acquisition in the
same lineage, distinguish memory write from read, reuse one unchanged local rule
across qualitatively different sequence families, and beat evolved wiring,
selection, fixed feedback and persistent-effector controls at full cost.

## Objective observations

### `SRC-0365` and `SRC-0366`: prediction is encoded by evolution

Tagkopoulos, Liu and Tavazoie show that networks evolved in correlated simulated
environments acquire predictive responses. Their E. coli measurements support a
temperature-to-oxygen anticipatory coupling consistent with ecological history.
The mechanism that learns the correlation is evolutionary optimization, not an
update executed within the assayed cell's lifetime.

Mitchell et al. show natural anticipatory regulation in E. coli and yeast and a
fitness benefit when an early ecological stimulus precedes a later one. They
also alter the E. coli response through repeated laboratory evolution. This is
strong causal evidence for selection of regulatory wiring, but it directly
fails the same-lineage acquisition and anti-selection gates. It does not show
training on one sequence improving prediction of an unseen sequence family.

### `SRC-0367` and `SRC-0369`: memory is persistent pathway machinery

Lambert and Kussell expose E. coli to controlled glucose-lactose fluctuations.
They identify inheritance of stable intracellular Lac proteins over one to ten
generations and a shorter hysteretic response in which expression persists after
the inducer is removed. These states reduce switching lag when lactose returns.

Zacharioudakis et al. independently dissect yeast galactose reinduction memory.
A heterokaryon assay argues against a self-propagating chromatin mark; residual
Gal1 galactokinase in the cytoplasm preserves the faster response. Both studies
therefore provide real local biological memory, but for the same previously
activated pathway through persistent effector abundance. Neither acquires a new
relation or transfers it across unrelated environmental sequences.

### `SRC-0368`: chemotaxis adaptation is fixed feedback

Alon et al. systematically vary chemotaxis-network protein concentrations and
show that adaptation precision remains robust even when other response features
change. This is compelling robustness evidence for an evolved receptor-
modification feedback architecture. It returns the network toward its operating
state under a present stimulus; it does not learn a novel correlation from a
training sequence. Integral feedback is therefore an adequate classical control.

### `SRC-0370`: synthetic conditioning authors the association

Zhang et al. physically implement Pavlovian-like sequential logic in E. coli.
The circuit stores whether its designed stimuli co-occurred and later changes
its response. The experiment is useful proof that molecular components can
realize conditioning semantics, but the designers specify the association and
assemble optimized AND, memory and OR modules. It is an authored finite-state
machine, not discovery by a natural general learner.

## Cross-source synthesis

The literature separates into five computational classes:

- evolution writes predictive regulatory connections (`SRC-0365`, `SRC-0366`);
- multi-generation laboratory selection changes those connections (`SRC-0366`);
- stable pathway proteins or hysteresis accelerate same-condition re-entry
  (`SRC-0367`, `SRC-0369`);
- fixed receptor-modification feedback performs homeostatic adaptation
  (`SRC-0368`);
- engineered sequential logic implements a pre-authored association
  (`SRC-0370`).

No source jointly supplies natural same-lineage acquisition, write/read
interventions, cross-family source identity, unseen-sequence transfer, lineage
and dilution controls, three scales and full cost. The corresponding software
translations are evolutionary population search, a persistent cache, leaky or
integral feedback, and a hand-written finite-state machine. Those controls
already explain the reported qualitative effects without a portable learned
representation.

## Interpretation and confidence

Microbial systems unquestionably predict and remember, but the word "learning"
conflates mechanisms with different computational implications. The strongest
natural prediction results place the correlation in evolved network wiring;
the strongest within-lineage memories preserve components of the exact pathway
that will be reused. Neither is evidence for a source-identical learner that
discovers and transfers an abstract temporal rule.

- Confidence `0.995` that none of the six sources passes the prospective gate.
- Confidence `0.99` that `SRC-0365` and `SRC-0366` establish evolved predictive
  wiring rather than within-lifetime correlation learning.
- Confidence `0.995` that `SRC-0367` and `SRC-0369` are explained by persistent
  pathway-specific machinery or hysteresis.
- Confidence `0.99` that chemotaxis supplies a fixed-feedback control rather
  than a learned predictor.
- Confidence `0.995` that the synthetic conditioning circuit authors its
  association and therefore cannot establish natural discovery.
- Confidence `0.92` that this route is exhausted absent a primary experiment
  satisfying same-lineage acquisition and cross-sequence transfer controls.

## Decision

`CLOSE_MICROBIAL_ADAPTIVE_PREDICTION_ROUTE_AS_EVOLVED_CORRELATION_FIXED_FEEDBACK_PERSISTENT_EFFECTOR_OR_AUTHORED_CIRCUIT`

No official hypothesis evidence, confidence or G1 experiment count changes.
The mechanisms remain useful mandatory controls, but no result justifies
software scoring or an apparatus change.

## Exact next discriminating search

Audit small-RNA transgenerational adaptive memory only for a primary experiment
where exposure writes a molecular state in one lineage, factor-specific
interventions separate write, transmission and read, and the same local update
rule learned on one stress or sequence improves an unseen qualitatively different
family without shared sequence address, terminal effector, chromatin persistence,
selection or experimenter-authored target pairing. Require lineage tracking,
matched scrambled and inheritance-null controls, at least three generation or
sequence scales, and full sensing, RNA production, amplification, transport,
maintenance, readout, reset and reuse cost. Do not score or alter apparatus
without a non-equivalent belief-changing causal thesis.
