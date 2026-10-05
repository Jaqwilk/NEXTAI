from __future__ import annotations

import json
import shutil
from pathlib import Path

from nextai_autoresearch.integrity import freeze_manifest, protected_files, verify_manifest
from nextai_autoresearch.metrics import aggregate_trials
from nextai_autoresearch.utils import load_json, project_root


def _copy_integrity_fixture(destination: Path) -> None:
    source = project_root()
    for relative in protected_files(source):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)


def test_every_aggregated_summary_field_is_serializable() -> None:
    root = project_root()
    result = load_json(root / "research" / "results" / "EXP-20260830-0053.json")
    summary = aggregate_trials(result["candidates"][0]["trials"])
    schema = load_json(root / "schemas" / "experiment_result.schema.json")
    allowed = set(schema["$defs"]["summary"]["properties"])
    assert set(summary) <= allowed


def test_semantic_registry_and_conformance_tests_are_candidate_bundle(
    tmp_path: Path,
) -> None:
    _copy_integrity_fixture(tmp_path)
    first = freeze_manifest(tmp_path)
    registry_path = tmp_path / "config" / "baseline_semantics.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    record = registry["baselines"]["unigram_recombination"]
    record["version"] = int(record["version"]) + 1
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    test_path = tmp_path / record["conformance_tests"][0]["path"]
    test_path.write_text(
        test_path.read_text(encoding="utf-8") + "\n# candidate semantic revision\n",
        encoding="utf-8",
    )
    second = freeze_manifest(tmp_path, overwrite=True)
    assert second["evaluator_sha256"] == first["evaluator_sha256"]
    assert second["candidate_bundle_sha256"] != first["candidate_bundle_sha256"]
    assert verify_manifest(tmp_path)["ok"] is True
