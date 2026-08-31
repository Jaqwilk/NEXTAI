# GEN-1 — three-family temporal-interface gate, cycle 69

## Scope

This was one design/audit-only cycle after the cycle-68 heterogeneous-equation rejection. It created no hypothesis, experiment plan, candidate, scoring seed, runner invocation, result, dependency, external model/API, or protected change. The active `heldout_mechanism_recombination_v3` cohort remains unchanged.

The audited proposal was one lossless anonymous `(history, action/intervention, next observation)` contract across three existing families: `action_conditioned_predictive_equivalence_v1`, `continuous_event_predictive_state_v1`, and `nonstationary_online_update_battery_v1`. Acceptance required a shape/content router no better than chance plus 0.10 and one repeated predictive-state equation in all three families.

## Native semantics

- Predictive equivalence supplies discrete transition records `(history, action, outcome, next_history)` and explicit planned action sequences.
- Continuous-event prediction supplies a fixed-length multichannel episode, a scalar next-value target, and a regime encoded inside one anonymous observation channel. It has no separate public action field.
- Online update supplies three labeled regression streams. Each observation is sampled independently and its scalar target is a function of the same observation under a hidden phase parameter. It has neither a state-transition target nor a public action/intervention.

Treating the online label as a next observation would therefore change its scientific task. Treating a continuous regime channel and an online hidden phase as explicit actions would expose privileged semantics. Empty-action padding would remain a task tag.

## Router control

The audit used only fixed worlds with seeds `1103/2207/3301`, K=`8/32`, and D=`1/4/6`. A lossless structural profile used event count, stream count, explicit-action presence, observation/history width, successor width, and target arity. Leave-one-seed-out nearest-profile classification was `9/9` in every one of six K×D cells and `54/54` overall, versus three-family chance `1/3`.

Content preserves a second perfect router even if envelopes are padded. Predictive values were integral with mean fraction `1.0`; continuous-event values had mean integral fraction `0.078125` because only the regime channel is discrete; online values had fraction `0.0`. Combined with next-observation linkage, the rule `integral > 0.5 → predictive; otherwise linkage > 0.5 → continuous; otherwise online` classifies every audited world.

## Predictive-state equation gate

- Predictive: `outcome == next_history[-1]` in every transition; linkage `1.0` for every audited world.
- Continuous: the best anonymous next-channel linkage had R² `0.755377–0.880616`, mean `0.814881`; resets prevent exact equality but the process is genuinely autoregressive.
- Online: the best target-to-next-observation-channel squared correlation was only `0.022614–0.262608`, mean `0.094322`, despite selecting the best channel post hoc. This is consistent with independently sampled observations and fails the required `>0.5` shared predictive-state signature in every world.

Thus the proposed equation exists in two families but not the third. A common wrapper would reduce all three to generic supervised regression, erasing action/transition semantics rather than discovering a shared predictive state.

## Decision

`reject-before-hypothesis` for `shared_temporal_predictive_state_transfer` on these three existing families. Do not register HYP-0023, create EXP-0058, implement a learner, or migrate the protected evaluator. This closes the current synthetic shared-representation search rather than weakening the gate again.

## Exact next discriminating step

Pivot to a real-data literature/data gate. In the next wake, use primary sources to audit three compact public system-identification datasets with native input/output time series—Silverbox, the DaISy hair-dryer process, and the DaISy robot-arm process—as candidates for one unchanged local input-conditioned predictive-state learner. Before downloading or migrating anything, verify authoritative provenance, license/redistribution terms, stable hashable downloads, sample counts, train/test chronology, absence of target leakage, and whether one source-identical `(past inputs, past outputs, future inputs) → future outputs` contract applies without dataset tags or manual state alignment. Run no scoring. Register HYP-0023 only if the data are legally and scientifically usable, each has enough disjoint chronology, and a predeclared dataset-router negative control cannot explain the proposed transfer; otherwise reject the real-data cohort and reconsider the project portfolio rather than returning to synthetic wrappers.
