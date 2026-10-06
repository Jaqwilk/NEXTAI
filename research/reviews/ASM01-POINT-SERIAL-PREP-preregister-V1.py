"""Freeze the exact opaque-coordinate preparation before implementation or data."""
from pathlib import Path
import hashlib
import shutil
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import auxiliary_reserve, status
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now
root = Path.cwd()
identity = 'ASM01-POINT-SERIAL-PREPARATION-V1'
path = root / f'research/plans/{identity}.json'
assert not path.exists()
implementation = 'research/preparations/ASM01-POINT-SERIAL-PREPARATION-V1/normalizer.py'
fixtures = 'research/preparations/ASM01-POINT-SERIAL-PREPARATION-V1/test_normalizer.py'
assert not (root / implementation).exists() and not (root / fixtures).exists()
assert not any((root / p).exists() for p in ('STOP', 'PAUSE', 'research/run.lock'))
wallet = status(root)
assert wallet['stage_b_registration_attempts_used'] == 1 and wallet['pending_fit_reservation_seconds'] == 0
assert wallet['protected_future_compute_seconds'] == 47000 and wallet['protected_future_registration_attempts'] == 7
assert wallet['fit_seconds_remaining'] - 47000 >= 1200 and not wallet['scoring_authorized']
archive = root / 'research/laboratory/archive/ASM01-point-serial-cycle330-parent-V1'
archive.mkdir()
metadata = ['research/eval_manifest.json', 'research/state.json', 'config/research.toml', 'research/laboratory/preflight_certificate.json']
for name in metadata:
    target = archive / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / name, target)
references = metadata + ['AGENTS.md', 'program.md', 'research/LAB_PLAN.md',
 'src/nextai_autoresearch/asm01_task.py', 'src/nextai_autoresearch/asm01_task_v3.py', 'src/nextai_autoresearch/asm01_task_v4.py',
 'research/plans/ASM01-POINT-SERIAL-METADATA-PROSPECTIVE-V1.json',
 'research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V3.receipt.json',
 'research/laboratory/NEXTAI-LITERATURE-CYCLE329-COMPLETION-V1.receipt.json',
 'research/results/EXP-20261006-0001.json']
