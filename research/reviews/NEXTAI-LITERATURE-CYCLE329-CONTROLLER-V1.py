"""Bound the entire new clone verification process tree to the frozen clock."""
from pathlib import Path
from dataclasses import asdict
from datetime import datetime, timezone
import os
import traceback
from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.utils import atomic_write_json, utc_now
root = Path.cwd()
clone = root.parent / 'NEXTAI-VALIDATION-20261002'
prefix = root / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-CONTROLLER-V1'
assert not prefix.with_suffix('.started.json').exists()
assert not any((p / gate).exists() for p in (root, clone) for gate in ('STOP', 'PAUSE', 'research/run.lock'))
env = os.environ.copy()
env.update(PYTHONPATH=str(clone / 'src'), NEXTAI_PROJECT_ROOT=str(clone), PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', PYTHONIOENCODING='utf-8', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
command = [str(clone / '.venv/Scripts/python.exe'), str(clone / 'research/reviews/NEXTAI-LITERATURE-CYCLE329-CLONE-VERIFIER-V1.py')]
seconds = (datetime.fromisoformat('2026-10-06T03:13:30+00:00') - datetime.now(timezone.utc)).total_seconds() - 90
assert seconds > 0
atomic_write_json(prefix.with_suffix('.started.json'), {'created_at': utc_now(), 'command': command, 'timeout_seconds': seconds, 'attempt': 1, 'new_fit': 0, 'new_EXP': 0})
try:
    result = run_bounded(command, cwd=clone, env=env, stdout_path=prefix.with_name(prefix.name + '.stdout.txt'), stderr_path=prefix.with_name(prefix.name + '.stderr.txt'), timeout_seconds=seconds)
except Exception:
    atomic_write_json(prefix.with_suffix('.json'), {'created_at': utc_now(), 'error': traceback.format_exc(), 'complete': False})
    raise
atomic_write_json(prefix.with_suffix('.json'), {'created_at': utc_now(), 'supervision': asdict(result), 'complete': result.returncode == 0})
print(asdict(result), flush=True)
raise SystemExit(result.returncode)
