# Repository bytecode superinstruction feasibility — cycle 172

## Scope

This was one bounded service-only feasibility cycle. It created no hypothesis,
immutable experiment plan, candidate, scoring seed or scored result and changed
no protected evaluator, manifest, runner, schema or baseline. The active cohort
remains `heldout_repository_sequence_compression_v5`.

## Observation

The repository contains enough real code for a deterministic whole-module
split and three held-out length scales. Hash partitioning of 534 tracked source
modules yields 391 train, 60 development and 83 test modules. Among the test
modules, 14 have 16–127 function-bytecode instructions, five have 128–511 and
19 have at least 512.

That availability does not establish an executable capability boundary. Across
compiled source and tests there are 2,157 anonymous trace-signature groups when
the representation retains opcode, operand class and stack effect but removes
values and symbols. 129 groups are semantically ambiguous and contain 1,139
functions. A minimal counterexample remains after excluding global-symbol
access: 46 `state_bytes`-style functions share the same two-instruction payload
shape yet return different constants, including 64, 72, 96 and 128. The
candidate-visible program is therefore identical while the required exact
state transformation differs.

The runtime is CPython 3.13.13 (`cpython-313`), whose 150-entry opcode map has
SHA-256 `d488f62014e4909a5d7d0809beb8484b31b62ce60631572b171c33d07c11587e`.
Exact execution additionally depends on constant values, symbol resolution,
object and call semantics, imports, exceptions and version-specific opcode
semantics.

## Interpretation

There are only two possible benchmark boundaries, and neither tests the stated
learned-instruction mechanism. If values and CPython semantics are supplied,
the evaluator or candidate receives a hand-authored instruction ontology and
the task becomes macro scheduling over an existing interpreter. If they are
withheld, exact execution is not identifiable from the anonymous trace.

Sequitur/BPE can compress trace strings, and a profile cache can replay seen
blocks, but neither executes a new held-out transformation. Bounded search can
select macro segmentations only after semantics are supplied. Calling CPython
as an oracle performs the essential work outside the candidate. A supplied
program VM repeats the limitation already measured in EXP-20260830-0013;
EXP-20260830-0022 showed that removing the supplied program led the learned VM
to recover only 11/48 exact programs and to lose full cost to finite search.

## Decision

`no_repository_bytecode_superinstruction_contract`. Do not create or freeze
this cohort and do not reopen this branch by weakening exact execution to trace
compression, next-op prediction or cache hit rate. This is a feasibility
rejection, not scientific evidence against every learned VM and not a change to
HYP-0009 confidence.

## Breadth constraint and next step

This is the first consecutive no-scoring cycle after EXP-20260901-0029. At most
two further no-scoring cycles are allowed by the user's breadth rule. The next
wake may perform one minimal service selection for a genuinely different scout
only where an existing frozen cohort cannot express it; it must not spend the
cycle on another review of bytecode, rewrite systems, caches or sequence
compression. The selected route must lead to a cheap scored scout no later than
cycle 175, with no promotion from the scout and no post-result tuning.

The exact discriminating target for that selection is a raw-observation active
identification scout: learn both an anonymous nonlinear sensor representation
and a bounded probe policy from train worlds, then identify unseen worlds under
runner-random sensor transforms. It must compare against exhaustive
observation, random/fixed probing, PCA or random-feature plus certified decision
trees, kernel information gain and a privileged latent-sensor control, at three
hypothesis-set scales with complete acquisition/fit/probe/update/state and
R1/R4/R16 cost. Existing `active_information_acquisition_v1` cannot express
this because it supplies the labeled codebook, so the next wake may freeze only
the smallest versioned successor needed for that distinction and must create no
hypothesis, plan, seed or score.
