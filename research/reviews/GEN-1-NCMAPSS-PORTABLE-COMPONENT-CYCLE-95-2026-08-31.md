# GEN-1 — portable N-CMAPSS DS08a component, cycle 95

## Scope

This was one evaluator-preparation service cycle. It created no hypothesis, experiment plan, scoring seed, candidate, runner call or scientific score. It did not activate or mutate the protected cohort. The component contract was frozen before export code was added or portable bytes were produced.

## Observation

Direct HDF5 execution would depend on an environment-specific VTK DLL outside the protected repository. The frozen contract therefore permits only six source arrays required for public dynamics and evaluator boundaries. `A_dev/A_test` were converted losslessly to `int16`; `W_dev/W_test` and `X_s_dev/X_s_test` were converted by numeric cast only to `float32`. No rows were selected, shuffled or normalized, and private `T`, `Y`, virtual sensors, paths and HDF metadata were excluded.

The six atomic `.npy` files total `688,671,648` bytes and load through ordinary `numpy.load(..., mmap_mode='r')` without HDF5. Every shape and dtype matches the frozen contract, all values are finite, maximum scaled float32 error is `5.96e-8`, and every unit has at least `299,301` legal history-32/horizon-50 anchors contained within one cycle. File hashes and conversion statistics are frozen in the portable manifest.

## Interpretation and uncertainty

The component is now portable and cheap enough to memory-map inside an audited subprocess. This removes a genuine infrastructure dependency without hiding acquisition or conversion cost. It does not yet justify a standalone N-CMAPSS experiment: the user's research question requires one unchanged learner across at least three distinct families, and activating a single-family cohort would narrow that objective.

The float32 cast is lossy in absolute units but bounded at less than `5.96e-8` after scale normalization; any future evaluator must treat these frozen bytes as the cohort source rather than silently compare them with float64 HDF results.

## Decision

`freeze_portable_component_defer_protected_activation`. Preserve the active DronePropA v6 manifest and preflight unchanged. Do not create EXP-0060 or activate a one-family replacement.

## Exact next discriminating step

In a separate design-only wake, freeze one candidate-visible sequence interface shared without family dispatch by this DS08a component, frozen DronePropA, `nonlinear_local_state_transfer_v1` and `continuous_event_predictive_state_v1`. Define lossless serialization, equal public shapes, train/test-world separation, training-only normalization and a fixed simple family-router gate before inspecting router output. Reject before protected implementation if the interface exposes family identity above the frozen ceiling; otherwise authorize one later protected multi-family evaluator migration.
