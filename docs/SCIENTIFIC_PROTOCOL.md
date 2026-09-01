# Scientific protocol

## Protocol version

Protocol v2 became active after the 35-result G0 portfolio audit. It preserves every v1 plan and result but applies the rules below only to new cohorts. EXP-20260830-0036 is preserved and append-only invalidated; it was never scored.

## Unit of research

The unit is not a code change. It is an immutable tuple:

```text
(hypothesis, prediction, intervention, controls, budget, observations, decision)
```

Every scored run has a preregistered JSON plan and a result whose `plan_sha256` matches the append-only registry.

## Evidence hierarchy

From weakest to strongest:

1. intuition or verbal mechanism;
2. one implementation on one visible toy task;
3. controlled ablation with a meaningful baseline;
4. multi-seed replication;
5. adversarial and OOD variants;
6. transfer to a different task family;
7. matched-capability scaling curve;
8. independent or blind replication.

Statuses must reflect this hierarchy. `promising` requires at least level 4 plus a prior-art check. `promoted` requires the configured gates and a concrete reason to allocate deeper compute.

## Preregistration

A valid plan states:

- one causal question;
- the changed principle;
- matched controls;
- K/D/seeds/budget;
- primary metrics and directions;
- quantitative or qualitative predicted signature;
- kill and promotion evidence;
- alternative explanations and confounds;
- conclusions permitted for positive, null and negative outcomes.

Editing a registered plan invalidates it. Create a child plan instead. Protocol-v2 plans commit the evaluator digest. Candidate implementation may follow preregistration and may update only the candidate bundle; changing the evaluator digest requires append-only invalidation and a new plan.

## Baselines

Choose baselines that isolate the question:

- negative/random control to detect evaluator leakage;
- simplest heuristic;
- appropriate symbolic/algorithmic solver;
- conventional neural control when the task tests learned representations;
- strongest relevant prior architecture that fits the same budget.

Never compare a specialized structured solver with a general LLM and call lower cost a win. Conversely, do not force an LLM baseline onto a task where an indexed table is the scientifically appropriate control.

## Budgets

`quick` may kill an implementation or reveal a large signal. It cannot promote a family.

`screen` uses at least three runner-realized scoring seeds and a broader K/D grid. It can justify `promising` only when the implementable effect is non-dominated and robust.

`deep` is reserved for replicated principles, targeted scaling measurements, or an experiment whose information value justifies the cost.

Within a cohort, every compared candidate receives the same matrix and limits. Unsupported scales are recorded, not silently removed.

## Randomness and uncertainty

- The plan fixes the scoring-seed generation method, count and range. Exact scoring seeds are sampled by the runner only after plan validation, integrity verification and transitive candidate-source audit, then stored in the immutable result.
- Fixed development seeds are public and disjoint in purpose: they may be used for debugging but never reported as blinded scoring evidence.
- Report realized seeds, per-seed values, mean, relative dispersion and failed seeds.
- Do not use repeated seed search as architecture search.
- A surprising effect requires the configured replication count and an adversarial variant.
- Latency is a noisy systems metric. Use repeated measurements and interpret exact operation counts separately.

## Observation versus explanation

Each analysis has six sections:

1. `OBSERVATION`: numbers and externally visible behavior only.
2. `INTERPRETATION`: candidate causal account.
3. `CONFIDENCE`: calibrated probability or low/medium/high with reasons.
4. `ALTERNATIVE EXPLANATIONS`: at least one credible competitor.
5. `DECISION`: keep, discard, inconclusive, replicate or promote.
6. `NEXT DISCRIMINATING EXPERIMENT`: cheapest test separating explanations.

“Candidate A scored higher” is an observation. “Local computation causes the gain” is an interpretation until an ablation isolates locality.

If a post-result audit discovers a preregistered invalidation condition, preserve the immutable result and append an `experiment_scientific_validity_correction` event with a reason. Doctor validates each correction. Reports and hypothesis-transition gates exclude scientifically invalid results even when their technical integrity hashes passed. Invalidity is terminal for that experiment ID; a corrected test requires a new plan and result.

## Kill rules

Reduce priority when repeated discriminating tests show any of:

