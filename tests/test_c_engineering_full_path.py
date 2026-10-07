"""Synthetic engineering integration, never native data or canonical science.

The real shared builder, registration ledger, runner, subprocess worker, source
audit, baseline hashes and preflight execute against an isolated temporary lab.
The ZIP/maintenance helper below is a fixture pattern, not a claim that a future
native scientific closure driver has been tested.
"""
from __future__ import annotations

import copy
from datetime import timedelta
import hashlib
from pathlib import Path
import re
import shutil
import textwrap
import zipfile

import pytest

from nextai_autoresearch import baseline_semantics, gates, integrity
from nextai_autoresearch import research_program as program
from nextai_autoresearch import research_program_c as c
from nextai_autoresearch import runner
from nextai_autoresearch import ledger, schemas
from nextai_autoresearch.config import load_config
from nextai_autoresearch.ledger import ensure_layout, read_jsonl
from nextai_autoresearch.utils import (
    atomic_write_json, load_json, project_root, sha256_file,
)


COHORT = "c_engineering_fixture_v1"
COMPLETE = "c_fixture_complete"
PARTIAL = "c_fixture_partial"
_BASELINE_TEST = "tests/test_synthetic_baseline.py"
_CANONICAL_LEDGERS = (
    "research/events.jsonl", "research/plan_registry.jsonl",
    "research/plan_status_events.jsonl", "research/hypothesis_events.jsonl",
    "research/experiments.tsv",
)


_BENCHMARK_SOURCE = textwrap.dedent('''\
    """Public synthetic engineering rows; no model, optimizer or native input."""
    from importlib import import_module
    BENCHMARK_VERSION = "c_engineering_fixture_v1"

    def run_suite(candidate, plan, *, trial_sink=None, fit_sink=None,
                  data_sink=None, phase_sink=None):
        model = import_module("nextai_autoresearch.candidates." + candidate).Candidate()
        assert model.synthetic_value() == 7
        if data_sink:
            data_sink({"fixture_only": True, "native_rows": 0, "array_bytes": 0})
        if fit_sink:
            fit_sink({"fixture_only": True, "optimizer_steps": 0,
                      "scientific_fit_seconds": 0, "benchmark_origin": __file__})
        if phase_sink:
            phase_sink("evaluation")
        trials = []
        for index in range(2):
            trial = {
                "status": "complete", "seed": plan["matrix"]["seeds"][0],
                "knowledge_size": 8, "reasoning_depth": 1, "query_count": 1,
                "accuracy": 1.0, "warm_accuracy": 1.0,
                "continual_retention": 1.0, "mean_query_ops": 1.0,
                "mean_warm_query_ops": 1.0, "p50_latency_us": 1.0,
                "p95_latency_us": 1.0, "fit_seconds": 0.0,
                "state_bytes": 8, "fact_top1_accuracy": 1.0,
                "dense_unknown_rejection": 1.0, "fit_ops": 0,
                "preprocessing_ops": 0, "fixture_index": index,
            }
            trials.append(trial)
            if trial_sink:
                trial_sink(trial)
            if candidate == "c_fixture_partial":
                raise RuntimeError("synthetic failure after the durable first trial")
        if phase_sink:
            phase_sink("complete")
        return trials
''')


def _tree_hashes(root: Path) -> dict[str, str]:
    """Compare names and bytes, including side effects outside known ledgers."""
    values = {}
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        values[relative + "/" if path.is_dir() else relative] = (
            "<directory>" if path.is_dir() else sha256_file(path)
        )
    return values


def _canonical_ledger_hashes(root: Path) -> dict[str, str | None]:
    return {
        relative: sha256_file(root / relative) if (root / relative).is_file() else None
        for relative in _CANONICAL_LEDGERS
    }


