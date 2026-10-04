"""Append a complete stored-result report; do not modify the frozen analysis."""
import json
from pathlib import Path

from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.utils import sha256_file, utc_now

b = Path.cwd()
identity = "EXP-20261004-0008"
primary_path = b/f"research/reviews/{identity}-PVM01-exposure-analysis.json"
diag_path = b/f"research/reviews/{identity}-PVM01-full-diagnostics-V2.json"
a, d = (json.loads(p.read_text(encoding="utf8")) for p in (primary_path, diag_path))
archive = json.loads((b/"research/reviews/PVM01-EXPOSURE-scientific-archive-V1.json").read_text())
old = b/f"research/analyses/{identity}.md"
old_sha = "45458d437156b92db3f9e75fc865b2764578b1daf1dca3ae024284a4b70089ac"
assert sha256_file(old) == old_sha
assert d["result_sha256"] == a["result_sha256"] == archive["result_sha256"]
assert d["all80_workers_and720_trials_finished"] and not d["frozen_comparison_validity_passed"]
assert a["decision"] == "INCONCLUSIVE comparison" and not a["failures"]
assert a["identical_legal_data_across_arms"] and a["identical_training_sets"]
assert all(all(v for k,v in unit.items() if k != "dense_cache_identical_weights")
           and not unit["dense_cache_identical_weights"] for unit in a["source_fit_identity"].values())

source_path = b/"research/sources.jsonl"
ids = {s["source_id"] for s in read_jsonl(source_path)}
assert "SRC-0445" in ids and not ids & {"SRC-0446", "SRC-0447"}
for source in (
    {"source_id":"SRC-0446", "title":"PyTorch 2.6 scaled_dot_product_attention",
     "url":"https://docs.pytorch.org/docs/2.6/generated/torch.nn.functional.scaled_dot_product_attention.html",
     "claims_supported":["CUDA attention can select optimized kernels; different backends can produce different floating point outputs; deterministic controls and explicit backend selection are documented."],
     "relevance":"Inference only: the tiny decoder drift in EXP-20261004-0008 is compatible with GPU numerical nondeterminism. The selected operator/backend was not logged, so this source does not identify the observed cause."},
    {"source_id":"SRC-0447", "title":"PyTorch 2.6 reproducibility notes",
     "url":"https://docs.pytorch.org/docs/2.6/notes/randomness.html",
     "claims_supported":["Controlling random seeds and avoiding nondeterministic algorithms are separate parts of reproducibility; deterministic operation settings can affect performance."],
     "relevance":"Prospective preparation-only determinism and telemetry checks, not a retrospective relaxation of exact hash identity or a paid retry."},
):
    append_jsonl(source_path, {**source, "authors":["PyTorch developers"], "year":2025,
        "checked_at":utc_now(), "primary_source":True, "source_type":"official_documentation"})

summary = d["descriptive_95_percent_intervals"]
def percent(v): return f"{100*v:.4f}%"
def mean(arm,key): return summary[arm][key]["mean"]
def ci(value,scale=100): return f"{scale*value['mean']:+.4f} [{scale*value['low']:+.4f}, {scale*value['high']:+.4f}]"
charges = [e for e in read_jsonl(b/"research/events.jsonl")
           if e.get("event") == "research_program_aux_fit_charged"
           and e.get("charge_id", "").startswith("PVM01-EXPOSURE-")]