- no held-out composition;
- dependence on a human-written ontology that carries the solution;
- full scans of dormant knowledge;
- compute or bytes moved grow with irrelevant K;
- large external model does the essential work;
- no path from the toy representation to learned real inputs;
- architecture collapses into an existing baseline without a distinct signature;
- improvements disappear under matched capability/budget.

Stop patching a family when patches change the thesis rather than test it. Preserve it as `dormant` or `falsified` with evidence.

## Scaling inference

A two-point log-log slope is descriptive screening evidence only. Inferential slope fields require at least three distinct scale points and include point count, regression standard error and R². Strong scaling claims require a broader range, interaction-aware specification and an adversarial variant; a perfect two-point fit is not uncertainty evidence.

## Promotion rules

Promotion requires all configured gates and at least one unusual property:

- near-zero K slope at fixed bounded relevance;
- strong systematic/OOD composition;
- reusable learned operations;
- local continual updates;
- declining warm inference cost with experience;
- favorable scaling relative to a strong matched baseline;
- transfer across task families.

The result must be on the accuracy-gated **implementable** Pareto frontier. Oracle candidates are reported separately as attainable lower bounds and can never be promoted. Missing metric values never count as favorable comparisons; only axes measured for every row in the cohort enter dominance.

The CLI enforces the configured minimum seed count, maximum seed CV, minimum per-cell accuracy, integrity, analysis presence, primary-source prior-art linkage and non-dominance. `promoted` additionally requires multiple qualifying cohorts, an adversarial or transfer variant and at least one deep result.

## Benchmark evolution

Protected harness files are frozen in `research/eval_manifest.json`.

Protocol v2 protects the complete local Python harness and candidate tree, tests, schemas, dependency lock, configuration and scientific contract. Re-freezing archives the previous manifest by content hash before writing the new one.

A valid harness correction or new benchmark requires:

1. document the defect or new question;
2. increment `benchmark_version`;
3. create a new comparison cohort;
4. rerun required baselines;
5. freeze a new manifest;
6. never compare old and new metrics as if identical.

Autonomous scheduled cycles may not perform this migration without user approval.

## Cross-family transfer cohorts

A cross-family claim requires one source-identical candidate and update rule across at least three frozen existing world families. The evaluator may serialize public observations into one common format, but may not expose family labels, native type names, oracle fields, hand-derived roles or separately tuned hyperparameters. Training-world seeds are public and fixed in the immutable plan; test worlds derive only from runner-realized scoring seeds after integrity and source audit.

The plan must include a machine-readable `transfer_protocol` naming the families, training seeds, shared candidate, specialist controls, declared horizons and invalidation rules. Test-result access during meta-fit, a train/test seed collision, family-specific candidate logic, test-time tuning or oracle-derived serialization invalidates the cohort rather than becoming a negative score.

Report overall unseen-world transfer and the minimum family mean. A high average cannot hide failure in one family. Full accounting includes observation acquisition, common serialization, pooled meta-fit, test support fit, updates, queries, bytes moved, all resident state and the declared repeated-use workload. A specialist ensemble pays the summed costs and states of every component. Native oracles remain separate lower bounds.

One scoring seed can only kill an implementation or justify a replicated screen. Cross-family success additionally requires the shared candidate to beat its no-cross-family ablation and avoid implementable Pareto dominance by a simpler shared probabilistic control or the fully charged specialist suite.

## Nonstationary online-update cohorts

An online-update claim uses a strict prequential boundary: the candidate predicts from the current public observation before the evaluator reveals its target, and only then may mutate fast state. Fit may inspect fixed-seed meta-training streams but never runner-random test observations, targets, schedules or coefficients. A test query contains no mechanism, regime, phase, boundary or future-time field. Violation invalidates the cohort rather than becoming a low score.

The immutable plan must include `online_update_protocol` with at least three mechanisms, fixed training-stream seeds, runner-random test-seed source, the shared candidate, classical controls, state budgets, horizons and invalidation rules. One source-identical slow model, feature rule and update law serves every anonymous test slot. An independent per-mechanism fit is an ablation, not a shared learner.

Report normalized prequential capability, minimum mechanism, worst phase, post-switch recovery, recurrence retention, distractor interference and raw loss. Full cost includes observation/target acquisition, feature construction, pooled meta-fit, every chronological query and update, bytes read/written, replay or dictionary storage, peak resident state and R1/R4/R16 workloads. Oracle segmentation is privileged and reported separately.

