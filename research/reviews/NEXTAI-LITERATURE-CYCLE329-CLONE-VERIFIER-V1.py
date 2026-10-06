"""One new no-scoring maintenance sequence, not a MUC stage retry."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
import nextai_autoresearch
from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now
root = Path(__file__).resolve().parents[2]
assert root.name == 'NEXTAI-VALIDATION-20261002'
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / 'src')
prefix = root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-CLONE-V1'
assert not prefix.with_suffix('.json').exists()
parent = load_json(root / 'research/laboratory/archive/NEXTAI-LITERATURE-CYCLE329-parent-V4/parent-bindings.json')
for name, binding in parent['files'].items():
    if name != 'research/state.json':
        assert sha256_file(root / name) == binding, name
for name, binding in parent['ledger_prefixes'].items():
    assert hashlib.sha256((root / 'research' / name).read_bytes()[:binding['bytes']]).hexdigest() == binding['sha256'], name
state = load_json(root / 'research/state.json')
assert state['completed_experiments'] == 123 and state['last_literature_review_completed_experiments'] == 123
for key, value in parent['state'].items():
    if key not in ('last_literature_review_completed_experiments', 'updated_at'):
        assert state[key] == value, key
evidence = load_json(root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-EVIDENCE-V1.json')
assert sha256_file(root / evidence['review_path']) == evidence['review_sha256']
sources = {e['source_id']: e for e in read_jsonl(root / 'research/sources.jsonl')}
assert [sources[i]['url'] for i in evidence['source_ids']] == evidence['fixed_pages_read']
for identity in evidence['source_ids']:
    validate_document('source', sources[identity], root)
checks = []
commands = [
 ('lifecycle', [sys.executable, '-m', 'pytest', '-q', 'tests/test_protocol_v2.py::test_checked_in_research_lifecycle_is_consistent', '--basetemp', str(root / 'research/tmp/NEXTAI-LITERATURE-CYCLE329-FIXTURES-V1'), '--junitxml', str(prefix.with_suffix('.xml'))], 160),
 ('doctor', [sys.executable, '-m', 'nextai_autoresearch.cli', 'doctor'], 240),
 ('lab', [sys.executable, '-m', 'nextai_autoresearch.cli', 'lab', 'status'], 180),
]
deadline = datetime.fromisoformat('2026-10-06T03:13:30+00:00')
for label, command, timeout in commands:
    remaining = (deadline - datetime.now(timezone.utc)).total_seconds() - 90
    if remaining <= 0:
        raise SystemExit('Deadline; preserve finished checks, stop unstarted scope')
    timed_out = False
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, timeout=min(timeout, remaining))
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        result = subprocess.CompletedProcess(command, 124, exc.stdout or b'', exc.stderr or b'')
    out = prefix.with_name(prefix.name + '.' + label + '.stdout.txt')
    err = prefix.with_name(prefix.name + '.' + label + '.stderr.txt')
    out.write_bytes(result.stdout)
    err.write_bytes(result.stderr)
    checks.append({'name': label, 'returncode': result.returncode, 'timed_out': timed_out, 'stdout_sha256': sha256_file(out), 'stderr_sha256': sha256_file(err)})
    atomic_write_json(prefix.with_suffix('.json'), {'created_at': utc_now(), 'checks': checks, 'complete': len(checks) == 3 and all(c['returncode'] == 0 for c in checks), 'scientific_parent_hashes_preserved': True, 'ledger_prefixes_preserved': True, 'actual_review_and_source_records_verified': True, 'package_origin': str(nextai_autoresearch.__file__), 'new_fit': 0, 'new_EXP': 0, 'new_scoring_seeds': 0})
    if result.returncode:
        sys.stdout.buffer.write(result.stdout)
        sys.stderr.buffer.write(result.stderr)
        raise SystemExit(result.returncode)
lab = json.loads(prefix.with_name(prefix.name + '.lab.stdout.txt').read_text(encoding='utf-8'))
assert not lab['errors'] and not lab['warnings'] and not lab['scoring_authorized']
print(json.dumps({'checks': checks, 'scoring': False, 'new_fit': 0, 'new_EXP': 0}))
