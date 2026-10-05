"""Maintenance seal for immutable failed intakes; never an execution readiness grant."""
from pathlib import Path
import json

from nextai_autoresearch.baseline_semantics import write_preflight_certificate,verify_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest,verify_manifest
from nextai_autoresearch.report import write_report
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now

root=Path(__file__).resolve().parents[1]
parent=root/'research/laboratory/archive/ASM01-cycle321-parent-V1'
manifest=json.loads((parent/'research/eval_manifest.json').read_text(encoding='utf-8'))
changed={'src/nextai_autoresearch/research_program.py','src/nextai_autoresearch/runner.py',
         'src/nextai_autoresearch/audit.py','src/nextai_autoresearch/integrity.py',
         'schemas/experiment_plan.schema.json','config/baseline_semantics.json','config/research.toml',
         'AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','.gitignore'}
for path,digest in manifest['files'].items():
    if path not in changed:
        assert sha256_file(root/path)==digest,path
old=json.loads((parent/'config/baseline_semantics.json').read_text(encoding='utf-8'))
new=json.loads((root/'config/baseline_semantics.json').read_text(encoding='utf-8'))
assert all(new['baselines'][name]==record for name,record in old['baselines'].items())
old_schema=json.loads((parent/'schemas/experiment_plan.schema.json').read_text(encoding='utf-8'))
new_schema=json.loads((root/'schemas/experiment_plan.schema.json').read_text(encoding='utf-8'))
assert new_schema['allOf'][:-1]==old_schema['allOf']
assert {k:v for k,v in new_schema.items() if k!='allOf'}=={k:v for k,v in old_schema.items() if k!='allOf'}
for version in (1,2):
    assert json.loads((root/f'research/data_manifests/ASM01-ACQUISITION-V{version}.json').read_text(encoding='utf-8'))['complete'] is False
current=freeze_manifest(root,overwrite=True)
write_preflight_certificate(root)
write_report(root)
integrity=verify_manifest(root);assert integrity['ok']
certificate=verify_preflight_certificate(root);wallet=status(root)
assert not wallet['scoring_authorized'] and not wallet['paid_run_pending'] and not wallet['ready']
assert wallet['protected_future_compute_seconds']==47000 and wallet['protected_future_registration_attempts']==7
assert wallet['stage_b_registration_attempts_used']==1
receipt=dict(created_at=utc_now(),protected_files=len(current['files']),all_historical_science_bytes_unchanged=True,
             all_historical_baseline_records_and_schema_clauses_unchanged=True,permitted_source_metadata_changes=sorted(changed),
             current_manifest_sha256=sha256_file(root/'research/eval_manifest.json'),
             preflight_sha256=certificate['certificate_sha256'],maintenance=True,scoring=False,ready=False,
             source_frozen=True,new_EXP=0,new_paid_registrations=0,new_research_fit_seconds=0,
             both_failed_intakes_preserved=True,program=wallet)
atomic_write_json(root/'research/reviews/ASM01-MAINTENANCE-SEAL-V1.json',receipt)
print(json.dumps({k:v for k,v in receipt.items() if k!='program'}),flush=True)