Required nulls include no update, LMS/delta, RLS/Kalman where realizable, a declared nonlinear feature or kernel estimator, change-point model banks and bounded replay/dictionary memory. A learned update must beat its independent ablation and the strongest fixed adaptive estimator at matched capability, remain within the declared state boundary and be implementably non-dominated. One seed may kill an implementation or authorize replication; it cannot promote.

## Lossless cross-family transfer v2 cohorts

Version 2 reuses the four frozen probabilistic, predictive-state, local-dynamics and behavioral-program world generators. Fixed development seeds create training worlds; every test world is derived only from runner-realized scoring seeds. All derived seeds must be disjoint.

The implementable interface is one lossless recursive serialization of public dataclasses, mappings, sequences, booleans, integers, floats and nulls. It preserves structural markers and every public value while omitting field names, class names, family labels, paths, native types, oracle objects and latent roles. Truncation, family-specific adapters and post-test tuning invalidate the cohort. Slow parameters are pooled once and frozen before test-world queries; test updates are explicit and charged.

One source-identical learner, representation rule, head, state limit and hyperparameter set serves every anonymous test slot. The causal transfer control is the same learner trained independently by family. Required shared controls are contextual Chow–Liu, empirical joint and autoregressive models; fully charged specialist suites use the same three model classes through native public views. Oracles are privileged lower bounds only.

Primary capability is runner-seed unseen-world accuracy, with minimum-family accuracy as a hard guardrail. Success requires a material advantage over the independent ablation, no family collapse and implementable Pareto non-dominance after charging acquisition, lossless serialization, pooled and support fit, all queries and updates, bytes touched, peak/resident state and R1/R4/R16 workloads. A one-seed quick can discard or authorize a replicated adversarial screen, never promote.

## Shared predictive-state transfer v3 cohorts

Version 3 preserves the v2 lossless public boundary and the same four frozen generators, but changes the tested causal mechanism. The shared candidate is one width-32 recurrent predictive-state update and readout rule whose slow parameters are fitted once over pooled training worlds. The independent ablation is source-identical except that the same rule is fitted separately to anonymous training-world groups before matching test support; no family label, native type or specialist branch is available to either candidate.

Test support may initialize world-local state only through the same frozen recurrent rule, and all support scanning, state construction and storage are charged. Test queries and targets remain absent during fit. The mandatory controls are the actual native contextual Chow–Liu, empirical-joint and autoregressive specialist suites plus a privileged oracle. Mislabeled nearest-template modes from v2 are not controls in this cohort.

Success requires at least `0.95` overall and `0.90` minimum-family transfer, at least `0.05` advantage over the source-identical independent ablation on both measures, and no Pareto dominance by an implementable specialist suite after acquisition, pooled/independent fit, support adaptation, queries, updates, state, bytes moved and R16 work. Quick remains one-seed screening and cannot promote.

## Relation-fragment graph transfer v4 cohorts

Version 4 retires the repeatedly failed recurrent-state route while preserving the v2 lossless public encoder, the same four generators, fixed training seeds, runner-random disjoint test worlds and native specialist controls. The changed causal mechanism is an anonymous graph of at most 64 induced input-output relation fragments. One frozen extractor creates typed structural fragments without field names, classes, family labels or native objects; one equality-join rule composes fragments and emits output components.

The shared candidate induces one pooled fragment graph. Its source-identical independent ablation differs only by inducing separate anonymous graphs before the same charged support matching. Atom relabeling and anonymous-world permutation must commute with extraction, composition and decoded output. A protected two-fragment fixture must require a translated two-component answer that no single stored complete example can emit. Retaining or selecting full training examples without a multi-fragment trace invalidates the cohort.

## DronepropA factor recombination v6 preflight contract

Version 6 is a maintenance-only successor to v5. It preserves the frozen data split and scoring task while adding a pre-seed certificate over the evaluator digest, runner, result/plan schemas, semantic baseline registry and evaluation manifest. A mismatch blocks the runner before seed realization. Final result metrics use shared domains: NRMSE and charged costs are nonnegative, accuracies and rates lie in `[0,1]`, and continuous conditional log loss may be any finite real number. Pareto axes are the plan's frozen benchmark contract; failed, timed-out or metric-incomplete candidates remain recorded but cannot delete axes or enter the implementable frontier. Any mandatory control that fails to complete blocks promotion.

