"""Run the one frozen synthetic matrix with explicit independent-clone imports."""
from pathlib import Path
import subprocess
import sys

import nextai_autoresearch

root = Path(__file__).resolve().parents[1]
assert root.name == "NEXTAI-VALIDATION-20261002"
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / "src")
original = root.parent / "NEXTAI"
prefix = original / "research/reviews/NEXTAI-B-327-inventory-fixtures-V1"
temporary = root / "research/tmp/ASM01-INVENTORY-V3-fixture-V1"
assert not temporary.exists() and not prefix.with_suffix(".xml").exists()
print("independent_clone_package=" + str(Path(nextai_autoresearch.__file__).resolve()), flush=True)
command = [sys.executable, "-m", "pytest", str(root / "tests/test_asm01_grammar_inventory.py"),
    str(root / "tests/test_asm01_inventory_v3.py"), "-q", "--basetemp", str(temporary),
    "--junitxml", str(prefix.with_suffix(".xml"))]
raise SystemExit(subprocess.run(command, cwd=root, timeout=160).returncode)
