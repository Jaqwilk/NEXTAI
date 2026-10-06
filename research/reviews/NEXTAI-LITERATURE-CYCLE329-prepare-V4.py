"""Freeze the actual, inspected metadata paths before literature or tests."""
from pathlib import Path
from nextai_autoresearch.utils import atomic_write_json, sha256_file
root = Path.cwd()
original = root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-prepare-V1.py'
failures = [{'version': i, 'error': message, 'source_sha256': sha256_file(root / f'research/reviews/NEXTAI-LITERATURE-CYCLE329-prepare-V{i}.py')} for i, message in (
 (1, 'FileNotFoundError: research/program.md'), (2, 'FileNotFoundError: LABORATORY.md'), (3, 'FileNotFoundError: research/experiments.jsonl'))]
assert not any((root / f'research/plans/NEXTAI-LITERATURE-CYCLE329-V{i}.json').exists() for i in (1, 2, 3, 4))
atomic_write_json(root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-PREPREREG-FAILURES-V3.json', {'failures': failures, 'papers_opened': 0, 'checks_started': 0, 'fit': 0, 'all_startup_time_charged_from': '2026-10-06T02:53:30Z', 'failed_source_and_partial_metadata_archives_preserved': True})
source = original.read_text(encoding='utf-8')
source = source.replace("identity = 'NEXTAI-LITERATURE-CYCLE329-V1'", "identity = 'NEXTAI-LITERATURE-CYCLE329-V4'")
source = source.replace('NEXTAI-LITERATURE-CYCLE329-parent-V1', 'NEXTAI-LITERATURE-CYCLE329-parent-V4')
source = source.replace("'research/program.md', 'research/LABORATORY.md'", "'program.md', 'research/LAB_PLAN.md'")
source = source.replace("'configs/research.yaml'", "'config/research.toml'")
source = source.replace("'experiments.jsonl'", "'experiments.tsv'")
source = source.replace("'id': identity, 'cycle': 329", "'preserved_prepreregistration_authoring_failures': failures, 'id': identity, 'cycle': 329")
exec(compile(source, str(__file__), 'exec'))