lines = [f"# {identity} — complete results and validity correction, ADDENDUM V1", "",
    "**Frozen decision: INCONCLUSIVE comparison. All 80 workers and 720 trials physically completed. The exact dense/cache decoder identity gate failed on all five units.** The feature-learning block passed its pairing and source/fit checks, but the whole comparison cannot be promoted or converted to DISCARD by relaxing a gate after the result.", "",
    "## Append-only correction and provenance", "",
    f"The initial report research/analyses/{identity}.md (raw SHA256 `{old_sha}`) and diagnostics V1 remain unchanged. Their incomplete branch conflated the analyzer field `all_workers_and_trials_complete` with physical completion. In the frozen analyzer that field also includes data and model-identity validity. The sentence that workers did not complete is therefore corrected here: 80/80 complete, 720/720 trials, no failed or unstarted worker, five fresh paired units, 230400 answers. The failure is exact decoder/loss identity, not missing workers. The analyzer, result, recipe, gates and official INCONCLUSIVE decision remain byte-identical.", "",
    f"- Immutable audited plan: research/plans/{identity}.json; canonical SHA256 `{a['plan_sha256']}`.",
    f"- Prospective study: research/plans/PVM01-CAPACITY-EXPOSURE-V1.json; raw SHA256 `{a['study_sha256']}`; committed before implementation/data/fit at `8fb10251a0c03356856469e1c37742c3956f15dc`.",
    f"- Result: research/results/{identity}.json; raw SHA256 `{a['result_sha256']}`.",
    f"- Frozen stored analysis: {primary_path.relative_to(b).as_posix()}; raw SHA256 `{sha256_file(primary_path)}`.",
    f"- Descriptive stored diagnostics: {diag_path.relative_to(b).as_posix()}; raw SHA256 `{sha256_file(diag_path)}`. No model or generator executed for this addendum.",
    "- The independent ordinary Git clone used its own source/state/runtime and shared only dependency binaries. Exactly one audited paid registration/run; no retry, replacement seed, final data, WT8–9, external model/API or schedule change.", "",
    "## OBSERVATION", "",
    "The prospective factor was feature-fit support exposure, alternating K32/128 versus K32/512. Both use 512 Fourier features, 512 optimizer steps, AdamW lr .003, weight decay 0, gradient clip 1, batch 4 and eight queries, with the unchanged 2048-step learned transport and beta 1 delta-write rule. Larger support pays more work: 163840 versus 557056 batched training writes per unit. Equal optimizer steps does not mean matched FLOPs. Every optimized arm draws the same full 4×512 label table and episode indices before truncation; its new stream differs from closed 0007, so comparisons are paired within v5 only.", "",
    "All 80 roles receive identical legal 128 train-set episodes per K32/128/512; the unchanged dense recipe still trains its decoder on K32/128. The K512 extension uses the same protected episode law with fresh train identities and zero updates. Train-only calibration uses all three K and updates 0/1/4. Development uses 45 episodes/2880 answers per worker. Update rounds are not reasoning depth. No dev query is fitted.", "",
    "Means over five independent combined seed/data units. Episodes and individual answers are not independent replications:", "",
    "| Arm | Full answer | Updated | Retained | UNKNOWN rejection | Known false abstention |",
    "|---|---:|---:|---:|---:|---:|"]
for arm in summary:
    lines.append("| "+arm+" | "+" | ".join(percent(mean(arm,k)) for k in
        ("accuracy","updated","retained","dense_unknown_rejection","known_false_abstention"))+" |")
lines += ["", "Four frozen paired Student-t df4 intervals are two-sided 98.75%, yielding 95% Bonferroni family coverage under the unit-level parametric model. Differences are percentage points:", "",
    "| Contrast | Mean [simultaneous interval] pp | Positive units | Frozen gate |",
    "|---|---:|---:|---|"]
labels = {"small":"Full large−small", "frozen":"Full large−frozen",
          "shuffled":"Full large−shuffled", "retained":"Retained large−RFF2048"}
for key,v in a["primary_simultaneous_intervals"].items():
    gate = "retention_noninferiority" if key == "retained" else key
    lines.append(f"| {labels[key]} | {ci(v)} | {v['positive_units']}/5 | {'PASS' if a['primary_gates'][gate] else 'FAIL'} |")
lines += ["", "Each full-answer gain requires mean ≥5 pp, interval lower ≥2 pp and 5/5 positive units; retained noninferiority requires lower ≥−2 pp. All four fail. This descriptive pattern is not substituted for the prior whole-comparison validity gate.", "",
    "| Arm | K32 full / UNKNOWN | K128 full / UNKNOWN | K512 full / UNKNOWN |",
    "|---|---:|---:|---:|"]
for arm in ("exposure_small","exposure_large","exposure_frozen","exposure_shuffled",
            "exposure_additive","delta","dense","dense_cached_cpu","ridge","ridge_pca_scan"):
    cells = [percent(summary[arm]["by_K"][str(k)]["accuracy"]["mean"])+" / "+
             percent(summary[arm]["by_K"][str(k)]["dense_unknown_rejection"]["mean"]) for k in (32,128,512)]
    lines.append("| "+arm+" | "+" | ".join(cells)+" |")
lines += ["", "Unchanged competence: mean full ≥95%, each unit full ≥90%, each K mean full ≥90%, mean UNKNOWN ≥95%, each unit UNKNOWN ≥90%, known false abstention ≤2%. Dense and both cache controls pass every competence check. The large-exposure memory fails the mean, per-unit, per-K, UNKNOWN and false-abstention requirements (the complete booleans are stored):", "",
    "```json",json.dumps(a["competence_gates"],indent=2,sort_keys=True),"```", "",
    "## Identity failure, without a validity rescue", "",
    "All five units have identical legal train/calibration/dev hashes across arms. Every feature-arm check passes: common initialization/transport/losses, feature initialization/precomputed inputs, common maximum-label draws, fixed steps, valid gradients, frozen features, support curricula and exact large/additive feature-fit equality. PCA scan/tree fitted weights, projection, selected grid and validation results are identical. Compact memory has no fact handle, so fact-top1 and handle-conditioned wrong-fact/stale metrics are inapplicable; None is never counted as a correct handle.", "",
    "Dense/cache encoder hashes and alignment losses match, but final decoder hashes do not. Cache comparisons below each cover all 2880 stored questions, with answer/handle/value/truth/target equality checked:", "",
    "| Unit / cache | Exact decoder hash | Same discrete predictions | Max loss difference | Max decision-score difference |",
    "|---|---|---:|---:|---:|"]
