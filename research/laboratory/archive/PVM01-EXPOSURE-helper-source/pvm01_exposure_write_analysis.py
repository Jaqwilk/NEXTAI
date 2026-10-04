"""Write an immutable complete report from preserved predictions only."""
import json
from pathlib import Path

from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.utils import sha256_file

b = Path.cwd()
identity = "EXP-20261004-0008"
primary_path = b/f"research/reviews/{identity}-PVM01-exposure-analysis.json"
diag_path = b/f"research/reviews/{identity}-PVM01-full-diagnostics-V1.json"
a,d = (json.loads(p.read_text()) for p in (primary_path,diag_path))
study = json.loads((b/"research/plans/PVM01-CAPACITY-EXPOSURE-V1.json").read_text())
archive = json.loads((b/"research/reviews/PVM01-EXPOSURE-scientific-archive-V1.json").read_text())
assert d["result_sha256"] == a["result_sha256"] == archive["result_sha256"]
if d.get("incomplete"):
    path = b/f"research/analyses/{identity}.md"
    assert not path.exists()
    text = (f"# {identity} — INCONCLUSIVE capacity-exposure comparison\n\n"
        f"Immutable plan:research/plans/{identity}.json; canonical SHA256`{a['plan_sha256']}`. "
        f"Result raw SHA256`{a['result_sha256']}`; study raw SHA256`{a['study_sha256']}`.\n\n"
        "## OBSERVATION\n\nThe audited attempt did not complete all80 workers/720 trials or pairing gates. "
        "Every produced prediction,journal,seed,failed worker and unstarted scope is preserved; no retry occurred.\n\n"
        +json.dumps(a['failures'],indent=2)+"\n\n"
        f"Full worker charge{d['full_charged_worker_seconds']:.6f}s; supervised phase{d['total_supervised_fit_phase_seconds']:.6f}s. "
        "All auxiliary reservations/tests/failures are append-only charged; exact final totals/deadline/unfinished scope appear in research/laboratory/PVM01-CYCLE-310-COMPLETION-V1.receipt.json.\n\n"
        "## INTERPRETATION\n\nINCONCLUSIVE comparison; an implementation or validity failure does not falsify a mechanism family. Frozen metrics,recipe,gates and completed historical studies remain unchanged.\n\n"
        "## CONFIDENCE\n\nNo complete five-unit causal/economic claim. Preseed V1 boundary failure and its charged source correction are preserved; V2 full conformance passed before research data.\n\n"
        "## NEXT DISCRIMINATING EXPERIMENT\n\nReview exact preserved cause under a new prospective study/remaining program authority; no same-plan retry,replacement seed,WT8–9,external API or schedule changes. "
        "Independent replication,adverse variant,scaling,economic non-domination and fresh final remain unexecuted.\n")
    path.write_text(text,encoding="utf-8",newline="\n")
    print(json.dumps({"analysis":str(path),"raw_sha256":sha256_file(path),"decision":a["decision"]}))
    raise SystemExit(0)
summary = d["descriptive_95_percent_intervals"]
def percent(v):
    return f"{100*v:.4f}%"
def ci(v,scale=100):
    return f"{scale*v['mean']:+.4f} [{scale*v['low']:+.4f},{scale*v['high']:+.4f}]"
def mean(arm,metric):
    return summary[arm][metric]["mean"]
