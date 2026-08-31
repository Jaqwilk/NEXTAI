# Nonstationary online-update identifiability and service gate — cycle 40

## Scope

This is a protected service cycle after EXP-0042. It creates no experiment plan, scoring seed, candidate implementation or scored result. Its purpose is to determine whether `nonstationary_online_update_battery_v1` can distinguish a shared learned fast-state update from strong fixed online estimators without leaking regimes or future targets. Evaluator construction is permitted only after the development sanity checks below pass.

## Common stream and no-leak boundary

Every public observation is `(opaque_slot, x_t)` with `x_t` a continuous raw vector. Slots are runner-random identifiers used only to isolate concurrent fast states; they are independently permuted and carry no mechanism, regime or phase information. There are no record IDs, boundary flags, time-to-switch values, repeated keys or oracle features.

For dimension `K`, draw `z_t ~ N(0,I)`, normalize it to the unit sphere, and expose `x_t = Q z_t`, where `Q` is a runner-seed-derived orthogonal mixing matrix. Every regime has the same input distribution. Therefore neither one observation nor its marginal moments reveal the active regime. Only previously revealed input-target pairs can identify change.

The evaluator enforces the order

```text
observation x_t -> candidate prediction -> immutable score capture -> reveal y_t -> candidate update
```

It never passes a test target, future observation, mechanism name, phase, coefficient, hazard or oracle segmentation to `fit` or `query`. Pooled meta-training contains only separate fixed-seed training streams. Runner-random test seeds and schedules are created after source audit and are disjoint from training seeds.

## Three mechanisms under one interface

Each mechanism uses two recurring regimes `A/B` plus one distractor regime `C`; coefficients and the orthogonal mixing are independently generated for every training or test world.

1. `mixed_linear`: `y_t = w_r^T z_t`. This is exactly realizable by raw-space RLS/Kalman and is the mandatory linear null.
2. `mixed_quadratic`: `y_t = (u_r^T z_t)(v_r^T z_t)`. This is exactly realizable by degree-two polynomial features plus RLS and tests whether feature learning adds anything beyond a declared nonlinear basis.
3. `mixed_periodic`: `y_t = sin(w_r^T z_t)`. A preregistered random-Fourier/kernel online estimator is the nonlinear control; the oracle uses the true coefficient only as an unattainable lower bound.

Periodic outputs are bounded; linear and quadratic outputs are finite but not clipped, because clipping would deliberately make the realizable linear/polynomial controls misspecified. Scores normalize squared error by evaluator-side target energy, so a zero predictor has score zero rather than benefiting from K-dependent target variance. The mechanisms share raw type, target type, schedule construction, update timing and accounting. A shared candidate receives no mechanism label and must use source-identical slow parameters, feature map and update rule for every slot.

## Unseen schedules and phases

Each stream has five hidden phases with runner-seed-jittered lengths: first adaptation to `A`, abrupt switch to `B`, recurrence of `A`, distractor `C`, and recovery of `A`. Training streams use different fixed seeds, coefficients and phase lengths. Test phase lengths derive solely from the realized scoring seed, K and D. Stable, abrupt, recurrence, distractor and recovery metrics are computed from immutable evaluator-side indices that are never public.

The matrix meaning is frozen: K is raw dimension; D scales phase duration and therefore adaptation horizon; Q is the nominal minimum samples per phase. Unsupported state or runtime scales must be recorded, not removed.

## Matched controls and state boundary

The EXP-0043 plan must include: no update, fixed LMS/delta, raw RLS/Kalman, degree-two polynomial RLS, random-Fourier/kernel LMS, change-point model-bank RLS, bounded replay/dictionary, additive fast weights, delta fast weights, independent learned-update ablation, the one shared learned update, and a privileged segmented oracle. The oracle is excluded from implementable Pareto analysis.

Every implementable method receives identical public observations and target timing. Feature construction, normalization, pooled meta-fit, replay, change detection, query, update, bytes read/written and all per-slot state are charged. The maximum allowed resident state is `262,144` bytes per active slot plus one shared slow-state allowance of `65,536` bytes; exceeding the summed boundary is an invalid candidate outcome. R1/R4/R16 workloads repeat query use only; acquisition, meta-fit and every chronological update are always charged once.

## Frozen metrics and decision gates

Primary capability metrics are prequential score `max(0, 1-MSE)`, minimum-mechanism score, worst-phase score, post-switch recovery score and recurrence retention. Raw prequential MSE and distractor interference are minimized. Cost axes are acquisition, meta-fit, mean query/update operations, bytes touched, state and R16 workload.

A positive quick requires overall prequential score at least `0.90`, every mechanism at least `0.85`, every phase at least `0.75`, better recovery and recurrence than both fixed delta and the strongest adaptive classical estimator, a strict advantage over the independent learned-update ablation, state compliance and implementable non-dominance. One seed can only authorize a three-seed adversarial screen.

Return HYP-0014 dormant after one valid quick if a fixed estimator matches the shared rule, if gains occur only where a supplied nonlinear feature basis solves the task, if recurrence is erased by the distractor, or if update/memory costs dominate. A crash rejects only an implementation. Any future-target access, regime leakage, training/test seed collision, post-score tuning or evaluator digest change invalidates the cohort.

## Development sanity gate before freeze

Before evaluator construction/freeze, deterministic development streams must show: raw batch/RLS features solve `mixed_linear`; degree-two features solve `mixed_quadratic`; a sufficiently expressive fixed Fourier/kernel approximation materially improves over raw linear regression on `mixed_periodic`; the marginal input generator is regime invariant by construction; and test targets are unavailable until after prediction. On development seed `1103`, the pre-construction check obtained linear MSE `1.06e-16`, quadratic MSE `5.32e-15`, raw-linear periodic MSE `0.08098` and RBF-kernel periodic MSE `0.00251`. These checks establish benchmark solvability and prevent deliberately weak controls, but are not blinded evidence and may never appear as an experiment result.

## Exact next scientific action

After this service migration passes tests and is frozen, reactivate HYP-0014 at unchanged confidence `0.28`. On the next wake, preregister EXP-20260830-0043 quick before implementing any learned candidate or scored baseline adapter. Change exactly the update rule while keeping feature/state architecture matched wherever possible. Do not score during this service cycle.
