"""Preserve the single technical result, charge full wall, keep science closed."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import shutil
import zipfile
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import auxiliary_charge, status
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now
root = Path.cwd()
clone = root.parent / 'NEXTAI-VALIDATION-20261002'
identity = 'ASM01-POINT-SERIAL-PREPARATION-V1'
path = root / 'research/laboratory/ASM01-POINT-SERIAL-PREP-COMPLETION-V1.receipt.json'
assert not path.exists()
plan = load_json(root / f'research/plans/{identity}.json')
controller = load_json(root / 'research/reviews/ASM01-POINT-SERIAL-PREP-CONTROLLER-V1.json')
native_paths = sorted((clone / 'research/reviews').glob('ASM01-POINT-SERIAL-PREP-CLONE-V1.*'))
for old in native_paths:
    new = root / 'research/reviews' / old.name
    assert not new.exists()
    shutil.copyfile(old, new)
proof_path = root / 'research/reviews/ASM01-POINT-SERIAL-PREP-CLONE-V1.json'
proof = load_json(proof_path) if proof_path.exists() else {'complete': False, 'counts': {'tests': 0}, 'failure': 'See raw controller outputs'}
parent = load_json(root / 'research/laboratory/archive/ASM01-point-serial-cycle330-parent-V1/parent-bindings.json')
for name, digest in parent['files'].items():
    assert sha256_file(root / name) == digest, name
for name, binding in parent['ledger_prefixes'].items():
    assert hashlib.sha256((root / 'research' / name).read_bytes()[:binding['bytes']]).hexdigest() == binding['sha256'], name
archive = root / 'research/laboratory/archive/ASM01-POINT-SERIAL-PREP-EVIDENCE-V1.zip'
paths = [root / plan['implementation_path'], root / plan['fixture_path'], root / f'research/plans/{identity}.json',
 root / 'research/reviews/ASM01-POINT-SERIAL-PREP-SOURCE-BINDINGS-V1.json', root / 'research/reviews/ASM01-POINT-SERIAL-PREP-SOURCE-BINDINGS-V2.json',
 root / 'research/reviews/ASM01-POINT-SERIAL-PREP-INDEPENDENT-REVIEW-V1.json']
paths += [root / 'research/reviews' / p.name for p in native_paths]
paths += list((root / 'research/reviews').glob('ASM01-POINT-SERIAL-PREP-CONTROLLER-V1.*'))
bindings = {}
with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
    for item in paths:
        relative = item.relative_to(root).as_posix()
        z.write(item, relative)
        bindings[relative] = sha256_file(item)
cutoff = datetime.now(timezone.utc)
elapsed = (cutoff - datetime.fromisoformat('2026-10-06T03:12:30+00:00')).total_seconds()
charged = min(1200, math.ceil(elapsed) + 150)
auxiliary_charge(root, identity, charged)
wallet = status(root)
assert wallet['stage_b_registration_attempts_used'] == 1 and not wallet['scoring_authorized']
assert wallet['protected_future_compute_seconds'] == 47000 and wallet['protected_future_registration_attempts'] == 7
review = load_json(root / 'research/reviews/ASM01-POINT-SERIAL-PREP-INDEPENDENT-REVIEW-V1.json')
complete = proof.get('complete', False) and controller.get('complete', False) and review['status'] == 'PASS' and elapsed <= 1200
receipt = {'created_at': utc_now(), 'id': identity, 'cycle': 330, 'status': 'completed_technical_preparation' if complete else 'incomplete_or_failed_exact_version',
 'decision': 'KEEP technical normalizer only' if complete else 'DISCARD/INCOMPLETE exact normalizer', 'scientific_comparison': 'INCONCLUSIVE; no scientific execution',
 'plan_sha256': sha256_file(root / f'research/plans/{identity}.json'), 'preregistration_commit': 'cf7faa8', 'source_freeze_commit': '3a86e52',
 'source_path': plan['implementation_path'], 'source_sha256': sha256_file(root / plan['implementation_path']),
 'fixture_path': plan['fixture_path'], 'fixture_sha256': sha256_file(root / plan['fixture_path']),
 'clone_proof': proof, 'controller': controller, 'independent_static_review': review,
 'lossless_archive_path': archive.relative_to(root).as_posix(), 'lossless_archive_sha256': sha256_file(archive), 'native_file_bindings': bindings,
 'all_parent_scientific_metadata_sources_and_ledger_prefixes_preserved': True,
 'new_native_bytes': 0, 'native_coordinate_conversions': 0, 'native_names_or_coordinates_emitted': False, 'fit_seconds': 0, 'EXP': 0, 'registrations': 0,
 'active_integration': False, 'scoring': False, 'retry': False, 'WT8_9': False, 'future_writer_access': False, 'external_model_API': False, 'schedule_change': False,
 'clock_start': '2026-10-06T03:12:30Z', 'deadline': '2026-10-06T03:32:30Z', 'accounting_cutoff': cutoff.isoformat(),
 'elapsed_seconds_at_cutoff': elapsed, 'closing_administration_reserve_seconds': max(0, charged-elapsed), 'actual_overrun_seconds': max(0, elapsed-1200),
 'auxiliary_seconds_charged': charged, 'auxiliary_seconds_cap': 1200, 'all_metadata_delegated_review_code_tests_failures_admin_Git_in_full_clock': True,
 'B_wallet_after': {k: wallet[k] for k in ('stage_b_compute_seconds_charged', 'stage_b_registration_attempts_used', 'protected_future_compute_seconds', 'protected_future_registration_attempts')},
 'unprotected_B_seconds_remaining': wallet['fit_seconds_remaining']-47000,
 'old74_native_array_conformance': 'NOT VERIFIED; old74 arrays were not persisted; requires separately frozen SHA-bound oldV4 reparse',
 'complete1830_native_feasibility': 'NOT VERIFIED', 'future_scientific_screen_feasibility': 'Current10800-second reservation remains unaffordable; a lower whole-cost cap needs separate evidence and freeze, with all roles and gates preserved.',
 'prior_Lab_timeout_preserved_and_not_retried': True, 'full_goal_status': 'ACTIVE, INCOMPLETE',
 'remaining_full_goal': ['Second independent-family transfer comparison', 'Independent replications and fresh finals at5pairs/3scales', 'Evidence-selected local fact/source/update/UNKNOWN prototype and full-cost comparison']}
atomic_write_json(path, receipt)
append_jsonl(root / 'research/events.jsonl', {'event': 'maintenance_preparation_closed', 'created_at': utc_now(), 'cycle': 330, 'plan_id': identity, 'receipt_path': path.relative_to(root).as_posix(), 'receipt_sha256': sha256_file(path), 'decision': receipt['decision'], 'native': 0, 'fit': 0, 'EXP': 0})
report = f'''# ASM01 — cykl330: normalizer punktowych seriali

## OBSERVATION

Prerejestracja cf7faa8 przed implementacją i danymi; source freeze3a86e52 przed
jedyną walidacją niezależnego klonu. Dokładnie38przypadków:8accept,20reject,
4caps,6invariants. Wynik: {proof.get('counts')}. Decyzja **{receipt['decision']}**.
Kod nie jest zintegrowany z aktywnym loaderem/parserem; dotychczasowe źródła,
modele, geometria, metryki, progi, wyniki i błędy pozostają niezmienione.

Normalizer przyjmuje wyłącznie kwalifikowany format release. Jawne monotoniczne
seriale wyznaczają grupy; zachowuje każdy punkt i kolejność oraz wszystkie puste
stroke1..N. X/Y pozostają tokenami; jedyny alias to literalne-0→0. Znane bareDOWN
iUP0 traktuje jako adnotacje. Inne wiersze/markery odrzuca. Emisja bareDOWN/bareUP
jest formatem legacy dla dokładnie zachowanegoV4; nie deklarujemy idempotencji.
Pełny rozmiar jest sprawdzany przed materializacją. Bez nowych nativebytes,
konwersji native, NPZ, fitu, rejestracji lub EXP.

## INTERPRETATION

Testy wykazały zachowanie syntetycznych starych tablicfloat32 i wszystkich trzech
deskryptorów write/nominal/adverse, także przy duplikatach na granicy stroke
i pustych identyfikatorach. Pułapka konwersji X/Y i kontrola AST potwierdzają
oddzielenie metadanych od geometrii. Dokładne prefiksy3ledgerów i parenthashes
zachowane. Procesy nadzorowane zakończone bez żywych potomków.

## CONFIDENCE

Wysoka dla deklarowanego skończonego zakresu syntetycznego, bez wniosków o
uczeniu, transferze lub ekonomii. Zgodność74 dawnych nativearrays i pełna
wykonalność1830próbek pozostają **NIEZWERYFIKOWANE**. Histogram nie dowodzi
monotoniczności rzeczywistych seriali ani tego, że podpisaneY są literalnym-0.

## ALTERNATIVE EXPLANATIONS

Możliwy niezerowy signedY, nieporządek seriali, zmiana deduplikacji lub
degeneracja geometrii zamkną tę dokładną trasę w późniejszym intake. Nie wolno
stosowaćabs/clamp/offset, usuwać punktów, próbek lub niekorzystnych jednostek.
Niezależny przegląd przedrunem domknął dwie luki pokrycia w tych samych namedcases;
V1draftbytes i V1/V2bindings zachowano. Nie było nieudanej próby testowej ani retry.

## DECISION

KEEP wyłącznie techniczny artefakt. NaukowoINCONCLUSIVE, scoring=false.
Pełny koszt od03:12:30Z: konserwatywnie **{charged}/1200s**, pomiar do rozliczenia
{elapsed:.3f}s, z buforem końcowej administracji. Fit0/EXP0. Koszt joba jest
zagnieżdżony w pełnym zegarze; nie sumujemy go ponownie. B:
{wallet['stage_b_compute_seconds_charged']:.6f}/72000s,1/12rejestracji;
chronione7/47000, marginesniechroniony{receipt['unprotected_B_seconds_remaining']:.6f}s.
Zachowano wcześniejszy Labtimeout180s, bez jego powtórzenia.

## NEXT DISCRIMINATING EXPERIMENT

Przed dalszymi bytes potrzebny nowy dokładny, opłacony kontrakt: SHA-bound
stare74parsowanieV4 i porównanie tablic/all3views; wszystkie1830próbki bez
filtrowania oraz niezmienione bounds/dedup/pointcap/geometry/view gates.
Przyszły wrapper ma jawnie zachować legacyobsługę; nie może używać fallbacku
do ukrycia różnicy dawnej zaakceptowanej tablicy. Obecne10800s rezerwacji
pełnego screeningu nie mieści się w marginesie. Niższy kompletny cap wymaga
oddzielnego uzasadnienia kosztów, z wszystkimi45rolami/810trials i bramkami;
przekroczenie zatrzyma niedokończony zakres. Nie finansujemy go rezerwą47k.

Cel drugiej rodziny transferu, niezależnych replikacji, świeżych finałów i
minimalnego lokalnego prototypu fact/source/update/UNKNOWN pozostaje ACTIVE.
Dowody: research/laboratory/ASM01-POINT-SERIAL-PREP-COMPLETION-V1.receipt.json
oraz losslessarchive z bindingami źródeł i surowych wyników.
'''
(root / 'research/analyses/ASM01-CYCLE330-POINT-SERIAL-PREPARATION-V1.md').write_text(report, encoding='utf-8', newline='\n')
print(json.dumps({'status': receipt['status'], 'decision': receipt['decision'], 'charged': charged, 'unprotected_remaining': receipt['unprotected_B_seconds_remaining']}))
