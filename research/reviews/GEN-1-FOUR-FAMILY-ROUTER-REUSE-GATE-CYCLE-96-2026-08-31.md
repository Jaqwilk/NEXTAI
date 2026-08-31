# GEN-1 — four-family router reuse gate, cycle 96

## Scope

This was one design/audit-only cycle. It created no hypothesis, EXP-0060 plan, scoring seed, candidate, runner call, scientific result, dependency or protected mutation. The active DronePropA v6 cohort remains unchanged.

## Observation

The proposed four-family gate included DS08a, DronePropA, nonlinear local-state transfer and continuous-event predictive state. Cycle 85 already audited the latter three native contracts: graph/categorical local state, dense scalar continuous event and 320-to-6 controlled flight dynamics. A structural router classified all `18/18` worlds against a frozen ceiling `0.4333`. Its immutable decision explicitly prohibited rebuilding that lossless interface.

Cycle 69 independently found a perfect `54/54` temporal-family router and showed that generic supervised wrapping would erase incompatible action/transition semantics. The new DS08a component has another native `18→14` numeric signature. Adding a uniquely shaped family cannot make the already perfectly routable three-family subset unidentifiable. Therefore no duplicate router was run and no new serializer code was written.

## Interpretation and uncertainty

The hard requirement that family identity itself be unrecoverable is stronger than necessary for the user's causal question. Observable source differences are a confound, but the direct test is whether cross-family data improves an unchanged learner beyond source-identical independent fitting and the same learner with cross-family slow-fit data removed. A model that merely learns implicit specialists may match those ablations; it cannot satisfy a preregistered positive transfer margin over them.

This does not revive the rejected graph/continuous/flight proposal. The revised candidate set removes nonlinear graph-state transfer and retains only three families with a defensible common native semantics: DS08a dynamics, DronePropA dynamics and continuous-event autoregression. Family identity will be measured and disclosed, never counted as transfer.

Confidence is `0.995` that rerunning the proposed four-family router could not change its rejection. Confidence is only `0.65` that the revised three-family continuous contract can avoid evaluator-authored feature meanings; that must be resolved before protected implementation.

## Decision

`reject_duplicate_four_family_router_gate_before_implementation`. Preserve the portable DS08a component, but do not combine it with the prohibited cycle-85 family set and do not create EXP-0060.

## Exact next discriminating step

In one separate design-only wake, freeze a generic fixed-size numeric contract for DS08a, DronePropA and continuous-event prediction: a padded history tensor, evaluator-supplied future-control tensor, fixed-size output and evaluator-private score mask. The transformation must be the same mechanical pad/cast rule for every native numeric array and may not name controls, states, regimes or families. Define one source-identical shared learner, its independent-per-family clone and the same learner with cross-family slow-fit data removed. Reject before protected migration if the common target/loss requires family-specific semantics or either causal ablation cannot be implemented exactly.
