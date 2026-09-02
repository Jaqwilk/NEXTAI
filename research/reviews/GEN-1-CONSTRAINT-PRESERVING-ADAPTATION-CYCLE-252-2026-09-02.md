# GEN-1 constraint-preserving adaptation search — cycle 252

## Scope and integrity

This is one bounded no-scoring SEARCH MODE cycle. It asks whether capability
can grow by locally restoring violated constraints or viability conditions,
without optimizing a scalar loss, reward, fitness or energy. It changes no
hypothesis, plan, candidate, benchmark, evaluator, runner, schema, manifest,
seed or score. The active SuiteSparse cohort and all protected files remain
unchanged. The persistent user objective authorizes continued SEARCH MODE
instead of forcing a causally aliased experiment.

## Identifiability lemma

For a state `x`, adaptation needs an update relation that prefers at least one
reachable successor `x'` over leaving `x` unchanged. Exactly one of the
following supplies that preference:

1. **A supplied constraint or violation measure.** The update is projection,
   constraint propagation, local search, message passing or coordinate descent
   over a known feasible set.
2. **A learned constraint or inconsistency measure.** Learning the measure is
   ordinary representation, density, energy or dynamics learning; restoration
   is case 1 after fit.
3. **Observed viability, acceptance or survival.** This is a binary or ordered
   selection signal. It need not be differentiable, but it is still credit and
   reduces to reinforcement, evolution, rejection/version-space elimination or
   counterexample-guided synthesis.
4. **No preference-bearing signal.** Useful restoration is not identifiable:
   the transcript cannot distinguish a capability-preserving update from an
   arbitrary drift that obeys the same local interface.

Replacing one scalar with a vector of local residuals does not escape the
partition. Aggregation may be implicit in update scheduling, feasibility
ordering, acceptance or survival, but it still determines which changes persist.

## Primary-literature contradiction search

The strongest direct counterexample is learned neural projection. Yang, He and
Zhu (`SRC-0273`) learn physical constraints from trajectories and recursively
correct a prediction. The implementation nevertheless outputs one scalar
constraint-satisfaction value and follows its gradient in a projection loop
motivated by classical position-based dynamics. It is case 2, not objective-free
adaptation.

ConsFormer (`SRC-0274`) avoids labeled feasible solutions and reward, but its
training target is a differentiable approximation of the supplied CSP
constraints. More test iterations repeatedly apply the learned local-search
improver. This is case 1 with learned amortization, and the constraint language
carries the violation semantics.

Predictive coding (`SRC-0275`) shows that local error units can reproduce exact
backpropagation gradients on arbitrary computation graphs. This is important
implementation evidence, but it localizes the transport of an objective rather
than removing the objective. Equilibrium propagation (`SRC-0188`) likewise
uses free and target-nudged phases of one energy system.

Homeostatic intrinsic plasticity (`SRC-0276`) appears autonomous, yet it
explicitly chooses scalar input/output statistics and a desired output
distribution, then minimizes KL divergence to that distribution. It preserves
an operating regime, not task capability without a supplied preference.

Most decisively, Local Inconsistency Resolution (`SRC-0272`) formalizes almost
the exact proposed phrase: attend to part of an inconsistent model and resolve
it using controlled parameters. The paper recovers EM, belief propagation,
adversarial training, GANs and GFlowNets as instances. Thus local inconsistency
repair is a useful unifying view, but not a causal primitive separated from
probabilistic optimization, energy models or classical message passing.

## NEXTAI duplication audit

- `EXP-20260901-0027` implemented learned local energy factors with monotone
  accepted energy and bounded critical depth. Iteration worsened conditional
  loss relative to the source-identical one-sweep and frozen-factor controls,
  while PPM was cheaper and better. The exact energy route is closed.
- The cycle-146 local-credit audit and subsequent Forward-Forward tests covered
  local goodness, negative construction and source-identical global-credit
  controls. Locality alone did not establish a full-system advantage.
- `SRC-0230`/`SRC-0231` and cycle-236 candidate C4 cover constraint learning,
  counterexample-guided feasibility and version-space elimination. They require
  a verifier, concept language or teacher-produced counterexample.
- Learned local update laws, population selection, cellular repair, predictive
  state and nonstationary online updates already tested cases 2 and 3 against
  classical LMS/RLS/Kalman, exact feasibility and frozen-update controls.

An experiment on supplied parity, conservation, CSP clauses, bounds or safety
sets would therefore test whether a learner amortizes a known solver. An
experiment that learns the set from observations revisits energy/dynamics
learning. A viability benchmark would encode the target in survival. None
isolates the proposed stronger claim.

## Admission gates

A future exception would need all of the following before apparatus exists:

1. a naturally occurring violation signal that is not a target, reward,
   fitness, likelihood, energy, verifier output or evaluator-authored ontology;
2. one source-identical local update and constants across at least three
   qualitatively different systems;
3. an externally checkable capability consequence beyond maintaining the
   statistic that generated the signal;
4. source-identical disabled-restoration and shuffled-violation ablations;
5. exact projection, propagation, message-passing, online-estimation,
   CEGIS/version-space and energy controls;
6. prospective matched-quality full-cost crossover including acquisition,
   violation detection, scheduling, every update, state and failed repairs.

No inspected primary result or existing natural NEXTAI contract passes gates
1–3 jointly. Gate 1 without a preference signal also makes gate 3 unidentifiable.

## Observation, interpretation and uncertainty

**Observation.** Local constraint repair, learned projections, predictive-error
updates and homeostasis are real. In every auditable case, the direction of
adaptation comes from a supplied feasible set, a learned scalar inconsistency,
a target distribution or selection/acceptance feedback. Recent LIR prior art
explicitly subsumes classical probabilistic and optimization algorithms.

**Interpretation.** “Constraint-preserving adaptation without scalar credit”
does not survive as a distinct testable causal thesis. Scalar differentiation
is optional; preference-bearing information is not. Removing that information
makes useful adaptation observationally unidentifiable, while retaining it
maps the mechanism to already tested energy, projection, message-passing,
online-learning or selection families.

- Confidence `0.99` in the four-case partition for an externally evaluable
  update.
- Confidence `0.98` that supplied-constraint repair is classical feasibility
  computation or learned amortization thereof.
- Confidence `0.97` that learned-constraint restoration is energy/density or
  dynamics learning followed by projection.
- Confidence `0.96` that viability/acceptance is non-differentiable credit, not
  absence of credit.
- Confidence `0.91` that no current natural contract yields an exception;
  uncertainty remains for future physical self-maintenance systems whose
  viability signal and task consequence arise independently.

## Decision

`REJECT_CONSTRAINT_PRESERVING_ADAPTATION_AS_PROJECTION_ENERGY_OR_SELECTION`.

Do not create a constraint-restoration benchmark, evaluator ontology,
hypothesis or score. Preserve the literature as a causal deduplication record.
Experiment ID: `none`. Immutable plan path: `none`. Scoring seed: `none`.

## Exact next discriminating action

Cycle 253 must perform a **residual search-space exhaustion audit**, combining
the cycle-236 assumption map with cycles 248–252 and the complete scored
history. Mechanically classify every remaining proposed causal factor as
`closed_by_valid_negative`, `classical_or_prior_art_duplicate`,
`unidentifiable_without_supplied_semantics`, `hardware_only`, or
`open_and_testable`. Admit at most one factor only if it has a natural existing
corpus or real-system contract, one source-identical learner, a decisive
source-identical ablation, strong classical controls and a prospective
matched-quality full-cost crossover. Otherwise report search-space exhaustion
and request a strategic direction change; do not create another microbenchmark
or score an alias.
