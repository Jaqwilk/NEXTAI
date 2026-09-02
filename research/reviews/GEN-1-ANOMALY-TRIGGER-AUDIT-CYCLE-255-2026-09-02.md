# GEN-1 anomaly-trigger audit — cycle 255

## Prospective screen and scope

This is one bounded no-scoring SEARCH MODE cycle. At
`2026-09-02T02:34:56Z`, before opening candidate results, the machine-readable
screen in `research/checks/anomaly_trigger_audit_cycle_255.json` froze the
required methods evidence: one primary empirical source, at least three
qualitatively unrelated natural interfaces, identical executable code and
constants, no family adapter or manual ontology, a learned-factor-only
ablation, classical/frozen controls, and full acquisition-to-reuse cost.

This cycle creates no hypothesis, plan, candidate, benchmark, evaluator,
runner, schema, manifest, seed or score and changes no protected file.

## Triggered candidate

DayDreamer (`SRC-0285`) is the strongest primary-source anomaly found. It runs
Dreamer online on four physical robots: Unitree A1 locomotion, UR5 and XArm
visual manipulation, and Sphero visual navigation. The paper explicitly claims
identical learning hyperparameters across all experiments and reports real
learning from scratch without a simulator. It therefore passes the headline
trigger and deserves a methods audit rather than abstract-level rejection.

## Methods audit before accepting reported performance

### Executable identity

The Dreamer core is common, but the executable systems are not source-identical
under the NEXTAI contract:

- the official repository invokes separate `a1`, `xarm` and `ur5` configs and
  separate real/dummy environment adapters;
- action spaces differ between continuous motor angles/torques and discrete
  Cartesian/gripper commands;
- the algorithm uses reparameterization gradients for continuous actions and
  REINFORCE for discrete actions;
- observation encoders consume different combinations of proprioception, RGB
  and depth; and
- the paper specifies task-specific rewards, controllers, action filters,
  movement restrictions, resets and safety interventions.

Identical optimizer and network-size hyperparameters do not make these complete
systems identical executable code and constants.

### Supplied semantics

The learned world model predicts observations and rewards, but the reward and
interface semantics are externally authored. The quadruped reward combines
upright orientation, named joint poses and forward velocity through a
curriculum. Manipulation uses gripper closure, bin membership, Cartesian axes,
automatic gripper behavior and predeclared bin locations. Navigation uses an
OpenCV position oracle to generate dense distance reward. These are legitimate
robotics choices but violate the no-manual-ontology gate.

### Causal isolation and controls

The paper compares Dreamer with appropriate task-specific model-free baselines:
SAC, Rainbow, PPO/R3M and DrQ-v2. It does not run one matched baseline set on all
four robots, nor an unchanged frozen-world-model or world-model-disabled
ablation that removes only learned imagination. The result therefore cannot
separate learned-model value from architecture, optimization, replay, reward
or task-specific systems choices under NEXTAI's causal standard.

### Full cost

Interaction time and task performance are reported, and the implementation
uses parallel actor/learner processes with large imagined batches on GPU. The
paper does not provide a common acquisition + replay + world-model fit + actor
critic fit + query + update + state + GPU/robot communication + reuse-horizon
cost against every baseline. Sample efficiency or physical elapsed time alone
is not the required full-system crossover.

## Seven-gate result

| Gate | Result | Methods evidence |
|---|:---:|---|
| ordinary natural interface | `N` | Real hardware, but authored observation/action/reward/controller interfaces |
| identical code/constants in >=3 systems | `N` | Common core and hyperparameters, different configs, adapters, spaces and gradient branches |
| no ontology or privileged support | `N` | Task rewards, coordinate actions, bin logic, pose terms and navigation oracle |
| learned-factor-only ablation | `N` | No unchanged world-model-disabled/frozen ablation across all robots |
| classical/frozen exclusion | `N` | Different task-specific baselines; no common frozen causal control |
| qualitative signature | `P` | Real online learning and post-perturbation adaptation across embodiments |
| matched-quality full-cost crossover | `N` | Interaction time reported; total compute, state and communication envelope absent |

DayDreamer passes only the qualitative-signature gate. It does not authorize a
NEXTAI quick, and constructing a robot-inspired microbenchmark would insert the
missing action and reward ontology.

## New anomaly: rule universality versus state transfer

The rejection exposes a useful contract distinction rather than a mechanism:

1. **Rule universality:** identical learning law independently starts from
   scratch and succeeds in several families.
2. **Representation transfer:** learned state from source worlds improves an
   unseen world relative to independent fitting.
3. **Foreign-source causal gain:** information from unrelated source families
   improves a target beyond target/support-only learning.

DayDreamer claims level 1, not levels 2 or 3. Many recent NEXTAI cohorts use
shared-vs-independent and cross-family-only-vs-support-only contrasts, which
test levels 2 and 3. The fixed objective asks for a source-identical learned
*principle* that generalizes across qualitatively different families, while the
G1 decision rule asks for causal gain in at least two families or tasks; neither
wording by itself proves that foreign-source state must help. This does not
weaken the demand for learned-factor ablation, classical controls or full cost.
It means the evidence contract may have conflated a universal learning rule
with universally transferable learned parameters.

## Observation, interpretation, confidence and decision

**Observation.** DayDreamer provides credible real-system evidence that one
world-model learning core and hyperparameter set can be trained independently
on multiple physical robot tasks. Its complete systems are task-specific, its
semantics are supplied, it lacks the required causal ablation and it does not
report a matched full-cost envelope.

**Interpretation.** The candidate does not falsify conditional exhaustion and
is causal-equivalent to dense model-based reinforcement learning over authored
interfaces. Its useful contribution is to reveal that algorithmic generality
and foreign-source representation transfer are different claims. NEXTAI must
audit which negative results address each claim before declaring the broader
principle space exhausted.

- Confidence `0.995` that DayDreamer fails the frozen prospective screen.
- Confidence `0.99` that reward/action/environment semantics are externally
  supplied.
- Confidence `0.98` that the publication lacks an all-robot learned-factor-only
  ablation and matched full-cost crossover.
- Confidence `0.82` that recent NEXTAI selection has operationally emphasized
  levels 2/3 more strongly than the fixed objective logically requires.

**Decision:** `REJECT_DAYDREAMER_TRIGGER_BUT_OPEN_RULE_VS_STATE_TRANSFER_AUDIT`.

Experiment ID: `none`. Immutable plan path: `none`. Scoring seed: `none`.
Scientific hypothesis evidence and confidence remain unchanged.

## Exact next discriminating action

Cycle 256 must perform one no-scoring cross-ledger contract audit separating
rule universality, representation transfer and foreign-source causal gain.
Classify every scientifically valid learned mechanism by which level its plan
actually tested and whether its negative result also falsifies level 1. Compare
that inventory with the fixed objective, AGENTS G1 decision rule and program
contract. Admit a new causal thesis only if a source-identical independently
instantiated learning rule retains the same non-classical qualitative gain in
at least two families at plausible full cost despite no foreign-source gain.
Otherwise confirm that the distinction does not reopen the space. Do not change
the apparatus or reinterpret completed outcomes.
