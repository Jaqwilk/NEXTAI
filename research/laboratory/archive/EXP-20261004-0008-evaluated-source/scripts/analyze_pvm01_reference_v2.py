"""Stored-result-only JSON repair; frozen v1 computations remain unchanged."""
import json
from pathlib import Path
import sys

from analyze_pvm01_reference import analyze as legacy_analyze
from nextai_autoresearch.utils import atomic_write_json


def analyze(base, experiment_id):
    # Dictionary unit indices become text keys at the JSON boundary.
    return json.loads(json.dumps(legacy_analyze(base, experiment_id), allow_nan=False))


def persist(base, experiment_id):
    result = analyze(base, experiment_id)
    destination = base / "research/reviews" / f"{experiment_id}-PVM01-reference-analysis.json"
    if destination.exists():
        if json.loads(destination.read_text(encoding="utf-8")) != result:
            raise ValueError("Existing stored analysis differs; preserve it without overwrite")
    else:
        atomic_write_json(destination, result)
    return result


if __name__ == "__main__":
    result = persist(Path(__file__).resolve().parents[1], sys.argv[1])
    print(json.dumps({key: result[key] for key in
                     ("experiment_id", "failures", "learning_gate", "competence_gates", "decision")}, indent=2))
