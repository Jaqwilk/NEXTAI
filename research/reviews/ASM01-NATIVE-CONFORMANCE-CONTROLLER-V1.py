from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict
import os
import sys
from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.utils import atomic_write_json,utc_now,load_json
root=Path.cwd();clone=root.parent/'NEXTAI-VALIDATION-20261002';kind=sys.argv[1];assert kind in {'fixtures','intake'}
prefix=root/f'research/reviews/ASM01-NATIVE-CONFORMANCE-CONTROLLER-{kind}-V1';assert not prefix.with_suffix('.started.json').exists()
assert not any((p/gate).exists() for p in (root,clone) for gate in ('STOP','PAUSE','research/run.lock'))
if kind=='intake':assert load_json(root/'research/reviews/ASM01-NATIVE-CONFORMANCE-CONTROLLER-fixtures-V1.json')['complete']
remaining=(datetime.fromisoformat('2026-10-06T03:54:20+00:00')-datetime.now(timezone.utc)).total_seconds()-160;assert remaining>0
env=os.environ.copy();env.update(PYTHONPATH=str(clone/'src'),NEXTAI_PROJECT_ROOT=str(clone),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
command=[str(clone/'.venv/Scripts/python.exe'),str(clone/'research/reviews/ASM01-NATIVE-CONFORMANCE-CLONE-RUNNER-V1.py'),kind]
atomic_write_json(prefix.with_suffix('.started.json'),{'created_at':utc_now(),'attempt':1,'kind':kind,'timeout_seconds':min(120,remaining),'command':command})
result=run_bounded(command,cwd=clone,env=env,stdout_path=prefix.with_name(prefix.name+'.stdout.txt'),stderr_path=prefix.with_name(prefix.name+'.stderr.txt'),timeout_seconds=min(120,remaining))
atomic_write_json(prefix.with_suffix('.json'),{'created_at':utc_now(),'complete':result.returncode==0,'kind':kind,'result':asdict(result)})
print(asdict(result),flush=True)
