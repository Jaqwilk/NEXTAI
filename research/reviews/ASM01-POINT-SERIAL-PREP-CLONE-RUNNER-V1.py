"""Only the frozen synthetic matrix, never native parser intake or fit."""
from pathlib import Path
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
import nextai_autoresearch
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now
root = Path(__file__).resolve().parents[2]
assert root.name == 'NEXTAI-VALIDATION-20261002'
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / 'src')
binding = load_json(root / 'research/reviews/ASM01-POINT-SERIAL-PREP-SOURCE-BINDINGS-V2.json')
assert sha256_file(root / binding['source_path']) == binding['source_sha256']
assert sha256_file(root / binding['fixture_path']) == binding['fixture_sha256']
prefix = root / 'research/reviews/ASM01-POINT-SERIAL-PREP-CLONE-V1'
assert not prefix.with_suffix('.json').exists()
command = [sys.executable, '-m', 'pytest', '-q', '-x', str(root / binding['fixture_path']),
 '--basetemp', str(root / 'research/tmp/ASM01-POINT-SERIAL-PREP-FIXTURES-V1'), '--junitxml', str(prefix.with_suffix('.xml'))]
timed_out = False
try:
    run = subprocess.run(command, cwd=root, capture_output=True, timeout=180)
except subprocess.TimeoutExpired as exc:
    timed_out = True
    run = subprocess.CompletedProcess(command, 124, exc.stdout or b'', exc.stderr or b'')
out = prefix.with_name(prefix.name + '.stdout.txt')
err = prefix.with_name(prefix.name + '.stderr.txt')
out.write_bytes(run.stdout)
err.write_bytes(run.stderr)
xml_path = prefix.with_suffix('.xml')
counts = {'tests': 0, 'failures': 0, 'errors': 0, 'skipped': 0}
if xml_path.exists():
    tree = ET.parse(xml_path)
    for suite in tree.getroot().iter('testsuite'):
        for key in counts:
            counts[key] += int(suite.attrib.get(key, 0))
complete = run.returncode == 0 and counts == {'tests': 38, 'failures': 0, 'errors': 0, 'skipped': 0}
atomic_write_json(prefix.with_suffix('.json'), {'created_at': utc_now(), 'complete': complete, 'returncode': run.returncode,
 'timed_out': timed_out, 'counts': counts, 'source_sha256': binding['source_sha256'], 'fixture_sha256': binding['fixture_sha256'],
 'stdout_sha256': sha256_file(out), 'stderr_sha256': sha256_file(err), 'package_origin': str(nextai_autoresearch.__file__),
 'new_native_bytes': 0, 'fit': 0, 'EXP': 0, 'active_integration': False, 'retry': False})
sys.stdout.buffer.write(run.stdout)
sys.stderr.buffer.write(run.stderr)
print(json.dumps({'complete': complete, 'counts': counts}), flush=True)
raise SystemExit(0 if complete else (run.returncode or 1))