The former v2 controls with `oracle` in their names remain immutable historical records. In v6 their unchanged computations are registered as `privileged_all_condition_support_arx_v3` and `privileged_same_condition_support_arx_v3`: privileged support controls, not oracles, bounds or promotion candidates. Their support acquisition, fit, query and state remain fully charged, and v6 reports a signed `privileged_support_gain` rather than an oracle-gap claim.

Every plan fixes the 64-fragment cap, `typed_equality_join_then_component_emit_v1`, the same four native suites, state boundary and all acquisition, fit, meta-fit, query, update, bytes, resident/peak state and R16 directions. Success retains the v3 thresholds: at least `0.95` overall, `0.90` minimum-family, a `0.05` shared advantage on both capability measures and no implementable Pareto dominance. One quick seed can discard or authorize adversarial replication only.

## Held-out parallel masked-infilling cohorts

The corpus is a frozen whole-file SHA-256 split disjoint from the repository-compression cohort. Training and validation bytes are visible only through anonymous file slots. Runner-random scoring seeds choose a 256-byte relabeling, test files and mask offsets after integrity and candidate audit; the same unknown relabeling applies to train, validation and test bytes. Local visible source remains screening evidence, not an independent hidden holdout.

One public refinement query contains a corrupted snapshot, the positions still masked and the current/maximum round. A candidate must return distributions for every currently masked position from that immutable snapshot in one call. The evaluator validates the complete batch before filling any position, then reveals only candidate-selected predictions between rounds. Truth is never revealed to an implementable candidate. Within-round teacher forcing, filesystem/path access, future snapshots or target access invalidate the cohort.

Span lengths are registered independently of refinement rounds and include a span longer than every quick round count. Report conditional bits per byte, byte accuracy, exact-span accuracy, maximum declared critical-path steps, every position-round probability and full work. Critical path includes candidate-declared internal sequential steps plus logarithmic confidence selection/reveal depth; source audit must reject hidden per-position dependencies. These counts are algorithmic estimates, separate from measured latency.

Mandatory controls are uniform and unigram sanity bounds, left-to-right PPM, context-tree weighting, a small dense autoregressive model, exact finite-order bidirectional Markov inference, parallel fixed Markov belief propagation, the same masked learner in one pass, and a privileged conditional oracle. Full accounting includes corpus verification and relabeling, allocation/corruption, fit/validation, every probability, confidence sort/reveal, bytes touched, resident/peak state and R1/R4/R16 workloads.

Baseline names are not semantic evidence. Before scoring, conformance tests must show that PPM and context-tree controls use registered higher-order context on a sequence where a first-order transition model is ambiguous; analogous named controls require a discriminating semantic fixture rather than only import and shape checks.

Quick success requires a preregistered loss and exact-span margin over implementable controls, strict improvement over the one-pass ablation, bounded critical depth as span length grows, and implementable Pareto non-dominance on quality, total work, critical path and state. A one-seed quick can discard or authorize a new-corpus three-seed screen; it cannot promote.

Reject before planning if fixed bidirectional inference solves all registered spans exactly, targets are not probabilistically identifiable beyond a uniform bound, simultaneous snapshot execution cannot be audited, or corpus/mask metadata leaks.

Version 3 is a service-only successor to masked infilling v2. It preserves all
48 whole-file hashes and roles, runner-random byte relabeling, masks, spans,
rounds, immutable-snapshot execution, metrics, cost formulas, state boundary,
seed policy, Pareto axes and eight classical controls. It changes only the
prospective causal roles to a locally learned sparse predictive code, its
source-identical forced-one-pass ablation and its source-identical frozen-code
ablation. The three roles must share patch geometry, latent width, sparsity,
initialization, data order, decoder and output rule; only inference iteration
and code learning may differ as preregistered. No candidate exists in the
migration cycle. Historical v1/v2 plans, results, analyses and manifests remain
immutable and are never reinterpreted.

