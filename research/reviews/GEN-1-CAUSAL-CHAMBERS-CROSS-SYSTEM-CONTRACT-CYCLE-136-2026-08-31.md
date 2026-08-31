# GEN-1 — Causal Chambers cross-system contract review, cycle 136

## Scope

This was exactly one no-scoring public-metadata review of `lt_walks_v1`,
`lt_interventions_standard_v1`, `wt_walks_v1` and
`wt_pressure_control_v1`. It created no hypothesis, plan, seed, candidate,
benchmark, schema or evaluator change. It did not download archive bodies, load
data arrays, inspect outcomes or invoke the runner. The active cohort remains
`heldout_three_family_continuous_transfer_v7`.

Cycle 135 required at least three already recorded physical worlds or
configurations with one mechanically common anonymous numeric interface,
immutable unseen-world splits, three genuine scales, source-identical classical
controls and complete cost metadata. All conditions had to pass.

## Public metadata boundary

The inspected metadata is fixed at dataset repository commit
`2f059123f4ac6f4724338154825630bf4ab74ac0`.

| Dataset | System/configuration | Published MD5 | HEAD bytes |
| --- | --- | --- | ---: |
| `lt_walks_v1` v1.1 | Light Tunnel Mk1 / standard | `dcad019186661a56de7a2d1db97fc2f0` | 2,003,074 |
| `lt_interventions_standard_v1` v1.0 | Light Tunnel Mk1 / standard | `476664d024f88e8b7640998bb5e9ee33` | 3,909,455 |
| `wt_walks_v1` v1.1 | Wind Tunnel Mk1 / standard | `19bb4e92cbe0b8dff49299b9b509ac36` | 46,471,335 |
| `wt_pressure_control_v1` v1.0 | Wind Tunnel Mk1 / pressure-control | `8cb1c9bf19cedc5baea7a9c15e54af6a` | 694,810 |

All are CC BY 4.0. The combined compressed size is 53,078,674 bytes. The
multipart `wt_walks_v1` S3 ETag was not treated as its published MD5.

## Gate observations

### 1. At least three independent recorded worlds — fail

Four dataset names yield only three physical-system/configuration pairs because
both Light Tunnel datasets use the same standard configuration. More
importantly, `wt_pressure_control_v1` contains one 10K `hatch_0` experiment with
fixed exogenous settings. It does not supply independent training, development
and held-out worlds inside the third configuration.

Different intervention files within one Light Tunnel configuration are
environments of the same apparatus and mixing system, not additional physical
worlds. Counting them as worlds would weaken the registered transfer question.

### 2. Mechanically common anonymous numeric interface — fail

The two Light Tunnel tables share their signal schema with each other, and the
two Wind Tunnel tables share most of theirs. Between Light and Wind Tunnel,
however, the signal columns are disjoint. Their only literal common fields are
generic metadata: timestamp, configuration, counter, flag and intervention.
Those fields alone contain no useful physical prediction task.

Identifying which remaining columns are controls, sensor parameters or measured
responses requires variable names, the protocol's semantic `SET` targets or the
published ground-truth graph. The pressure-control table additionally exposes
PID input, error, derivative, integral, gains and output. Selecting or aligning
these by meaning would install a family-specific ontology before learning.

An exchangeable padding/mask serializer would not solve this. The different
native widths and PID-only fields mechanically identify the family, recreating
the routing confound already demonstrated in v7.

### 3. Immutable unseen-world splits — fail

`wt_walks_v1` alone has useful natural replication: ten random-walk seeds, five
slow/fast waveform runs and two 32-regime series. `lt_walks_v1` instead contains
different protocols rather than repeated draws of one protocol;
`lt_interventions_standard_v1` contains one reference and target/strength
environments; `wt_pressure_control_v1` contains one experiment. There is no
source-identical rule for train/development/unseen-world splits across all three
configurations.

### 4. Three genuine scales — fail

Source-run or regime count can be varied for Wind Tunnel standard, but the same
scale does not exist in Light Tunnel standard or Wind Tunnel pressure-control.
Using 1K/5K/10K row subsets would be sample-efficiency scaling inside fixed
worlds, not the required world/knowledge scaling.

### 5. Source-identical classical controls — fail

Persistence, VAR/RLS and autoregressive controls are appropriate for the walk
series. The Light Tunnel intervention collection is i.i.d. by construction, and
the pressure-control experiment is closed-loop with a PID. Defining a common
target and horizon would require configuration-specific logic. Therefore even
the baseline interface would violate the source-identical constraint.

### 6. Full cost and immutable metadata — pass

Licenses, checksums, archive sizes, experiment counts and sequence lengths are
public. Acquisition, parsing, fitting, querying, memory and workload could be
charged. This does not repair the missing causal contrast.

## Observation

Only the cost/integrity gate passes. Five scientific contract gates fail before
data acquisition. There are fewer than three independently repeatable worlds,
no nonsemantic signal interface shared between Light and Wind Tunnel, no common
three-scale axis and no common prediction task for classical controls.

## Interpretation

Combining these datasets would manufacture apparent breadth by padding unrelated
schemas and routing on masks or PID-only fields. It would repeat the exact v7
failure mode—regularization or family recognition without transferable
representation—while adding a human-written control/response ontology. The
branch is therefore closed rather than migrated.

This is a contract result, not evidence against learning reusable physical
operators. The public data were simply collected for different case studies,
not for a source-identical cross-system transfer claim.

## Confidence

High confidence. Dataset descriptions, variable manifests and experiment counts
directly establish the system/configuration identity, schemas and repetitions.
No outcome-dependent judgment or downloaded data was needed.

## Decision

`no_causal_chambers_cross_system_contract`.

Stop the Causal Chambers dataset branch. Do not download these archives, create
a protected migration, create a hypothesis or score a candidate from this
result.

## Exact next discriminating cycle

Perform one bounded, no-scoring `real_multisystem_contract_shortlist` using only
primary metadata for at most three existing public datasets outside Causal
Chambers. Start with perturbational single-cell resources because they can have
natural repeated entities, interventions and multiple experimental contexts.

Retain at most one source only if it already provides at least three independent
contexts with a shared mechanically recorded feature coordinate system,
pre-existing train/development/unseen-intervention splits or enough immutable
replicates to freeze them without outcomes, three genuine context/knowledge
scales, negative controls, public checksums/license/size and source-identical
PCA/CCA, nearest-neighbor, adaptive/probabilistic and intervention-aware
baselines. Stable measured feature IDs may be anonymized consistently but may
not be enriched with pathways, gene ontology or human causal graphs.

If none passes, append `no_public_real_multisystem_contract_shortlisted` and
return to an algorithmic portfolio decision rather than opening another dataset
branch. If one passes, only a later service wake may propose its protected
migration; scoring remains a separate subsequent wake.
