from __future__ import annotations

import json
import shutil
from pathlib import Path

from jsonschema import Draft202012Validator

from nextai_autoresearch.audit import audit_benchmark_boundary, audit_candidate
from nextai_autoresearch.config import load_config
from nextai_autoresearch.integrity import PROTECTED_FILES, freeze_manifest, verify_manifest
from nextai_autoresearch.ledger import latest_hypotheses, read_jsonl
from nextai_autoresearch.schemas import check_all_schemas, validate_document
from nextai_autoresearch.utils import load_json, project_root


def test_repository_documents_validate() -> None:
    root = project_root()
    assert check_all_schemas(root) == []
    validate_document("research_state", load_json(root / "research" / "state.json"), root)
    for hypothesis in latest_hypotheses(root).values():
        validate_document("hypothesis", hypothesis, root)
    for source in read_jsonl(root / "research" / "sources.jsonl"):
        validate_document("source", source, root)


def test_result_integrity_contract_accepts_verifier_payload() -> None:
    root = project_root()
    schema = load_json(root / "schemas" / "experiment_result.schema.json")
    integrity = verify_manifest(root)
    Draft202012Validator(schema["$defs"]["integrity"]).validate(integrity)
    result = load_json(root / "research" / "results" / "EXP-20260830-0038.json")
    result["integrity_before"] = integrity
    result["integrity_after"] = integrity
    validate_document("experiment_result", result, root)


def test_all_shipped_candidates_pass_source_audit() -> None:
    root = project_root()
    config = load_config(root)
    candidate_dir = root / "src" / "nextai_autoresearch" / "candidates"
    names = [path.stem for path in candidate_dir.glob("*.py")]
    names = [name for name in names if name not in {"__init__", "base"}]
    results = [audit_candidate(name, config, root) for name in names]
    assert results
    assert {problem for result in results for problem in result.problems} == set()
    assert any(len(result.dependencies) > 1 for result in results)


def test_retired_active_benchmark_uses_contract_not_candidate_core() -> None:
    root = project_root()
    config = load_config(root)
    assert audit_benchmark_boundary(config.benchmark_version, root) == ()


def _copy_integrity_fixture(destination: Path) -> None:
    source = project_root()
    for relative in PROTECTED_FILES:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)


def test_eval_manifest_detects_tampering(tmp_path: Path) -> None:
    _copy_integrity_fixture(tmp_path)
    manifest = freeze_manifest(tmp_path)
    assert len(manifest["files"]) == len(PROTECTED_FILES)
    assert verify_manifest(tmp_path)["ok"] is True

    protected = tmp_path / "src" / "nextai_autoresearch" / "metrics.py"
    protected.write_text(protected.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
    verification = verify_manifest(tmp_path)
    assert verification["ok"] is False
    assert "changed protected file: src/nextai_autoresearch/metrics.py" in verification["problems"]


def test_candidate_bundle_can_change_after_plan_without_changing_evaluator_digest(
    tmp_path: Path,
) -> None:
    _copy_integrity_fixture(tmp_path)
    first = freeze_manifest(tmp_path)
    candidate_relative = next(
        relative
        for relative in PROTECTED_FILES
        if relative.startswith("src/nextai_autoresearch/candidates/")
        and not relative.endswith(("/__init__.py", "/base.py"))
    )
    candidate = tmp_path / candidate_relative
    candidate.write_text(
        candidate.read_text(encoding="utf-8") + "\n# candidate-only revision\n",
        encoding="utf-8",
    )
    second = freeze_manifest(tmp_path, overwrite=True)
    assert second["evaluator_sha256"] == first["evaluator_sha256"]
    assert second["candidate_bundle_sha256"] != first["candidate_bundle_sha256"]
    assert verify_manifest(tmp_path)["ok"] is True


def test_original_manifest_is_preserved_verbatim_after_heading() -> None:
    root = project_root()
    preserved = (root / "docs" / "ORIGINAL_MANIFEST.md").read_text(encoding="utf-8")
    assert preserved.startswith("# AUTORESEARCH: SEARCHING FOR A SUCCESSOR TO LARGE LANGUAGE MODELS")
    assert "# 35. Final Research Doctrine" in preserved
    assert "Your job is to determine whether nature allows them." in preserved
