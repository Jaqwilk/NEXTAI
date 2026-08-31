# Causal intervention v1

This quick cohort tests whether a learned factorized structural state composes
interventions that were never seen together. Each hidden world is a permuted binary
XOR chain. Training exposes two observational trajectories and every labeled
single-node intervention; queries always contain two interventions and half are
inconsistent with every observational trajectory.

The dense and local candidates learn the same parent and bias invariants. Dense
execution recomputes all K variables; local execution follows only the target's D+1
ancestors. Observational conditioning and exact intervention memorization test
correlation and episodic recall. The oracle receives the true chain and bounds the
cost of learning.

Operation counts charge structure search, query composition, and update validation.
This deterministic, fully observed, identifiable chain is intentionally an easiest
case. It does not test latent confounding, noisy data, perception, natural language,
or general causal discovery.
