"""Freeze source and38-case fixture hashes before the single clone run."""
from pathlib import Path
import hashlib
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now
root = Path.cwd()
plan_path = root / 'research/plans/ASM01-POINT-SERIAL-PREPARATION-V1.json'
assert sha256_file(plan_path) == '679a82220eeb6c0998038ebdbefbe9b2a988ffe2e4e48e974ce46d6ba48950db'
plan = load_json(plan_path)
parent = load_json(root / 'research/laboratory/archive/ASM01-point-serial-cycle330-parent-V1/parent-bindings.json')
for name, digest in parent['files'].items():
    assert sha256_file(root / name) == digest, name
for name, binding in parent['ledger_prefixes'].items():
    assert hashlib.sha256((root / 'research' / name).read_bytes()[:binding['bytes']]).hexdigest() == binding['sha256'], name
path = root / 'research/reviews/ASM01-POINT-SERIAL-PREP-SOURCE-BINDINGS-V1.json'
assert not path.exists()
atomic_write_json(path, {'created_at': utc_now(), 'plan_sha256': sha256_file(plan_path),
 'source_path': plan['implementation_path'], 'source_sha256': sha256_file(root / plan['implementation_path']),
 'fixture_path': plan['fixture_path'], 'fixture_sha256': sha256_file(root / plan['fixture_path']),
 'frozen_cases': 38, 'old_parent_bindings_and_ledger_prefixes_preserved': True,
 'new_native_bytes': 0, 'fit': 0, 'EXP': 0, 'active_integration': False})
print(load_json(path))
