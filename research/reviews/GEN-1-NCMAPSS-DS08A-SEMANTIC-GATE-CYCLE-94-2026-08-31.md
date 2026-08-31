# GEN-1 — N-CMAPSS DS08a semantic gate, cycle 94

## Scope

This was one service-only real-file gate. It created no hypothesis, EXP-0060 plan, scoring seed, candidate, runner call, scientific score, evaluator migration or dependency. The active v6 cohort remains unchanged. Parameters were frozen and hashed before the existing audit was generalized or any metric was viewed.

## Observation

Dataset, reader, partition and gate-spec hashes passed. The fixed-prefix candidate-visible train/holdout router scored `7/15 = 0.466667`, below the frozen training-majority ceiling `9/15 = 0.60`. No visible `W+X_s` column exactly matched a private `Fc`, `hs`, `T` or `Y` column; maximum absolute correlation was `0.631252`, below `0.999999`.

All diagnostic one-step controls were finite. Persistence NRMSE was `0.0109444`, training-pooled ridge without holdout adaptation was `0.0101580`, and per-unit prefix-adapted ridge was `0.0106519`. A second independent temporary output had the same SHA-256 `d037450b6eab6ea693a3297afabda13b36254c2259dc5e68e91ed6932b6aafa1`; the temporary file was then removed.

## Interpretation and uncertainty

The frozen partition passes the preregistered structural gate: its role is not recovered by the simple visible router and no direct private-field leakage was found. This authorizes evaluator design, not scientific evidence or a transfer claim.

The pooled no-adaptation control is already slightly better than per-unit adaptation on this diagnostic. Any later learner must therefore beat the pooled control at matched full cost; merely improving over persistence or independent adaptation would not establish transferable representation learning. More expressive routers and longer-horizon leakage remain possible.

Confidence is `0.98` that the exact gate implementation and result are deterministic and correctly computed. Confidence that a shared learner will beat the pooled null is intentionally low and unquantified before a preregistered experiment.

## Decision

`authorize_protected_evaluator_design_only`. Do not activate a cohort, create EXP-0060, realize a scoring seed or score anything in this wake.

## Exact next discriminating step

In one separate protected service-only wake, specify the DS08a evaluator component with whole-unit isolation, training-only normalization, fixed adaptation/query boundaries, horizons, full acquisition/fit/query/update/state/bytes/R1-R4-R16 accounting, source-identical shared and independent learners, the strong pooled no-adaptation control, and explicitly named privileged-support diagnostics. Freeze and preflight it without scoring. Treat it as one real-data family component; do not claim the requested 3–4-family transfer until additional source-identical families are frozen under the same learner interface.
