# GEN-1 — DronePropA sparse-support redundancy and predictive-chart v6 service, cycle 212

## Scope

This was exactly one protected service-only cycle. It created no hypothesis, experiment plan, candidate implementation, runner seed or scored result. Completed plans, results and analyses remain unchanged. The user-authorized migration was held in maintenance until the full suite passed, then activated and frozen separately.

## DronePropA redundancy observation

The proposed shared actuator-to-state Jacobian support graph is observationally identical to ordinary masked ARX under the frozen DronePropA interface. Candidate-visible history is one vector `x` in R^320 and every locally adapted output has the proposed form `y_j = b_j + sum(i in S_j) w_ji x_i`. Define an ordinary ARX coefficient row `a_j` by setting `a_ji = w_ji` on `S_j` and zero elsewhere. Then `b_j + a_j x` gives exactly the same prediction for every visible history, flight and rollout. Learning one `S_j` across flights is classical multi-task or group-sparse feature selection; fitting `w_ji` on each adaptation prefix does not add a new computational operation. Shuffled-edge and dense-support controls remain inside the same linear ARX hypothesis class.

The frozen rule required rejection if the graph aliased ordinary sparsified ARX. This exact algebraic mapping is decisive without inspecting new test targets, choosing a threshold or running a scoring seed. The earlier rank-12 learner parameterized the same broad linear ARX family differently and was already inferior to pooled/RLS controls in valid EXP-20260830-0059. Therefore `heldout_dronepropa_factor_recombination_v7` was not created and no support learner was implemented. Excitation quality cannot rescue a mechanism that already fails the nonredundancy gate.

## Minimal breadth successor

To prevent methodology work from replacing exploration, `continuous_local_cellular_v6` was activated as a role-only wrapper over byte-identical v1. It preserves all worlds, 384 training transitions, anonymous signed channel permutations, OOD amplitudes, corruption, K=`64/256/1024`, D=`4/8/16`, Q=`8`, targets, metrics, thresholds, costs and five controls. It adds only three prospective role identifiers:

- `learned_predictive_coordinate_chart_v1`;
- `source_identical_shuffled_predictive_coordinate_chart_v1`;
- `source_identical_frozen_predictive_coordinate_chart_v1`.

These roles prospectively test observation-learned minimal predictive coordinates rather than coefficient masking: choose a bounded anonymous coordinate chart using training-only reconstruction and one-step predictive sufficiency, evolve only the selected chart, and decode to the public four-channel space. All roles must share inputs, chart capacity, feature library, fit, prediction, update, output bounds and accounting; only aligned, preregistered shuffled or frozen chart selection may differ. Candidate files do not exist. Bottleneck dimension, feature library, selection score, shuffle, fit/update constants and meaningful effect must be frozen in HYP-0054 and the immutable plan before implementation.

This causal factor is distinct from HYP-0023: that experiment compressed a collection of full ARX operator coefficients across flights, whereas v6 asks whether the observation representation itself contains a smaller predictive state. It is also directly controlled against full ambient ridge, quantized FSM, nearest-row kernel event and privileged support.

## Verification

- v1 evaluator SHA-256 unchanged: `43b6fdc34be399aa9c6607cd53388eaf4c432359543d7c335ebc3cbb12760baf`.
- v6 wrapper SHA-256: `231dea383af9b826fa063c75889965f827b15b34c79fc2e12fce8df8b0948d6f`.
- Both role-only and prospective-candidate-absence regressions: PASS.
- Full pytest before active freeze: PASS after regenerating the maintenance certificate; the initial run's only failure was the intentionally stale preflight certificate.
- Full pytest after active freeze: PASS, 569 tests.
- Protected integrity: PASS, 740 files.
- Evaluator digest: `a0083f36c8387c25cb1172da79adabc79914f50619f1aff7df58e5ed77415e35`.
- Candidate bundle: `0ff1ff3a3ef3706dd229eece5f89b12e472a953910b08970adb9fa9034c9bf98`.
- Preflight certificate: `15ba613639b1f7bc09a9da6a2651c2719f57bf0af75141955ae612c10d159ef6`.
- Doctor: PASS; pending plans: zero.

## Decision and next discriminator

Reject the DronePropA sparse-support proposal before implementation as an exact masked-ARX alias. Keep no scientific evidence or confidence change from this service cycle. Activate only the prospective v6 predictive-chart roles.

Cycle 213 must score and cannot perform another audit-only wake. Before implementation, preregister expected `HYP-0054` and immutable `EXP-20260901-0050`, freezing one bounded source-identical chart core and its aligned/shuffled/frozen selection rules. Execute exactly one runner-random quick on v6 against all five frozen controls. Require aggregate NRMSE at least `0.01` lower than both source-identical controls and the strongest complete implementable baseline, the same direction at every K for D8 and D16, stable rollout `1.0`, no damaged-input or worst-scale regression, effectively zero K query slope, full R1/R4/R16 accounting and implementable Pareto non-dominance. A negative ends that exact chart rule without tuning; one positive seed is scout evidence only and cannot promote.
