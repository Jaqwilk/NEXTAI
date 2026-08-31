# GEN-1 — lt_crl real multiview contract review, cycle 135

## Scope

This was exactly one no-scoring, public-metadata-and-paper-only contract review
of `lt_crl_benchmark_v1`. It created no hypothesis, plan, seed, candidate,
benchmark, schema or evaluator change. It did not download the 2.76 GB archive,
load benchmark arrays, inspect held-out outcomes or invoke the audited runner.
The active cohort remains `heldout_three_family_continuous_transfer_v7`.

The eight gates were frozen append-only by cycle 134 before this review. Passing
all eight was required before a later service migration could be considered.

## Immutable public boundary

- dataset: `lt_crl_benchmark_v1` v1.0;
- dataset repository commit:
  `2f059123f4ac6f4724338154825630bf4ab74ac0`;
- official implementation commit:
  `2532cd4998695cccf566803b2061cb13be72496e`;
- published archive MD5: `8ec492afffd0142abd70b1fa7082b104`;
- HTTP HEAD content length: `2763884276` bytes;
- dataset license: CC BY 4.0;
- local free space observed: `130193059840` bytes.

The multipart S3 ETag was recorded only diagnostically and was not treated as
the published archive MD5. No bytes from the ZIP body were requested.

## Gate observations

### 1. Synchronized views, interventions and evaluator-only factors — conditional pass

The dataset rows pair each image with numeric sensor measurements and the five
actuator settings. The Buchholz experiments separate observational and five
single-target intervention environments; CITRIS provides an intervention flag.
An evaluator could replace environment names with opaque IDs and withhold
`R,G,B,pol_1,pol_2` from the learner. Thus the raw information needed for
pair-breaking and intervention-shuffle controls exists.

### 2. Frozen unseen-world split — fail

The official CCRL split is 80/10/10 while explicitly preserving the same
fraction of every intervention environment in every subset. Multiview CRL also
randomly splits the pooled 60K rows 80/10/10. CITRIS uses the first 80K steps for
training and the next 10K/10K from the same stochastic process, then evaluates
factor recovery on a uniform sample. None holds out a physical system, mixing
function or already-defined world.

Holding out one intervention file prospectively would create a new NEXTAI
cohort, not reveal an existing public unseen-world contract. More importantly,
all such environments share the same physical light tunnel and camera mixing
function.

### 3. Three common scientific scales — fail

The 60K interventional, 100K temporal and 2K uniform datasets are different
sampling processes serving different method assumptions. They are not three
scales of one causal transfer contrast. Artificial row subsamples would measure
sample efficiency inside one world and would not supply the required
knowledge/world scaling signature.

### 4. Ontology-free negative controls — pass

Opaque environment IDs and row indices suffice for view pair-breaking,
intervention-label shuffling and consistent channel permutations. These controls
need not expose semantic factor names to a candidate.

### 5. Matched classical controls and full cost — partial fail

PCA, ICA and CCA are meaningful on paired views. Autoregressive and adaptive
linear controls apply to CITRIS, while intervention-aware causal controls apply
to Buchholz environments. They do not operate on one common input/task
contract, so a single source-identical comparison would confound mechanism with
interface and task. End-to-end acquisition, preprocessing, fit, query, state,
peak memory and workload accounting is feasible but does not repair that causal
confound.

### 6. License, checksum, size and storage — pass

The official page supplies a CC BY 4.0 license and MD5 checksum. A metadata-only
HEAD request confirmed a 2,763,884,276-byte ZIP, and available local space was
about 130 GB. Storage is not the blocking condition.

### 7. Source-identical interface without ontology — fail

The official multiview experiment constructs four views using the known causal
structure of the tunnel and explicitly relies on ground-truth content selection
during training. The image, scalar sensor and temporal inputs also use different
method-specific adapters. Reusing those groupings would move the sought ontology
into preprocessing; replacing them with separate learned modality adapters would
violate the frozen source-identical learner requirement.

### 8. Transfer rather than exposed-label recovery — fail

All real protocols come from one Light Tunnel Mk1 camera configuration. The
published metrics recover its five actuator factors, their grouping or their
causal graph. This is a valuable real-world sanity check, but it cannot answer
whether one representation transfers across unseen physical worlds.

## Observation

Four gates pass fully or conditionally, one is partial, and four decisive gates
fail. The dataset is unusually well documented and scientifically useful, but
its existing contract tests representation recovery under one physical mixing
system rather than cross-world transfer.

## Interpretation

`lt_crl_benchmark_v1` should not be migrated into NEXTAI for the current
multi-world question. Doing so would either weaken the claim to within-system
factor recovery or require NEXTAI to invent the missing worlds, scales and view
ontology after reading a published benchmark. The failure is contractual, not
evidence against causal or multiview representation learning.

## Confidence

High confidence in the negative contract decision. The public README, protocol
generators, peer-reviewed paper and official implementation agree on the single
physical system, factor-recovery objective and split semantics. Uncertainty
remains only about whether a broader bundle of already published Causal Chamber
datasets can supply several physical systems through one anonymous numeric
interface; that is a different contract and was not inspected in this cycle.

## Decision

`no_existing_real_multiview_contract`.

Do not download the archive, create a hypothesis, migrate a protected cohort or
score a candidate from this result.

## Exact next discriminating cycle

Perform one no-scoring, metadata-only
`causal_chambers_cross_system_numeric_contract_review` over existing published
Light Tunnel and Wind Tunnel datasets only. Do not download their data.

The review must determine whether at least three already recorded physical
worlds/configurations provide a mechanically common anonymous numeric
observation/control interface, immutable unseen-world splits, three genuine
world/knowledge scales, source-identical classical controls and full-cost
metadata without using variable names, ground-truth graphs, simulators or
family-specific adapters. Inspect at most the official metadata for
`lt_walks_v1`, `lt_interventions_standard_v1`, `wt_walks_v1` and
`wt_pressure_control_v1`.

If fewer than three worlds share such a contract, append
`no_causal_chambers_cross_system_contract` and stop this dataset branch. If all
conditions pass, only a later service wake may propose a minimal protected
migration, and only a separate later wake may preregister scoring.