def _write_synthetic_package(base: Path) -> None:
    """Copy Python source only; no research corpus, model states or history."""
    shutil.copytree(
        project_root() / "src/nextai_autoresearch", base / "src/nextai_autoresearch",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        dirs_exist_ok=True,
    )
    shutil.copytree(project_root() / "schemas", base / "schemas", dirs_exist_ok=True)
    package = base / "src/nextai_autoresearch"
    (package / "benchmarks" / f"{COHORT}.py").write_text(
        _BENCHMARK_SOURCE, encoding="utf-8",
    )
    for candidate in (COMPLETE, PARTIAL):
        (package / "candidates" / f"{candidate}.py").write_text(
            "class Candidate:\n    def synthetic_value(self):\n        return 7\n",
            encoding="utf-8",
        )
    test = base / _BASELINE_TEST
    test.parent.mkdir(parents=True, exist_ok=True)
    test.write_text(
        "def test_synthetic_control():\n    assert 2 + 5 == 7\n", encoding="utf-8",
    )
    records = {
        name: {
            "implementation_files": {
                f"src/nextai_autoresearch/candidates/{name}.py": sha256_file(
                    package / "candidates" / f"{name}.py"
                ),
            },
            "conformance_tests": [{
                "path": _BASELINE_TEST,
                "node_id": _BASELINE_TEST + "::test_synthetic_control",
                "sha256": sha256_file(test),
            }],
        }
        for name in (COMPLETE, PARTIAL)
    }
    atomic_write_json(base / "config/baseline_semantics.json", {"baselines": records})


def _lab(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, partial: bool = False):
    from test_research_program_c import _fixture, _science_inputs

    base, clock, contract, study = _fixture(tmp_path, monkeypatch)
    ensure_layout(base)
    _write_synthetic_package(base)
    task = "research/plans/fixture-task.json"
    atomic_write_json(base / task, {"fixture_only": True, "native_data": False})
    candidates = [COMPLETE, PARTIAL] if partial else [COMPLETE]
    study.update(
        question="Can the isolated synthetic engineering path preserve complete and partial worker evidence?",
        candidates=candidates,
        matrix={"knowledge_sizes": [8], "reasoning_depths": [1], "queries_per_cell": 1,
                "seed_policy": {"method": "runner_random_v1", "count": 1,
                                "minimum": 1_000_000, "maximum": 2_147_483_647}},
        roles={name: {"fixture_only": True} for name in candidates},
        recipe={"fixture_only": True, "optimizer_steps": 0},
        data={"fixture_only": True, "native_rows": 0},
        diagnostics={}, diagnosis_gates={}, reference_gates={},
        task_contract_path=task, task_contract_sha256=sha256_file(base / task),
        decision_policy="Synthetic engineering only; preserve partial failures and never claim scientific transfer.",
        study_deadline_at="2099-01-01T00:00:00Z",
    )
    study["resources"].update(
        compute_charge_basis="full_worker_wall_v1", fit_seconds_per_role_cap=1,
        worker_seconds_cap=30, max_rss_bytes=2 * 1024**3,
        max_cuda_reserved_bytes=64 * 1024**2,
    )
    atomic_write_json(base / contract["scientific_plan_path"], study)
    canonical_config = load_config(project_root())
    config = canonical_config.path.read_text(encoding="utf-8")
    config = config.replace(
        f'benchmark_version = "{canonical_config.benchmark_version}"',
        f'benchmark_version = "{COHORT}"', 1,
    ).replace(
        f'benchmark_status = "{canonical_config.benchmark_status}"',
        'benchmark_status = "active"', 1,
    )
    config = config.replace(
        f"protocol_version = {canonical_config.protocol_version}", "protocol_version = 2", 1,
    )
    config = re.sub(r"(?ms)^\[research_program_c\].*?(?=^\[|\Z)", "", config)
    config += f'\n[research_program_c]\nstudy_path = "{c.ENGINEERING}"\n'
    (base / "config/research.toml").write_text(config, encoding="utf-8")
    atomic_write_json(base / "research/state.json", {
        "active_experiment_id": None, "cycle_number": 0, "completed_experiments": 0,
        "last_experiment_id": None, "last_reflection_completed_experiments": 0,
        "last_literature_review_completed_experiments": 0,
    })
    c.activate(base)
    _science_inputs(base, contract)
    # Isolated protection contains the exact synthetic authority and source.
    # Production protection rules remain unchanged outside this monkeypatch.
    monkeypatch.setattr(integrity, "FIXED_PROTECTED_FILES", (
        "config/research.toml", "config/baseline_semantics.json",
        c.CONTRACT, c.AUTHORITY, c.ENGINEERING, contract["scientific_plan_path"], task,
        *[f"schemas/{filename}" for filename in schemas.SCHEMA_FILES.values()],
    ))
    integrity.freeze_manifest(base)
    baseline_semantics.write_preflight_certificate(base)
    assert load_config(base).benchmark_version == COHORT
    assert integrity.verify_manifest(base)["ok"]
    assert not c.status(base)["scoring_authorized"]
    assert c.prospective_admission_problems(base) == []
    return base, clock, contract


