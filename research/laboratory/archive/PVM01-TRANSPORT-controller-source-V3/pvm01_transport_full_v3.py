from pathlib import Path
import subprocess
from nextai_autoresearch.report import write_report
b=Path.cwd();write_report(b)
completed=subprocess.run(['uv','run','--no-sync','pytest','-q','--junitxml=research/checks/PVM01-TRANSPORT-full-V3.xml'],cwd=b)
raise SystemExit(completed.returncode)
