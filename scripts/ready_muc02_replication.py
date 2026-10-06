"""One immutable clone conformance receipt activates only the prospective stage."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from nextai_autoresearch.baseline_semantics import write_preflight_certificate, verify_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.muc02_replication_stage import status, PLAN_SHA256, PLAN, ID, COHORT
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
clone = root.parent / "NEXTAI-VALIDATION-20261002"
assert root.name == "NEXTAI"
relative = "research/reviews/MUC02-REPLICATION-READINESS-V1.json"
assert not (root / relative).exists()
check = json.loads((root / "research/reviews/MUC02-REPL-preseed-conformance-V1.json").read_text())
assert check["result"]["returncode"] == 0 and not check["error"]
assert check["result"]["exit_job_active_process_count"] == 0
proof_path = clone / "research/reviews/MUC02-REPLICATION-CLONE-PRESEED-V1.json"
proof = json.loads(proof_path.read_text())
assert proof["complete"] and proof["clone_package_origin_verified"] and proof["scoring_seed_draws"] == 0 and proof["fit_seconds"] == 0
assert [c["name"] for c in proof["checks"]] == ["targeted_conformance", "doctor", "lab"]
assert all(c["returncode"] == 0 for c in proof["checks"])
xml_path = proof_path.with_suffix(".xml")
xml = ET.parse(xml_path).getroot()
suites = list(xml.iter("testsuite"))
assert suites and sum(int(s.get("tests", 0)) for s in suites) > 40
assert all(int(s.get(k, 0)) == 0 for s in suites for k in ("failures", "errors", "skipped"))
lab_path = clone / "research/reviews/MUC02-REPLICATION-CLONE-PRESEED-V1.lab.stdout.txt"
lab = json.loads(lab_path.read_text(encoding="utf-8"))
assert not lab["errors"] and not lab["warnings"] and not lab["scoring_authorized"]
assert status(root)["registrations_used"] == 0 and status(clone)["registrations_used"] == 0
assert verify_manifest(root)["ok"] and verify_manifest(clone)["ok"]
assert sha256_file(root / PLAN) == sha256_file(clone / PLAN) == PLAN_SHA256
p = root / "config/research.toml"
text = p.read_text(encoding="utf-8")
assert 'benchmark_status = "maintenance"' in text
text = text.replace('benchmark_status = "maintenance"', 'benchmark_status = "active"', 1)
p.write_text(text, encoding="utf-8", newline="\n")
freeze_manifest(root, overwrite=True)
write_preflight_certificate(root)
verify_preflight_certificate(root)
write_report(root)
atomic_write_json(root / relative, {"created_at": utc_now(), "status": "validated_ready", "cohort": COHORT,
    "plan_sha256": PLAN_SHA256, "required_checks_passed": True, "scoring_seed_draws": 0,
    "fit_seconds_charged": 0, "clone_package_origin_verified": True,
    "conformance_check_sha256": sha256_file(root / "research/reviews/MUC02-REPL-preseed-conformance-V1.json"),
    "clone_proof_sha256": sha256_file(proof_path), "junit_sha256": sha256_file(xml_path),
    "tests_passed": sum(int(s.get("tests", 0)) for s in suites),
    "active_manifest_sha256": sha256_file(root / "research/eval_manifest.json"),
    "active_preflight_sha256": sha256_file(root / "research/laboratory/preflight_certificate.json"),
    "B_wallet_preserved": True})
append_jsonl(root / "research/events.jsonl", {"event": "muc02_replication_ready", "created_at": utc_now(),
    "stage_id": ID, "plan_sha256": PLAN_SHA256, "receipt_path": relative, "receipt_sha256": sha256_file(root / relative)})
assert status(root)["scoring_authorized"] and verify_manifest(root)["ok"]
print(json.dumps({"ready": True, "tests": sum(int(s.get("tests", 0)) for s in suites), "fit": 0, "seeds": 0}))
