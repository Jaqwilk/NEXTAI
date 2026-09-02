# Mechanical material-memory monitor — cycle 272

## Scope and prospective boundary

This SEARCH MODE cycle created no hypothesis, experiment plan, scoring seed,
candidate, benchmark or score and changed no protected apparatus. The admission
contract was frozen in
`research/checks/mechanical_material_memory_monitor_cycle_272.json` before new
sources were inspected, at source cutoff `SRC-0340`.

Cycle 259 already rejected supervised free/clamped coupled learning as
gradient-equivalent and non-source-identical across electrical and mechanical
substrates. This cycle asked a different question: can unlabeled mechanical
history itself write a local state rule that improves an unseen, qualitatively
different function rather than merely storing an amplitude, path or supplied
target?

## Objective observations

### `SRC-0341`: multiple shear-amplitude memories

Paulsen et al. physically demonstrate multiple transient memories in a
non-Brownian suspension and show that noise can stabilize them. This is genuine
autonomous material memory. The readout identifies previously applied cyclic
shear amplitudes in the same protocol; it does not demonstrate useful transfer
to another load family or function, a factor-specific write-rule intervention,
three scales or full cost.

### `SRC-0342`: tactile Hopfield metasheet

Riley et al. combine bistable mechanical domes, piezoresistive sensing and
memristors. A manually applied sequence of patterns accumulates pairwise firing
events in six memristors of a 2-by-2 array. Those values populate the classical
Hebbian Hopfield interaction matrix. Offline asynchronous energy minimization
retrieves corrupted versions of stored patterns with reported 90–95% accuracy.

The experiment is impressive embodied storage, but its computational mechanism
is the known Hopfield outer product, test cases are perturbations of stored
patterns, and retrieval is performed offline. It supplies no unrelated-family
transfer or full physical versus classical cost boundary.

### `SRC-0343`: non-Abelian history logging

Sirote-Katz et al. demonstrate a frustrated periodic metamaterial whose final
state depends on operation order, allowing a static read to identify a prior
sequence. The geometry and transition landscape are designed in advance. No
rule is learned from experience and no response becomes more capable; this is a
fixed noncommutative state machine rather than transfer learning.

### `SRC-0344`: resettable pluripotent LCE arrays

Gowen et al. provide the strongest evidence that one material can acquire very
different functions. LCE arrays are directed-aged under bulk compression into
an auxetic response, thermally reset, and later trained for local allostery.
Comparison with a non-liquid-crystal elastomer and thermal erasure support a
material-specific persistent state.

Crucially, the first function is erased before the second is trained. Auxetic
training directly imposes compression for 24 hours; allosteric training directly
clamps chosen source and target nodes for 48 hours at 80 °C. This is material
pluripotency and supplied-target directed aging, not transfer from previous
experience to an unseen function.

### `SRC-0345`: autonomous adaptation to unknown loads

Chen et al. report the strongest current hardware result. A physical beam with
16 binary-stiffness elements, local strain gauges, magnetic actuators and an
Arduino adapts in seconds under three previously unknown loads. It does not
require a precomputed structural solution and tolerates imperfections and tested
damage.

The desired global displacement is nevertheless encoded as local strain targets,
and the controller applies a model-free stiffness-selection algorithm with
Pareto-selected hyperparameters. All physical test cases are variants of one
tip-displacement regulation function. The study therefore advances autonomous
adaptive structures but does not supply unlabeled cross-function learning or a
complete fabrication, sensing, control, actuation, reset and reuse crossover.

## Cross-source synthesis

The sources occupy four established computational classes:

- cyclic random organization and threshold/amplitude memory (`SRC-0341`);
- classical Hebbian associative memory in physical devices (`SRC-0342`);
- a fixed designed history-dependent state machine (`SRC-0343`);
- target-imprinted directed aging or feedback reconfiguration (`SRC-0344`,
  `SRC-0345`).

None trains on one load family and improves a previously unseen unrelated
function. Combining resettable pluripotency from one study with autonomous
feedback from another would not create a source-identical causal mechanism.
No source jointly provides the frozen-update, fatigue/damage, external-control,
three-scale, matched-quality and complete-cost controls.

## Interpretation and confidence

Mechanical media can store rich histories and can be physically reprogrammed.
The evidence does not yet show that history teaches an abstract operator or
representation reusable outside the training function. The strongest current
system is better described as embodied supplied-target feedback control; the
strongest multi-function material is erased and retrained separately.

- Confidence `0.995` that none of the five sources passes the frozen admission
  gate.
- Confidence `0.99` that `SRC-0342` is causal-equivalent to classical Hebbian
  Hopfield storage.
- Confidence `0.98` that `SRC-0344` shows retrainability, not cross-function
  transfer.
- Confidence `0.97` that `SRC-0345` is a meaningful hardware advance but retains
  an authored target and external controller.
- Confidence `0.90` that no currently audited material-memory result hides the
  required portable learned rule; genuinely new physical evidence could change
  this conclusion.

## Decision

`CLOSE_MECHANICAL_MATERIAL_MEMORY_ROUTE_AS_THRESHOLD_RECALL_DIRECTED_AGING_HOPFIELD_STORAGE_OR_TARGET_DRIVEN_RECONFIGURATION`

No official scientific evidence, hypothesis confidence or G1 experiment count
changes. A software simulation would remove the physical resource and retest
known hysteresis, Hopfield, gradient or feedback algorithms, so no apparatus is
justified.

## Exact next discriminating search

Audit biomolecular conformational or condensate memory, including prion-like
states, only for a primary factor-specific experiment where transient unlabeled
exposure writes a local protein-state rule that persists through turnover or
division and improves response across at least two unrelated stress or function
families. Require matched genetics, expression, selection, persistent stimulus,
metabolite, generic stress-gain and phase-separation controls; a state-specific
erase or blocked-conversion intervention; three biological scales or horizons;
and full synthesis, conversion, maintenance, read, growth, reset and reuse cost.
Do not score or modify apparatus without a non-equivalent belief-changing causal
thesis.
