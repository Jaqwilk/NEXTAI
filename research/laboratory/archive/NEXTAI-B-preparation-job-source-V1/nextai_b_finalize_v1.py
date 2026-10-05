from pathlib import Path
import hashlib,json,subprocess,xml.etree.ElementTree as ET
from nextai_autoresearch.utils import atomic_write_json,load_json,sha256_file,utc_now
from nextai_autoresearch.ledger import append_jsonl,read_jsonl
from nextai_autoresearch.research_program import status
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
root=Path(__file__).resolve().parents[2]
original=root.parent/'NEXTAI'
passed=['NEXTAI-B-targeted-V1','NEXTAI-B-preclosure-conformance-V2','NEXTAI-B-clone-gates-V2','NEXTAI-B-queue-conformance-V3','NEXTAI-B-original-gates-V1']
for check in passed:
 d=load_json(root/f'research/reviews/{check}.json');assert d['result']['returncode']==0 and not d['error'],check
 assert not d['result']['exit_job_active_process_count'] and not d['result']['exit_live_descendant_pids'],check
counts={}
for check in ['NEXTAI-B-full-V1','NEXTAI-B-full-V2','NEXTAI-B-queue-conformance-V3','NEXTAI-B-original-gates-V1']:
 xml=ET.parse(root/f'research/reviews/{check}.xml').getroot();suites=[xml] if xml.tag=='testsuite' else list(xml)
 counts[check]={key:sum(int(s.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']}
assert counts['NEXTAI-B-full-V1']==dict(tests=1337,failures=2,errors=0,skipped=0)
assert counts['NEXTAI-B-full-V2']==dict(tests=1343,failures=1,errors=0,skipped=0)
for check in ['NEXTAI-B-queue-conformance-V3','NEXTAI-B-original-gates-V1']:assert counts[check]==dict(tests=59,failures=0,errors=0,skipped=0)
source=load_json(root/'research/reviews/NEXTAI-B-tested-source-V3.json')
for relative,digest in source['files'].items():assert sha256_file(root/relative)==digest and sha256_file(original/relative)==digest,relative
before=load_json(root/'research/reviews/NEXTAI-B-tested-source-V2.json')
for relative,digest in before['files'].items():
 if relative!='scripts/check_transfer_preparation.py':assert sha256_file(root/relative)==digest,relative
for project in [root,original]:assert verify_manifest(project)['ok'];verify_preflight_certificate(project)
value=status(root);assert value['stage_b_registration_attempts_used']==0 and not value['scoring_authorized']
assert value['protected_future_compute_seconds']==47000 and value['stage_a_accounting']['fit_seconds_charged']==35649.98936010008
events=read_jsonl(root/'research/events.jsonl')
reserved={e['charge_id'] for e in events if e.get('event')=='research_program_aux_fit_reserved' and e.get('program_id')==value['id']}
charged={e['charge_id'] for e in events if e.get('event')=='research_program_aux_fit_charged' and e.get('program_id')==value['id']};assert reserved==charged
cycle_charges={e['charge_id']:e['seconds'] for e in events if e.get('event')=='research_program_aux_fit_charged' and str(e.get('charge_id','')).startswith('NEXTAI-B-')};cycle_total=sum(cycle_charges.values());assert cycle_total<=4800
state=load_json(root/'research/state.json');assert state['cycle_number']==318 and state['completed_experiments']==121 and state['last_experiment_id']=='EXP-20261005-0006' and state['active_experiment_id'] is None
state['updated_at']=utc_now();atomic_write_json(root/'research/state.json',state)
receipt_path='research/laboratory/NEXTAI-B-CYCLE-318-COMPLETION-V1.receipt.json';assert not (root/receipt_path).exists()
references=['research/plans/NEXTAI-A-CLOSURE-B-PREPARATION-V1.json','research/plans/NEXTAI-TRANSFER-PREPARATION-V1.json','research/plans/NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-V1.json','research/plans/NEXTAI-B-CURRENT-QUEUE-CONFORMANCE-ADDENDUM-V1.json','research/analyses/NEXTAI-A-RESOLUTION-GATE-CLARIFICATION-V1.md','research/reviews/NEXTAI-B-protected-Git-checkout-conformance-V1.json','research/reviews/NEXTAI-B-history-clone-queue-repair-V3.json','research/reviews/NEXTAI-B-history-original-V1.json','research/reviews/NEXTAI-B-tested-source-V3.json','research/reviews/NEXTAI-B-final-administration-prepaid-V1.json']
receipt={'id':'NEXTAI-B-CYCLE-318-COMPLETION-V1','created_at':utc_now(),'cycle':318,'study_path':'research/plans/NEXTAI-TRANSFER-PREPARATION-V1.json','study_sha256':sha256_file(root/'research/plans/NEXTAI-TRANSFER-PREPARATION-V1.json'),'status':'complete_no_scoring','decision':'KEEP technical B preparation;whole scientific transfer/prototype goal remains ACTIVE','latest_scientific_experiment_id':'EXP-20261005-0006','new_experiment_id':None,'new_registrations':0,'new_research_fit_seconds':0,'new_target_data_or_download':False,'source_fit_replayed':False,'regression_evidence':counts,'single_all_green_full_V2_invocation':False,'coverage_rule':'1342 unchanged full-suite cases passed;the sole obsolete20-ticket queue assertion was prospectively corrected to exact B26=14+12 and the entire affected module plus authority/schema/lifecycle tests59/59 passed in clone and original.Production research code remains exactly the full-V2 tested code.','passed_checks':passed,'failed_checks_preserved':['NEXTAI-B-full-V1','NEXTAI-B-full-V2','NEXTAI-B-clone-gates-V1'],'stage_a_registration_attempts':11,'stage_a_compute_seconds_charged':35649.98936010008,'prior_MUC03_registration_attempts':3,'prior_MUC03_compute_seconds_charged':2655.336484700005,'program_budget_before_preparation_completion_event':value,'cycle_auxiliary_charges':cycle_charges,'cycle_auxiliary_seconds_charged':cycle_total,'cycle_auxiliary_cap':4800,'all_auxiliary_reservations_resolved':True,'protected_future_registration_attempts':7,'protected_future_compute_seconds':47000,'both_roots_old_nonmutable_files_verified':61099,'all112_scientific_source_bytes_preserved':True,'actual25_fitted_states_and50_files_verified':True,'reference_sha256':{p:sha256_file(root/p) for p in references},'finalizer_sha256':sha256_file(Path(__file__)),'extended_goal_completed':False,'exact_next_discriminating_experiment':'Separate prospective native-task intake/recipe/metrics/threshold/cost/decision contract before data or implementation,five paired source/target units,three justified scales,actual trained/untrained/shuffled source-state controls with identical permitted adaptation,competent target Transformer,strong native classical controls,adverse variants and one audited EXP;reserve independent replication and fresh finals;then second independent family and evidence-selected local fact/source/update/UNKNOWN prototype.'}
atomic_write_json(root/receipt_path,receipt)
append_jsonl(root/'research/events.jsonl',{'event':'research_program_preparation_completed','created_at':utc_now(),'program_id':value['id'],'study_path':receipt['study_path'],'study_sha256':receipt['study_sha256'],'receipt_path':receipt_path,'receipt_sha256':sha256_file(root/receipt_path),'cycle':318,'no_scoring':True,'extended_goal_completed':False})
after=status(root);assert after['study_terminal'] and not after['program_closed'] and not after['scoring_authorized']
report='research/analyses/NEXTAI-B-CYCLE-318-V1.md';assert not (root/report).exists()
(root/report).write_text(f"""# Cykl318: rozliczenie A i zweryfikowane przygotowanie B

## OBSERVATION

Bez nowego EXP,rejestracji,fitu badawczego,nowych danych lub odtwarzania source fit. Prerejestracja: research/plans/NEXTAI-A-CLOSURE-B-PREPARATION-V1.json;kontynuacja: research/plans/NEXTAI-TRANSFER-PREPARATION-V1.json. Ostatni eksperyment: EXP-20261005-0006,niezmienny plan research/plans/EXP-20261005-0006.json.

A zamknięto po zweryfikowanym świeżym finale:11/17 prób i35649.98936010008/69344s. Zachowano wcześniejsze MUC03:3 próby/2655.336484700005s. Nie przeniesiono niewykorzystanych6 prób/33694.01063989992s do B. B ma osobne12 prób/72000s;dotychczas0 prób i{after['stage_b_compute_seconds_charged']:.0f}s rozliczonych kontroli,pozostało{after['fit_seconds_remaining']:.0f}s,z czego47000s/7 prób chroni replikacje,finały i ocenę prototypu.

Pełna regresja V1:1335/1337 i dwie niezgodności schematu metadanych oraz aktualności raportu. V2:1342/1343;jedyną niezgodnością był stary test oczekujący20 zamiast zatwierdzonych26 prób. Poprawiono tylko jawną kontrolę nowego i historycznego budżetu,zachowując stary test w archiwum. Cały dotknięty moduł i kontrole autoryzacji/schematu/lifecycle:59/59 w klonie i59/59 w oryginale. Nie deklarujemy pojedynczego pełnego przebiegu bez błędów:pełna regresja niezmienionego kodu i osobne poprawione kontrole tworzą łączne świadectwo. Wszystkie wyniki,błędy i koszty zachowano.

Doctor/lab passed w obu checkoutach;maintenance/scoring=false. Zweryfikowano61099 wcześniejszych niezmienianych plików w każdym checkoutcie,prefiksy ksiąg,112 naukowych źródeł oraz25 faktycznych stanów/50 plików i ich ZIP. Jedyny zmieniony dawny test jest jawnie archiwizowany.1303 chronione pliki odtwarzają zgodne bajty;trzy historyczne deklaracje eol=crlf zachowują swoje dawne Git blobs i checkout bytes. Bez WT8-9,zewnętrznych modeli/API,zmiany harmonogramu lub retry płatnego planu.

Łączny koszt kontroli cyklu:{cycle_total:.0f}/4800s,wliczając błędy i450s konserwatywnej administracji końcowej. Dokładne rozliczenie: {receipt_path}. Limit pracy4h/deadline2026-10-05T14:52:01Z pozostaje niezmieniony.

## INTERPRETATION AND CONFIDENCE

To walidacja techniczna i rozliczenie,bez nowych wyników naukowych. W niezmienionym0006 uczony transport/PCA i ridge/PCA spełniły18/18 indywidualnych bramek ekonomicznych. Uczona droga nie przechodzi łącznej kwalifikacji wobec ridge/PCA-scan w osobnych mocnych porównaniach klasycznych. Korekta nieprecyzyjnego zdania starego podsumowania jest append-only:research/analyses/NEXTAI-A-RESOLUTION-GATE-CLARIFICATION-V1.md. Decyzje i progi nie zmieniają się. Uczenie lokalnej mapy KEEP;neuralna kwalifikacja ekonomiczna DISCARD;klasyczna droga lokalnego finału KEEP. Nie jest to dowód transferu,nowej architektury,LLM,naturalnego języka lub ogólnej inteligencji. Niepewność naukowa pozostaje pięcioparową niepewnością0006 i nie zostaje obniżona przez testy techniczne.

## DECISION AND NEXT DISCRIMINATING EXPERIMENT

KEEP przygotowanie B;cały cel pozostaje ACTIVE. Metadane dwóch rodzin z UCI są opisane w research/analyses/NEXTAI-B-TASK-FEASIBILITY-V1.md;nie pobrano ani nie widziano przykładów. Niepewność niezależnych autorów/podmiotów,liczebności i konkretnych widoków wymaga prospektywnego intake.

Następny oddzielny cykl zamraża rodzimą rodzinę,kontrakt intake,recepturę,metryki,progi,budżet i decyzję przed implementacją/danymi:pięć nowych sparowanych jednostek,trzy uzasadnione skale,rzeczywiste source-trained/untrained/shuffled stany z identyczną dozwoloną adaptacją,kompetentny target Transformer,mocne stałe kontrole klasyczne,trudny wariant,rozdzielone ranking/źródło/retencja/aktualizacje/UNKNOWN i pełne koszty. Preferencja warunkowa:rodzina fizyczna z podmiotami,jeśli zamrożony intake jest wykonalny. Jeden audytowany EXP;bez poprawiania receptury po wynikach. Replikacje,świeże finały,druga niezależna rodzina i minimalny lokalny prototyp fact/source/update/UNKNOWN pozostają niewykonanym zakresem B;samą aktywację programu nie uznajemy za ukończenie celu.
""",encoding='utf-8',newline='\n')
print(json.dumps({'cycle':318,'decision':'KEEP technical preparation','cycle_auxiliary_charged':cycle_total,'B_charged':after['stage_b_compute_seconds_charged'],'B_remaining':after['fit_seconds_remaining'],'whole_goal_completed':False}),flush=True)
