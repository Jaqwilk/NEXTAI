"""Record the actual completed three-page review before advancing cadence."""
from pathlib import Path
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now
root = Path.cwd()
plan_path = root / 'research/plans/NEXTAI-LITERATURE-CYCLE329-V4.json'
plan = load_json(plan_path)
assert sha256_file(plan_path) == 'bb49ad3dc82569073742f935d57e3c8460ff3b7b267c045cd932d205391fb709'
review = root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-V1.md'
entries = [
 {'title': 'Contrastive Learning with Hard Negative Samples', 'authors': ['Joshua Robinson', 'Ching-Yao Chuang', 'Suvrit Sra', 'Stefanie Jegelka'], 'year': 2020, 'url': plan['fixed_primary_urls'][0], 'claims_supported': ['The abstract describes an unsupervised hard-negative sampling family with controllable hardness and reports representation improvements.'], 'relevance': 'MUC inference: hard negatives have prior art; representation improvements do not establish UNKNOWN, full costs or supervised sampler efficacy.'},
 {'title': 'Selective Classification for Deep Neural Networks', 'authors': ['Yonatan Geifman', 'Ran El-Yaniv'], 'year': 2017, 'url': plan['fixed_primary_urls'][1], 'claims_supported': ['The abstract describes constructing a selective classifier that trades prediction coverage for a user-specified risk level.'], 'relevance': 'NEXTAI inference: report false abstention and coverage separately; paper guarantees do not transfer to our procedure or distributions.'},
 {'title': "Know What You Don't Know: Unanswerable Questions for SQuAD", 'authors': ['Pranav Rajpurkar', 'Robin Jia', 'Percy Liang'], 'year': 2018, 'url': plan['fixed_primary_urls'][2], 'claims_supported': ['The abstract introduces adversarially authored unanswerable questions resembling answerable ones and a task requiring abstention when context lacks support.'], 'relevance': 'NEXTAI inference: ranking and unsupported-answer rejection require separate endpoints; no SQuAD dataset evaluation was performed.'},
]
now = utc_now()
last = max(int(s['source_id'].split('-')[1]) for s in read_jsonl(root / 'research/sources.jsonl'))
for i, entry in enumerate(entries, 1):
    entry.update(source_id=f'SRC-{last+i:04d}', checked_at=now, source_type='paper', primary_source=True, checked_scope='Primary abstract and bibliographic page read after fe49209; full PDF and experimental reproduction not reviewed.')
    validate_document('source', entry, root)
assert all(section in review.read_text(encoding='utf-8') for section in plan['review_sections'])
state_path = root / 'research/state.json'
state = load_json(state_path)
assert state['completed_experiments'] == 123 and state['last_literature_review_completed_experiments'] == 117
for entry in entries:
    append_jsonl(root / 'research/sources.jsonl', entry)
atomic_write_json(root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-EVIDENCE-V1.json', {'created_at': now, 'preregistration_commit': 'fe49209', 'plan_sha256': sha256_file(plan_path), 'review_path': str(review.relative_to(root)).replace('\\', '/'), 'review_sha256': sha256_file(review), 'source_ids': [e['source_id'] for e in entries], 'fixed_pages_read': [e['url'] for e in entries], 'checked_scope': plan['checked_scope'], 'new_fit': 0, 'new_EXP': 0})
state['last_literature_review_completed_experiments'] = 123
state['updated_at'] = now
atomic_write_json(state_path, state)
append_jsonl(root / 'research/events.jsonl', {'event': 'literature_review_completed', 'created_at': now, 'cycle': 329, 'completed_experiments': 123, 'review_path': str(review.relative_to(root)).replace('\\', '/'), 'review_sha256': sha256_file(review), 'source_ids': [e['source_id'] for e in entries], 'new_research_fit_or_scoring': False, 'hypothesis_confidence_unchanged': True, 'cadence_unchanged': True, 'auxiliary_charge_id': plan['id'], 'auxiliary_seconds_cap': 1200})
append_jsonl(root / 'research/events.jsonl', {'event': 'authorized_maintenance_completed', 'created_at': now, 'cycle': 329, 'scope': 'Actual three-primary-page literature review only; clone checks remain unstarted', 'scoring': False})
print({'source_ids': [e['source_id'] for e in entries], 'cadence_pointer': 123})
