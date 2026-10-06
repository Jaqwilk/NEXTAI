from pathlib import Path
import hashlib
from nextai_autoresearch.research_program import status, auxiliary_reserve
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now
root=Path.cwd(); identity='ASM01-SYNTHETIC-COST-PREPARATION-V1'
path=root/f'research/plans/{identity}.json'
assert not path.exists()
assert not (root/'research/reviews/ASM01-COST-PREP-probe-V1.py').exists()
wallet=status(root)
assert wallet['stage_b_registration_attempts_used']==1 and wallet['pending_fit_reservation_seconds']==0
assert wallet['fit_seconds_remaining']-47000>=600 and not wallet['scoring_authorized']
names=['AGENTS.md','config/research.toml','research/state.json','research/eval_manifest.json','research/laboratory/preflight_certificate.json','src/nextai_autoresearch/asm01_task.py','src/nextai_autoresearch/candidates/asm01_core.py','src/nextai_autoresearch/benchmarks/asm01_native_memory_v2.py','research/plans/ASM01-POINT-SERIAL-PREPARATION-V1.json','research/laboratory/ASM01-POINT-SERIAL-PREP-COMPLETION-V1.receipt.json']
prefixes={}
for name in ('events.jsonl','sources.jsonl','experiments.tsv'):
 data=(root/'research'/name).read_bytes();prefixes[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
plan={'id':identity,'cycle':331,'created_at':utc_now(),'study_kind':'preparation_only','execution_authority':True,'native_execution_authority':False,'clock_start':'2026-10-06T03:27:00Z','deadline':'2026-10-06T03:37:00Z','auxiliary_seconds_cap':600,'fit_seconds_cap':0,'EXP_cap':0,'registration_cap':0,
 'question':'Measure unchanged DTW and geometry-transform service cost on synthetic data; assess only a conservative engineering forecast, never native/scientific feasibility.',
 'recipe':{'seed':424331,'DTW_K':[16,32,64],'DTW_calls_each_K':16,'include_first_call':True,'keys_and_queries':'independent seeded Gaussian float32 64-vectors normalized to unit L2; no native data','transform_lengths':[39,213,691],'transform_views':['write','nominal','adverse'],'transform_calls_each_cell':16,'synthetic_path':'float32 x=linspace(0,3900,n),y=1500+700*sin(linspace(0,6,n))+linspace(0,500,n)','threads':1,'single_clone_process_tree_timeout_seconds':90,'one_attempt':True},
 'frozen_counts':{'DTW_calls_each_K_all5roles':10680,'DTW_calls_total':32040,'transform_calls_all45roles':1007380,'prior_HAR_worker_seconds':180.55024020007113},
 'metrics':['all48 DTW calls finite shape K; no score emission','all144 transform calls finite float32 shape64','all latency samples including first','max latency each K and overall transform maximum','protected source hashes and old ledger prefixes unchanged','clone package provenance and drained process tree'],
 'forecast_formula':'2*10680*sum(max_DTW_seconds_each_K)+2*1007380*max_transform_seconds+2*180.55024020007113',
 'thresholds':{'all192_calls_pass':True,'engineering_worker_proxy_seconds_max':1000,'prospective_total_cap_seconds':2200,'prospective_auxiliary_cap_seconds':1200},
 'decision_rule':'If complete exact probe and worker proxy<=1000, KEEP runtime evidence only: a NEW separately frozen <=2200s whole-cost attempt is financially possible after full600s gate charge, with native validity/completion unknown. Otherwise INCONCLUSIVE/NOT COST JUSTIFIED. Neither outcome authorizes native, fit, scientific registration or retry. Proxy is not a statistical upper bound; HAR residual is cross-family and may underestimate ASM overhead.',
 'administration':'All startup since03:27, delegated metadata reads, code, failures, clone, report, Git included; the initially contemplated300s cap was not frozen/executed.600s is frozen before code/test; prior600s plus2200s fits2867.4497598 unprotected. No new clock reset.',
 'limitations':['No native geometry/old74/full1830 conformance','No guarantee for other40workers, calibration grids, model startup, intake/checks/admin','Independent replications, fresh finals and prototype remain active','Earlier Lab timeout preserved; no Doctor/Lab retry'],
 'forbidden':['native bytes/names/coordinates','new download/extraction/NPZ','fit/EXP/registration','source/model/geometry/grid/gate modification','WT8-9','futurewriters6-15/21-30','external models/API','schedule changes','retry','protected7tickets/47000s spending'],
 'parent_file_bindings':{n:sha256_file(root/n) for n in names},'ledger_prefixes':prefixes,'B_wallet_at_freeze':wallet}
atomic_write_json(path,plan)
append_jsonl(root/'research/events.jsonl',{'event':'maintenance_preparation_preregistered','created_at':utc_now(),'cycle':331,'plan_id':identity,'plan_sha256':sha256_file(path),'before_implementation_and_execution':True})
auxiliary_reserve(root,identity,600)
print({'plan_sha256':sha256_file(path),'reserved':600,'native':0,'fit':0})
