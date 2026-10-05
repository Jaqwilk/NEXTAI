"""Restore only an exact hash-bound published native outcome; no experiment execution."""
from pathlib import Path
import re
import sys

import restore_pvm01_transport_result as frozen


if __name__ == "__main__":
    identity = sys.argv[1]
    if not re.fullmatch(r"EXP-\d{8}-\d{4}", identity):
        raise ValueError("Invalid immutable experiment identity")
    frozen.ID = identity
    frozen.RELATIVE = f"research/results/{identity}.json"
    frozen.main(Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[1])