charges = [e for e in read_jsonl(b/"research/events.jsonl") if e.get("event") == "research_program_aux_fit_charged" and e.get("charge_id","").startswith("PVM01-EXPOSURE-")]
charged = sum(e["seconds"] for e in charges)
lines = [f"# {identity} — frozen capacity-exposure screen", "",
    f"**Decision: {a['decision']}.** All80 workers and720 trials finished across five fresh paired seed/data units. This closes the exact preregistered study, not the continuation program.","",
    "## Contract and provenance","",
    f"- Immutable plan: research/plans/{identity}.json; canonical SHA256 `{a['plan_sha256']}`.",
    f"- Prospective study: research/plans/PVM01-CAPACITY-EXPOSURE-V1.json; raw SHA256 `{a['study_sha256']}`.",
    "- Preregistration Git commit: `8fb10251a0c03356856469e1c37742c3956f15dc`, before new source, research random seeds, data or fit.",
    f"- Result: research/results/{identity}.json; raw SHA256 `{a['result_sha256']}`.",
    f"- Frozen primary analyzer: scripts/analyze_pvm01_capacity_exposure.py; stored output `{sha256_file(primary_path)}`.",
    f"- Descriptive diagnostic output: {diag_path.relative_to(b).as_posix()}; raw SHA256 `{sha256_file(diag_path)}`.",
    "- Independent Git clone used its own source/state/runtime; only the dependency environment is shared with the original checkout. No direct scored fit, retry, replacement seed, external model/API, WT8–9 or schedule change.","",
    "## OBSERVATION","",
    "The factor was support-size exposure during feature optimization: alternating K32/128 versus K32/512. Both use the same512 Fourier features,512 optimizer steps,AdamW lr.003,WD0,clip1,batch4,eight queries,correct frozen2048-step transport and beta1 delta writes. Larger support changes paid training work as well as exposure; equal steps is not matched FLOPs. Every optimized feature arm draws the same full4×512 value-label table and episode indices before truncating to K. The new draw stream differs from closed0007; only within-v5 pairing is causal.","",
    "All80 roles receive legal train sets at K32/128/512; unchanged dense fitting still chooses K32/128. The K512 extension uses the same protected episode law, fresh train-only identities, zero update rounds and legal training target positions. No calibration/dev query is optimized. Fixed train-only calibration uses all three K and updates0/1/4. Development has45 episodes and2880 answers per worker,230400 total. Update rounds are not reasoning depth.","",
    "Means over five independent units; answers and episodes are not independent replication units:","",
    "| Arm | Full answer | Updated | Retained | UNKNOWN rejection | Known false abstention |",
    "|---|---:|---:|---:|---:|---:|"]
for arm in summary:
    lines.append("| "+arm+" | "+" | ".join(percent(mean(arm,k)) for k in ("accuracy","updated","retained","dense_unknown_rejection","known_false_abstention"))+" |")
lines += ["","Four preregistered paired Student-t df4 intervals are two-sided98.75%, giving95% familywise Bonferroni coverage under the parametric model. Effects below are percentage points:","",
    "| Contrast | Mean [simultaneous interval] | Positive units | Frozen gate |",
    "|---|---:|---:|---|"]
labels = {"small":"Full large−small","frozen":"Full large−frozen","shuffled":"Full large−shuffled","retained":"Retained large−RFF2048"}
for key,value in a["primary_simultaneous_intervals"].items():
    gate = "retention_noninferiority" if key == "retained" else key
    lines.append(f"| {labels[key]} | {ci(value)} | {value['positive_units']}/5 | {'PASS' if a['primary_gates'][gate] else 'FAIL'} |")
lines += ["","Each full-answer gain requires mean≥5pp, simultaneous lower≥2pp and all5 gains positive. Retained noninferiority requires lower≥−2pp. These are the new prospective exposure endpoints; closed0007 endpoints and its DISCARD decision are unchanged. Descriptive K512 updated metrics do not replace failed primaries.","",
    "| Arm | K32 full / UNKNOWN | K128 full / UNKNOWN | K512 full / UNKNOWN |",
    "|---|---:|---:|---:|"]
for arm in ("exposure_small","exposure_large","exposure_frozen","exposure_shuffled","exposure_additive","delta","dense","dense_cached_cpu","ridge","ridge_pca_scan"):
    cells = [percent(summary[arm]["by_K"][str(k)]["accuracy"]["mean"])+" / "+percent(summary[arm]["by_K"][str(k)]["dense_unknown_rejection"]["mean"]) for k in (32,128,512)]
    lines.append("| "+arm+" | "+" | ".join(cells)+" |")
