"""Preserve failed native intake and seal maintenance without changing its recipe."""
import json
from pathlib import Path
import shutil

from nextai_autoresearch.baseline_semantics import write_preflight_certificate, verify_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.report import write_report
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
assert root.name == 'NEXTAI'
parent = root / 'research/laboratory/archive/ASM01-cycle324-parent-V1'
manifest = json.loads((parent / 'research/eval_manifest.json').read_text())
allowed = {'AGENTS.md', 'program.md', 'research/LAB_PLAN.md', 'docs/CURRENT_STATUS.md',
           'config/research.toml', 'config/baseline_semantics.json', 'schemas/experiment_plan.schema.json',
           'src/nextai_autoresearch/research_program.py', 'src/nextai_autoresearch/runner.py',
           'src/nextai_autoresearch/integrity.py'}
for relative, digest in manifest['files'].items():
    if relative not in allowed:
        assert sha256_file(root / relative) == digest, relative
old_schema = json.loads((parent / 'schemas/experiment_plan.schema.json').read_text())
new_schema = json.loads((root / 'schemas/experiment_plan.schema.json').read_text())
assert new_schema['allOf'][:-1] == old_schema['allOf']
assert {k: v for k, v in new_schema.items() if k != 'allOf'} == {k: v for k, v in old_schema.items() if k != 'allOf'}
old_semantics = json.loads((parent / 'config/baseline_semantics.json').read_text())
new_semantics = json.loads((root / 'config/baseline_semantics.json').read_text())
assert new_semantics['baselines'] == old_semantics['baselines']
assert new_semantics['cohorts'][:-1] == old_semantics['cohorts']
intake_path = 'research/data_manifests/ASM01-ACQUISITION-V3.json'
intake = json.loads((root / intake_path).read_text())
assert intake['complete'] is False and intake['error'] == 'ValueError: Native point grammar'
assert intake['native_files_attempted'] == 75 and intake['native_files_converted'] == 74
assert (intake['current_writer'], intake['current_sample'], intake['D_samples_opened']) == (1, 75, 0)
assert len(intake['attempted_sample_text_sha256']) == 75
assert intake['new_download_bytes'] == 0 and intake['excluded_foreign_member_numeric_reads'] == 0
for version in (1, 2):
    assert json.loads((root / f'research/data_manifests/ASM01-ACQUISITION-V{version}.json').read_text())['complete'] is False
archive = root / 'research/laboratory/archive/ASM01-cycle324-prospective-metadata-V1'
assert not archive.exists()
paths = ['AGENTS.md', 'program.md', 'research/LAB_PLAN.md', 'docs/CURRENT_STATUS.md', 'research/state.json']
for relative in paths:
    target = archive / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / relative, target)
header = ("# Current cycle324 — ASM01 V3 native intake invalidity (2026-10-05)\n\n"
          "The scientific V3 study was frozen before implementation and remaining data.\n"
          "Independent clone conformance131/131 PASS; unchanged models/geometry/grids/gates.\n"
          "One native intake converted74 samples of writer1, then sample75 failed\n"
          "Native point grammar.75 attempted text hashes preserved; D0,NPZ0,fit0,EXP0.\n"
          "Stop unstarted scope; no same-cycle parser/geometry/sample rescue or paid retry.\n"
          "Exact offending row form remains uninstrumented; failure is not a valid\n"
          "learning/transfer/economic null. Scientific comparison INCONCLUSIVE.\n"
          "Current V3 maintenance,scoring=false; full failures and costs retained.\n"
          "B and extended goal remain active,protected7tickets/47000s unchanged.\n"
          "Next separately preregistered preparation should inventory complete lexical\n"
          "forms of the fixed screen cohort before another scientific intake,without\n"
          "coordinate/name emission,numeric conversion,fit,new sample replacement or\n"
          "future writer access. Distinguish release metadata from changed geometry;\n"
          "freeze concrete rules before repair and preserve every earlier failed version.\n"
          "No WT8-9,external model/API or schedule change.\n\n"
          "Earlier stage-specific sections below remain preserved history.\n\n").encode()
for relative in paths[:4]:
    (root / relative).write_bytes(header + (root / relative).read_bytes())
state_path = root / 'research/state.json'
state = json.loads(state_path.read_text())
assert state['cycle_number'] == 323 and state['completed_experiments'] == 122 and state['active_experiment_id'] is None
state.update(cycle_number=324, updated_at=utc_now())
atomic_write_json(state_path, state)
append_jsonl(root / 'research/events.jsonl', {
    'event': 'native_intake_invalidity_preserved', 'created_at': utc_now(), 'cycle': 324,
    'program_id': 'NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1',
    'study_path': 'research/plans/ASM01-FROZEN-SOURCE-SCREEN-V3.json',
    'intake_receipt_path': intake_path, 'intake_receipt_sha256': sha256_file(root / intake_path),
    'attempted': 75, 'converted': 74, 'D_opened': 0, 'unstarted_scope_stopped': True,
    'new_EXPs': 0, 'scoring': False,
})
current = freeze_manifest(root, overwrite=True)
write_preflight_certificate(root)
write_report(root)
assert verify_manifest(root)['ok']
certificate = verify_preflight_certificate(root)
wallet = status(root)
assert not wallet['scoring_authorized'] and not wallet['ready'] and not wallet['paid_run_pending']
assert wallet['stage_b_registration_attempts_used'] == 1
assert wallet['protected_future_compute_seconds'] == 47000 and wallet['protected_future_registration_attempts'] == 7
receipt = dict(created_at=utc_now(), cycle=324, protected_files=len(current['files']),
               all_historical_science_bytes_unchanged=True,
               old_schema_clauses_and_semantic_records_unchanged=True,
               archived_prospective_metadata_path=archive.relative_to(root).as_posix(),
               allowed_new_cohort_metadata_paths=sorted(allowed),
               intake_receipt_sha256=sha256_file(root / intake_path),
               manifest_sha256=sha256_file(root / 'research/eval_manifest.json'),
               preflight_sha256=certificate['certificate_sha256'],
               maintenance=True, ready=False, scoring=False, native_intake_complete=False,
               new_EXP=0, new_research_fit=0, program=wallet)
atomic_write_json(root / 'research/reviews/ASM01-V3-FAILED-INTAKE-MAINTENANCE-SEAL-V1.json', receipt)
print(json.dumps({k: v for k, v in receipt.items() if k != 'program'}), flush=True)