def _mark_fixture_ready_from_actual_dry_run(base: Path, dry: dict) -> None:
    """Bind the real dry-run output before allowing the fixture paid commit."""
    binding = c._study_binding(read_jsonl(base / c.EVENTS))
    evidence = load_json(base / "research/laboratory/fixture-inputs.json")["gate_evidence"]
    dry_path = "research/checks/fixture-actual-dry-run.json"
    atomic_write_json(base / dry_path, {
        "fixture_only": True, "plan": dry, "scientific_registration_attempts_used": 0,
        "scoring_entropy_drawn": False, "plan_committed": False,
    })
    evidence["same_builder_dry_run"] = {"path": dry_path, "sha256": sha256_file(base / dry_path)}
    ready_check_path = "research/checks/fixture-readiness-check.json"
    assert integrity.verify_manifest(base)["ok"]
    baseline_semantics.verify_required_baselines(dry, base, run_tests=False)
    baseline_semantics.verify_preflight_certificate(base)
    assert c.status(base)["registration_attempts_used"] == 0
    atomic_write_json(base / ready_check_path, {
        "fixture_only": True, "validated": True,
        "manifest_sha256": sha256_file(base / "research/eval_manifest.json"),
        "dry_run_sha256": sha256_file(base / dry_path),
    })
    evidence["readiness"] = {"path": ready_check_path, "sha256": sha256_file(base / ready_check_path)}
    ready = {
        "program_id": c.PROGRAM_ID, "contract_sha256": c.CONTRACT_SHA256, **binding,
        "status": "validated_ready", "release_checks": {key: True for key in c.RELEASE_CHECKS},
        "gate_evidence": evidence,
    }
    atomic_write_json(base / "research/laboratory/fixture-ready.json", ready)
    c.mark_ready(base, "research/laboratory/fixture-ready.json")
    assert c.status(base)["scoring_authorized"]


def _normalized_plan(plan: dict) -> dict:
    value = copy.deepcopy(plan)
    for key in ("experiment_id", "created_at", "git_before"):
        value.pop(key, None)
    return value