for unit, caches in d["cache_checks"].items():
    for arm,v in caches.items():
        assert v["predictions_handles_values_equal"] and not v["decoder_weights_identical"]
        lines.append(f"| {unit} / {arm} | FAIL | {v['count']}/{v['count']} | {v['max_set_loss_absolute_difference']:.12g} | {v['max_decision_score_absolute_difference']:.12g} |")
lines += ["", "The maximum loss drift is 1.1920928955078125e−7 and maximum decision-score drift is 3.5762786865234375e−7. All 28800 paired discrete prediction checks agree. Tiny floating differences do not satisfy the preregistered exact identity requirement; no epsilon gate is introduced after inspection.", "",
    "The PyTorch 2.6 documentation describes optimized attention backends with possible floating-point differences and separate reproducibility controls. GPU numerical nondeterminism is a compatible explanation, an inference rather than an identified operator: the chosen decoder kernel/backend was not logged. These sources support a prospective deterministic fixture study, not retrospective validation. [PyTorch 2.6 attention](https://docs.pytorch.org/docs/2.6/generated/torch.nn.functional.scaled_dot_product_attention.html), [PyTorch 2.6 reproducibility](https://docs.pytorch.org/docs/2.6/notes/randomness.html); source records SRC-0446/0447.", "",
    "## Costs and training diagnostics", "",
    "Mean per unit; loaded full service totals all nine development cells. These are descriptive measurements on one fixed machine, not an economic promotion:", "",
    "| Arm | Supervised fit phase s | Full service s | Query p95 µs | Logical state KiB | Full charged worker s |",
    "|---|---:|---:|---:|---:|---:|"]
for arm,row in summary.items():
    costs = row["costs"]
    values = [costs[k]["mean"] for k in ("fit_phase_seconds","full_workload_seconds","p95_query_us","logical_state_bytes","charged_worker_seconds")]
    values[3] /= 1024
    lines.append("| "+arm+" | "+" | ".join(f"{v:.6f}" for v in values)+" |")
lines += ["", "The service boundary includes copies, normalization/transport/Fourier expansion, allocation, ingest, updates, index/cache construction and invalidation, warmup, queries, synchronization, decoding and Python outputs. Update time is an ingest subset and is not added twice. Data generation, calibration, initialization/library loading and repeated control fits also enter full charged worker time. Whole-worker RSS/CUDA allocator peaks and component costs are stored; inference-only GPU peak is not isolated. Operation counts are estimates. Fixed serial role order and differing CPU/GPU deployment limit generalization, and timing alone establishes no complexity or energy claim.", "",
    f"Trusted supervised fit phase: **{d['total_supervised_fit_phase_seconds']:.6f} s**; internal algorithm fit: **{d['total_internal_algorithm_fit_seconds']:.6f} s**; all full workers charged: **{d['full_charged_worker_seconds']:.6f} s /16640 s**. Auxiliary charges at addendum creation: {sum(e['seconds'] for e in charges):g} s; final tests/accounting remain to be closed in research/laboratory/PVM01-CYCLE-310-COMPLETION-V1.receipt.json (auxiliary cap 1800 s). That immutable receipt is authoritative for final totals. Fixed start 2026-10-04T20:50:36Z, deadline 2026-10-05T00:50:36Z; no old budget reset.", "",
    "| Feature arm / unit | First50 mean CE | Last50 mean CE | Support K | Batched train writes |",
    "|---|---:|---:|---|---:|"]
for key,v in d["feature_training_traces"].items():
    lines.append(f"| {key} | {v['first50_mean']:.6f} | {v['last50_mean']:.6f} | {v['support_sizes']} | {v['training_write_count']} |")
