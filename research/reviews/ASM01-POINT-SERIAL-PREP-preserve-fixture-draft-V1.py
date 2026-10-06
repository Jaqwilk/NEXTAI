"""Recover exact pre-first-run fixture bytes and check the already frozen SHA."""
from pathlib import Path
import hashlib
root = Path.cwd()
path = root / 'research/preparations/ASM01-POINT-SERIAL-PREPARATION-V1/test_normalizer.py'
source = path.read_text(encoding='utf-8')
source = source.replace('import hashlib\n', '')
source = source.replace("('oversize-normalized', (BASE.replace(b'STROKE_COUNT: 1', b'STROKE_COUNT: 16384'), BASE.replace(b'STROKE_COUNT: 1', b'STROKE_COUNT: 20000')))", "('oversize-normalized', BASE.replace(b'STROKE_COUNT: 1', b'STROKE_COUNT: 20000'))")
source = source.replace("    for item in (payload if identity == 'oversize-normalized' else (payload,)):\n        with pytest.raises(ValueError):\n            normalizer.normalize_release_bytes(item)", "    with pytest.raises(ValueError):\n        normalizer.normalize_release_bytes(payload)")
source = source.replace("    parent_path = ROOT / 'research/laboratory/archive/ASM01-point-serial-cycle330-parent-V1/parent-bindings.json'\n    assert sha256_file(parent_path) == load_json(PLAN_PATH)['parent_bindings_sha256']\n    parent = load_json(parent_path)", "    parent = load_json(ROOT / 'research/laboratory/archive/ASM01-point-serial-cycle330-parent-V1/parent-bindings.json')")
source = source.replace("    for name, binding in parent['ledger_prefixes'].items():\n        assert hashlib.sha256((ROOT / 'research' / name).read_bytes()[:binding['bytes']]).hexdigest() == binding['sha256'], name\n", '')
source = source.replace('ASM01-POINT-SERIAL-PREP-SOURCE-BINDINGS-V2.json', 'ASM01-POINT-SERIAL-PREP-SOURCE-BINDINGS-V1.json')
payload = source.encode('utf-8')
assert hashlib.sha256(payload).hexdigest() == 'b24bc87c7aabbdc07711be521f6ea83b384fbf2a36d56a1adc69f06e5cae60bf'
destination = root / 'research/laboratory/archive/ASM01-point-serial-cycle330-fixture-drafts-V1/test_normalizer.py'
destination.parent.mkdir()
assert not destination.exists()
destination.write_bytes(payload)
print('Exact V1 fixture draft preserved; no test or native execution')
