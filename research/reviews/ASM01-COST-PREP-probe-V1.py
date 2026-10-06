from pathlib import Path
from time import perf_counter
import hashlib
import numpy as np
import torch
import nextai_autoresearch
from nextai_autoresearch.asm01_task import transform
from nextai_autoresearch.candidates.asm01_core import banded_dtw_scores
from nextai_autoresearch.utils import load_json, sha256_file, atomic_write_json, utc_now
root=Path.cwd(); assert root.name=='NEXTAI-VALIDATION-20261002'
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to((root/'src').resolve())
plan_path=root/'research/plans/ASM01-SYNTHETIC-COST-PREPARATION-V1.json'
assert sha256_file(plan_path)=='2661ba173ac15add040ea7d40966a2335c4609fda45ddd56158d1510966ccb75'
plan=load_json(plan_path)
for name,digest in plan['parent_file_bindings'].items(): assert sha256_file(root/name)==digest,name
for name,binding in plan['ledger_prefixes'].items(): assert hashlib.sha256((root/'research'/name).read_bytes()[:binding['bytes']]).hexdigest()==binding['sha256'],name
binding=load_json(root/'research/reviews/ASM01-COST-PREP-source-binding-V1.json')
assert sha256_file(Path(__file__))==binding['probe_sha256']
out=root/'research/reviews/ASM01-COST-PREP-CLONE-V1.json';assert not out.exists()
torch.set_num_threads(1);rng=np.random.default_rng(424331);dtw={};geometries={}
for k in (16,32,64):
 keys=rng.normal(size=(k,64)).astype(np.float32); keys/=np.linalg.norm(keys,axis=1,keepdims=True)
 queries=rng.normal(size=(16,64)).astype(np.float32);queries/=np.linalg.norm(queries,axis=1,keepdims=True)
 times=[]
 for query in queries:
  start=perf_counter();value=banded_dtw_scores(keys,query);times.append(perf_counter()-start)
  assert value.shape==(k,) and np.isfinite(value).all()
 dtw[str(k)]={'seconds':times,'maximum_seconds':max(times),'calls':16}
for n in (39,213,691):
 path=np.column_stack((np.linspace(0,3900,n),1500+700*np.sin(np.linspace(0,6,n))+np.linspace(0,500,n))).astype(np.float32)
 for view in ('write','nominal','adverse'):
  times=[]
  for _ in range(16):
   start=perf_counter();value=transform(path,view);times.append(perf_counter()-start)
   assert value.shape==(64,) and value.dtype==np.float32 and np.isfinite(value).all()
  geometries[f'{n}:{view}']={'seconds':times,'maximum_seconds':max(times),'calls':16}
dtw_proxy=2*10680*sum(cell['maximum_seconds'] for cell in dtw.values())
transform_proxy=2*1007380*max(cell['maximum_seconds'] for cell in geometries.values())
residual=2*180.55024020007113;forecast=dtw_proxy+transform_proxy+residual
atomic_write_json(out,{'created_at':utc_now(),'complete':True,'clone_package_path':str(Path(nextai_autoresearch.__file__).resolve()),'plan_sha256':sha256_file(plan_path),'probe_sha256':sha256_file(Path(__file__)),'DTW':dtw,'transform':geometries,'calls':{'DTW':48,'transform':144,'total':192},'forecast_seconds':{'DTW':dtw_proxy,'transform':transform_proxy,'cross_family_HAR_residual':residual,'total_worker_proxy':forecast},'engineering_proxy_pass':forecast<=1000,'native_bytes':0,'fit_seconds':0,'EXP':0,'registration':0,'scoring':False,'statistical_upper_bound':False})
print({'complete':True,'calls':192,'forecast_seconds':forecast,'engineering_proxy_pass':forecast<=1000},flush=True)