def _fixture_analysis(base: Path, result_path: Path) -> tuple[Path, dict]:
    """Read actual worker journals; synthetic success is never scientific KEEP."""
    result = load_json(result_path)
    identity = result["experiment_id"]
    workers = []
    for outcome in result["candidates"]:
        prefix = base / "research/tmp" / identity / outcome["candidate"]
        journal = read_jsonl(prefix.with_suffix(".trials.jsonl"))
        assert journal == outcome["trials"]
        fits = read_jsonl(prefix.with_suffix(".fits.jsonl"))
        assert len(fits) == 1 and fits[0]["optimizer_steps"] == 0
        assert fits[0]["scientific_fit_seconds"] == 0
        assert Path(fits[0]["benchmark_origin"]).resolve().is_relative_to(
            (base / "src").resolve()
        )
        execution = outcome["execution"]
        assert execution["research_compute_seconds"] == execution["wall_seconds"]
        workers.append({
            "candidate": outcome["candidate"], "status": outcome["status"],
            "durable_trials": len(journal),
            "full_worker_seconds": execution["research_compute_seconds"],
            "supervised_fit_seconds": execution["supervised_fit_seconds"],
        })
    analysis = {
        "fixture_only": True, "scientific_evidence": False,
        "decision": "INCONCLUSIVE", "result_sha256": sha256_file(result_path),
        "workers": workers,
        "full_workers_seconds": sum(row["full_worker_seconds"] for row in workers),
        "supervised_fit_seconds": sum(row["supervised_fit_seconds"] for row in workers),
        "optimizer_steps": 0, "native_rows": 0,
    }
    path = base / "research/analyses" / f"{identity}-fixture.json"
    assert not path.exists()
    atomic_write_json(path, analysis)
    (base / "research/analyses" / f"{identity}.md").write_text(
        "Synthetic engineering fixture. Scientific decision: INCONCLUSIVE.\n",
        encoding="utf-8",
    )
    return path, analysis


def _archive_and_maintenance_pattern(base: Path, plan_path: Path, result_path: Path,
                                     analysis_path: Path) -> tuple[Path, dict]:
    """Honest fixture pattern preserving active evidence before maintenance."""
    identity = plan_path.stem
    selected = {
        "config/research.toml", "research/eval_manifest.json",
        "research/checks/preflight_certificate.json",
        "research/laboratory/preflight_certificate.json", c.EVENTS,
        "research/laboratory/fixture-cost.json", "research/laboratory/fixture-ready.json",
        "research/checks/fixture-actual-dry-run.json", "research/checks/fixture-readiness-check.json",
        *[path.relative_to(base).as_posix() for path in (plan_path, result_path, analysis_path)],
        *_CANONICAL_LEDGERS,
    }
    selected.update(
        path.relative_to(base).as_posix()
        for path in (base / "research/tmp" / identity).rglob("*") if path.is_file()
    )
    selected.update(
        path.relative_to(base).as_posix()
        for path in (base / "research/logs").glob(identity + "*") if path.is_file()
    )
    selected.update(load_json(base / "research/eval_manifest.json")["files"])
    selected.update(
        path.relative_to(base).as_posix()
        for path in (base / "research/laboratory").glob("fixture-*.json") if path.is_file()
    )
    selected = {relative for relative in selected if (base / relative).is_file()}
    hashes = {relative: sha256_file(base / relative) for relative in sorted(selected)}
    archive_path = base / "research/laboratory/archive" / f"{identity}-fixture.zip"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "x", zipfile.ZIP_DEFLATED) as archive:
        for relative in hashes:
            archive.write(base / relative, relative)
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(hashes)
        for relative, digest in hashes.items():
            assert hashlib.sha256(archive.read(relative)).hexdigest() == digest
        assert b'benchmark_status = "active"' in archive.read("config/research.toml")
    config_path = base / "config/research.toml"
    source = config_path.read_text(encoding="utf-8")
    assert source.count('benchmark_status = "active"') == 1
    config_path.write_text(
        source.replace('benchmark_status = "active"', 'benchmark_status = "maintenance"'),
        encoding="utf-8",
    )
    integrity.freeze_manifest(base, overwrite=True)
    baseline_semantics.write_preflight_certificate(base)
    assert integrity.verify_manifest(base)["ok"]
    receipt = {
        "fixture_only": True, "scientific_evidence": False,
        "archive_sha256": sha256_file(archive_path), "archived_files": hashes,
        "worker_costs_nested_in_outer_wall": True, "cost_refund": False,
        "benchmark_status": "maintenance",
    }
    atomic_write_json(base / "research/laboratory/fixture-completion.json", receipt)
    return archive_path, receipt


