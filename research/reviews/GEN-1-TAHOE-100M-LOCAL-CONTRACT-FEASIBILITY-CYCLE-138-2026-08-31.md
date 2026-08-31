# GEN-1 — Tahoe-100M local contract feasibility, cycle 138

## Scope

This was exactly one no-scoring feasibility audit of the Tahoe-100M public
artifact pinned at commit
`2dc57900b7981cfcf5e211527169a0b006546a95`. It read repository manifests,
dataset schemas and small public metadata rows. It downloaded no expression or
pseudobulk shard, read no expression outcome and created no hypothesis, plan,
seed, candidate, benchmark, schema or evaluator change. The active cohort
remains `heldout_three_family_continuous_transfer_v7`.

## Immutable artifact boundary

The complete public path/size/object manifest contains 4,427 files and
428,806,855,684 bytes. Of these, 4,419 large files expose content-addressed Xet
hashes. The deterministic SHA-256 over sorted
`path|size|object-id|xet-hash` records is
`3811015df8da65f672a9505a22167773b4deb8deb5653162310234721f35e7ad`.

| Collection | Files | Compressed bytes | Manifest SHA-256 |
| --- | ---: | ---: | --- |
| Sparse full-filter expression | 3,388 | 337,644,770,670 | `30ff1ada3c95b751ff9743ed2acd0f368b98f85fcb0831f4f0e7bf7c9a436fd3` |
| Pseudobulk differential expression | 1,026 | 88,859,715,303 | `339c390781bdda772e5e9260012afe4147a34f34158c0769e44ca15642938d80` |
| All metadata, including pseudobulk | 1,033 | 91,161,683,653 | included above |

The pinned `LICENSE.md` is CC0 1.0 and hashes to
`82fe759ab83e7619dfe956bb8b295b0ce640ed3706b68b871c15645a0f695a6b`.
This gate passes: provenance, version, content identifiers and acquisition size
are explicit.

## Metadata observations

The hosted schema reports 95,624,334 full-filter expression examples over one
62,710-token gene vocabulary. The separate observation table contains
100,648,790 rows and is 2,293,981,573 compressed bytes. The precomputed
pseudobulk representation has 4,089,820,780 gene-condition rows.

The 1,344-row sample table covers 14 plates and 380 treatment labels including
DMSO. There are exactly 28 DMSO samples, two on every plate. This establishes a
plate-matched negative-control design without inspecting expression values.

The small cell-line reference table contains 102 distinct Cellosaurus IDs,
whereas the experiment reports 50 lines and uses 47 after QC. It is therefore
an overinclusive annotation reference, not an authoritative eligible-context
manifest. Determining the actual context-by-drug-dose coverage requires scanning
the observation metadata; it cannot be inferred safely from names or the paper.

## Outcome-blind split proposal

Before any expression outcome, the following non-active proposal was fixed for
the feasibility test:

1. A context is eligible only from metadata if it has at least 100,000
   full-filter cells and at least 32 drug-dose conditions with at least 128
   treated and 128 plate-matched DMSO cells each.
2. Eligible Cellosaurus IDs are ordered by
   `SHA256("nextai-tahoe-contract-v1|context|" + id)`. The first 32 form the
   source pool, the next seven development and at least eight remaining IDs the
   unseen-context test set. Fewer than 47 eligible contexts is a gate failure.
3. The nested source scales are exactly 8, 16 and 32 whole contexts from that
   order. Every qualifying cell and condition from a selected context is used;
   row sampling is forbidden.
4. In development/test contexts, anonymous drug-dose keys are independently
   hash-ordered. The first 20% are public support and the rest are unseen
   context-by-intervention queries, provided each query key occurs in source
   contexts.

The candidate interface would expose only a cohort-local anonymous permutation
of stable gene-token coordinates, numeric dose and anonymous intervention keys.
Cell-line/drug names, tissues, mutations, targets, MOA, SMILES, gene symbols,
pathways and ontology are excluded.

