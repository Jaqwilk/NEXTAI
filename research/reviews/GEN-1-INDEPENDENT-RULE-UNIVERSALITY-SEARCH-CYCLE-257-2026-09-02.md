# GEN-1 — independent-rule universality search, cycle 257

## Scope frozen before result reading

This SEARCH MODE cycle asks whether primary empirical evidence already exposes
one exact observation-learned rule that can be instantiated independently in at
least two qualitatively different natural domains and retain an isolated
capability-per-full-cost advantage. The prospective gate is immutable at
`research/checks/independent_rule_universality_search_cycle_257.json`; it was
written before the source outcomes below were accepted. No benchmark,
evaluator, runner, candidate, hypothesis, plan or seed was created.

The search deliberately separates a common mathematical slogan from a common
executable mechanism. A reported rule does not pass merely because its outer
equation is shared while frontends, teaching signals, dynamics, constants or
controls are selected per domain.

## Primary-source audit

### Traces Propagation — strongest computational near-candidate

Pes et al. define a forward-only contrastive rule whose input and target traces
are propagated through every layer. The paper spans event-camera object and
gesture recognition, spiking speech recognition and user-specific keyword
fine-tuning. It reports a common learning rate and a useful qualitative
signature: local forward updates avoid storing the full BPTT activation
history, with explicit MAC and memory formulas.

The complete systems are not source-identical. The released repository has
separate MLP and CNN implementations. Even CIFAR10-DVS and DVS-Gesture use
different thresholds and membrane/target leak constants (`0.5/0.18/0.19`
versus `1.0/0.53/0.98`) and different epoch budgets; SHD changes architecture,
width and dynamics again. A one-hot class target and dataset preprocessing are
fed into the learning rule. There is no source-identical frozen-target-trace
ablation in every domain, and BPTT is more accurate in direct N-MNIST and other
comparisons. The cost calculation compares selected training MACs and state,
not acquisition, preprocessing, fit, query, update, deployment and reuse at
matched useful quality. Its causal core is local gradient descent on a supplied
contrastive label signal, neighboring already-falsified HYP-0032 layer-local
goodness and HYP-0052 eligibility credit rather than opening a new causal class.

Gate vector: `Y, P, N, N, N, P, N, Y, N`.

### Differential extrinsic plasticity — strongest embodiment near-candidate

Der and Martius provide a more important conceptual counterexample. DEP is a
deterministic local rule that develops locomotion, wheel interaction and
coupled behavior without an explicit reward, and the authors apply the same
rule form to simulated humanoid and hexapod bodies. The qualitative mechanism
is spontaneous symmetry breaking in the brain-body-environment loop, not a
static predictor or lookup table.

It still fails the prospective contract. All demonstrations are rigid-body
simulations sharing one proprioceptive joint-angle-to-motor interface. The
controller receives an aligned inverse sensor-to-motor model, and the paper
explicitly uses appropriately selected time scale `tau` and gain `kappa`.
Observed behaviors are qualitative and morphology-contingent; there is no
common externally scored useful task, learned-factor-only ablation across each
body, strong matched control suite or acquisition-to-reuse cost crossover.
DEP therefore falsifies only an overbroad claim that local objective-free
self-organization never occurs. It does not yet falsify NEXTAI's conditional
exhaustion statement for natural, source-identical, controlled computation.

Gate vector: `Y, N, N, N, P, N, N, Y, N`.

### Meta-learned plasticity — rule discovery but classical collapse

Shervani-Tabar and Rosenbaum cleanly isolate a shared plasticity rule from
weight initialization: each inner model starts randomly and uses one
layer-shared rule found by an outer meta-gradient. This is directly relevant to
the requirement that the rule itself be learned.

The empirical scope is MNIST/EMNIST, not qualitatively different natural
domains. The search space is a hand-authored pool of local terms, and the
survivors are a backprop-like term, classical Oja/PCA plasticity and an
error-Hebbian term whose identified effect is better alignment with
backpropagated gradients. It therefore fails both cross-domain evidence and the
prospective non-classical-causal gate, with no complete system cost crossover.

Gate vector: `Y, N, N, N, Y, Y, P, P, N`.

### Existing e-prop and equilibrium-propagation controls

The already registered e-prop source (`SRC-0195`) uses different supervised
and reward-based learning signals, task-specific recurrent/CNN systems and
actor-critic machinery. Its causal purpose is an online approximation to the
loss gradient, and it approaches rather than exceeds BPTT quality without a
common acquisition-to-reuse cost envelope. Equilibrium propagation
(`SRC-0188`) is explicitly a gradient-computing relaxation method and has
already been deduplicated from the energy and local-credit families. Neither
changes this audit.

## Observation

Three different notions repeatedly collapse under methods inspection:

1. **Equation universality:** a top-level update equation is reused while
   architecture, constants or teaching signals change.
2. **Substrate universality:** one physical coupling principle works across
   related morphologies but inherits an aligned sensor-effector ontology.
3. **Discovered-rule universality:** a meta-learner selects a rule, but the
   selected rule is classical gradient alignment or PCA and is tested in one
   authored family.

No audited system jointly passes the nine prospective gates. Traces
Propagation is the strongest computational near-candidate; DEP is the strongest
conceptual counterexample and the only source that changes the next search
action.

## Interpretation

Conditional local exhaustion remains supported, not proven. The new evidence
does not justify a scored NEXTAI experiment because its missing causal controls
and full-cost crossover are properties of the claim, not merely missing lab
plumbing. Building a new benchmark would manufacture the required interface
before a natural causal thesis exists.

DEP does, however, expose one residual neighborhood that the earlier passive
physical-reservoir audit did not fully close: **active extrinsic plasticity on
real hardware**. Its decisive discriminator is whether one frozen,
dimensionless local rule and constants can produce quantitatively useful
adaptation on unrelated morphologies without an aligned inverse model. That is
different from passive substrate computation, active sensing and ordinary
gradient credit.

## Confidence and decision

Confidence is `0.91` that no currently audited independent-rule claim warrants
apparatus or scoring. Uncertainty is concentrated in real-hardware follow-ups
to DEP and related morphology-independent plasticity, not in another variant of
Forward-Forward, e-prop, equilibrium propagation or meta-gradient rule search.

Decision: `NO_ADMISSIBLE_RULE; OPEN_REAL_HARDWARE_EXTRINSIC_PLASTICITY_TRIGGER`.

## Exact next discriminating cycle

Cycle 258 must perform one prospective primary-source anomaly search for a
DEP-like local rule executed on **real hardware** in at least two unrelated
morphologies. Before outcomes, require one frozen executable rule and constants,
no aligned inverse sensor-to-motor model or task ontology, a disabled/shuffled
extrinsic-signal ablation on every body, differential-Hebbian plus strong
classical adaptive controls, an external quantitative perturbation/recovery or
task measure, and enough accounting for a conservative full interaction-to-
reuse cost bound. Admit at most one causal thesis. If no source passes, close
active extrinsic plasticity and move to a non-embodied assumption; do not build
a simulator, benchmark or candidate.