def _forbid_scoring_entropy(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args, **kwargs):
        pytest.fail("registration validation drew scoring entropy")

    monkeypatch.setattr(runner.secrets, "SystemRandom", forbidden)
    monkeypatch.setattr(runner.secrets, "token_hex", forbidden)
    monkeypatch.setattr(runner, "_realize_evaluation_matrix", forbidden)


def test_shared_dry_run_and_actual_fixture_registration_have_same_body_and_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical = project_root()
    canonical_before = _canonical_ledger_hashes(canonical)
    base, _, _ = _lab(tmp_path, monkeypatch)
    legacy_before = (base / "research/events.jsonl").read_bytes()
    before = _tree_hashes(base)
    calls, built = [], []
    for module, name, label in (
        (gates, "ensure_can_create_plan", "admission"),
        (schemas, "validate_document", "schema"),
        (baseline_semantics, "verify_required_baselines", "baseline"),
        (baseline_semantics, "verify_preflight_certificate", "preflight"),
    ):
        original = getattr(module, name)

        def wrapped(*args, _original=original, _label=label, **kwargs):
            calls.append(_label)
            return _original(*args, **kwargs)

        monkeypatch.setattr(module, name, wrapped)
    original_builder = program.build_and_validate_plan

    def shared_builder(*args, **kwargs):
        value = original_builder(*args, **kwargs)
        built.append(copy.deepcopy(value))
        return value

    monkeypatch.setattr(program, "build_and_validate_plan", shared_builder)
    with monkeypatch.context() as no_entropy:
        _forbid_scoring_entropy(no_entropy)
        dry = program.dry_run_plan(base)
        dry_calls = list(calls)
        assert _tree_hashes(base) == before
        assert c.status(base)["registration_attempts_used"] == 0
        assert list((base / "research/plans").glob("EXP-*.json")) == []
        _mark_fixture_ready_from_actual_dry_run(base, dry)
        calls.clear()
        plan_path = program.create_plan(base)
    registered = load_json(plan_path)
    assert len(built) == 2
    assert _normalized_plan(dry) == _normalized_plan(registered)
    assert dry_calls == calls == ["admission", "schema", "baseline", "preflight"]
    assert c.status(base)["registration_attempts_used"] == 1
    assert c.status(base)["experiment_id"] == registered["experiment_id"]
    assert len(read_jsonl(base / "research/plan_registry.jsonl")) == 1
    assert not (base / "research/tmp" / registered["experiment_id"]).exists()
    assert "seeds" not in registered["matrix"]
    assert (base / "research/events.jsonl").read_bytes() == legacy_before
    assert _canonical_ledger_hashes(canonical) == canonical_before


@pytest.mark.parametrize("gate", ["admission", "schema", "baseline", "preflight"])
def test_failed_dry_run_has_no_file_ticket_registration_or_entropy_side_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, gate: str,
) -> None:
    base, _, _ = _lab(tmp_path, monkeypatch)
    before = _tree_hashes(base)
    module, name = {
        "admission": (gates, "ensure_can_create_plan"),
        "schema": (schemas, "validate_document"),
        "baseline": (baseline_semantics, "verify_required_baselines"),
        "preflight": (baseline_semantics, "verify_preflight_certificate"),
    }[gate]

    def failure(*args, **kwargs):
        raise RuntimeError("synthetic " + gate + " rejection")

    monkeypatch.setattr(module, name, failure)
    _forbid_scoring_entropy(monkeypatch)
    monkeypatch.setattr(c, "reserve_registration", lambda *a: pytest.fail("dry-run claimed a ticket"))
    monkeypatch.setattr(ledger, "register_plan", lambda *a: pytest.fail("dry-run registered a plan"))
    with pytest.raises(RuntimeError, match="synthetic " + gate):
        program.dry_run_plan(base)
    assert _tree_hashes(base) == before
    assert c.status(base)["registration_attempts_used"] == 0


