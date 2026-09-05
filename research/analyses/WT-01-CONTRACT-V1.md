# WT-01 contract preparation — causal isolation before scoring

## OBSERVATION

The immutable audit records for `EXP-20260831-0006` and
`EXP-20260831-0007` resolve all three recorded dependencies from Git commit
`49525156586e765c07f96e2f41ea17c709a3debb`. The candidate source SHA-256 is
`4471f2a999f9432e9d2e6fb56d309ebe7af52cca6dff246ab1b439b38f035104`.
`nextai provenance` independently resolved those exact Git blobs without
executing historical code.

The rule fits next-state deltas from `[1, x_t, x_t-x_(t-1), u_t]`, recursively
feeds predictions, clips cumulative displacement to ±4 from the last revealed
origin and performs slot-local RLS after reveal. Before clipping this is exactly
an affine controlled VAR(2)/ARX rule:

`x_(t+1) = b + (I+A+B)x_t - Bx_(t-1) + cu_t`.

The old candidate NRMSE was `0.6728036610592184` versus
`1.0071290063754978` for the best complete simple control, but its R16 workload
was `16,683,197` operations versus `7,886,525`. The three-seed result reused the
same two physical test files and changed runner permutations; its metric values
were nearly identical. It therefore adds implementation/permutation robustness,
not three independent physical replications.

All ten `wt_changepoints_v1` files, including the former train 0–5, development
6–7 and test 8–9 files, have already been visible and used. No repartition can
make them fresh. The official `wt_walks_v1` metadata describes ten random-walk
seeds, repeated waveform runs and two regime-jump recordings from Wind Tunnel
Mk1 in the standard configuration. That is useful independent same-device data,
but it is a different actuation protocol and is not a replication of the
changepoint task. No archive or outcomes were downloaded or inspected here.

The frozen mechanism design contains all eight `R×U×C` cells. `R` changes only
recursive self-feeding after a first prediction, `U` changes only post-reveal
slot-local RLS mutation, and `C` changes only origin-relative clipping. The
`R1-U1-C1` cell must match the historical source and a separately named
VAR(2)/ARX implementation within `1e-12` before any score. The independent unit
is a physical recording, never a window, horizon or runner seed.

## INTERPRETATION

The historical result supports a narrow statement: this particular classical
adaptive and bounded recurrence produced better quality than the old control
set on two visible Wind Tunnel changepoint recordings. It does not yet show that
recurrence caused the gap. RLS may explain it, clipping may stabilize an otherwise
poor rollout, or their interaction may be decisive. The exact VAR identity means
the historical implementation cannot support architectural novelty by itself.

The clean next question is causal, not architectural: after keeping the same fit,
data, constants and reveal schedule, does recursive self-feeding add a meaningful
paired effect beyond RLS and bounding? The factorial and its interactions answer
that question. The separately named algebraic control protects against relabeling
a classical VAR/ARX model as a novel mechanism.

The currently available data can support historical diagnosis only. A replication
claim requires at least five fresh independently recorded traces under the same
load-in changepoint protocol. `wt_walks_v1` can later test robustness to a different
operation after an outcome-blind split, but cannot repair the missing replication.

## CONFIDENCE

Confidence is high that the historical source identity and algebraic equivalence
are correct because both immutable result hashes and exact Git bytes agree. It is
high that the three runner seeds are not physical replications and that the old
quality win is not an economic dominance result. Confidence is moderate that
`wt_walks_v1` can support a legal adversarial forecasting interface: primary
metadata establishes independent runs and the same physical configuration, but
no archive body or outcome was inspected and the interface has not been frozen.

There is intentionally no numerical smallest effect of interest yet. Importing
the historical `0.132526...` threshold would be arbitrary for this causal contrast.
Service cycle 2 must prospectively estimate measurement/numerical noise and freeze
a development-only scale before final access, or scoring must remain blocked.

## ALTERNATIVE EXPLANATIONS

- The old gap may be entirely due to post-reveal RLS, not recursive dynamics.
- Clipping may turn an unstable linear rollout into a bounded heuristic and account
  for most of the observed gain.
- The two test recordings may favor the exact control levels or transition order;
  seed invariance does not address this source-specific sampling explanation.
- A competent nonlinear NARX model might capture residual structure, but adding it
  inside this mechanism factorial would alter a second fundamental factor. It is
  justified only as a separately preregistered question if a residual survives on
  development data after the exact VAR identity is verified.
- A future `wt_walks_v1` failure could reflect task/protocol shift rather than failure
  to replicate the changepoint effect; it must be interpreted as adversarial scope.

## DECISION

Keep the WT-01 mechanism contract and do not score. Treat the historical positive
as real but causally unresolved and economically non-dominant. Freeze the eight
cell semantics, VAR identity control, independent-unit policy, failure reporting
and claim boundaries. Mark same-protocol replication as a hard data blocker.
Do not update numerical beliefs, promote an architecture, train, download data or
register an experiment in this cycle.

## NEXT DISCRIMINATING EXPERIMENT

First perform one separately authorized final WT-01 service cycle, still without
scoring: decide whether fresh same-protocol physical recordings can be acquired;
if yes, hash-bind at least five outcome-blind recordings and their split. If not,
explicitly narrow WT-01 to historical diagnosis. Then implement one source-identical
factorial core and a separately named algebraic VAR(2)/ARX control, prove exact
fixture equivalence, freeze measurement-noise/effect thresholds and all cost fields,
and stop again before any scored runner invocation. `wt_walks_v1` may be acquired
only as a separately labeled adversarial source after size/checksum and free-space
checks; it must never be substituted for same-task replication.
