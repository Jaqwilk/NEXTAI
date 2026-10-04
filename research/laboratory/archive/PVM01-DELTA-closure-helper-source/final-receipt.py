from pathlib import Path
import json,time,subprocess,hashlib,math
from datetime import datetime, timezone
from nextai_autoresearch.research_program import auxiliary_reserve,auxiliary_charge,status
from nextai_autoresearch.utils import atomic_write_json,utc_now,sha256_file
from nextai_autoresearch.report import write_report
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.ledger import read_jsonl,append_jsonl

b=Path.cwd();cid='PVM01-DELTA-final-accounting-wrapper-allowance-V1'
auxiliary_reserve(b,cid,120)
auxiliary_charge(b,cid,120)
start=time.perf_counter()
identity='EXP-20261004-0006'
original=json.loads((b/'research/reviews/PVM01-DELTA-original-fastforward-doctor-V1.json').read_text(encoding='utf8'))
assert original['error'] is None and all(x.get('returncode',0)==0 for x in original['checks'])
plan=json.loads((b/f'research/plans/{identity}.json').read_text(encoding='utf8'))
costs={}
runtime=b/f'research/laboratory/archive/{identity}-runtime/research/tmp/{identity}'
for name,role in plan['research_program_protocol']['roles'].items():
    p=runtime/(name+'.device.json');value=json.loads(p.read_text(encoding='utf8'))
    assert value['reserved']>=value['allocated']>=0
    costs.setdefault(role['arm'],{})[str(role['seed_index'])]={**value,'artifact':p.relative_to(b).as_posix(),'raw_sha256':sha256_file(p)}
rows=['| Metoda | Średni peak allocated MiB | Średni peak reserved MiB | Zakres reserved MiB |','|---|---:|---:|---:|']
for arm,units in sorted(costs.items()):
    allocated=[v['allocated']/1024**2 for v in units.values()];reserved=[v['reserved']/1024**2 for v in units.values()]
    rows.append(f'| {arm} | {sum(allocated)/5:.3f} | {sum(reserved)/5:.3f} | {min(reserved):.3f}–{max(reserved):.3f} |')
