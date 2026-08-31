# GEN-1 — Real multisystem contract shortlist, cycle 137

## Scope

This was exactly one no-scoring public-metadata shortlist of three existing
perturbational single-cell resources: CausalBench, sci-Plex 3 and Tahoe-100M.
It downloaded no archive body, loaded no expression array, inspected no held-out
outcome and created no hypothesis, plan, seed, candidate, benchmark, schema or
evaluator change. The active cohort remains
`heldout_three_family_continuous_transfer_v7`.

The registered gate required at least three independent contexts, one
mechanically shared feature coordinate system, an existing unseen-intervention
split or enough immutable replication to freeze one without outcomes, three
genuine context/knowledge scales, negative controls, immutable cost and license
metadata, and source-identical classical baselines without biological ontology.
At most one resource could be retained, and retention authorizes only a later
feasibility audit.

## Public metadata boundary

| Resource | Immutable public reference | Recorded contexts | Public acquisition boundary | Decision |
| --- | --- | ---: | ---: | --- |
| CausalBench | repository `1a2143cffdc85f835b41ce8d52034be1bf903e71` and published article | 2 cell lines | not needed after structural failure | reject |
| sci-Plex 3 | GEO `GSE139944`; repository `079639c50811dd43a206a779ab2f0199a147c98f` | 3 cancer cell lines | 9.2 GB GEO supplementary archive | reject |
| Tahoe-100M | Hugging Face commit `2dc57900b7981cfcf5e211527169a0b006546a95` | 50 published; 47 used after QC | 429 GB reported | feasibility audit only |

No dataset body was downloaded. Repository references were resolved with
read-only remote metadata. The 429 GB Tahoe figure is the hosting page's
reported total, not a locally measured byte count; the later audit must pin the
complete file manifest and exact content identifiers.

## Resource observations

### CausalBench — reject

CausalBench exposes two perturbational contexts, K562 and RPE1. Its
observational, partial-interventional and full-interventional regimes vary how
much intervention data is visible inside those contexts; they do not create a
third independently recorded biological context. The resource therefore fails
before any question about feature alignment or baselines: two contexts cannot
provide distinct training, development and unseen-context transfer or three
source-context scales.

### sci-Plex 3 — reject

sci-Plex 3 is a coherent screen: A549, K562 and MCF7 were exposed to 188
compounds at four doses in duplicate, and the processed/raw release is public
as GEO GSE139944. It nevertheless contains exactly three relevant cancer cell
lines. Holding out one context leaves two source contexts. Manufacturing three
"scales" by selecting cells, wells or rows from those same contexts would test
sample efficiency, not growth in transferable knowledge. The publication does
not provide an immutable unseen-compound split that changes this context-count
limitation. The resource is rejected without inspecting expression outcomes.

### Tahoe-100M — retain for one feasibility audit only

Tahoe-100M is structurally different. The publication reports 50 cell lines,
with 47 sufficiently covered after QC, 379 distinct drugs, 1,135 drug-dose
combinations and 52,886 cell-line-drug-dose conditions. DMSO controls are
plate-matched, and sample identifiers distinguish replicate treatments. The
hosted raw-count table represents nonzero expression with stable integer gene
token IDs shared across cell lines. Thus neither human gene meaning nor a
hand-written cross-world ontology is needed to align measured coordinates.

Whole source-context counts can provide at least three genuine scales while
reserving unseen cell lines. Drug and cell-line identifiers also permit a split
rule to be defined by hashes before outcomes. Curated drug targets, mechanisms,
tissues, driver mutations, gene symbols and pathways are explicitly outside the
candidate contract. Stable gene token IDs are allowed only as mechanically
recorded coordinates.

This is not yet a migration decision. The full public artifact is reported as
429 GB and over four billion sparse rows on the hosting representation. The
current page exposes one `train` split, not a frozen NEXTAI train/development/
test contract. Coverage, negative-control replication, exact file digests and a
budget-feasible whole-context acquisition have not been verified locally.

## Baseline boundary

A later contract may proceed only if one raw-count/pseudobulk transformation is
frozen before outcomes and applied identically across contexts. Eligible
controls must consume the same anonymous token coordinates, intervention ID and
dose fields. They may include PCA/CCA-style projection, nearest-neighbor,
regularized linear/adaptive prediction and a simple intervention-aware
probabilistic control. They may not consume MOA, targets, SMILES, tissue,
mutations, semantic gene names, pathways or an external biological model.

Acquisition, parsing, aggregation, fit, query, updates, resident/peak state and
all stored source examples must be charged. Streaming cannot make uncharged
remote preprocessing disappear.

## Observation

CausalBench fails the minimum context count with two contexts. sci-Plex 3 has
exactly three contexts but cannot retain an unseen context and still expose
three genuine source-context scales. Tahoe-100M alone has the necessary
context breadth, common mechanical gene coordinates, negative controls and
identifier-level structure for outcome-blind splits and scaling. Its 429 GB
boundary and unverified coverage/digest manifest prevent immediate migration.

## Interpretation

One public resource is worth a bounded feasibility audit, not a scientific
experiment. Tahoe-100M could test whether transferable structure grows with
the number of complete source contexts on real measured data, while avoiding
the family-routing and hand-ontology defects of v7. But a convenient streamed
sample would be scientifically inadequate: it could silently select outcomes,
collapse replication or replace world scaling with row scaling.

No evidence for or against any NEXTAI learner changed in this cycle.

## Confidence

High confidence in both rejections because their context counts are explicit in
the primary publications. Moderate confidence in Tahoe retention: its high-level
structure is explicit, but exact condition coverage, content-digest completeness
and a local whole-context cost envelope remain unresolved without reading the
metadata manifest.

## Decision

`retain_tahoe_100m_for_feasibility_audit_only`.

Do not download expression shards, create a protected migration, create a
hypothesis or score a learner from this result.

## Exact next discriminating cycle

Perform one bounded, no-scoring `tahoe_100m_local_contract_feasibility` audit at
the pinned dataset commit. Read only repository/file manifests and the smallest
metadata tables needed to establish exact content digests, license, byte counts,
cell-line by drug-dose coverage, DMSO and replicate counts. Before reading any
expression outcome, define an outcome-blind identifier-hash proposal for train,
development and unseen cell-line/drug partitions and three whole-source-context
scales.

Pass only if every required partition has adequate controls and replication,
the same anonymous token-coordinate interface and source-identical baselines
apply everywhere, and an explicit acquisition/aggregation/fit/query/state budget
fits the configured local limits without row sampling. On failure record
`tahoe_100m_local_contract_infeasible` and return to an algorithmic portfolio
decision. On pass, only a separate later service wake may propose a protected
cohort migration; scoring remains another later wake.
