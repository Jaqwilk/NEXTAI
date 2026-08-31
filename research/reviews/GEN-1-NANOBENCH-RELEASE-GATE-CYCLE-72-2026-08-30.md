# GEN-1 — NanoBench release and transfer gate, cycle 72

## Scope

This was one source-resolution and repository-tree audit. It created no dataset download, protected migration, hypothesis, experiment plan, candidate, scoring seed, runner invocation, score, result, dependency, external model/API, or benchmark mutation. The active `heldout_mechanism_recombination_v3` cohort remains unchanged.

Acceptance required a licensed, complete and immutable artifact; an executable published system-identification split; at least three independently held-out worlds with identical observable fields; no duplicate-content leakage; and a negative control separating shared dynamics adaptation from trajectory classification.

## Observation

### Rights and stable identity

The repository explicitly places the dataset and code under BSD-3-Clause. This passes the rights gate that rejected the previous two cohorts. The audited main commit is `0ae7d689749db174dc779ab2f7c416cc12e14e2b`; its complete Git tree was not truncated and can serve as an immutable identity for exactly the files it contains.

There is no tagged release or DOI-backed complete archive. The README explicitly says the complete NanoBench dataset will be deposited on a public repository after paper acceptance. The current commit therefore cannot be treated as the final 170-recording release.

### Claimed versus present artifacts

The paper and README describe 170 recordings, 27 trajectory types, about 603,942 timesteps and 97.5 minutes. The authoritative commit tree contains:

- 107 dataset CSV paths and 107 paired metadata paths;
- 87 unique CSV Git blob IDs and 87 unique metadata blob IDs;
- 18 duplicate-blob groups, producing 20 extra CSV names that are byte-identical to another named repetition;
- 290,797,892 bytes across the present CSV blobs when duplicate paths are counted.

The exact duplicates are concentrated in named trefoil repetitions. Distinct filenames and repetition indices therefore do not imply independent recordings. Any filename-random split could place identical content in training and test unless deduplication is performed before splitting.

### Missing system-identification protocol

The README documents `benchmarks/task1_sysid/run_nanobench_sysid.py` and a roughly 70/30 train/test conversion. In the authoritative tree, `benchmarks/task1_sysid` is instead a Git gitlink at commit `1038275426ba41135ac35afb1d8597c757b032b0`. The parent contains no `.gitmodules` mapping, and the GitHub contents record has a null submodule URL. The documented Task 1 files and exact split list are consequently unavailable. An open repository issue independently reproduces the same failure.

Without the splitter, it is impossible to verify whether trajectory type, speed, repetition, collection session, controller, battery range, or identical blobs cross the train/test boundary. The README's approximate percentage is not a frozen evaluation protocol.

### Multi-world identifiability

All 51 columns use a common schema, which is favorable. The data include trajectory, speed, controller and battery variation with multiple repetitions. However, the repository describes one Crazyflie 2.1 platform, and the inspected metadata identifies `CF_01`. Vehicle, sensor stack and coordinate ontology are therefore fixed in the available evidence.

The three advertised tasks cannot be counted as three worlds: system identification predicts next state, control predicts/actions motor commands, and state estimation compares EKF signals with Vicon truth. Their input/output contracts differ materially. A common learner across them would require a hand-written ontology or task dispatch, recreating the earlier confound.

The current files could eventually support a narrower leave-trajectory/speed/controller/battery-regime-out study, but only after an exact deduplicated split and full release are frozen. They do not yet prove three independent system worlds.

## Interpretation and uncertainty

NanoBench is materially better licensed and richer than NanoDrone, but the presently published commit is not a reproducible benchmark artifact. Confidence is `1.00` in the commit-tree counts and duplicate identities, `1.00` that Task 1 is an unresolved gitlink in this commit, `0.99` that the exact split cannot be reconstructed from published files, and `0.95` that the current data vary operating conditions rather than physical platforms. A future release may resolve every artifact issue; this decision applies only to commit `0ae7d689…`.

## Decision

`reject-current-release-before-download` for `nanobench_multiworld_dynamics_transfer`.

Passed gates:

- explicit BSD-3-Clause rights;
- uniform 51-column record schema;
- immutable Git commit identity;
- multiple trajectory, speed and repetition labels.

Failed gates:

1. incomplete release: 107 named/87 unique CSV blobs versus 170 claimed recordings;
2. exact duplicate recordings under different repetition names;
3. missing Task 1 source and frozen split caused by an unresolved gitlink;
4. no verifiable three-world system split and only one documented vehicle;
5. no tagged or DOI-backed final artifact.

Do not register HYP-0023, create EXP-0058, download/vendor the repository, realize a seed, implement a learner, or migrate the protected evaluator from this commit.

## Exact next discriminating step

In the next wake, perform one no-download primary-source gate on `DronePropA` as a same-schema multi-condition dynamics cohort. Verify its DOI/Mendeley version, CC-BY-4.0 coverage, file hashes, exact 130-flight inventory, vehicle IDs, healthy and defect type/severity factorial structure, actuator/state columns, independent repetitions, and whether at least three entire defect conditions or physical configurations can be held out while every constituent factor is represented in training. Require a content-deduplicated split, no filename/condition tags at candidate input, a condition-router negative control, healthy-only and independent-per-condition ablations, and matched classical system-identification baselines. If the conditions merely label faults without shared predictive dynamics, or files exceed the bounded local acquisition budget, reject before download.