note=b/f'research/analyses/{identity}-CUDA-COST-ADDENDUM-V1.md'
assert not note.exists()
note.write_text('# '+identity+' — uzupełnienie kosztu pamięci CUDA\n\nTabela głównej analizy zawiera logiczny stan i peak RSS procesu. Poniżej dodano odczyty szczytu alokatora CUDA z wszystkich75 zachowanych dzienników device. Są to maksima z całego workera, obejmujące fit i ewaluację. Nie izolowano bieżącej rezerwacji CUDA podczas samej inferencji CPU i nie twierdzimy, że proces wcześniej trenujący na GPU ma wtedy zerową zajętość GPU. Odczyty PyTorch nie obejmują całej pamięci sterownika/kontekstu ani innych procesów. Energia nie była mierzona. Żadne wyniki, źródła naukowe lub bramki nie zmieniły się.\n\n'+'\n'.join(rows)+'\n\nPełne wartości pięciu jednostek, ścieżki i hashe: research/reviews/EXP-20261004-0006-CUDA-COST-DIAGNOSTICS-V1.json.\n',encoding='utf8',newline='\n')
atomic_write_json(b/f'research/reviews/{identity}-CUDA-COST-DIAGNOSTICS-V1.json',{'id':identity+'-CUDA-COST-DIAGNOSTICS-V1','created_at':utc_now(),'arms':costs,'model_executed':False,'basis':'torch.cuda max_memory_allocated/max_memory_reserved whole worker, includes fit/eval; not isolated CPU inference VRAM or full driver memory'})
atomic_write_json(b/'research/reviews/PVM01-DELTA-final-accounting-wrapper-allowance-V1.json',{'id':cid,'created_at':utc_now(),'seconds_cap':120,'charged_seconds':120,'charge_basis':'Entire allowance retired conservatively for final ledger/report/hash checks plus outer wrapper initialization and bookkeeping beyond timed child-test spans. It may overcount; not presented as measured research fit. No past charge reduced.','research_fit_or_new_scoring':False})
program=status(b);events=read_jsonl(b/'research/events.jsonl')
charges=[e for e in events if e.get('event')=='research_program_aux_fit_charged' and e.get('charge_id','').startswith('PVM01-DELTA-')]
reserves=[e for e in events if e.get('event')=='research_program_aux_fit_reserved' and e.get('charge_id','').startswith('PVM01-DELTA-')]
assert {e['charge_id'] for e in charges}=={e['charge_id'] for e in reserves}
stage_aux=sum(e['seconds'] for e in charges);assert stage_aux<=1800
assert program['fit_seconds_charged']<=program['fit_seconds_cap'] and not program['paid_run_pending'] and not program['program_closed']
assert program['registration_attempts_used']==6 and program['continuation_registration_attempts_used']==3
assert program['scoring_authorized'] is False and verify_manifest(b)['ok']
write_report(b)
receipt_path=b/'research/laboratory/PVM01-CYCLE-308-COMPLETION-V1.receipt.json';assert not receipt_path.exists()
now=datetime.now(timezone.utc);started=datetime.fromisoformat('2026-10-04T18:02:25+00:00');deadline=datetime.fromisoformat('2026-10-04T22:02:25+00:00');assert now<deadline
receipt={'id':'PVM01-CYCLE-308-COMPLETION-V1','created_at':utc_now(),'cycle':308,'experiment_id':identity,'plan_path':f'research/plans/{identity}.json','result_sha256':sha256_file(b/f'research/results/{identity}.json'),'analysis_path':f'research/analyses/{identity}.md','analysis_sha256':sha256_file(b/f'research/analyses/{identity}.md'),'decision':'KEEP narrow delta mechanism for further validation','whole_program_complete':False,'checks':{'preregistration_before_implementation_commit':'6555a6ac87e74a9ab34ebce00d3af416e9a35fd8','evaluated_source_commit':'399d7eceaa4e56f7ba96072107625f7700f27289','validated_maintenance_source_commit':'489498bd66015247da7b415980b2f48a8f52ba03','preseed_tests':1096,'postrun_tests':1096,'errors_failures_skips_final':0,'workers_complete':75,'trials_complete':675,'fresh_paired_units':5,'data_pairs_source_identity_valid':True,'integrity_before_after_files':1111,'archived_raw_source_runtime_files':1728,'archive_and_native_diagnostics_indexed_raw_sha_files':1732,'doctor_and_lab_status_pass_in_clone_and_original':True,'original_old_scientific_bytes_and_prefixes_preserved':True,'BELIEFS_original_raw_unchanged':True,'original_completed_counter':113,'current_integrity':verify_manifest(b),'failed_checks_preserved':True,'no_paid_or_model_retry':True,'WT8_9_access':False,'external_model_api':False,'schedule_changed':False},'budget':{'original_started_at':'2026-10-04T18:02:25Z','original_deadline_at':'2026-10-04T22:02:25Z','elapsed_seconds_at_closure':(now-started).total_seconds(),'closed_before_deadline':True,'research_supervised_fit_phase_seconds':223.5436152999755,'internal_algorithm_fit_seconds':160.0469089999824,'charged_full_worker_seconds':449.76211150000745,'worker_compute_cap_seconds':11100,'stage_auxiliary_seconds_charged':stage_aux,'stage_auxiliary_seconds_cap':1800,'all_auxiliary_reservations_closed':True,'stage_total_compute_seconds':stage_aux+449.76211150000745,'auxiliary_charges':charges,'budget_or_deadline_reset':False,'program':program},'unexecuted_scope':['learned compact feature/controller alternative','adversarial task variant','independent mechanism replication','frozen fresh final and strong classical non-domination'],'next_discriminating_question':'Preregister learned compact feature memory vs source-identical frozen and shuffled controls at fixed smaller capacity, strong classical/retrieval and optimized dense, fresh5 paired units. If not justified, bounded alternatives review; no implementation/data before freeze. No second EXP in this cycle.'}
atomic_write_json(receipt_path,receipt)
append_jsonl(b/'research/events.jsonl',{'event':'bounded_research_cycle_completed','created_at':utc_now(),'program_id':program['id'],'cycle':308,'experiment_id':identity,'completion_receipt_path':receipt_path.relative_to(b).as_posix(),'completion_receipt_sha256':sha256_file(receipt_path),'whole_program_complete':False,'next_scoring_requires_new_study_freeze':True})
write_report(b)
paths=['research/events.jsonl','research/REPORT.md','research/REPORT.provenance.json','research/reviews/PVM01-DELTA-original-fastforward-doctor-V1.json','research/reviews/PVM01-DELTA-final-accounting-wrapper-allowance-V1.json',f'research/reviews/{identity}-CUDA-COST-DIAGNOSTICS-V1.json',f'research/analyses/{identity}-CUDA-COST-ADDENDUM-V1.md',receipt_path.relative_to(b).as_posix()]
subprocess.run(['git','add','--',*paths],check=True)
for path in paths:
    blob=subprocess.check_output(['git','cat-file','blob',':'+path])
    assert hashlib.sha256(blob).hexdigest()==sha256_file(b/path),path
subprocess.run(['git','diff','--cached','--check'],check=True)
p=subprocess.run(['git','commit','-m','Record completed cycle308 exact budgets CUDA peaks and original validation'],capture_output=True,text=True,encoding='utf8',check=True)
assert not subprocess.check_output(['git','status','--porcelain']).strip()
print(p.stdout.splitlines()[0],flush=True)
print(json.dumps({'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'stage_auxiliary_seconds':stage_aux,'stage_total_compute_seconds':stage_aux+449.76211150000745,'fit_seconds_remaining':program['fit_seconds_remaining'],'continuation_tickets_remaining':17-program['continuation_registration_attempts_used'],'receipt_sha256':sha256_file(receipt_path),'closure_bookkeeping_elapsed_seconds':time.perf_counter()-start}),flush=True)

