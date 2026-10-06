"""Actual metadata bindings; preserved failed authoring did not start review/checks."""
from pathlib import Path
import json
from nextai_autoresearch.utils import atomic_write_json, sha256_file
root = Path.cwd()
original = root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-prepare-V1.py'
assert not any((root / f'research/plans/NEXTAI-LITERATURE-CYCLE329-V{i}.json').exists() for i in (1, 2))
failures = [
 {'version': 1, 'error': 'FileNotFoundError: research/program.md', 'source_sha256': sha256_file(original)},
 {'version': 2, 'error': 'FileNotFoundError: LABORATORY.md', 'source_sha256': sha256_file(root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-prepare-V2.py')},
]
atomic_write_json(root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-PREPREREG-FAILURES-V2.json', {
 'failures': failures, 'all_costs_included_from': '2026-10-06T02:53:30Z', 'papers_opened': 0,
 'checks_started': 0, 'new_fit': 0, 'old_drafts_not_preregistered': True,
 'correction_scope': 'Metadata paths only, before any scientific code, paper or verification execution.'})
source = original.read_text(encoding='utf-8')
source = source.replace("identity = 'NEXTAI-LITERATURE-CYCLE329-V1'", "identity = 'NEXTAI-LITERATURE-CYCLE329-V3'")
source = source.replace('NEXTAI-LITERATURE-CYCLE329-parent-V1', 'NEXTAI-LITERATURE-CYCLE329-parent-V3')
source = source.replace("'research/program.md', 'research/LABORATORY.md'", "'program.md', 'research/LAB_PLAN.md'")
source = source.replace("'configs/research.yaml', ", '')
source = source.replace("'id': identity, 'cycle': 329", "'preserved_prepreregistration_authoring_failures': failures, 'id': identity, 'cycle': 329")
exec(compile(source, str(__file__), 'exec'))