@pytest.mark.parametrize("partial", [False, True], ids=["complete", "partial-crash"])
def test_real_fixture_worker_analysis_archive_and_maintenance_preserve_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, partial: bool,
) -> None:
    canonical = project_root()
    canonical_before = _canonical_ledger_hashes(canonical)
    base, clock, contract = _lab(tmp_path, monkeypatch, partial=partial)
    legacy_before = (base / "research/events.jsonl").read_bytes()
    legacy_subset_before = copy.deepcopy(c._legacy_subset(base))
    dry = program.dry_run_plan(base)
    _mark_fixture_ready_from_actual_dry_run(base, dry)
    plan_path = program.create_plan(base)
    assert _normalized_plan(dry) == _normalized_plan(load_json(plan_path))
    result_path = runner.run_experiment(plan_path, base)
    result = load_json(result_path)
    assert result["status"] == ("complete_with_failures" if partial else "complete")
    assert result["integrity_before"]["ok"] and result["integrity_after"]["ok"]
    runtime = load_json(base / "research/tmp" / plan_path.stem / "runtime-plan.json")
    assert len(runtime["matrix"]["seeds"]) == 1
    assert "seeds" not in load_json(plan_path)["matrix"]
    analysis_path, analysis = _fixture_analysis(base, result_path)
    assert analysis["decision"] == "INCONCLUSIVE" and not analysis["scientific_evidence"]
    assert analysis["supervised_fit_seconds"] == 0
    assert analysis["full_workers_seconds"] > 0
    if partial:
        crash = result["candidates"][-1]
        assert crash["candidate"] == PARTIAL and crash["status"] == "crash"
        assert crash["error_type"] == "RuntimeError"
        assert "durable first trial" in crash["error"] and crash["traceback"]
        assert len(crash["trials"]) == 1 and crash["summary"]["status"] == "partial"
        assert crash["execution"]["return_code"] == 1
    binding = c._study_binding(read_jsonl(base / c.EVENTS))
    cost_path = "research/laboratory/fixture-cost.json"
    atomic_write_json(base / cost_path, {
        **c._binding(), **binding, "experiment_id": plan_path.stem,
        "full_worker_seconds": analysis["full_workers_seconds"],
        "supervised_fit_seconds": analysis["supervised_fit_seconds"],
    })
    before_cost = c.status(base)["total_seconds_charged"]
    c.record_scientific_cost(base, cost_path)
    assert c.status(base)["total_seconds_charged"] == before_cost
    assert c.status(base)["full_worker_seconds"] == analysis["full_workers_seconds"]
    clock[0] += timedelta(seconds=analysis["full_workers_seconds"] + 1)
    c.checkpoint(base, "synthetic-outer-work-completed")
    archive_path, receipt = _archive_and_maintenance_pattern(
        base, plan_path, result_path, analysis_path,
    )
    receipt.update(
        program_id=c.PROGRAM_ID, contract_sha256=c.CONTRACT_SHA256,
        whole_goal_complete=False, optimizer_steps=0, native_rows=0,
    )
    receipt_path = "research/laboratory/fixture-completion.json"
    atomic_write_json(base / receipt_path, receipt)
    c.close(base, receipt_path)
    final = c.status(base)
    assert final["program_terminal"] and not final["scoring_authorized"]
    assert final["registration_attempts_used"] == 1
    assert final["B_preserved"] == contract["B_preserved"]
    assert load_config(base).benchmark_status == "maintenance"
    assert archive_path.is_file()
    with pytest.raises((ValueError, RuntimeError)):
        program.create_plan(base)
    assert c.status(base)["registration_attempts_used"] == 1
    assert (base / "research/events.jsonl").read_bytes().startswith(legacy_before)
    assert c._legacy_subset(base) == legacy_subset_before
    assert _canonical_ledger_hashes(canonical) == canonical_before
