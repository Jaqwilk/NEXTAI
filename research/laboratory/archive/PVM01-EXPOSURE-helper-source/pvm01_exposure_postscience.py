"""Preserve and analyze one paid result; never execute a candidate or generator."""
from pathlib import Path
import subprocess

b = Path.cwd()
commands = [
    ["uv","run","--no-sync","python","scripts/analyze_pvm01_capacity_exposure.py","EXP-20261004-0008"],
    ["uv","run","--no-sync","python","research/tmp/pvm01_exposure_archive.py"],
    ["uv","run","--no-sync","python","research/tmp/pvm01_exposure_diagnostics.py"],
    ["uv","run","--no-sync","python","research/tmp/pvm01_exposure_write_analysis.py"],
]
for command in commands:
    subprocess.run(command,cwd=b,check=True)
print("One result analyzed, raw source/runtime archived, complete immutable report written before lifecycle checks.")
