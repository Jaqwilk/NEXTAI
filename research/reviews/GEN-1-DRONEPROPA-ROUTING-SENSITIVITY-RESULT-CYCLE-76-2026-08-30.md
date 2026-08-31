# GEN-1 — DronePropA candidate-visible routing sensitivity, cycle 76

## OBSERVATION

This was one preregistered, no-score identifiability audit. The immutable preregistration is `research/reviews/GEN-1-DRONEPROPA-ROUTING-SENSITIVITY-PREREG-CYCLE-76-2026-08-30.json`, SHA-256 `68fada2f74671792b2ddee12d312f443da724f9d8351b429dcfcadfa529accac`. The result is `research/checks/dronepropa_routing_sensitivity_cycle76.json`, SHA-256 `7776e29dd35b8954b1592a977d0ed9b424f8687ecee3970ca98a5130eac40b3d`. The audit script SHA-256 is `c3a1d0caecf3edb2ab4231b762a0d5f3140c78786da52149b072a48f21e280f2`.

Across 72 faulty t1/t2/t3/t5 flights, each of eight folds withheld one complete trajectory-speed cell and trained only on the other speed and the other three trajectories. Every test fold contained all nine fault/severity worlds. Features used exactly 32 deterministic adaptation anchors per file: 32-sample histories of the four motor and six state channels plus the one-step six-state adaptation targets. No whole-flight statistic, evaluation sample, source path, filename or header timestamp entered a candidate-visible feature.

Nested routing accuracies were:

- amplitude: `6/72 = 0.083333`;
- normalized histogram: `8/72 = 0.111111`;
- lag: `5/72 = 0.069444`;
- combined: `7/72 = 0.097222`.

Chance was `1/9 = 0.111111`. The combined two-sided Wilson 95% interval was `[0.047896, 0.187350]`. Under 5,000 preregistered within-trajectory-speed-cell label permutations with fixed audit seed 7601, the null 95th percentile was `0.166667` and the combined p-value was `0.706859`. Every visible group was below the frozen `0.25` ceiling. The source-header session diagnostic, excluded from the decision, scored `0.111111`. The visibility audit found zero forbidden accesses. The synthetic fold-contract test passed before the corpus run.

No HYP-0023, EXP-0058, runner scoring seed, candidate learner, predictive score, protected evaluator migration, dependency, external model/API, redownload or data copy was created.

## INTERPRETATION

The prior whole-flight router result `0.361111` is not evidence that the proposed learner-visible adaptation interface trivially identifies fault/severity worlds. It used a materially wider diagnostic view: whole-flight values and a source-header session field. Under the separately preregistered legal view and a stricter simultaneous trajectory-and-speed holdout, routing is statistically indistinguishable from the balanced null and lies below chance by one prediction.

This does not prove that every possible classifier fails, nor that a shared representation will transfer. It clears only the cheap anti-routing identifiability gate. The whole-flight result remains preserved as diagnostic history and still warns that a future evaluator must enforce the adaptation boundary mechanically.

## CONFIDENCE

- `0.99` that the frozen pass inequalities are satisfied.
- `0.98` that the implementation used only the preregistered adaptation samples for pass/fail features.
- `0.90` that simple nearest-centroid routing from the declared summaries is not a credible explanation for a future transfer gain.
- `0.65` that a richer nonlinear router could remain near chance; this was not tested and must not be claimed.
- `0.35` that the proposed shared operator-subspace learner will beat matched ARX/RLS/probabilistic controls after full cost.

## ALTERNATIVE EXPLANATIONS

- Nearest centroids may underfit a nonlinear but easy condition signature in the same legal features.
- Thirty-two deterministic anchors may remove routing information while also making the intended system-identification task too data-starved.
- Condition transfer may still collapse because all faults occur on one airframe and trajectories are closed-loop responses.
- A positive learner could exploit dynamical identification rather than a transferable representation, which is why source-identical independent and no-sharing controls remain mandatory.

## DECISION

`keep` the exact DronePropA protocol for one later protected evaluator-migration service cycle. This is permission to build and freeze the audited harness only, not evidence for HYP-0023, not permission to score in this wake, and not promotion.

## NEXT DISCRIMINATING EXPERIMENT

In the next wake, perform exactly one protected service migration under the user's standing authorization: create `heldout_dronepropa_factor_recombination_v1` in maintenance state; reuse the existing archive/extraction; freeze the anonymous 64/8/24 split plus 8 OOD and 26 t4 reserved files; implement the selected-channel loader and adaptation-boundary guard; register exact version/specification/implementation hash/conformance-test hash for every mandatory baseline; add the one-step teacher-forced and 10/50-step controlled-rollout metrics plus R1/R4/R16 full-cost fields; freeze a new evaluator manifest and pass all tests/integrity/doctor. Do not create HYP-0023, EXP-0058, a runner seed or any predictive score in that migration wake. If any baseline semantic fixture or protected integrity gate fails, keep the benchmark in maintenance and record the blocker.