This proposal proves that the split need not use outcomes or a hand ontology.
It is not frozen or authorized because the acquisition gate fails before the
eligible set can be materialized.

## Baseline boundary

In principle, zero response, per-intervention source mean, nearest-context by
public support, ridge/PLS, low-rank matrix completion and an empirical Gaussian
control can all consume the same anonymous token-dose-intervention interface.
Shared, independent, foreign-context-only and support-only roles could use
source-identical code and differ only in allowed contexts.

This is only a design-level compatibility result. No baseline runtime, state or
quality was measured, and no baseline was registered.

## Hard local budget failure

The C: drive had 129,784,401,920 free bytes (120.871 GiB) at the gate. The
project's previous real-data acquisitions preserve at least 40 GiB after a
bounded acquisition.

- The 337,644,770,670-byte raw collection exceeds all free space by
  207,860,368,750 bytes.
- The 88,859,715,303-byte pseudobulk collection alone would leave
  40,924,686,617 bytes (38.114 GiB), already 2,024,986,343 bytes below the
  40 GiB guard.
- Adding the required 2,293,981,573-byte observation table leaves 35.978 GiB,
  before a derived cohort, temporary extraction state, manifests or logs.

Streaming does not produce a valid escape. The pseudobulk data contain more
than four billion rows in 1,026 generic shards rather than context-addressable
files, so whole-context selection still requires a complete 88.86 GB scan. The
raw representation similarly uses 3,388 generic shards. The current environment
has no Parquet reader, and autonomous dependency installation is prohibited.

The official Arc distribution is fourteen plate-level h5ad files, not one file
per cell line. It is now hosted through a Requester Pays cloud bucket and its
documentation explicitly warns that local streaming is typically prohibitively
slow. Cloud billing/credentials and an unbounded remote preprocessing job are
outside the current autonomous boundary.

## Observation

Tahoe-100M has the desired scientific structure: many contexts, common measured
coordinates, interventions and matched controls. The immutable public artifact
does not fit the current local acquisition contract. Neither the raw nor
pseudobulk route preserves the required disk guard, and the data layout prevents
downloading only complete chosen contexts without scanning the whole collection.

## Interpretation

This is an infrastructure/resource rejection, not evidence against shared
representation learning. Creating a tiny streamed row sample would turn the
question into another toy sample-efficiency test and violate the preregistered
whole-context scale rule. Quietly using curated differential-expression subsets,
MOA or target annotations would also install the ontology that the experiment
is supposed to discover.

The branch should therefore close under current local resources. It may be
reconsidered only after a material external-state change: substantially more
safe local storage plus an approved Parquet dependency, or an official
context-partitioned immutable release with complete hashes. No such change is
assumed or requested by this cycle.

## Confidence

High confidence in the resource decision. File counts, byte totals, hashes,
schemas, free disk and installed modules were measured directly. Moderate
confidence in the scientific contract proposal because exact per-context
coverage remains deliberately unread.

## Decision

`tahoe_100m_local_contract_infeasible`.

Do not download Tahoe shards, create a protected migration, preregister a
learner or score this branch under current resources.

## Exact next discriminating cycle

Return to one no-scoring `post_real_data_gate_algorithmic_portfolio_review` on
the existing frozen cohorts. Synthesize cycles 125–138 and select at most one
genuinely different mechanism only if the current v7 or another already frozen
cohort can discriminate a qualitative three-scale signature against its strongest
classical controls without a schema change. Prioritize sparse inference whose
query cost is weakly dependent on knowledge size, local updates without global
retraining, declining inference cost with experience, or self-discovered OOD
operators. Do not reopen Tahoe/Causal Chambers, create another dataset search or
preregister during that review. If no existing cohort can discriminate such a
principle, record that result and identify the smallest missing measurement
rather than inventing another benchmark.
