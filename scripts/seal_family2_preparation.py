"""No-scoring maintenance seal after preserving the previous manifest/queue bytes."""
from pathlib import Path
import json

from nextai_autoresearch.baseline_semantics import write_preflight_certificate, verify_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.report import write_report
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, utc_now

root=Path(__file__).resolve().parents[1]
parent=json.loads((root/'research/laboratory/archive/FAMILY2-cycle320-parent-V1/research/eval_manifest.json').read_text())
changed={'.gitattributes','config/research.toml','AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md'}
from nextai_autoresearch.utils import sha256_file
for name,digest in parent['files'].items():
    if name not in changed:
        assert sha256_file(root/name)==digest,name
manifest=freeze_manifest(root,overwrite=True)
write_preflight_certificate(root)
write_report(root)
assert verify_manifest(root)['ok']
verify_preflight_certificate(root)
wallet=status(root)
assert not wallet['scoring_authorized'] and not wallet['paid_run_pending']
assert wallet['protected_future_compute_seconds']==47000 and wallet['protected_future_registration_attempts']==7
assert wallet['stage_b_registration_attempts_used']==1
receipt=dict(created_at=utc_now(),protected_files=len(manifest['files']),old_scientific_bytes_unchanged=True,
             permitted_metadata_changes=sorted(changed),manifest_sha256=sha256_file(root/'research/eval_manifest.json'),
             maintenance=True,scoring=False,program=wallet,fit=0,new_EXP=0)
atomic_write_json(root/'research/reviews/FAMILY2-MAINTENANCE-SEAL-V1.json',receipt)
print(json.dumps({k:v for k,v in receipt.items() if k!='program'}))
