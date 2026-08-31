# GEN-1 — adaptive-halt certificate-gap feasibility, cycle 131

## Scope

This was one preregistered no-scoring audit. It created no hypothesis,
experiment plan, scoring seed, candidate, benchmark, schema or protected-file
change and did not call `nextai run`. The masked diagnostic read only its 35
train-role and four validation-role corpus files; no test-role file, WT test
file or three-family test target was read.

The immutable diagnostic is
`research/checks/adaptive_halt_certificate_gap_feasibility_preregistered_v1.json`
(SHA-256
`340bf874266dbdefed7593b207385200d59025e2b878e5fe56adb5e6108ef307`).

## OBSERVATION

The frozen iterative byte estimator was fitted to 32,768 train bytes and
evaluated on 4,096 validation bytes under the exact four-round confidence
scheduler. For positions that survived into another round, the offline label
recorded whether the next already-frozen public distribution improved true-byte
log loss by at least 0.25 bits. Entropy was the prospective uncertainty signal;
total-variation change from the preceding distribution was the classical
convergence certificate.

At span 8, entropy AUC was `0.6681` versus certificate AUC `0.5014`, but the
cell contained only 48 observations, below the frozen minimum 50. At spans 32
and 128, entropy AUC fell to `0.4119` and `0.3530`, while the residual
certificate reached `0.6451` and `0.6149`. The entropy margins were therefore
`-0.2332` and `-0.2619`, not the required `+0.10`. Mean next-round true-byte
log-loss gains were negative at every scale: `-1.3635`, `-0.6025` and
`-0.1961` bits.

Contract inspection also failed. Masked infilling fixes the global round count,
reveal quota and completion in the evaluator; the candidate cannot halt.
WT exposes horizons 16/32/96, but the horizon itself specifies output length
and no frozen target-free variable independently states required internal
iterations. Active three-family v7 has only reasoning depth 1.

## INTERPRETATION

The available uncertainty does not identify useful extra computation beyond a
cheap change-in-distribution certificate. On longer spans it ranks future
benefit worse than random and worse than the residual. The negative mean gains
also reproduce, on validation-only data, the implementation-level pattern that
self-filled refinement can amplify errors.

More importantly, the only multi-round contract implements adaptive allocation
in the evaluator's confidence scheduler, not as a candidate action. Calling a
new threshold a learned halter would therefore change the scheduler or merely
rename evaluator logic. This is precisely the confound that EXP-0031's
transition gate exposed in a different system.

PonderNet confirms that learned halting is a legitimate prior architecture, but
it does not remove the need to beat a convergence certificate. DEQ strengthens
the requirement that residual/root-finding stopping be the matched control.

## CONFIDENCE AND LIMITATIONS

Confidence is high (`0.98`) that the preregistered gate failed: every span
failed at least one numerical condition and no frozen contract gives the
candidate the required three-level halt action. This does not falsify adaptive
computation in general. The diagnostic uses one small Markov estimator and
visible repository validation bytes; a richer model could have calibrated
uncertainty, but testing it would be post-gate model search without an adequate
contract.

This service diagnostic is not scientific evidence and changes no hypothesis
confidence.

## DECISION

`no_adaptive_halt_certificate_gap_contract`. Keep HYP-0004 dormant. Do not tune
entropy, thresholds, round counts, span allocation or the old learned halter,
and do not create a new benchmark merely to rescue the direction.

## Exact next discriminating cycle

Run one no-scoring `recursive_conditional_independence_feasibility` audit over
existing WT fit/development observations and three-family training worlds.
Before reviving HYP-0013, require one source-identical observable partition rule
that exposes at least two nested context/independence levels, survives a
permutation and split-stability fixture, and cannot be represented by a single
or mixture-of-Chow-Liu control. Native-width masks, family labels and test
targets remain forbidden. If the hierarchy is absent or collapses to a tree
mixture, record `no_recursive_pc_structure_contract` and create no hypothesis,
plan or new cohort.
