"""Archive parent maintenance and activate only the newly authorized preparation overlay."""
import json
from pathlib import Path
import shutil
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import status as program_status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
tag = "MUC02-NEGATIVES-REPLICATION-20261006-V1"
plan_path = f"research/plans/{tag}.json"
auth_path = f"research/laboratory/{tag}.json"
assert sha256_file(root / plan_path) == "cbde3b9e16bc6a8b59139249d065a9faaa2cbad41c2891293b3156d5ae7ef4a4"
assert (root / "research/laboratory/ASM01-CYCLE327-COMPLETION-V1.receipt.json").is_file()
assert not any((root / p).exists() for p in ("STOP", "PAUSE", "research/run.lock"))
wallet = program_status(root)
assert wallet["study_terminal"] and not wallet["program_terminal"]
archive = root / "research/laboratory/archive/MUC02-REPLICATION-parent-V1"
assert not archive.exists()
files = ["config/research.toml", "AGENTS.md", "program.md", "research/LAB_PLAN.md",
         "docs/CURRENT_STATUS.md", "research/eval_manifest.json",
         "research/laboratory/preflight_certificate.json", "research/state.json",
         "src/nextai_autoresearch/laboratory.py", "src/nextai_autoresearch/integrity.py",
         "src/nextai_autoresearch/audit.py", "schemas/experiment_plan.schema.json"]
for relative in files:
    destination = archive / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / relative, destination)
parent = json.loads((root / "research/eval_manifest.json").read_text())
prefixes = {}
for name in ("events.jsonl", "experiments.tsv", "plan_registry.jsonl", "plan_status_events.jsonl", "hypothesis_events.jsonl", "sources.jsonl"):
    p = root / "research" / name
    prefixes[name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
atomic_write_json(archive / "parent-bindings.json", {"created_at": utc_now(),
    "files": {p: sha256_file(root / p) for p in files}, "ledger_prefixes": prefixes,
    "protected_scientific_files": parent["files"], "B_wallet": wallet,
    "plan_sha256": sha256_file(root / plan_path)})
header = ("# Current separate MUC02 negative-sampling replication (2026-10-06)\n\n"
    "New human-authorized independent development stage; prior MUC failures/decisions remain consumed.\n"
    "Frozen MUC02-NEGATIVES-REPLICATION-20261006-V1 before implementation/data.\n"
    "Same model,4096 pairs,192 steps; random versus hard,5 fresh paired seeds.\n"
    "Deadline2026-10-06T05:50:00Z,stage wall14400s,total fit3600s; no execution retry.\n"
    "Same two primary effect/CI/sign and known-answer/symbolic gates; no outcome tuning.\n"
    "Canonical independent-clone experiment only after conformance,freeze/preflight/readiness.\n"
    "Separate wallet; B remains active with protected7tickets/47000s unchanged.\n"
    "ASM/HAR future writers,WT8-9,external models/API,architectures and schedule changes forbidden.\n"
    "Earlier stage-specific sections below remain preserved history.\n\n")
for relative in ("AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md"):
    p = root / relative
    p.write_bytes(header.encode("utf-8") + p.read_bytes())
p = root / "config/research.toml"
text = p.read_text(encoding="utf-8")
assert 'benchmark_version = "asm01_native_memory_v3"' in text
assert "[muc02_replication]" not in text
text = text.replace('benchmark_version = "asm01_native_memory_v3"', 'benchmark_version = "mutable_contact_ledger_negatives_replication_v1"', 1)
text += '\n[muc02_replication]\nactive = true\n'
p.write_text(text, encoding="utf-8", newline="\n")
append_jsonl(root / "research/events.jsonl", {"event": "muc02_replication_authorized", "created_at": utc_now(),
    "stage_id": tag, "authorization_path": auth_path, "authorization_sha256": sha256_file(root / auth_path),
    "plan_path": plan_path, "plan_sha256": sha256_file(root / plan_path)})
print(json.dumps({"overlay": "preparation_only", "new_EXP": 0, "new_fit": 0, "B_wallet_preserved": True}))
