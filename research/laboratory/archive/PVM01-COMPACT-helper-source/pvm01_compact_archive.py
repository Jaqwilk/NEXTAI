"""Preserve evaluated bytes and every runtime artifact before maintenance."""
import hashlib
import json
from pathlib import Path
import shutil

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b=Path.cwd(); identity="EXP-20261004-0007"
result_path=b/f"research/results/{identity}.json"
result=json.loads(result_path.read_text())
assert verify_manifest(b)["ok"]
events=read_jsonl(b/"research/events.jsonl")
assert not any(e.get("event")=="research_program_outcome_preserved" and e.get("experiment_id")==identity for e in events)
append_jsonl(b/"research/events.jsonl", {"event":"research_program_outcome_preserved","created_at":utc_now(),
    "program_id":"NEXTAI-CONTINUATION-20261004-V1","experiment_id":identity,
    "result_sha256":sha256_file(result_path),"all_outcomes_preserved":True})
manifest=json.loads((b/"research/eval_manifest.json").read_text())
source=b/f"research/laboratory/archive/{identity}-evaluated-source"
runtime=b/f"research/laboratory/archive/{identity}-runtime"
assert not source.exists() and not runtime.exists()
extras=["research/eval_manifest.json",f"research/plans/{identity}.json",
        "research/laboratory/PVM01-COMPACT-FEATURE-SCREEN-V1-readiness.receipt.json",
        "research/laboratory/preflight_certificate.json",
        "research/reviews/PVM01-COMPACT-prepaid-gates-V1.json",
        "research/reviews/PVM01-COMPACT-history-source-conformance-V2.json"]
source_names=sorted(set(manifest["files"]) | set(extras))
runtime_names=[p.relative_to(b).as_posix() for p in sorted((b/f"research/tmp/{identity}").rglob("*")) if p.is_file()]
runtime_names += [p.relative_to(b).as_posix() for p in sorted((b/"research/logs").rglob("*"))
                 if p.is_file() and identity in p.relative_to(b).as_posix()]
runtime_names += [p.relative_to(b).as_posix() for p in sorted((b/"research/reviews").glob("PVM01-COMPACT-*-V1*"))
                 if p.is_file() and any(tag in p.name for tag in ("register-", "run-", "audited-controller-"))]
runtime_names=sorted(set(runtime_names))
footprint=sum((b/name).stat().st_size for name in source_names+runtime_names)
free=shutil.disk_usage(b).free
assert free-footprint>10*1024**3
copies={}
for root,names in ((source,source_names),(runtime,runtime_names)):
    for name in names:
        original=(b/name).resolve()
        assert original.is_relative_to(b.resolve())
        relative=".gitattributes.raw" if name==".gitattributes" else name
        output=root/relative
        output.parent.mkdir(parents=True,exist_ok=True)
        payload=original.read_bytes()
        output.write_bytes(payload)
        expected=hashlib.sha256(payload).hexdigest()
        assert sha256_file(output)==expected
        copies[output.relative_to(b).as_posix()]={"source":name,"sha256":expected,"bytes":len(payload)}
atomic_write_json(b/"research/reviews/PVM01-COMPACT-scientific-archive-V1.json",{
    "created_at":utc_now(),"experiment_id":identity,"result_sha256":sha256_file(result_path),
    "source_count":len(source_names),"runtime_count":len(runtime_names),"copies":copies,
    "footprint_bytes":footprint,"free_before_bytes":free,"free_after_bytes":shutil.disk_usage(b).free,
    "protected_source_verified_before_maintenance":True,"no_archive_scope_deleted":True})
print("Raw source",len(source_names),"runtime",len(runtime_names),"bytes",footprint,"preserved")
