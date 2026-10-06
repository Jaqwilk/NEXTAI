"""Freeze a finite, no-scoring literature maintenance scope before reading papers."""
from pathlib import Path
import hashlib
import json
import shutil
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import auxiliary_reserve
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path.cwd()
identity = 'NEXTAI-LITERATURE-CYCLE329-V1'
plan_path = root / 'research/plans' / (identity + '.json')
assert not plan_path.exists()
state = json.loads((root / 'research/state.json').read_text())
assert state['completed_experiments'] == 123
assert state['last_literature_review_completed_experiments'] == 117
archive = root / 'research/laboratory/archive/NEXTAI-LITERATURE-CYCLE329-parent-V1'
archive.mkdir()
paths = ['research/state.json', 'configs/research.yaml', 'research/eval_manifest.json',
         'research/results/EXP-20261006-0001.json', 'research/reviews/EXP-20261006-0001-paired-analysis.json',
         'AGENTS.md', 'research/program.md', 'research/LABORATORY.md']
# Copy metadata only. Results stay in place and are bound by hash.
bindings = {}
for name in paths:
    path = root / name
    if not path.exists():
        if name == 'configs/research.yaml':
            continue
        raise FileNotFoundError(name)
    bindings[name] = sha256_file(path)
    if name in ('research/state.json', 'research/eval_manifest.json'):
        shutil.copyfile(path, archive / path.name)
prefixes = {}
for name in ('events.jsonl', 'sources.jsonl', 'experiments.jsonl'):
    path = root / 'research' / name
    data = path.read_bytes()
    prefixes[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
atomic_write_json(archive / 'parent-bindings.json', {'files': bindings, 'ledger_prefixes': prefixes, 'state': state})
plan = {
    'id': identity, 'cycle': 329, 'created_at': utc_now(),
    'authority': 'Existing active B authority permits bounded no-scoring maintenance; no new scientific authority.',
    'start_including_metadata_startup': '2026-10-06T02:53:30Z', 'deadline': '2026-10-06T03:13:30Z',
    'auxiliary_seconds_cap': 1200, 'fit_seconds_cap': 0, 'registrations_cap': 0, 'EXP_cap': 0,
    'scope': 'Three fixed primary abstract/bibliographic pages; evidence-based review, source records, real cadence pointer, one independent clone maintenance check sequence.',
    'fixed_primary_urls': ['https://arxiv.org/abs/2010.04592', 'https://arxiv.org/abs/1705.08500', 'https://aclanthology.org/P18-2124/'],
    'checked_scope': 'Abstract and bibliographic page only, no full-PDF review claimed.',
    'review_sections': ['OBSERVATION', 'INTERPRETATION', 'CONFIDENCE', 'ALTERNATIVE EXPLANATIONS', 'DECISION', 'NEXT DISCRIMINATING EXPERIMENT'],
    'counter_gate': 'Advance 117 to actual completed_experiments=123 only after all three primary pages and schema-valid source records and review exist.',
    'clone': 'C:/Users/NATAN/Documents/ChatGPT/NEXTAI-VALIDATION-20261002',
    'checks_once_in_order': ['parent scientific hashes and real review evidence', 'checked-in lifecycle pytest', 'CLI doctor', 'CLI lab status'],
    'check_validity': 'All executed checks must pass; scoring remains false. Not evidence of learning, transfer or goal completion.',
    'stop_rule': 'First required page, recording, fixture or check failure stops unstarted scope; no retry/replacement/filtering. Deadline or cap stops all unfinished work and preserves artifacts.',
    'unchanged': ['all models, scientific source, geometry, metrics, thresholds and grids', 'all previous outcomes, failures, costs and stage authorities', 'B protected 7 tickets / 47000 seconds', 'review cadence', 'config and eval manifest', 'AGENTS.md and program/LAB history'],
    'forbidden': ['research fit', 'new scoring seeds or arrays', 'native ASM/HAR bytes or future writers', 'WT8-9', 'new architectures', 'external model/API', 'schedule changes', 'MUC scientific or postrun retry'],
    'startup_observations': ['Read-only rg Windows wildcard/path errors and missing literature/test paths; no intake, fixture or scientific execution. All startup time charged.'],
    'parent_bindings_sha256': sha256_file(archive / 'parent-bindings.json'),
}
atomic_write_json(plan_path, plan)
append_jsonl(root / 'research/events.jsonl', {'event': 'literature_maintenance_preregistered', 'created_at': utc_now(), 'cycle': 329, 'plan_path': str(plan_path.relative_to(root)).replace('\\', '/'), 'plan_sha256': sha256_file(plan_path), 'new_research_fit_or_scoring': False})
auxiliary_reserve(root, identity, 1200)
print(json.dumps({'plan': str(plan_path), 'sha256': sha256_file(plan_path), 'reservation': 1200}))
