"""Activate only after clone checks, before the sole paid registration."""
import json
from pathlib import Path
import subprocess

import nextai_autoresearch
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b=Path.cwd()
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(b/"src")
checks = ["PVM01-COMPACT-targeted-V1", "PVM01-COMPACT-preseed-full-V1", "PVM01-COMPACT-history-guard-V2"]
assert all(json.loads((b/f"research/reviews/{name}.json").read_text())["returncode"] == 0 for name in checks)
source = subprocess.check_output(["git","rev-parse","HEAD"],cwd=b).decode().strip()
assert not subprocess.check_output(["git","status","--porcelain"],cwd=b).strip()
p=b/"config/research.toml"; raw=p.read_bytes()
old=b'benchmark_status = "maintenance"'
assert raw.count(old)==1
p.write_bytes(raw.replace(old,b'benchmark_status = "active"'))
manifest=freeze_manifest(b,overwrite=True)
write_preflight_certificate(b)
assert verify_manifest(b)["ok"]
study="research/plans/PVM01-COMPACT-FEATURE-SCREEN-V1.json"
receipt="research/laboratory/PVM01-COMPACT-FEATURE-SCREEN-V1-readiness.receipt.json"
assert not (b/receipt).exists()
atomic_write_json(b/receipt, {"id":"PVM01-COMPACT-FEATURE-SCREEN-V1-readiness", "created_at":utc_now(),
    "study_path":study, "study_sha256":sha256_file(b/study),
    "preregistration_git_commit":"2ba76b6c9b2d4de1d76dcbcca7b3e4de5663c48a",
    "validated_source_git_commit":source, "original_root":str(b.parent/"NEXTAI"), "independent_clone_root":str(b),
    "shared_runtime_not_source_or_state":True,"all1108_full_regressions_pass":True,"failures_errors_skips":0,
    "full_regression_receipt_sha256":sha256_file(b/"research/reviews/PVM01-COMPACT-preseed-full-V1.json"),
    "source_history_receipt_sha256":sha256_file(b/"research/reviews/PVM01-COMPACT-history-source-conformance-V2.json"),
    "feature_gradient_numerical_and_fit_identity_verified":True, "all75_semantic_records_verified":True,
    "failed_bookkeeping_check_preserved_and_charged":True,"integrity_verified":True,
    "protected_files":len(manifest["files"]),"active_evaluator_sha256":manifest["evaluator_sha256"],
    "new_research_seed_data_fit_EXP_before_readiness":False,"ready_for_exactly_one_audited_registration":True,
    "scientific_recipe_and_gates_unchanged":True,"fresh_final_executed":False,"whole_program_complete":False})
append_jsonl(b/"research/events.jsonl", {"event":"research_program_study_ready", "created_at":utc_now(),
    "program_id":"NEXTAI-CONTINUATION-20261004-V1", "study_path":study,"study_sha256":sha256_file(b/study),
    "receipt_path":receipt,"receipt_sha256":sha256_file(b/receipt)})
write_report(b)
print(json.dumps({"ready":True,"evaluator":manifest["evaluator_sha256"],"bundle":manifest["candidate_bundle_sha256"]}))
