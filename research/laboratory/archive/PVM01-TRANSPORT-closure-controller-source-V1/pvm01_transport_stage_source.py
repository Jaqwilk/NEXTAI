from pathlib import Path
import subprocess
b=Path.cwd()
for args in [
 ['research/tmp/pvm01_transport_save_source_v4.py'],
 ['research/tmp/pvm01_transport_history.py','--label','validated'],
 ['research/tmp/pvm01_transport_commit.py']]:
 p=subprocess.run(['uv','run','--no-sync','python',*args],cwd=b)
 if p.returncode:raise SystemExit(p.returncode)