lines += ["","Unchanged competence requires mean full≥95%,each unit full≥90%,each K mean full≥90%,mean UNKNOWN≥95%,each unit UNKNOWN≥90%,known false abstention≤2%. All gates are stored with their booleans:","",
    "```json",json.dumps(a["competence_gates"],indent=2,sort_keys=True),"```","",
    "Source/data checks cover common transport weights/losses,initial frequency/precomputed input hashes,common max-label draw digests,frozen feature identity,exact large/additive losses/final features,fixed step counts and curricula,plus identical dense/cache encoder/decoder hashes and losses,and actual PCA scan/tree weight/projection/grid fields. All five units passed. Every role has identical paired T/D hashes. Compact memories do not output a fact handle; their fact-top1 and handle-conditioned stale/wrong-fact metrics are explicitly inapplicable, never inferred from None==None.","",
    "## Costs and training diagnostics","",
    "| Arm | Supervised fit phase s | Full service s | Query p95 µs | Logical state KiB | Full worker s |",
    "|---|---:|---:|---:|---:|---:|"]
for arm in summary:
    row = summary[arm]["costs"]
    values = [row[k]["mean"] for k in ("fit_phase_seconds","full_workload_seconds","p95_query_us","logical_state_bytes","charged_worker_seconds")]
    values[3] /= 1024
    lines.append("| "+arm+" | "+" | ".join(f"{v:.6f}" for v in values)+" |")
lines += ["","The service boundary includes input copies,normalize/transport/Fourier expansion,memory allocation,all ingest/update/index/cache work,warmup,query,decoding,synchronization and Python output. Update time is an ingest subset,not added twice. Data generation,calibration,initialization/library loading and all repeated control fits are additionally included in supervised/full worker accounting. All80 process walls are charged. Operation counts are coarse estimates; timings from fixed sequential arm order on this one machine do not establish complexity,energy use or a deployment-independent speedup. Whole-process RSS/CUDA allocator peaks are retained; inference-only CUDA memory is not separately isolated.","",
    f"Trusted supervised fit phase total: **{d['total_supervised_fit_phase_seconds']:.6f}s**; internal algorithm fit: **{d['total_internal_algorithm_fit_seconds']:.6f}s**; charged full workers: **{d['full_charged_worker_seconds']:.6f}s /16640s**. Aux tests are reserved before execution and failed work retained. At report creation, auxiliary charges are{charged:g}s; final exact auxiliary/global accounting,original validation and deadline status are sealed separately in research/laboratory/PVM01-CYCLE-310-COMPLETION-V1.receipt.json (aux cap1800s,deadline2026-10-05T00:50:36Z). Prior3 registrations/2655.336485s remain consumed.","",
    "Feature fitting traces (mean CE over the first/last50 optimizer steps;512 steps,full gradient through initial writes). Separate first/last50-per-K traces are retained in the diagnostic JSON:","",
    "| Arm/unit | First50 mean | Last50 mean | Support K | Actual batched train writes |",
    "|---|---:|---:|---|---:|"]
for key,trace in d["feature_training_traces"].items():
    lines.append(f"| {key} | {trace['first50_mean']:.6f} | {trace['last50_mean']:.6f} | {trace['support_sizes']} | {trace['training_write_count']} |")
