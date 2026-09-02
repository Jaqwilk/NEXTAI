# GEN-1 — endogenous-intervention rule-discovery monitor, cycle 265

## Scope and prospective gate

This is one bounded no-scoring SEARCH MODE cycle. The gate in
`research/checks/endogenous_intervention_rule_discovery_monitor_cycle_265.json`
was frozen before source search. It asks whether self-generated interventions
make an observationally non-identifiable relation identifiable while the
system learns a reusable update rule, without authored semantic actions,
reward, goal or verifier. No hypothesis, experiment, plan, candidate, seed,
score, benchmark or protected apparatus was created or changed.

The internal historical boundary is strict. In `EXP-20260830-0029`, a learned
active policy reached the same exact lower bound as a certified decision tree
but used more fit, query, update and state cost. In `EXP-20260901-0030`, the
shared raw-sensor active learner scored `269/288`, between frozen/Gaussian
(`270/288`) and kernel (`271/288`) controls, while its fit cost was about
`513x` the frozen/Gaussian control. `HYP-0042` was falsified without tuning.
Active observation selection is therefore a known classical component, not a
new thesis by itself.

## Audited observations

`SRC-0313` is the strongest direct example. Bongard, Zykov and Lipson's
physical robot chooses an exploratory action that maximizes disagreement among
candidate self-model predictions, observes the response and updates its
morphology model. This is a genuine information-seeking intervention, but the
disagreement objective, candidate-model search, motor interface and desired
behavior are authored. The learned object is robot state/morphology under a
fixed active-system-identification rule, in one platform and without the
required full-cost comparison.

`SRC-0314` learns a free-form kinematic simulator from video of commanded robot
motion and reuses it for planning and damage recovery. It removes explicit
kinematic priors, but the observation setup, prediction loss, optimizer and
planning interface remain supplied. It does not isolate adaptive intervention
selection or learning of the update rule.

`SRC-0315` uses random motor babbling to fit an egocentric visual forward model
for a legged robot. Deployment selects among proposals with an explicit reward.
After damage, the robot gathers `7000` new steps over about `30` minutes and
re-trains against visual-odometry labels. This is real-hardware adaptation, but
random excitation does not target an identifiability ambiguity and the fixed
training rule updates only model parameters.

`SRC-0316` trains CARL, a goal-conditioned reinforcement-learning policy, to
intervene locally in simulated Lenia. It generalizes soliton creation and
steering to unseen update rules and action scales. The declared intervention
function, goal set and reward carry the objective; evidence is one simulated
cellular-automaton family and comparisons are heuristic rather than matched
classical experimental-design controls.

## Observation

All four apparent anomalies decompose into a fixed information-acquisition or
optimization rule plus learned state: maximum model disagreement, commanded or
random excitation, prediction-error fitting, model-predictive reward, or
goal-conditioned reinforcement learning. Self-generated action can reveal
hidden dynamics, but none of these studies learns the rule that decides what
counts as informative or useful under the frozen source-identical gate.

## Interpretation, uncertainty and confidence

The external evidence agrees with NEXTAI's two direct negative experiments:
active acquisition is valuable when its query objective and action semantics
are supplied, but that is classical active system identification or
experimental design. Repackaging it as self-modeling, motor babbling or an
artificial experimentalist would not add a new causal factor.

Confidence is `0.995` that none of `SRC-0313` through `SRC-0316` passes the
prospective gate, `0.99` that `SRC-0313` and `SRC-0315` learn state under fixed
rules, and `0.99` that `SRC-0316` depends on explicit goals/rewards in one
simulated family. Confidence is only `0.70` that no future empirical system can
discover an intervention rule without those supplied channels.

## Decision

`CLOSE_ENDOGENOUS_INTERVENTION_ROUTE_ACTIVE_SYSTEM_IDENTIFICATION_OR_REWARD_EQUIVALENCE`.

Experiment ID: `none`. Immutable plan path: `none`. Seed: `none`. Existing
hypothesis evidence and confidence remain unchanged. Do not score or rename
active acquisition, motor babbling, maximum-disagreement self-modeling, MPC or
autotelic-RL variants.

## Exact next discriminating action

Keep this route event-triggered only. Reopen it solely for a new primary
empirical result where self-generated intervention makes a relation identifiable
without authored goals, rewards, semantic action routing or a fixed
information-gain criterion; the same learned update rule must then be isolated
across at least two unrelated systems against passive and strong classical
controls with a full end-to-end cost. Without such a result, create no
benchmark, hypothesis or scored mechanism.
