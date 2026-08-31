# Test-time learned memory design gate — cycle 38

## Scope and portfolio reason

This was a literature/design-only cycle after EXP-0040. No evaluator, candidate, immutable experiment plan, scoring seed or scored result was created. The purpose was to challenge the portfolio with an online-learning mechanism rather than another static representation compiler.

The current portfolio has tested retrieval, program induction, adaptive recurrence, vector-symbolic storage, cellular computation, energy relaxation, predictive state, learned virtual machines, modular routing, experience compilation and probabilistic circuits. HYP-0011 compiles repeated solved problems into persistent artifacts; HYP-0004 changes how long a fixed transition runs. The proposed family is different: the same frozen slow parameters must update a bounded fast state after each newly revealed observation and use that state for later predictions in a nonstationary stream.

## Primary prior art and novelty boundary

- SRC-0106 proves that linearized attention is already a fast-weight programmer. Pure outer-product writes and delta-rule correction are controls, not project novelty.
- SRC-0107 expresses kernelized linear attention as a recurrent state update with linear sequence cost. Recurrent execution alone is not a new principle.
- SRC-0105 makes the hidden state itself a linear model or MLP trained by a self-supervised update at test time. A learned fast state is therefore established prior art.
- SRC-0095 updates a neural long-term memory during inference and combines it with short-term attention. Persistent test-time neural memory is also established.
- Classical dictionary lookup, LMS/delta learning, recursive least squares, Kalman filtering and change-point filtering are mandatory nulls wherever the generator matches their assumptions.

HYP-0014 cannot claim that test-time learning, fast weights, recurrent linear attention or surprise-gated memory is new. The only project-level question is whether one compact learned update law transfers across changing streams and provides a capability/cost signature not reproduced by the strongest matched classical online estimator.

## Rejected easy experiment

Reject a streaming key–value recall benchmark before implementation. Exact or near-exact repeated keys make a hash table, LRU cache or nearest-neighbor index the correct solver. Continuous linear targets make RLS or a Kalman filter the correct solver. Exposing stable entity IDs, regime boundaries, a hand-selected feature basis or a surprise label would place the essential representation or change detector in the evaluator. Winning such a task would measure an implementation constant or reward hidden ontology, not learned online state formation.

Also reject a single piecewise-linear stream with only an online neural candidate and a no-update baseline. That comparison cannot distinguish learned meta-updates from ordinary delta learning, exact least squares, Bayesian filtering or replay.

## Proposed hypothesis

Create HYP-0014, `meta_learned_online_state_update`, as `proposed` with confidence `0.28`.

The causal claim is deliberately narrow: after slow parameters are frozen, a shared learned local update law can decide what to write, revise and retain in bounded fast state across nonstationary streams, yielding better prequential capability per fully charged update/query cost than fixed online estimators and replay.

This is not evidence for an LLM successor. It is a falsifiable candidate mechanism for local continual adaptation and experience-dependent inference.

## Required identifiability gate for `nonstationary_online_update_battery_v1`

Before any evaluator is written, the next cycle must specify and analytically inspect a shared battery with these constraints:

1. The learner predicts before each target is revealed, then may update. Scoring is strictly prequential; future observations cannot leak into fit or normalization.
2. Inputs are continuous raw vectors with no stable record IDs, exact key repeats, regime labels or boundary markers. Recurring regimes return without notification.
3. At least two held-out stream mechanisms share the same input/output interface: one where RLS/Kalman is the strong realizable null and one nonlinear mechanism where a preregistered finite feature expansion or kernel online estimator is the strong realizable null. Training and scoring stream families, hazard rates and seeds are disjoint.
4. The same slow parameters and state budget are used across stable, abrupt-switch, recurrence and adversarial distractor phases. Only fast state changes during scoring.
5. The causal ablation keeps the state model, features and budget fixed while changing only the update rule: no update, fixed delta/LMS, exact RLS/Kalman, learned rate/gate and learned update.
6. Additional implementable controls are hash/nearest-neighbor memory, finite-window replay SGD, change-point detector plus RLS, additive fast weights, delta fast weights, recurrent linear attention, TTT-Linear, a smallest viable TTT-MLP and a fixed recurrent/reservoir state. Oracle regime segmentation is reported separately as a lower bound.
7. Metrics include prequential loss and calibrated uncertainty, cold-start sample efficiency, post-switch recovery area, recurrence retention, distractor interference, worst-phase performance, update/query operations, bytes read/written, maximum state, fit/meta-training work and R1/R16 full workload.
8. Every method receives the same observations and target timing. Offline meta-training, feature construction, replay, normalization and oracle hyperparameter selection are charged and disclosed.

The identifiability proof must show that a positive score cannot be obtained by recognizing a leaked regime code, exact-key caching or using a privileged feature map. It must also demonstrate on fixed development streams that the classical controls solve the subfamilies for which they are realizable; deliberately weakening them invalidates the benchmark.

## Decision rules

Pass from design to evaluator construction only if one frozen learned update can be compared at matched state and workload across both mechanisms without receiving privileged structure unavailable to controls.

A quick positive requires the learned update to pass every preregistered phase gate, remain implementably non-dominated, improve recovery/retention over both fixed delta fast weights and the best classical adaptive estimator, and retain the effect under an unseen change schedule. It only authorizes multi-seed screening.

The family returns dormant after one valid quick if the learned rule is behaviorally equivalent to delta/RLS/change-point filtering, if a dictionary or replay dominates it, if the advantage appears only in the nonlinear subfamily whose representation was supplied, if interference destroys recurrence, or if update and memory traffic erase the inference benefit.

## Exact next action

Perform one design-only identifiability gate for `nonstationary_online_update_battery_v1`. Write the two stream generators mathematically, prove the no-future-leak prequential boundary, define the common observation interface and matched state/work accounting, and run development-only sanity checks for RLS/Kalman, change-point RLS, delta fast weights and the nonlinear kernel control. Do not create an evaluator, candidate or scored plan until that gate passes.