prefixes = {}
for name in ('events.jsonl', 'sources.jsonl', 'experiments.tsv'):
    data = (root / 'research' / name).read_bytes()
    prefixes[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
atomic_write_json(archive / 'parent-bindings.json', {'files': {p: sha256_file(root / p) for p in references}, 'ledger_prefixes': prefixes, 'B_wallet': wallet})
accept = ['canonical-single', 'canonical-multi-whitespace-leading-zero-metadata', 'misplaced-release', 'missing-markers', 'repeated-down', 'leading-middle-trailing-empty-ids', 'literal-zero-alias', 'duplicates-within-and-across-strokes']
reject = ['missing-header', 'misplaced-header', 'duplicate-header', 'malformed-header', 'stroke-count-zero', 'stroke-count-negative', 'serial-zero', 'serial-out-of-range', 'serial-decrease', 'state-zero', 'negative-x', 'negative-y', 'plus-x', 'negative-double-zero', 'decimal-y', 'unknown-row', 'point-arity', 'down-extra-operand', 'up-wrong-release', 'too-few-point-rows']
caps = ['wrong-type', 'oversize-input', 'non-ascii', 'oversize-normalized']
invariants = ['coordinate-conversion-trap', 'old-accepted-arrays-and-all-three-views', 'all-parent-protected-files-unchanged', 'pure-imports-and-no-file-model-access', 'no-native-authority-or-scoring', 'exact-plan-source-fixture-bindings']
plan = {
 'schema_version': 1, 'id': identity, 'cycle': 330, 'created_at': utc_now(), 'study_kind': 'preparation_only',
 'authority': 'Active B permits bounded no-scoring preparation. This is a new exact synthetic contract, not reactivation or retry of any failed scientific intake.',
 'execution_authority': True, 'native_execution_authority': False, 'implementation_path': implementation, 'fixture_path': fixtures,
 'clock_start_including_all_metadata_startup': '2026-10-06T03:12:30Z', 'deadline': '2026-10-06T03:32:30Z',
 'auxiliary_seconds_cap': 1200, 'fit_seconds_cap': 0, 'EXP_cap': 0, 'registration_cap': 0,
 'question': 'Can a pure release-format normalizer make explicit point serial metadata authoritative, preserve every opaque point token/order and declared empty ID, and retain exact synthetic old-accepted arrays/three descriptors?',
 'recipe': {
  'API': 'normalize_release_bytes(payload: bytes) -> bytes; versioned preparatory module only, no active loader/parser integration.',
  'input_gate': 'bytes only, <=262144 before ASCII decode; strip nonempty lines; first starts CHARACTER_NAME:, second matches STROKE_COUNT:\\s*[1-9][0-9]*, last starts END_CHARACTER:. Exact X Y STYLUS_STATE STROKE occurs once at nonempty index2. Reject all nonqualified forms; active old V4 and legacy handling remain untouched.',
  'body_grammar': 'ONLY exact tokens [PEN_DOWN], [PEN_UP,0] or four point tokens. These two marker forms are annotations only, ignored regardless of missing/repeated/misplaced positions. All other marker operands and unknown rows reject; no arbitrary-row suppression.',
  'point_rule': 'X/Y each match [0-9]+ or exact literal -0; ONLY -0 aliases0. No int/float/Decimal conversion of X/Y, bounds checks, sorting, deduplication or geometry here. State and serial match [0-9]+; categorical int(state)==1; 1<=int(serial)<=declared count; serials monotonically nondecreasing. Preserve all four point token strings/order apart from literal coordinate alias.',
  'size_and_count': 'Require >=4 raw point rows (necessary only, not geometric feasibility). Derive count feasibility16*N<=262144 before allocating; compute exact ASCII normalized length from stripped header/count/column/end lines+all point token lines+16*N and reject >262144 BEFORE output materialization.',
  'emission': 'Preserve stripped first/count/column/end strings. For EVERY declared id1..N in order emit bare PEN_DOWN, its original point rows in original order joined by one space, bare PEN_UP; include leading/internal/trailing empty IDs. ASCII LF lines with final LF. Ignore only declared annotation marker rows; no point filtering or replacement.',
  'delegation': 'Synthetic tests may pass normalized bytes to exact unchanged V4/V3/V1 parser and transform for independent geometry comparison. No new active parser/loader/model/fit. Future integration must separately freeze legacy gate and old-accepted compatibility before native bytes.',
 },
 'frozen_cases': {'accept': accept, 'reject': reject, 'caps': caps, 'invariants': invariants, 'total': 38, 'short_ids_only': True},
 'metrics': ['exact point-row token/order conservation apart from literal-0', 'exact old-accepted synthetic float32 arrays and write/nominal/adverse descriptors', 'all38 declared cases PASS', 'all historical protected-file hashes and ledger prefixes preserved', 'pure-module AST and coordinate conversion trap', 'independent clone package/source/fixture binding'],
 'thresholds': 'Exact equality for every applicable assertion; all38 PASS, no missing/filtered cases; zero native bytes/fit/EXP/registration/scoring.',
 'decision_rule': 'KEEP technical normalizer only if single complete38-case clone run and independent source review pass. Any fixture/binding failure stops unstarted scope with immutable source/output; no repair/retry/sample filtering. Otherwise DISCARD/INCOMPLETE exact version. Never infer learning, transfer or scientific readiness.',
 'validation': 'One source-hash-bound38-case pytest run in independent clone, process tree bounded<=200s and total frozen deadline. Preserve XML/raw output in lossless archive. No repeat Doctor/Lab or MUC postrun; earlier Lab timeout remains.',
 'budget_at_freeze': wallet, 'parent_bindings_sha256': sha256_file(archive / 'parent-bindings.json'),
 'known_exposures': {'raw_native_attempts_before_inventory': 75, 'completed_native_conversions': 74, 'lexically_inventoried_screen_texts': 1830, 'new_native_bytes_this_scope': 0, 'old74_array_hashes_persisted': False},
 'limitations': ['Histogram does not prove native monotonicity or literal signed-zero values', 'Synthetic equality does not verify the74 old-native arrays or1830 feasibility', 'Later SHA-bound old74 comparison requires exact oldV4 reparse, not invented stored array hashes', 'Current10800-second scientific screen reservation is unaffordable:3756.44976 unprotected seconds before prep. No promise or authority for cheaper full screen without separately justified scope.'],
 'future_required': ['New fully costed exact intake/cohort binding before native; all1830 mandatory without filtering', 'Exact74 old-accepted arrays and all3 descriptor equality', 'Complete unchanged geometry/bounds/dedup/pointcap/view feasibility', 'New science freeze/preflight/readiness before one audited EXP', 'Second-family transfer, independent replications, fresh finals and local fact/source/update/UNKNOWN prototype remain unfinished'],
 'forbidden': ['native payload/coordinate/name emission', 'new sample/download/extraction/NPZ', 'future ASM6-15/21-30 or HAR future subjects or Data_Table', 'WT8-9', 'model/geometry/grid/metric/threshold changes', 'fit/EXP/retry', 'external models/API', 'schedule change', 'protected7tickets/47000s spending', 'use of unused A or separate MUC budget'],
}
atomic_write_json(path, plan)
append_jsonl(root / 'research/events.jsonl', {'event': 'maintenance_preparation_preregistered', 'created_at': utc_now(), 'cycle': 330, 'program_id': wallet['id'], 'plan_path': path.relative_to(root).as_posix(), 'plan_sha256': sha256_file(path), 'before_implementation_and_new_native_bytes': True})
auxiliary_reserve(root, identity, 1200)
print({'plan_sha256': sha256_file(path), 'cases': 38, 'native': 0, 'fit': 0, 'reserved': 1200})