The v3 quick plan generator must emit K=`8/32`, refinement rounds=`1/4/6`
and eight cases per K/round cell. A single-round global quick default is invalid
because it makes the learned iterative role observationally identical to its
forced-one-pass ablation.

## Held-out repository sequence-compression cohorts

A real-sequence screening cohort uses immutable, hashed, whole-file train/validation/test roles. An implementable candidate receives only evaluator-supplied anonymous bytes: never paths, roles, file names, extensions, hashes, test offsets, future bytes or filesystem access. Corpus mismatch, fragment-level splitting or cross-slot test-state leakage invalidates the cohort. Local visible source is screening evidence only.

The immutable plan must include `compression_protocol`, runner-random scoring seeds, a predict-then-reveal boundary, a bounded state budget and explicit invalidation rules. `knowledge_size` is the declared offline byte budget; `reasoning_depth` is raw context length. Test updates may mutate only slot-local fast state. Shared slow parameters remain frozen, so cold held-out performance is reported separately from online adaptation.

Report mean, worst-file and cold bits per byte plus top-1 byte accuracy. Full accounting includes corpus verification/acquisition, train and validation selection, fit/meta-selection, every 256-way probability query, every revealed-byte update, bytes touched, resident and peak state, and R1/R4/R16 workload. Required implementable nulls are unigram, variable-order PPM, context-tree weighting, LZ-style dictionary prediction and a small dense autoregressive model; uniform coding is a sanity bound and a test-table oracle is privileged. One seed cannot promote.

Version 3 is a service-only successor to repository compression v2. It preserves
all 43 whole-file hashes and roles, anonymous bytes, predict-then-reveal order,
K=`8/20/32`, D=`4/16/64`, query allocation, loss and cost formulas, state
boundary, seed policy, Pareto axes and six classical controls. It changes only
the prospective three causal role identifiers from the completed layer-local
credit experiment to an orthogonal recurrent reservoir, a source-identical
recurrence-disabled ablation and a source-identical frozen-readout ablation.
The next immutable plan must freeze every reservoir constant before candidate
implementation. Historical v1/v2 plans, results, candidates and manifests
remain append-only and are never reinterpreted.

## Held-out anonymous mechanism-recombination cohorts

This cohort tests a narrower claim than raw cross-family representation learning. Three existing deterministic mechanisms are normalized by one frozen numeric rule and lifted by the same Feistel construction onto 144 opaque states. Implementable candidates receive only anonymous state-to-state examples with equal public shapes; module names, source families, native types, extraction paths and composition graphs remain evaluator-only.

Training contains singleton mechanisms and registered ordered-pair factorial coverage. The ordered `CB` pair is absent from training while both constituents and both order positions are present. Runner-random scoring seeds conjugate every state ID with one common permutation, shuffle anonymous worlds and choose support/query partitions only after integrity, semantic-baseline and candidate-source audit. Any train/test composition overlap, shape classifier above chance plus `0.10`, privileged metadata exposure or post-score tuning invalidates the cohort.

Mandatory implementable controls are unigram, order-5 Markov, complete-map nearest-template and exact MDL module-library search. The same learner fitted independently and without cross-mechanism sharing are causal ablations. The composition-graph oracle is privileged and reported separately. Baseline names require registered implementation/test hashes and discriminating semantic fixtures before scoring-seed realization.

Report held-out accuracy and minimum-combination accuracy. Full accounting includes acquisition, common serialization, structure search/meta-fit, support fit, all queries and updates, bytes moved, resident/peak state and R1/R4/R16 workload. Success requires at least `0.95` held-out and `0.90` minimum-combination accuracy, a `0.10` advantage over both source-identical ablations and no implementable Pareto dominance. One quick seed can discard or authorize a three-seed adversarial screen; it cannot promote.

Version 2 preserves the v1 worlds, split, public/privileged boundary, metrics, directions, budgets and seed policy. It corrects only result serialization, candidate-semantic digest roles and durable post-seed failure recording. V1 and V2 results are separate cohorts and must not be presented as identical runs.

