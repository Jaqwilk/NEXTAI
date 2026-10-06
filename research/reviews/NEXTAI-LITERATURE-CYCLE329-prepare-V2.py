"""Separate metadata binding after preserved pre-preregistration path failure."""
from pathlib import Path
import json
import hashlib

root = Path.cwd()
original = root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-prepare-V1.py'
source = original.read_text(encoding='utf-8')
assert not (root / 'research/plans/NEXTAI-LITERATURE-CYCLE329-V1.json').exists()
failure = {'status': 'authoring_failed_before_preregistration_or_reservation', 'error': 'FileNotFoundError: research/program.md',
           'source_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
           'papers_opened': 0, 'checks_started': 0, 'fit': 0,
           'scope_stopped': 'V1 metadata authoring stopped; separate V2 binds actual root metadata paths before any paper or check.',
           'cost': 'Included from 02:53:30Z in the unchanged 1200-second total auxiliary cap.'}
(root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-PREPREREG-FAILURE-V1.json').write_text(json.dumps(failure, indent=2) + '\n', encoding='utf-8', newline='\n')
source = source.replace("identity = 'NEXTAI-LITERATURE-CYCLE329-V1'", "identity = 'NEXTAI-LITERATURE-CYCLE329-V2'")
source = source.replace('NEXTAI-LITERATURE-CYCLE329-parent-V1', 'NEXTAI-LITERATURE-CYCLE329-parent-V2')
source = source.replace("'research/program.md', 'research/LABORATORY.md'", "'program.md', 'LABORATORY.md'")
source = source.replace("'configs/research.yaml'", "'config.yaml'")
source = source.replace("'id': identity, 'cycle': 329", "'prepreregistration_failure': failure, 'id': identity, 'cycle': 329")
exec(compile(source, str(__file__), 'exec'))
