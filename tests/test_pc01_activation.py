"""Prospective scope tests. No production training or registration."""
import shutil
import pytest
from nextai_autoresearch import gates, laboratory, pc01_execution as execution
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json, load_json, project_root, sha256_file
from test_lab_restart import _lab_fixture
from test_pc01_execution import plan


@pytest.fixture
def authorized(tmp_path):
    _lab_fixture(tmp_path)
    for relative in (laboratory.ACTIVATION_PATH, "schemas/pc01_plan.schema.json", "research/plans/PC-01-CONTRACT-V1.json"):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project_root() / relative, target)
    append_jsonl(tmp_path / "research/events.jsonl", {
        "event": "pc01_activation_authorized", "authorization_path": laboratory.ACTIVATION_PATH,
        "authorization_sha256": laboratory.ACTIVATION_SHA256})
    config = tmp_path / "config/research.toml"
    text = config.read_text().replace('benchmark_status = "maintenance"', 'benchmark_status = "active"')
    text = text.replace('benchmark_version = "wt01_causal_contract_v1"',
                        'benchmark_version = "pc01_byte_lm_learning_measurement_v1"')
    text = text.replace('benchmark_version = "pc01_byte_lm_learning_measurement_v3"',
                        'benchmark_version = "pc01_byte_lm_learning_measurement_v1"')
    text = text.replace('benchmark_version = "pc01_byte_lm_learning_measurement_v2"',
                        'benchmark_version = "pc01_byte_lm_learning_measurement_v1"')
    config.write_text(text.replace('benchmark_version = "heldout_suitesparse_cross_matrix_prolongation_v1"',
                                   'benchmark_version = "pc01_byte_lm_learning_measurement_v1"'))
    atomic_write_json(tmp_path / "research/eval_manifest.json", {"evaluator_sha256": "a"*64})
    return tmp_path


def test_authorization_allows_only_one_scoped_development_registration(authorized):
    root = authorized
    assert laboratory.laboratory_contract(root)["status"] == "dev_authorized"
    assert load_json(root / laboratory.CONTRACT_PATH)["status"] == "preparation_only"
    assert laboratory.pc01_scope_problems(root, candidate="pc01_byte_gpt_v1", phase="dev") == []
    for candidate, phase in ((None, None), ("other", "dev"), ("pc01_byte_gpt_v1", "final")):
        assert laboratory.pc01_scope_problems(root, candidate=candidate, phase=phase)
    path, value = plan(root)
    append_jsonl(root / "research/plan_status_events.jsonl", {"experiment_id": path.stem, "status": "invalidated", "reason": "fixture"})
    assert laboratory.pc01_scope_problems(root, candidate="pc01_byte_gpt_v1", phase="dev")
    assert laboratory.pc01_scope_problems(root, experiment_id=path.stem)


def test_scoped_run_accepts_only_exact_registered_dev(authorized, monkeypatch):
    path, value = plan(authorized)
    value["candidate"] = "pc01_byte_gpt_v1"
    monkeypatch.setattr(execution, "registered_plans", lambda root: [value])
    assert laboratory.pc01_scope_problems(authorized, experiment_id=path.stem) == []
    for key, bad in (("phase", "final"), ("attempt", 2), ("series_sha256", "b"*64), ("development_seed", 1104)):
        original = value[key]
        value[key] = bad
        assert laboratory.pc01_scope_problems(authorized, experiment_id=path.stem)
        value[key] = original
    assert laboratory.pc01_scope_problems(authorized, experiment_id="EXP-20990101-9999")


@pytest.mark.parametrize("fault", ["missing", "modified", "duplicate", "event_hash", "other_cohort"])
def test_activation_fails_closed(authorized, fault):
    path = authorized / laboratory.ACTIVATION_PATH
    if fault == "missing":
        path.unlink()
    elif fault == "modified":
        path.write_text(path.read_text().replace('"max_registered_attempts": 1', '"max_registered_attempts": 3'))
    elif fault == "duplicate":
        append_jsonl(authorized / "research/events.jsonl", {"event": "pc01_activation_authorized"})
    elif fault == "event_hash":
        event = authorized / "research/events.jsonl"
        event.write_text(event.read_text().replace(laboratory.ACTIVATION_SHA256, "a"*64))
    else:
        config = authorized / "config/research.toml"
        config.write_text(config.read_text().replace("pc01_byte_lm_learning_measurement_v1", "other"))
    assert laboratory.laboratory_problems(authorized, scoring=True)


def test_authorization_cannot_bypass_maintenance_stop_or_integrity(authorized, monkeypatch):
    root = authorized
    module = root / "src/nextai_autoresearch/benchmarks/pc01_byte_lm_learning_measurement_v1.py"
    module.parent.mkdir(parents=True)
    module.write_text("# fixture")
    monkeypatch.setattr(gates, "lifecycle_problems", lambda root: [])
    monkeypatch.setattr(gates, "verify_manifest", lambda root: {"ok": True})
    kwargs = {"pc01_candidate": "pc01_byte_gpt_v1", "pc01_phase": "dev"}
    gates.ensure_can_create_plan(root, **kwargs)
    for name in ("STOP", "PAUSE"):
        (root / name).touch()
        with pytest.raises(gates.GateViolation, match=name):
            gates.ensure_can_create_plan(root, **kwargs)
        (root / name).unlink()
    monkeypatch.setattr(gates, "verify_manifest", lambda root: {"ok": False, "problems": ["changed"]})
    with pytest.raises(gates.GateViolation, match="integrity"):
        gates.ensure_can_create_plan(root, **kwargs)
    monkeypatch.setattr(gates, "verify_manifest", lambda root: {"ok": True})
    config = root / "config/research.toml"
    config.write_text(config.read_text().replace('benchmark_status = "active"', 'benchmark_status = "maintenance"'))
    with pytest.raises(gates.GateViolation, match="not active"):
        gates.ensure_can_create_plan(root, **kwargs)


def test_real_authorization_denies_final_and_legacy_without_mutation(monkeypatch):
    root = project_root()
    # Exercise historical dev-only authority even after a separate final activation.
    from nextai_autoresearch import pc01_final_authority
    monkeypatch.setattr(pc01_final_authority, "authority", lambda root: None)
    before = sha256_file(root / "research/plan_registry.jsonl")
    with pytest.raises(gates.GateViolation):
        gates.ensure_can_create_plan(root)
    with pytest.raises(gates.GateViolation):
        execution.create_plan(root, candidate="pc01_byte_gpt_v1", phase="final", question="must be denied")
    with pytest.raises(gates.GateViolation):
        execution.freeze_series(root, "EXP-20990101-0001")
    assert sha256_file(root / "research/plan_registry.jsonl") == before
