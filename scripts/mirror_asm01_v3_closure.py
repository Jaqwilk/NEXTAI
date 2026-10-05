"""Mirror settled cycle324 records and verify both checkouts under prepaid administration."""
import json
from pathlib import Path
import shutil
import subprocess
import time

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.report import write_report
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

started = time.monotonic()
root = Path(__file__).resolve().parents[1]
clone = root.parent / 'NEXTAI-VALIDATION-20261002'
assert root.name == 'NEXTAI' and (clone / '.git').is_dir() and root.resolve() != clone.resolve()
proof_path = 'research/reviews/ASM01-V3-FINAL-ADMIN-MIRROR-V1.json'
assert not (root / proof_path).exists()
assert (root / 'research/laboratory/ASM01-CYCLE324-COMPLETION-V1.receipt.json').exists()
write_report(root)
mutable = {'research/events.jsonl', 'research/state.json', 'research/REPORT.md',
           'research/REPORT.provenance.json', 'research/eval_manifest.json',
           'research/laboratory/preflight_certificate.json'}
owned = set(mutable)
for item in subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'],
                                    cwd=root).decode().split('\0'):
    if not item:
        continue
    relative = item[3:]
    assert relative in mutable or relative.startswith((
        'research/reviews/NEXTAI-B-324-', 'research/reviews/ASM01-V3-',
        'research/laboratory/ASM01-CYCLE324-', 'research/analyses/ASM01-CYCLE324-',
        'scripts/mirror_asm01_v3_closure.py',
        'scripts/close_asm01_v3_intake_invalidity.py')), relative
    owned.add(relative)
assert (root / 'research/events.jsonl').read_bytes().startswith((clone / 'research/events.jsonl').read_bytes())
for relative in sorted(owned):
    source, destination = root / relative, clone / relative
    if destination.exists() and relative not in mutable:
        assert destination.read_bytes() == source.read_bytes(), relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
manifest = json.loads((root / 'research/eval_manifest.json').read_text())
paths = set(manifest['files']) | owned | {'research/experiments.tsv', 'research/sources.jsonl'}
digests = {}
for relative in sorted(paths):
    digest = sha256_file(root / relative)
    assert sha256_file(clone / relative) == digest, relative
    digests[relative] = digest
checks = {'original': verify_manifest(root), 'clone': verify_manifest(clone)}
assert all(item['ok'] for item in checks.values()), checks
wallets = {'original': status(root), 'clone': status(clone)}
assert wallets['original'] == wallets['clone']
wallet = wallets['original']
assert wallet['study_terminal'] and not wallet['program_terminal']
assert not wallet['scoring_authorized'] and not wallet['paid_run_pending'] and not wallet['ready']
assert wallet['pending_fit_reservation_seconds'] == 0
for directory in (root, clone):
    assert sha256_file(directory / 'research/results/EXP-20261005-0007.json') == '78380a19ffacf4a58af0bd8586425fbacee44b2e5a92c6e056f3699f769ed255'
    assert sha256_file(directory / 'research/results/EXP-20261005-0006.fitted-state.zip') == '3576935b401f6c9324f2f4ed426de104b632a22ba74fb04da55757421f7632a8'
    assert not any((directory / name).exists() for name in ('STOP', 'PAUSE', 'research/run.lock'))
    state = json.loads((directory / 'research/state.json').read_text())
    assert state['cycle_number'] == 324 and state['completed_experiments'] == 122
    assert state['active_experiment_id'] is None and state['last_experiment_id'] == 'EXP-20261005-0007'
assert not (clone / 'research/data/asm01_native_v1/screen-v3.npz').exists()
receipt = dict(created_at=utc_now(), cycle=324, original_root=str(root), clone_root=str(clone),
               files_compared=len(digests), file_sha256=digests, protected_files=len(manifest['files']),
               both_current_manifests_ok=True, manifest_verification=checks,
               both_program_status_identical=True, program=wallet,
               whole_wall_seconds=time.monotonic() - started,
               charged_by='NEXTAI-B-324-administration-prepaid', prepaid_seconds=300,
               new_EXPs=0, new_registrations=0, research_fit=0, scoring=False,
               native_data_decoded_in_mirror=False, extended_goal_completed=False,
               disk_free_bytes=shutil.disk_usage(root).free)
atomic_write_json(root / proof_path, receipt)
(clone / proof_path).write_bytes((root / proof_path).read_bytes())
print(json.dumps({'mirror_ok': True, 'files_compared': len(digests),
                  'protected_files': len(manifest['files']), 'both_manifests_ok': True,
                  'B_seconds': wallet['stage_b_compute_seconds_charged'],
                  'whole_wall_seconds': receipt['whole_wall_seconds'], 'study_terminal': True,
                  'goal_complete': False}), flush=True)
