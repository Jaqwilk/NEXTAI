"""Close paid study after preserving evaluated bytes and completed analysis."""
import json
from pathlib import Path

from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.research_program import status
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b = Path.cwd()
identity = "EXP-20261004-0008"
archive = json.loads((b/"research/reviews/PVM01-EXPOSURE-scientific-archive-V1.json").read_text())
a = json.loads((b/f"research/reviews/{identity}-PVM01-exposure-analysis.json").read_text())
d = json.loads((b/f"research/reviews/{identity}-PVM01-full-diagnostics-V2.json").read_text())
assert archive["protected_source_verified_before_maintenance"] and verify_manifest(b)["ok"]
assert sha256_file(b/f"research/results/{identity}.json") == archive["result_sha256"] == a["result_sha256"]
assert (b/f"research/analyses/{identity}.md").is_file()
assert (b/f"research/analyses/{identity}-ADDENDUM-V1.md").is_file()
assert d["all80_workers_and720_trials_finished"] and not d["frozen_comparison_validity_passed"]
assert a["decision"] == "INCONCLUSIVE comparison"
programme = status(b)
assert programme["study_terminal"] and not programme["scoring_authorized"]
assert not programme["paid_run_pending"] and not programme["program_closed"]
bundle = json.loads((b/"research/eval_manifest.json").read_text())["candidate_bundle_sha256"]
header = ("# Current cycle310 — EXP-20261004-0008 completed (2026-10-04)\n\n"
    f"PVM01-CAPACITY-EXPOSURE-V1 decision: {a['decision']}.\n"
    "One audited attempt,five fresh paired units,16 arms,K32/128/512,updates0/1/4.\n"
    "512 features and512 steps; K32/128 versus K32/512 fit support exposure.\n"
    "All strong dense/cache/ridge/PCA/tree/kernel/exact retrieval controls retained.\n"
    "Exact dense/cache decoder hashes fail on all5 units despite identical decisions.\n"
    "Feature pairing passed; whole comparison invalid,official INCONCLUSIVE unchanged.\n")
if not d.get("incomplete"):
    primary = a["primary_simultaneous_intervals"]["small"]
    summary = d["descriptive_95_percent_intervals"]
    header += (f"80/80 workers,720/720 trials. Full large-small {100*primary['mean']:+.4f}pp,\n"
        f"simultaneous98.75% CI[{100*primary['low']:+.4f},{100*primary['high']:+.4f}]pp.\n"
        f"Large full{100*summary['exposure_large']['accuracy']['mean']:.4f}%,UNKNOWN{100*summary['exposure_large']['dense_unknown_rejection']['mean']:.4f}%;\n"
        f"small full{100*summary['exposure_small']['accuracy']['mean']:.4f}%. Gates unchanged.\n")
header += (f"Trusted supervised fit phase{d['total_supervised_fit_phase_seconds']:.6f}s;\n"
    f"charged full workers{d['full_charged_worker_seconds']:.6f}s /16640s. Larger fitting work paid.\n"
    "Auxiliary cap1800s includes startup,failed boundary/readiness checks and all tests.\n"
    "Deadline2026-10-05T00:50:36Z; no budget/history reset.\n"
    "Complete corrected report:research/analyses/EXP-20261004-0008-ADDENDUM-V1.md.\n"
    "Initial report preserved; exact final accounting:\n"
    "research/laboratory/PVM01-CYCLE-310-COMPLETION-V1.receipt.json.\n"
    "Current v5 study terminal,maintenance/scoring=false; global continuation active.\n"
    "5/17 new tickets used,12 remain; old3/2655.336485s carried unchanged.\n"
    "No retry,WT8–9,external model/API,novelty/economic/transfer promotion or schedule change.\n"
    "No exposure improvement observed; failed identity gate cannot become DISCARD.\n"
    "Next: preregister preparation-only deterministic decoder/telemetry conformance\n"
    "in independent fixed-fixture children,no research data/EXP/paid retry.\n"
    "Then a distinct prospective alternative/adverse task versus strongest classics.\n"
    "Freeze before implementation/data; no automatic step rescue or gate relaxation.\n"
    "Three-scale/full-cost comparison,independent replication and frozen fresh final remain.\n"
    "No second EXP in this completed cycle. Previous sections are preserved history.\n\n")
for name in ("AGENTS.md","program.md","research/LAB_PLAN.md","docs/CURRENT_STATUS.md","docs/SCIENTIFIC_PROTOCOL.md"):
    path = b/name
    assert not path.read_bytes().startswith(b"# Current cycle310")
    path.write_bytes(header.encode()+path.read_bytes())
config = b/"config/research.toml"
payload = config.read_bytes()
assert payload.count(b'benchmark_status = "active"') == 1
config.write_bytes(payload.replace(b'benchmark_status = "active"',b'benchmark_status = "maintenance"'))
manifest = freeze_manifest(b,overwrite=True)
write_preflight_certificate(b)
assert manifest["candidate_bundle_sha256"] == bundle and verify_manifest(b)["ok"]
write_report(b)
atomic_write_json(b/"research/reviews/PVM01-EXPOSURE-maintenance-transition-V1.json",{
    "created_at":utc_now(),"experiment_id":identity,"completed_result_unchanged":True,
    "evaluated_source_preserved_before_transition":True,"completed_analysis_before_postrun_checks":True,
    "source_and_runtime_receipt_sha256":sha256_file(b/"research/reviews/PVM01-EXPOSURE-scientific-archive-V1.json"),
    "candidate_bundle_unchanged":True,"current_evaluator_sha256":manifest["evaluator_sha256"],
    "protected_files":len(manifest["files"]),"maintenance":True,"scoring_authorized":False,
    "no_new_research_data_fit_seed_or_registration":True,"whole_program_complete":False})
print(json.dumps({"maintenance":True,"protected_files":len(manifest["files"]),"source_bundle_unchanged":True}))
