"""Activate after clone conformance, before the sole paid registration."""
import json
from pathlib import Path
import subprocess

import nextai_autoresearch
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b = Path.cwd()
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(b/"src")
checks = ["PVM01-EXPOSURE-targeted-V2","PVM01-EXPOSURE-preseed-full-V2","PVM01-EXPOSURE-history-guard-V1"]
assert all(json.loads((b/f"research/reviews/{name}.json").read_text())["returncode"] == 0 for name in checks)
history = json.loads((b/"research/reviews/PVM01-EXPOSURE-history-source-conformance-V1.json").read_text())
source = subprocess.check_output(["git","rev-parse","HEAD"],cwd=b).decode().strip()
changes = set(subprocess.check_output(["git","diff","--name-only","HEAD"],cwd=b).decode().splitlines())
assert changes <= {"research/events.jsonl","research/REPORT.md","research/REPORT.provenance.json"},changes
assert not subprocess.check_output(["git","ls-files","--others","--exclude-standard"],cwd=b).strip()
assert verify_manifest(b)["ok"]  # Timed wrapper reserves the ledger before this child.
p = b/"config/research.toml"
raw = p.read_bytes()
old = b'benchmark_status = "maintenance"'
assert raw.count(old) == 1
p.write_bytes(raw.replace(old,b'benchmark_status = "active"'))
manifest = freeze_manifest(b,overwrite=True)
write_preflight_certificate(b)
assert verify_manifest(b)["ok"]
study = "research/plans/PVM01-CAPACITY-EXPOSURE-V1.json"
receipt = "research/laboratory/PVM01-CAPACITY-EXPOSURE-V1-readiness.receipt.json"
assert not (b/receipt).exists()
atomic_write_json(b/receipt,{"id":"PVM01-CAPACITY-EXPOSURE-V1-readiness","created_at":utc_now(),
    "study_path":study,"study_sha256":sha256_file(b/study),
    "preregistration_git_commit":history["preregistration_git_commit"],"validated_source_git_commit":source,
    "original_root":str(b.parent/"NEXTAI"),"independent_clone_root":str(b),"shared_runtime_not_source_or_state":True,
    "full_regression_tests":history["full_regression_tests"],"failures_errors_skips":0,
    "full_regression_receipt_sha256":sha256_file(b/"research/reviews/PVM01-EXPOSURE-preseed-full-V2.json"),
    "source_history_receipt_sha256":sha256_file(b/"research/reviews/PVM01-EXPOSURE-history-source-conformance-V1.json"),
    "common_draw_curriculum_feature_gradient_and_fit_identity_verified":True,"all80_semantic_records_verified":True,
    "first_bookkeeping_readiness_failure_preserved": "research/reviews/PVM01-EXPOSURE-readiness-V1.json",
    "only_current_wrapper_ledger_report_changes_allowed":True,
    "protected_files":len(manifest["files"]),"active_evaluator_sha256":manifest["evaluator_sha256"],
    "new_research_seed_data_fit_EXP_before_readiness":False,"ready_for_exactly_one_audited_registration":True,
    "scientific_recipe_and_gates_unchanged":True,"fresh_final_executed":False,"whole_program_complete":False})
append_jsonl(b/"research/events.jsonl",{"event":"research_program_study_ready","created_at":utc_now(),
    "program_id":"NEXTAI-CONTINUATION-20261004-V1","study_path":study,"study_sha256":sha256_file(b/study),
    "receipt_path":receipt,"receipt_sha256":sha256_file(b/receipt)})
write_report(b)
print(json.dumps({"ready":True,"evaluator":manifest["evaluator_sha256"],"bundle":manifest["candidate_bundle_sha256"]}))
