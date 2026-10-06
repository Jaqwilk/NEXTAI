"""Preserve the finite maintenance sequence and charge all elapsed administration."""
from pathlib import Path
from datetime import datetime, timezone
import json
import math
import shutil
import zipfile
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import auxiliary_charge, status
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now
root = Path.cwd()
clone = root.parent / 'NEXTAI-VALIDATION-20261002'
identity = 'NEXTAI-LITERATURE-CYCLE329-V4'
receipt_path = root / 'research/laboratory/NEXTAI-LITERATURE-CYCLE329-COMPLETION-V1.receipt.json'
assert not receipt_path.exists()
controller = load_json(root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-CONTROLLER-V1.json')
native_paths = sorted((clone / 'research/reviews').glob('NEXTAI-LITERATURE-CYCLE329-CLONE-V1.*'))
for path in native_paths:
    target = root / 'research/reviews' / path.name
    assert not target.exists()
    shutil.copyfile(path, target)
check_path = root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-CLONE-V1.json'
checks = load_json(check_path) if check_path.exists() else {'complete': False, 'checks': [], 'failure': 'Verifier stopped before first completed check; see controller raw outputs.'}
raw = list(native_paths)
raw += sorted((root / 'research/reviews').glob('NEXTAI-LITERATURE-CYCLE329-CONTROLLER-V1.*'))
archive_path = root / 'research/laboratory/archive/NEXTAI-LITERATURE-CYCLE329-NATIVE-EVIDENCE-V1.zip'
bindings = {}
with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
    for path in raw:
        relative = 'research/reviews/' + path.name
        archive.write(path, relative)
        bindings[relative] = sha256_file(path)
now = datetime.now(timezone.utc)
start = datetime.fromisoformat('2026-10-06T02:53:30+00:00')
elapsed = (now - start).total_seconds()
charged = min(1200, math.ceil(elapsed) + 150)
auxiliary_charge(root, identity, charged)
wallet = status(root)
assert wallet['protected_future_compute_seconds'] == 47000 and wallet['protected_future_registration_attempts'] == 7
assert wallet['stage_b_registration_attempts_used'] == 1 and not wallet['scoring_authorized']
complete = controller.get('complete', False) and checks.get('complete', False) and elapsed <= 1200
receipt = {'created_at': utc_now(), 'id': identity, 'status': 'completed' if complete else 'incomplete_after_first_failure_or_limit',
 'plan_path': f'research/plans/{identity}.json', 'plan_sha256': sha256_file(root / f'research/plans/{identity}.json'),
 'review_path': 'research/reviews/NEXTAI-LITERATURE-CYCLE329-V1.md', 'review_sha256': sha256_file(root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-V1.md'),
 'source_ids': ['SRC-0463', 'SRC-0464', 'SRC-0465'], 'actual_cadence_pointer': 123, 'completed_experiments': 123,
 'checks': checks, 'controller': controller, 'native_archive_path': str(archive_path.relative_to(root)).replace('\\', '/'), 'native_archive_sha256': sha256_file(archive_path), 'native_file_bindings': bindings,
 'clock_start': '2026-10-06T02:53:30Z', 'accounting_cutoff': now.isoformat(), 'elapsed_seconds_at_cutoff': elapsed,
 'closing_administration_reserve_seconds': max(0, charged - elapsed), 'auxiliary_seconds_charged': charged, 'auxiliary_seconds_cap': 1200,
 'actual_overrun_seconds': max(0, elapsed - 1200),
 'fit_seconds': 0, 'new_EXP': 0, 'scoring': False, 'experiment_retry': False, 'old_MUC_failed_postrun_preserved': True,
 'preprereg_authoring_failures': ['research/program.md missing', 'LABORATORY.md missing', 'research/experiments.jsonl missing'],
 'all_failures_startup_read_errors_web_review_tests_Git_admin_in_full_clock': True,
 'B_wallet_after': {k: wallet[k] for k in ('stage_b_compute_seconds_charged', 'stage_b_registration_attempts_used', 'protected_future_compute_seconds', 'protected_future_registration_attempts')},
 'unprotected_B_seconds_remaining': wallet['fit_seconds_remaining'] - 47000,
 'MUC_decision_unchanged': 'discard_proposed_recipe', 'full_transfer_prototype_goal': 'active_incomplete',
 'limitations': ['Abstract-level review only; no transfer or learning evidence from maintenance', 'Current ASM scope remains maintenance/scoring=false; new exact prospective preparation required'],
 'unfinished_scope': [] if complete else [name for name in ('lifecycle', 'doctor', 'lab') if not any(c['name'] == name and c['returncode'] == 0 for c in checks.get('checks', []))]}
atomic_write_json(receipt_path, receipt)
append_jsonl(root / 'research/events.jsonl', {'event': 'literature_maintenance_closed', 'created_at': utc_now(), 'cycle': 329, 'receipt_path': str(receipt_path.relative_to(root)).replace('\\', '/'), 'receipt_sha256': sha256_file(receipt_path), 'status': receipt['status'], 'fit': 0, 'EXP': 0})
text = f'''# MUC0001 — osobne domknięcie utrzymania w cyklu329

Wynik naukowy i decyzja **discard_proposed_recipe** pozostają niezmienione.
Historyczny postrun MUC pozostał przerwany po należnym przeglądzie; nie powtórzono
go ani eksperymentu. Nowy, osobno prerejestrowany zakres {identity} wykonał
rzeczywisty przegląd trzech pierwotnych abstraktów, zapisał źródła0463–0465
i dopiero wtedy przesunął wskaźnik przeglądu117→123, bez zmiany kadencji6.

Status nowego zakresu: **{receipt['status']}**. W niezależnym klonie wykonano:
{json.dumps(checks.get('checks', []), ensure_ascii=False, indent=2)}

Zero fitu, nowego EXP i scoringu. Pełny koszt od02:53:30Z, wraz z trzema zachowanymi
błędami ścieżek przygotowania, przeglądem, testami i administracją: konserwatywnie
**{charged}/1200s**; pomiar do rozliczenia{elapsed:.3f}s. Pozostały bufor zamknięcia
jest częścią opłaconego zegara. To odrębny koszt B, nie reset lub kredyt dawnego MUC.
Natywne bajty diagnostyczne są zachowane losslessly w archiwumZIP z hashami.

Portfel B: {wallet['stage_b_compute_seconds_charged']:.6f}/72000s,1/12rejestracji;
chronione7/47000 pozostają, niechroniony margines{receipt['unprotected_B_seconds_remaining']:.6f}s.
Pełny cel transferu, replikacji, świeżych finałów i prototypu pozostaje aktywny.
Nie otwierano native/future writerów lub WT8–9, nie zmieniano modeli, progów,
geometrii, harmonogramu lub zamrożonych wyników. ASM nadal scoring=false.

Dowód: research/laboratory/NEXTAI-LITERATURE-CYCLE329-COMPLETION-V1.receipt.json.
Niedokończony zakres tej konserwacji: {receipt['unfinished_scope']}.
'''
(root / 'research/analyses/EXP-20261006-0001-maintenance-addendum-V1.md').write_text(text, encoding='utf-8', newline='\n')
print(json.dumps({'status': receipt['status'], 'charged': charged, 'remaining_unprotected': receipt['unprotected_B_seconds_remaining'], 'native_archive_sha256': receipt['native_archive_sha256']}))