Version 4 is a visible synthetic experience-curve cohort over the same three frozen source mechanisms. It trains on anonymous length-one/two operator views, holds out the length-four `CBAC` composition, supplies raw-distinct exact-equivalent pairs and pair-breaking negatives, measures exposures 1/4/16 at K=8/32/128, and tests local mutation plus retention. Mandatory implementable controls are exact interpretation, raw-key cache, structural-result cache, canonical-table cache, verified anti-unification cache, nearest canonical fallback and random output. A one-seed result is scout evidence only.

Version 5 is a maintenance-only successor to v4. It preserves every source table, split, term encoding, candidate, control, K/exposure cell, query, mutation, metric formula, direction, budget and seed policy. It adds the already emitted `continual_new_fact_accuracy` trial field to the common aggregate summary and freezes universal Pareto axes to exact quality, false reuse and full acquisition/fit/query/update/state/bytes/R1/R4/R16 costs. `reuse_coverage` remains diagnostic and cannot prevent a simpler exact control from dominating. Historical v4 and EXP-20260901-0002 remain immutable and scientifically invalid; they are never recomputed or reinterpreted.

## Held-out DronePropA factor-recombination cohorts

The v1 cohort uses the DOI-pinned DronePropA version-1 archive and a frozen whole-MAT-file split. Implementable candidates receive anonymous slots containing only QDrone motor-command rows 47/49/51/53 and gyroscope/accelerometer rows 27–32. Source names, paths, hashes, fault/severity, speed, trajectory, drone, repetition, timestamps and all other channels are evaluator-private. Defective ESC rows 48/50/52/54 are excluded uniformly; raw files remain unchanged.

Train, validation and test contain 64, 8 and 24 whole flights. The unseen test pairs are F1/SV3, F2/SV2 and F3/SV1; validation is F3/SV3. Healthy D2/D3 flights are OOD diagnostics only and all t4 flights are reserved adversarial evidence. No file or history/target window may cross roles. Candidate-visible normalization uses training anchors only.

One-step prediction is teacher-forced. Ten- and 50-step predictions are recursive state rollouts with evaluator-supplied future motor controls delivered identically to every model; future state targets remain hidden. Test adaptation is restricted to 32 deterministic examples in the first fifth of the central usable interval. Runner-random evaluation anchors are realized only after integrity, baseline semantics and source audit.

Mandatory controls are persistence, pooled ridge ARX, RLS ARX, nearest operator template, source-identical independent ARX, no-sharing pooled ARX, empirical Gaussian joint and contextual Gaussian Chow–Liu. A fully charged condition specialist and same-condition oracle are privileged diagnostics excluded from the implementable frontier. Every named control requires an exact version/specification, implementation hash and discriminating conformance-test hash before scoring.

Report mean, worst-flight, worst-condition and per-horizon normalized RMSE, conditional log loss where defined, finite/stable rollout rate, minimum condition/trajectory transfer gain and oracle-gap closure. Full accounting includes archive acquisition, extracted-byte verification, preprocessing, pooled fit, adaptation, query/update work, bytes touched, resident/peak state and R1/R4/R16 totals. Success additionally requires positive transfer in all three held-out conditions and at least three trajectories, advantage over the source-identical independent/no-sharing controls and no Pareto domination. One seed cannot promote.

Version 1 remains in maintenance and has no scientific results. A pre-score execution audit proved that every exact held-out fault/severity pair is absent from training, so the registered exact-condition specialist and same-condition oracle are undefined on all test flights. They may not silently fall back to another condition or use reserved `t4` targets. A corrected evaluator requires a new cohort version with renamed, explicitly identifiable privileged controls before activation.

Version 2 preserves the 64/8/24 train/validation/test files, candidate-visible boundary, anchors, normalization, horizons, metrics and implementable controls. It changes only the 26 `t4` files from unused adversarial reserve to evaluator-only `privileged_oracle_support`. The fully charged condition specialist fits all 26 support flights and dispatches by exact evaluator-private condition. The same-condition oracle fits only the six support flights matching the three test conditions. Both are privileged, forbidden to implementable candidates, barred from Pareto evidence and charged for support acquisition, preprocessing, fit, state and queries. Test targets remain forbidden. V1 and v2 are separate cohorts; no v1 result exists.

Version 3 is a pre-score metadata-wiring correction over v2. It preserves the v2 corpus, split, execution path, candidates, controls, budgets, thresholds, seeds and every numerical metric. It only registers the already-required `workload_ops_r1` and `workload_ops_r4` axes as minimized costs so the CLI can create a schema-valid immutable plan. V2 and v3 remain version-separated cohorts; v2 has no scientific result.

