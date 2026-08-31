# GEN-1 — three-family continuous transfer v1 service, cycle 98

## Scope

One protected service-only cycle under the user's standing migration approval. No hypothesis, experiment plan, scoring seed, audited runner scoring call, scientific result, evidence or confidence update was created. `EXP-20260830-0060` remains absent. Completed plans, results and analyses were not changed.

## Frozen evaluator

The active cohort is `heldout_three_family_continuous_transfer_v1`. It implements the frozen tensor contract SHA-256 `63c0e64273a1ffb2d4fd2fd6f24fc2d8701066ef9fd07d46eafeefa73fbf0296` over DS08a, DronePropA and continuous-event worlds.

- One mechanical float32 upper-left pad and boolean-mask adapter produces support 108×32, history 32×32 and future/output 50×32 tensors. It has no family paths, native types, semantic channel names, manual alignment or family-specific transform.
- Normalization is fit only from the slow-fit worlds assigned to the current causal control. Masked cells are excluded and holdout outputs cannot enter fit or adaptation.
- The evaluator-private roles are shared pooled, source-identical independent, cross-family-only leave-one-family-out and support-only. Family routing never reaches the learner; all clone fit/state costs are summed.
- Primary loss is masked normalized MSE, with equal trial counts per family. The mask-width router is explicitly reported as accuracy `1.0`; it is a confound and never positive transfer evidence.
- The runner derives `shared_vs_independent_gain` and `cross_family_transfer_gain` per family before aggregation. The plan schema fixes both causal roles, directions, K=`[4,9]`, depth=`[1]`, all full-cost axes and invalidation rules.

## Controls and diagnostics

Seven hashed semantic controls share one compact tensor baseline core: persistence, affine ridge ARX, predict-then-update RLS, empirical joint Gaussian conditioning, Gaussian Chow–Liu tree conditioning, recursive autoregressive ARX and a fully charged privileged support control. The privileged control receives all public test-support pairs but never query outputs; it is not called an oracle or bound and is excluded from the implementable frontier.

A one-query K=4 development smoke (fixed seed 1500001; not runner scoring and not scientific evidence) completed for all controls and all three real/development family adapters. Persistence NRMSE was `1.099/0.974/0.706` for DS08a/DronePropA/continuous-event. Gaussian Chow–Liu was `668914.520/1.004/0.003`. Ridge, RLS, empirical joint, autoregressive and privileged support were finite but the DS08a open rollout hit the common ±1e6 standardized finite guard and reported stability zero. This is preserved as an infrastructure diagnostic: it neither invalidates the evaluator nor supports a learner, but it makes stability a mandatory reported outcome.

## Verification

- Exact real-file adapter smoke: PASS for all three families and frozen world/cycle boundaries.
- Baseline semantic registry: PASS for all seven required controls.
- Source audit: PASS for 307 candidate modules.
- Full pytest: PASS, 317 tests.
- Integrity: PASS, 488 protected files.
- Doctor: PASS; active cohort, no STOP/PAUSE/lock/pending plan.
- Free disk after the cycle: 128.98 GiB.

Evaluator SHA-256: `cbe30bce16db4d47eb879cfccbc526e7d9602b7f5d4b4a407cd30295e7274f8d`. Candidate bundle SHA-256: `cbebe6ddbfca06ff767d3979f46455d0541b78287e594df8259395b215e52074`. Manifest file SHA-256: `e8c6ce3e616a23088c4fc68cf728a0dd46053e6d450df1715d3a521d1cab2847`. Preflight content digest: `351487067fe9ad0eac5ff680b144e08d3efc229053008259af4a1f6f33b2760a`; certificate file SHA-256: `2293f12be3173fa7b1cb599c55ea75a43214ae156d057fa415cc2ed1c7ccce8f`.

## Decision and exact next discriminator

Decision: `keep` and activate this evaluator infrastructure; infrastructure is not scientific evidence.

In the next wake, preregister exactly one quick `EXP-20260830-0060` under a new hypothesis for one source-identical shared tensor learner. Implement the learner only after registration; the independent, cross-family-only and support-only entry modules must be source-identical aliases of that same core. Score once through the audited runner. Success requires positive shared-versus-independent gain overall and in every family, positive cross-family-only versus support-only gain in every family, non-domination on the full declared cost frontier and no promotion from the single seed. Any missing source alias, baseline semantic mismatch, non-finite output, required-control timeout or preflight mismatch must stop before or block promotion after scoring as declared.
