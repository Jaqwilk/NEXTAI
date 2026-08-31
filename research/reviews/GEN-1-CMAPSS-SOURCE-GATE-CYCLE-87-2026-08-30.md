# GEN-1 — classic C-MAPSS source gate, cycle 87

## Scope

This was one no-download, no-scoring primary-source gate. It created no hypothesis, EXP-0060 plan, candidate, seed, runner invocation, result, dependency, evaluator mutation or confidence update. The active v6 cohort and all immutable experiment history remain unchanged.

## Observation

### Provenance and scientific structure

NASA's official Open Data entry identifies one ZIP containing four same-schema multivariate engine-fleet datasets. Every row has unit number, cycle, three operating settings and 21 sensor measurements. The official counts total 708 train and 708 test engines. FD001/FD002 contain one HPC degradation mode under one/six conditions; FD003/FD004 contain HPC and fan degradation under one/six conditions. Training trajectories reach failure, while test trajectories stop earlier and have one true remaining-life value per engine.

This passes the basic same-schema and whole-engine separation gates. Unit IDs can be removed, chronology is explicit, and hundreds of independent engines are available. A single unchanged temporal learner could therefore be compared with pooled, per-engine adaptation, ARX/RLS/Kalman and autoregressive controls without inventing a cross-domain ontology.

### Rights and immutable identity

The exact official dataset page and ZIP-resource page both say `License not specified`. `accessLevel=public` establishes public access, not explicit redistribution terms. The CKAN record gives a stable resource ID and URL but leaves resource size, content hash and last-modified empty. A metadata-only HEAD request to the official ZIP returned HTTP 403, so this gate could not establish even a server validator without downloading content.

NASA-wide open-data guidance cannot silently replace a missing dataset-specific license because NASA pages may include third-party material and explicit restrictions take precedence. The original PHM paper also has an external GE coauthor. Local research use may be intended, but the required right to freeze or redistribute the exact archive is not proven. No mirror was treated as authoritative and no bytes were downloaded.

### Leakage and identifiability

Combining FD001–FD004 creates a trivial subset router: the number/distribution of operating conditions separates one-condition from six-condition groups, and those groups are coupled to the declared fault-complexity regimes. Removing a dataset label does not remove this observable source identity. Restricting evaluation to FD004 would avoid the four-subset router and still leave hundreds of engines, but public files do not expose a per-engine fault-mode label suitable for preregistering held-out fault combinations. It would test ordinary unseen-engine RUL generalization, not identifiable recombination of fault mechanisms.

RUL is also supervised asymmetrically: full training failures make per-cycle RUL derivable, whereas each censored test engine supplies only a final evaluator truth. A supposedly separate test-engine learner cannot be matched to a pooled supervised learner without carefully freezing what labels are available during adaptation. That protocol is possible, but it cannot be justified before artifact and rights gates pass.

## Interpretation and uncertainty

Classic C-MAPSS is substantially better aligned than heterogeneous three-family proposals because it provides one native contract and many engines. The rejection is not evidence against shared temporal representation learning. It is a source-contract rejection: exact rights and artifact identity are absent, and the advertised four-subset factorial structure does not expose per-engine factor labels needed to distinguish representation transfer from subset routing.

Confidence is `1.00` in the official counts and schema, `1.00` that the official metadata says `License not specified`, `0.99` that no authoritative size/hash/version was exposed in the audited interfaces, and `0.93` that an FD001–FD004 pooled success would remain confounded by observable subset routing. A written clarification or versioned repository could change the legal/artifact decision.

## Decision

`reject_before_download` for `classic_cmapss_shared_engine_representation`. Do not download or vendor `CMAPSSData.zip`, create EXP-0060, implement a learner, migrate an evaluator or realize a seed from this proposal.

## Exact next discriminating step

Next wake: perform one no-download gate on the newer N-CMAPSS DS02 source described by Arias Chao et al. Its primary descriptor explicitly declares the dataset CC0 1.0 and identifies six development engines plus three held-out engines with common flight/scenario/sensor/health fields. Verify the authoritative NASA artifact URL, exact release/version, published or computable digest, full size versus the 68.24 GB free-disk boundary, fixed engine/class split, candidate-visible versus evaluator-only health/fault fields, and a router/no-adaptation negative control. Only after every gate passes may a later protected evaluator migration occur; EXP-0060 remains forbidden until after that migration.
