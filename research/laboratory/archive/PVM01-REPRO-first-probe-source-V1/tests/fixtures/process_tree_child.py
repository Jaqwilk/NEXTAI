"""Public auxiliary process fixture: inherited descendants and file heartbeat."""
import os
from pathlib import Path
import subprocess
import sys
import time

directory, role, early_exit = Path(sys.argv[1]), sys.argv[2], sys.argv[3] == "yes"
(directory / f"{role}.pid").write_text(str(os.getpid()))
if role in {"parent", "child"}:
    next_role = "child" if role == "parent" else "grandchild"
    subprocess.Popen([sys.executable, __file__, str(directory), next_role, sys.argv[3]])
deadline = time.monotonic() + 20.
while time.monotonic() < deadline:
    (directory / f"{role}.heartbeat").write_text(str(time.monotonic()))
    if role == "parent" and early_exit and (directory / "grandchild.heartbeat").exists():
        break
    time.sleep(.03)
