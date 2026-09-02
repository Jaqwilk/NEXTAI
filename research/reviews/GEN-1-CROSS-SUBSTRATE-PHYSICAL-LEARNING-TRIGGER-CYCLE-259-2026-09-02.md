# GEN-1 — cross-substrate physical-learning trigger, cycle 259

## Frozen question

This SEARCH MODE cycle tests the last hardware-only A13 residual identified by
cycle 253 and narrowed by cycles 257–258. The prospective check at
`research/checks/cross_substrate_physical_learning_trigger_cycle_259.json` was
written before accepting source outcomes. Admission requires one executable
local physical-learning rule and constants on at least two unrelated physical
substrates, causal controls and a measured matched-quality full-cost crossover.
No benchmark, evaluator, runner, candidate, hypothesis, plan, seed or score was
created.

## Primary-source audit

### Abstract coupled learning across flow and elasticity

Stern et al. derive contrastive local updates for computational flow and
elastic networks and compare them with global gradient descent and directed
aging. This is the strongest cross-substrate mathematical result: both systems
use free and clamped equilibria and local changes align with descent on a task
cost. It also supplies the decisive deduplication. The mechanism is an
equilibrium-propagation/gradient family, not a new nonclassical credit source.

The two systems are simulations using substrate-specific learning degrees of
freedom and equations—conductance for flow and stiffness or rest length for
springs. The paper says physical implementation is plausible rather than
measuring it. It supplies neither one executable physical implementation nor
energy, calibration, clamping, readout and reuse measurements.

Gate vector: `N, P, N, P, P, Y, P, P, N`.

### Twin variable-resistor network — strongest physical result

Dillavou et al. build two simultaneous 16-edge resistor networks. Local
circuits compare voltage drops and apply a Boolean one-step resistance change;
the system learns allostery, regression and a small Iris classification task
without a central training processor. It recovers after removal of selected
edges, demonstrating a real local physical adaptation signature.

This is one electrical substrate. Its update is an explicitly discrete sign
approximation to coupled learning, uses a twin network, a global clock and
supervisor-applied target clamps, and has no mechanism-disabled physical
control. The current prototype runs at 3–5 Hz. The claimed 500-edge crossover
is a projection from parallel scaling, not a measured comparison. The reported
rough 10–25 mW is output-network dissipation and does not include the twin,
clamp generation, measurement/application hardware, resistor programming,
training or fabrication. It therefore cannot satisfy the frozen full-cost
gate.

Gate vector: `Y, N, N, Y, N, P, P, Y, N`.

### Spring–turnbuckle networks — physical but not autonomous

Altman et al. demonstrate three mechanical networks trained by free/clamped
spring lengths. Their paper is unusually explicit about the boundary: an
experimenter measures lengths with a ruler, clamps nodes and manually turns
each turnbuckle. The authors state that this supervisor undercuts locality,
scalability and compute-time benefits. Mechanical buckling can decouple an
edge while the nominal update continues in the wrong direction.

The mechanical update is continuous rest-length change, not the electrical
Boolean resistance rule. It relies on temporal memory instead of twin
hardware, uses different learning rates in the range 0.1–1 across trials and
full nudging rather than the electrical setup. Tasks are proof-of-concept
motion/symmetry/allostery demonstrations; there is no common quality or cost
comparison with the electrical system.

Gate vector: `Y, N, N, N, N, P, N, N, N`.

## Observation

The phrase “coupled learning” spans two physical publications, but the complete
mechanisms do not. Electrical learning is autonomous, discrete, simultaneous
and twin-network based. Mechanical learning is continuous, sequential and
human executed. Their parameters, clamping, memory, state update, tasks and
cost boundaries differ. Combining them after the fact yields a shared
mathematical analogy, not a source-identical cross-substrate learner.

No audited source passes gates 1–5 jointly. No publication measures the full
cost crossover required by gate 9. Consequently a local software simulation
would test an already known gradient-equivalent algorithm while omitting the
only claimed advantage—the physical substrate—and would not change NEXTAI's
beliefs.

## Interpretation, uncertainty and decision

Physical coupled learning is valid evidence that local relaxation can replace
centralized gradient calculation inside one engineered electrical substrate.
It is not evidence for a portable observation-learned principle across
substrates, and current cost claims are forecasts rather than end-to-end
measurements. The hardware-only A13 residual is therefore closed under the
fixed NEXTAI contract.

Confidence is `0.98` that the audited electrical and mechanical systems are
not source-identical; `0.97` that neither establishes a measured full-cost
crossover; and `0.93` that a scored software implementation would be causal-
equivalent to equilibrium propagation or gradient descent. Bibliographic
uncertainty remains, but it does not justify apparatus absent a source meeting
the prospective gate.

Decision:
`CLOSE_HARDWARE_ONLY_A13_RESIDUAL_NO_SOURCE_IDENTICAL_CROSS_SUBSTRATE_FULL_COST_EVIDENCE`.

## Exact next discriminating cycle

Strategically redirect outside local digital architectures and engineered
learning hardware. Perform one prospective primary-source synthesis of
conserved biological computation: require a quantitatively specified,
observation-driven update law independently instantiated in at least two
unrelated natural sensing or adaptation systems, an intervention isolating the
rule, useful held-out adaptation and measurable energetic/state cost. Before
admission, deduplicate integral feedback, Kalman/Bayesian filtering, ordinary
Hebbian plasticity and supplied reward. Do not build a biological benchmark
or candidate unless a natural result first exposes a non-equivalent causal
thesis.
