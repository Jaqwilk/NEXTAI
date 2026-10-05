"""Restore the exact independent-replication record with the frozen lossless restorer."""
from pathlib import Path
import sys
import restore_pvm01_transport_result as frozen

if __name__ == "__main__":
    frozen.ID = "EXP-20261005-0002"
    frozen.RELATIVE = f"research/results/{frozen.ID}.json"
    frozen.main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