lines += ["", "All 512 losses/gradient norms, per-K traces, thresholds, raw predictions and timing/state components remain preserved. Changed feature weights and nonzero gradients establish that fitting happened; modest loss change at a fixed step count does not establish convergence. Training has no updates, so online updates test generalization. Larger exposure pays roughly 2.79× the supervised fit phase of small exposure while full-answer accuracy changes from 90.4028% to 90.1736%. It does not show a compensating quality gain.", "",
    "## INTERPRETATION", "",
    "Official decision remains **INCONCLUSIVE comparison** because exact decoder control identity fails. The correctly paired feature sub-block supplies a narrow negative observation: this larger-support 512-feature/512-step recipe does not show the frozen learning/exposure improvements, and retained accuracy is about 16.42 pp below the unchanged 2048-feature memory. It gives no reason for another step-count rescue. This is not a valid whole-study DISCARD, a family falsification, novelty claim, architecture promotion, transfer result or economic advantage.", "",
    "The local quality/cost table also keeps the strongest classical controls visible: ridge/PCA/kernel retrieval has about 99.9722% full-answer accuracy, versus 90.1736% for the tested large compact memory; PCA scan state is 68.25 KiB versus 185 KiB. A proposed LLM-successor advantage is unsupported. The wider continuation programme remains active and alternatives require new prospective contracts.", "",
    "## CONFIDENCE", "",
    "Five fresh independent combined seed/data units support a local synthetic screen, with paired Student-t assumptions and broad n=5 intervals. Source/data pairing is sound in the feature block; dense decoder identity invalidates the complete comparison. Identical observed decisions do not prove equivalent fitted models or unseen behavior. The task/evaluator is locally inspectable, not an externally blinded fresh final. Timing, capacity and training exposure on this toy do not demonstrate scaling, transfer or general intelligence.", "",
    "## Integrity, tests and preservation", "",
    "Before paid seeds, 1114/1114 full regression cases passed in the independent clone. The preceding V1 full run passed 1113 and failed the evaluator boundary due to a direct candidate hashing import. Before paid execution, that import was replaced by a local evaluator hash of the public fitted decoder, an explicit boundary assertion was added, 13 targeted repair cases passed, then all 1114 passed. The original failure/output/276 s charge remains. Metrics, task, recipe and gates were unchanged. A readiness wrapper also failed before activation/seed because its own required reservation dirtied the ledger/report before a clean-checkout assertion; the 19 s failure remains and the corrected wrapper independently verifies all protected source while permitting only its three expected bookkeeping files.", "",
    f"Evaluated source was preserved before maintenance: **{archive['source_count']} source plus {archive['runtime_count']} runtime raw files**, {archive['footprint_bytes']} bytes, hash/disk checked. All seeds, fits, outcomes, journals and closed historical records remain. Original raw history and append-only prefixes were checked before any original integration. Final maintenance conformance, critical postrun tests, original-source doctor/lab, staged raw hash verification and exact budget are recorded separately in the cycle310 receipt. This addendum does not claim these not-yet-run checks already passed.", "",
    "Stored analysis reproduction executes no model: `uv run --no-sync python scripts/analyze_pvm01_capacity_exposure.py EXP-20261004-0008`. This is analysis of immutable evidence, not permission to rerun the paid plan. The stored V2 diagnostics and archived helpers reproduce the reporting/accounting path. The initial V1 prose remains visible and corrected by this versioned addendum.", "",
    "## NEXT DISCRIMINATING EXPERIMENT", "",
    "First preregister a bounded preparation-only decoder determinism/telemetry repair, using fixed synthetic fixtures in independent child processes. Require exact encoder/decoder/loss equality across dense and cache fit paths, record actual CUDA attention/backend and deterministic settings, and preserve all failures and costs. No research data, scoring, registration or paid-plan retry in that preparation; do not alter the closed EXP-0008 hashes or decision. Only after conformance can a distinct new five-unit study compare an alternative learned-transport/indexed memory against unchanged strongest classical controls on a prospectively justified adverse paired-view task. Freeze before implementation/data. No second EXP in cycle310.", "",
    "Independent mechanism replication, adversarial generalization, at least three matched-quality scale points, economic non-domination and frozen fresh final remain unexecuted. No automatic closure of the whole programme from this recipe or validity failure; no positive claim without those deliverables.", ""]
path = b/f"research/analyses/{identity}-ADDENDUM-V1.md"
assert not path.exists()
path.write_text("\n".join(lines),encoding="utf8",newline="\n")
assert sha256_file(old) == old_sha
append_jsonl(b/"research/events.jsonl", {"event":"research_analysis_addendum_preserved",
    "created_at":utc_now(), "experiment_id":identity, "original_analysis_sha256":old_sha,
    "addendum_path":path.relative_to(b).as_posix(), "addendum_sha256":sha256_file(path),
    "physical_completion_corrected_without_gate_relaxation":True,
    "frozen_decision_unchanged":a["decision"], "new_model_fit_or_seed":False})
print(json.dumps({"addendum":str(path),"sha256":sha256_file(path),"decision":a["decision"]}))