Version 4 is a second pre-score schema-wiring correction over v3. DronePropA evaluates fixed rollout horizons 1/10/50 inside every cell, so its generic `reasoning_depths` matrix is intentionally `[1]`; duplicating D would repeat identical trials. V4 permits one D value only for `heldout_dronepropa_*` plans while every other cohort retains the historical minimum of two. Corpus, split, execution, controls, metrics, directions, budgets, thresholds and seed policy are unchanged. V3 and v4 are version-separated cohorts and neither v2 nor v3 has a scientific result.

Version 5 is a post-EXP-0058 result-integrity correction over v4. Continuous `conditional_log_loss` is a differential log-density score and may be any finite real number, including negative values; its minimize direction and formula are unchanged. After each candidate process, the parent atomically stores a supervisor-normalized artifact before aggregate validation, including timeout, memory-limit, audit-failure and crash outcomes, and hashes those artifacts in any post-seed failure event. Corpus, split, execution semantics, candidates, baselines, matrices, budgets, thresholds and seed policy are unchanged. EXP-0058 remains terminally invalid and is never reinterpreted.

## Claims language

Allowed early claim:

> On successor_graph_v1, candidate X preserved exact accuracy while measured query operations had a K slope near zero over the preregistered range.

Forbidden early claim:

> Candidate X proves knowledge and computation are decoupled or replaces LLMs.

## Held-out WT changepoint prequential v1 cohort

This local-visible screening cohort uses the frozen Causal Chambers
`wt_changepoints_v1` archive. Whole files 0--5 are fit-only, 6--7 are
development-only and 8--9 are test-only. The archive, manifest and all ten CSV
hashes are immutable. Test files remain locally inspectable, so results are
screening evidence rather than an independent hidden holdout.

A train-only mechanical rule selects the sole control channel and ten varying
response channels. Candidate-visible values are normalized with train-only
statistics and then consistently permuted into anonymous channels. A query
contains only a 32-sample prechange history, the current anonymous control,
an anonymous slot and horizon 16, 32 or 96. File identity, channel names,
timestamps, intervention markers, future controls and targets are forbidden.
The evaluator validates, copies, freezes and hashes the complete prediction
artifact before it reads the corresponding target and issues a reveal/update.
Updates may mutate only slot-local fast state.

Plans freeze K=18/36/54 training episodes, fit depth and fit horizon 32, the
three test horizons, a 16 MiB state limit and persistence, pooled mean, exact
control-level residual bank, normalized LMS, RLS, prechange transition bank,
bounded replay and fixed ridge FIR controls. Each named control requires an
exact implementation hash and a discriminating semantic test before runner
seed realization. Channel-permutation equivariance and the query--artifact--
reveal--update ordering are mandatory fixtures.

Report overall, worst-file, worst-transition and per-horizon normalized RMSE,
rollout stability, acquisition and preprocessing, fit, every query and update,
bytes touched, resident state and R1/R4/R16 workload. The implementable Pareto
frontier uses the plan-frozen universal capability and cost axes. Incomplete
mandatory controls block promotion without deleting complete candidates from
the frontier. Horizon 96 tests evaluator-created depth extrapolation beyond the
32 fitted target samples; it is not claimed as naturally occurring response-
length OOD. One seed may discard an implementation or authorize replication,
never promote.
## Three-family continuous transfer v2 Pareto contract

Version 2 preserves every world, split, tensor, normalization, causal assignment, baseline, metric value and budget from `heldout_three_family_continuous_transfer_v1`. It changes only prospective decision semantics. Historical v1 plans and results remain immutable and are never recomputed.

The implementable Pareto frontier uses only capability and full-cost fields present for every complete implementable row: transfer accuracy, minimum-family accuracy, rollout stability, normalized RMSE, acquisition, preprocessing, fit, adaptation, query work, resident/peak state, bytes touched and R1/R4/R16 workloads. Candidate-specific causal contrasts are not universal dominance axes.