lines += ["","Per-K loss traces,all512 individual losses/gradient norms,threshold grids,predictions,state and timing components remain in the stored diagnostic and raw journals. Changed feature hashes and nonzero gradients show optimization occurred; neither loss reduction nor a fixed512-step endpoint establishes convergence. Training has zero update rounds; online update behavior is measured as generalization. No additional fit or data was run for these diagnostics.","",
    "## INTERPRETATION","",
    f"The frozen decision is **{a['decision']}**. Evidence applies to this exact512-dimensional Fourier map,fixed beta1 delta memory and support curriculum. The large−small contrast tests exposure under the fixed-step resource recipe; large−frozen and large−shuffled separate learned features from initialization and corrupted association. The additive arm isolates the known overwrite correction with identical feature fitting. Strong ridge/PCA/kernel/exact retrieval remain legal fitted competitors and may dominate. No architecture novelty,LLM-successor,transfer or end-to-end economic advantage is claimed.","",
    "A valid failure ends this exposure recipe and the preregistered compact-Fourier branch on this task,after the distinct feature-learning and support-exposure alternatives. It does not falsify all fast-weight or learned-memory families. The programme still owes independently replicated adverse/scaling evidence and a frozen fresh final,or an evidence-based infeasibility resolution with unexecuted scope disclosed.","",
    "## CONFIDENCE","",
    "Five independent fresh combined seed/data units support a local synthetic screen. Paired intervals assume a Student-t unit-level model and are wide at n5. Calibration is train-only and source/hashes are controlled,but the local agent can inspect the task/evaluator; this is not an externally blinded final. Fixed device/thread settings and serial role order limit timing generalization. Teacher structure is not exposed to candidates,but legal pairs permit strong conventional transport,which is part of the scientific comparison.","",
    "## Integrity and reproducibility","",
    "Before seeds,all1114 full regression cases and34 memory/exposure tests passed in the independent clone. The first full run passed1113 and failed the evaluator boundary because v5 directly imported a candidate hashing helper. The import was removed and the evaluator computes the public fitted-decoder hash locally; an explicit boundary assertion was added. A targeted13-case repair check and the full1114-case V2 rerun passed before any paid registration or research seed. V1 failure/output/276s conservative charge remain preserved; metrics,task,recipe and gates did not change. Raw preregistration Git bytes,old plans/results/analyses/source archives,original checkout and append-only prefixes were verified. The report is written before postrun lifecycle checks so the required completed analysis exists. Final clone/original doctor/lab checks and raw Git index guard are recorded in the closure receipt; this prose is not retroactively changed to claim unrun checks.","",
    f"Evaluated source was archived before maintenance: **{archive['source_count']} source and{archive['runtime_count']} runtime files**,{archive['footprint_bytes']} bytes,with exact raw SHA256 and disk-space checks. The first readiness wrapper failed because its own mandatory budget reservation dirtied the ledger/report before a whole-checkout clean assertion. Its19s charge and raw traceback are preserved; the child now permits only those three ledger/report files and independently verifies every protected source hash. No scientific recipe,gates,data or paid attempt was changed. All failed bookkeeping/native evidence is preserved. No paid retry occurred.","",
    "Reproduce the stored analysis without executing a model: `uv run --no-sync python scripts/analyze_pvm01_capacity_exposure.py EXP-20261004-0008`. Readonly diagnostics/helper sources and captured CLI outputs are archived; the audited EXP plan binds evaluator,source,roles,private artifact and every seed. A fresh scientific replication requires a new preregistration and new units,not a rerun of this plan.","",
    "## NEXT DISCRIMINATING EXPERIMENT","",
    "If all frozen large-exposure gates pass,preregister a fresh independent replication/adverse variant of that exact recipe against unchanged strongest controls at K32/128/512. If the valid exposure recipe fails,stop compact Fourier retuning and preregister a distinct learned-transport/indexed-memory comparison on an adverse paired-view task that challenges conventional transport,with strong nonlinear kernel/classical controls and all legal preprocessing/index costs. Select no alternative by reading a future holdout. In either case,freeze before new implementation/data,retain five independent units,no same-plan retry,one EXP per bounded cycle. Fresh final/economic non-domination remain unexecuted.","",
    "Established prior art: Schlag,Irie,Schmidhuber(2021)delta fast weights;Rahimi,Recht(2007)RFF;Li et al.(2021)learnable Fourier positional features;official SciPy cKDTree exact lookup. This task's feature memory is a narrow application,not a faithful paper reproduction or novel computational principle.",""]
path = b/f"research/analyses/{identity}.md"
assert not path.exists()
path.write_text("\n".join(lines),encoding="utf-8",newline="\n")
print(json.dumps({"analysis":str(path),"raw_sha256":sha256_file(path),"decision":a["decision"]}))