`shared_vs_independent_gain` on the shared row and `cross_family_transfer_gain` on the cross-family-only row remain mandatory hard gates. Both summaries are minima over all family/K/seed cells and must be strictly positive before `promising` or `promoted` is admissible. Missing, zero, negative or incomplete causal controls block promotion. Timeouts remain durable failures; a timed-out mandatory control also blocks promotion but does not erase the capability frontier of completed candidates.

## Three-family continuous transfer v3 predictive-index controls

Version 3 preserves the v2 real worlds, train/test separation, anonymous tensor mapping,
training-only normalization, metrics, directions, causal contrasts, budgets, Pareto axes and
promotion semantics. Historical v1/v2 plans, results and analyses remain immutable. V3 adds
only two mandatory implementable controls needed to distinguish a learned predictive binding
from classical indexing: exact raw-window nearest-prototype lookup and a frozen random-projection
hash. Both use the same 32-bucket limit, eight samples per bucket, masked affine ridge operator
with lambda 0.001, touched-bucket-only public-support update and 64 MiB state boundary.

The prospective learned candidate and its independent, cross-family-only and support-only
ablations must use one source and frozen constants. The comparison matrix is K=4/6/9. Query
work and bytes touched must remain structurally independent of dormant training-window count;
representation fit, index construction, collision handling, local inserts, state and R1/R4/R16
work are charged. Candidate code may not read family labels, native types, paths, semantic
channel names or test outputs. Semantic conformance includes a future-equivalence counterexample
to raw proximity plus slot relabeling, world-order and consistent channel-permutation fixtures.
V3 was activated in a service-only cycle with no hypothesis, plan, scoring seed or scored result.

## Three-family continuous transfer v4 empty-bucket contract

Version 4 is a maintenance-only successor to v3. It preserves every real world, split, anonymous
tensor, training-only normalization, learner bit, target moment, bucket count and cap, local ridge
operator, support update, metric, direction, threshold, K value, budget, seed policy, Pareto axis
and causal promotion gate. Historical v3 and EXP-20260831-0004 remain immutable and cohort-separated.

V4 corrects only the inherited fallback when a selected index bucket has no stored rows and all
32 current input coordinates are evaluator-public controls. The fallback is the same padded
persistence rule already used by the tensor baseline: copy any mechanically available trailing
state coordinates and zero-pad the remainder to the declared output width. It never reads a target,
changes a bucket key or operator, or adds fit/query dependence on dormant knowledge. Before a seed
can be realized, a real-file continuous-event fixture with 32 visible input/control coordinates,
at least one required output coordinate and a deliberately emptied selected bucket must complete
for the true random-hash control and all four source-identical predictive-index roles.

## Three-family continuous transfer v5 report provenance contract

Version 5 is a service-only successor to v4. It preserves every world, split, tensor,
normalization, candidate, control, metric, direction, threshold, K value, budget, seed policy,
Pareto axis and causal promotion gate. Historical v4 and EXP-20260831-0005 remain immutable.

V5 corrects only evidence-report provenance. A report cohort obtains universal Pareto axes from
the immutable result `pareto_metrics` written by the audited runner, never from the broader plan
`primary_metrics`. Candidate-specific causal contrasts remain visible as promotion-only gates and
never enter universal dominance. If a scientifically valid legacy result lacks `pareto_metrics`,
or valid results in one benchmark/budget cohort disagree, the report shows the exact problem and
computes no frontier for that cohort instead of guessing, intersecting or silently deleting axes.

## Three-family continuous transfer v6 recurrent-residual roles

Version 6 is a service-only successor to v5. It preserves every real world, split, anonymous
tensor, training-only normalization, K value, metric, direction, threshold, baseline, full-cost
boundary, seed policy, Pareto axis and causal promotion gate. Historical v1-v5 plans, results,
analyses, manifests and hashes remain immutable and cohort-separated.

V6 changes only the four prospective causal role identifiers to shared, independent,
cross-family-only and support-only bounded recurrent residual roles. All four resolve to one
source-identical implementation with frozen constants and update law; only the evaluator-private
training-data assignment may differ. Family labels, native types, paths, semantic channel names,
handwritten ontologies and test outputs remain forbidden. The candidate is intentionally neither
implemented nor scored in this migration: implementation may begin only after a later immutable
experiment plan preregisters its exact constants and success, invalidation and seed rules.
