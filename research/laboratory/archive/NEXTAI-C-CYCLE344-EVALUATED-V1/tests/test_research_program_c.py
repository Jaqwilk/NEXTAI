"""C wallet fixtures: synthetic files only; no canonical tickets, data or fits."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re

import pytest

from nextai_autoresearch import research_program_c as c
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_json


def _write(base, path, value):
    target = base / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, dict):
        atomic_write_json(target, value)
    else:
        target.write_text(value, encoding="utf-8")
    return hashlib.sha256(target.read_bytes()).hexdigest()


def _fixture(tmp_path, monkeypatch):
    """Reusable complete isolated authority. Patches hashes, never production files."""
    base = tmp_path
    start = datetime(2026, 10, 7, 23, 42, tzinfo=timezone.utc)
    clock = [start + timedelta(seconds=10)]
    monkeypatch.setattr(c, "_now", lambda: clock[0])
    monkeypatch.setattr(c, "AUTHORITY_SHA256", _write(base, c.AUTHORITY, "Synthetic engineering authority only\n"))
    source_path, publication_path, closure_path = ("research/results/fixture-source.json",
                                                 "research/laboratory/fixture-publication.json",
                                                 "research/laboratory/fixture-A-closure.json")
    anchors = {path: _write(base, path, {"fixture": path}) for path in (source_path, publication_path, closure_path)}
    b_contract = {"source_result_path": source_path, "source_state_publication_path": publication_path,
                  "carry_forward": {"completion_receipt_path": closure_path, "document_sha256": anchors}}
    b_digest = _write(base, c.B_CONTRACT, b_contract)
    for ticket in (1, 2):
        append_jsonl(base / "research/events.jsonl", {"event": "research_program_registration_started",
                     "program_id": c.B_ID, "ticket": ticket})
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_aux_fit_charged",
                 "program_id": c.B_ID, "seconds": 30999.55024020007})
    b_prefix = hashlib.sha256((base / "research/events.jsonl").read_bytes()).hexdigest()
    liability_path = "research/laboratory/fixture-old-admin.json"
    liability_digest = _write(base, liability_path, {"unfunded_admin_overrun_minimum_seconds": 110.724645})
    engineering = {"id": "NEXTAI-C-ENGINEERING-PREREGISTRATION-V1", "parent_contract_path": c.CONTRACT,
                   "engineering_phase_seconds_max": 10800}
    monkeypatch.setattr(c, "ENGINEERING_SHA256", _write(base, c.ENGINEERING, engineering))
    science_path = "research/plans/ASM01-C-STABILIZED-SCREEN-V1.json"
    contract = {"id": c.PROGRAM_ID, "authority_copy_path": c.AUTHORITY, "authority_sha256": c.AUTHORITY_SHA256,
                "engineering_plan_path": c.ENGINEERING, "scientific_plan_path": science_path,
                "work_started_at": "2026-10-07T23:42:00Z", "wall_deadline_at": "2026-10-08T11:42:00Z",
                "effective_budget_deadline_at_with_initial600_debt": "2026-10-08T11:32:00Z",
                "total_seconds_cap": 43200, "scientific_registration_attempts_cap": 1,
                "scientific_full_workers_seconds_cap": 9000, "scientific_supervised_fit_seconds_cap": 3600,
                "historical_admin_liability": {"evidence_path": liability_path, "evidence_sha256": liability_digest,
                    "initial_conservative_settlement_seconds": 600, "upper_bound_verified": False,
                    "unmeasured_later_work_is_not_zero": True, "additional_proven_liability_must_increase_C_charge": True},
                "B_preserved": {"registration_attempts_used": 2, "compute_seconds_charged": 30999.55024020007,
                    "protected_registration_attempts": 6, "protected_seconds": 41000,
                    "events_prefix_sha256": b_prefix, "contract_sha256": b_digest, "C_credit_added_to_B": False},
                "scientific_release_gates": list(c.RELEASE_CHECKS)}
    monkeypatch.setattr(c, "CONTRACT_SHA256", _write(base, c.CONTRACT, contract))
    config = 'schema_version=1\n[project]\nbenchmark_version="c_engineering_fixture_v1"\n'
    config += '[research_program_c]\nstudy_path="' + c.ENGINEERING + '"\n'
    for tier in ("quick", "screen", "deep"):
        config += f'[budgets.{tier}]\ndevelopment_seeds=[1]\nscoring_seed_count=1\n'
    _write(base, "config/research.toml", config)
    study = {"id": "C-SYNTHETIC-FIXTURE", "cohort": "c_engineering_fixture_v1", "stage": "transfer_family_2_screen",
             "study_kind": "fixture", "registration_attempts_for_this_study_cap": 1,
             "resources": {"fit_seconds_study_cap": 9000, "supervised_fit_seconds_study_cap": 3600}}
    _write(base, science_path, study)
    return base, clock, contract, study


def _science_inputs(base, contract):
    c.freeze_scientific_study(base)
    config_path = base / "config/research.toml"
    config = config_path.read_text(encoding="utf-8")
    config = re.sub(r'(\[research_program_c\]\s*study_path\s*=\s*)"[^"]*"',
                    lambda match: match[1] + '"' + contract["scientific_plan_path"] + '"', config)
    config_path.write_text(config, encoding="utf-8")
    binding = c._study_binding(read_jsonl(base / c.EVENTS))
    evidence = {}
    for key in c.INPUT_CHECKS:
        path = "research/laboratory/fixture-" + key + ".json"
        evidence[key] = {"path": path, "sha256": _write(base, path, {"fixture_check": key, "passed": True})}
    inputs = {"program_id": c.PROGRAM_ID, "contract_sha256": c.CONTRACT_SHA256, **binding,
              "status": "validated_prospective_inputs", "release_checks": {key: True for key in c.INPUT_CHECKS},
              "gate_evidence": evidence}
    _write(base, "research/laboratory/fixture-inputs.json", inputs)
    c.mark_inputs_ready(base, "research/laboratory/fixture-inputs.json")
    return binding


def _science_ready(base, contract):
    binding = _science_inputs(base, contract)
    evidence = load_json(base / "research/laboratory/fixture-inputs.json")["gate_evidence"]
    for key in ("same_builder_dry_run", "readiness"):
        path = "research/laboratory/fixture-" + key + ".json"
        evidence[key] = {"path": path, "sha256": _write(base, path, {"fixture_check": key, "passed": True})}
    ready = {"program_id": c.PROGRAM_ID, "contract_sha256": c.CONTRACT_SHA256, **binding,
             "status": "validated_ready", "release_checks": {key: True for key in c.RELEASE_CHECKS},
             "gate_evidence": evidence}
    _write(base, "research/laboratory/fixture-ready.json", ready)
    c.mark_ready(base, "research/laboratory/fixture-ready.json")
    return binding


def _register(base, contract):
    binding = _science_ready(base, contract)
    c.reserve_registration(base)
    protocol = {"authority_path": c.AUTHORITY, "program_contract_path": c.CONTRACT,
                "program_contract_sha256": c.CONTRACT_SHA256, "registration_ticket": 1,
                "study_path": binding["study_path"], "study_sha256": binding["study_sha256"]}
    plan = {"experiment_id": "EXP-FIXTURE-0001", "benchmark": binding["cohort"], "research_program_protocol": protocol}
    path = "research/plans/EXP-FIXTURE-0001.json"
    _write(base, path, plan)
    c.mark_registered(base, plan, path, sha256_json(plan))
    return binding


def test_activation_preserves_b_and_charges_one_outer_window(tmp_path, monkeypatch):
    base, clock, contract, _ = _fixture(tmp_path, monkeypatch)
    legacy = (base / "research/events.jsonl").read_bytes()
    assert c.is_active(base) is False and c.status(base) is None
    value = c.activate(base)
    assert c.is_active(base) is True and value["total_seconds_charged"] == 610
    assert value["B_preserved"] == contract["B_preserved"]
    assert "stage_b_registration_attempts_used" not in value
    assert value["registration_attempts_used"] == 0 and value["scoring_authorized"] is False
    c.auxiliary_reserve(base, "fixture-checks", 100)
    clock[0] += timedelta(seconds=50)
    c.auxiliary_charge(base, "fixture-checks", 50)
    c.checkpoint(base, "nested-checks")
    assert c.status(base)["total_seconds_charged"] == 660
    assert (base / "research/events.jsonl").read_bytes() == legacy
    with pytest.raises(ValueError):
        c.activate(base)


def test_cannot_register_during_engineering_or_ready_with_missing_gate(tmp_path, monkeypatch):
    base, _, contract, _ = _fixture(tmp_path, monkeypatch)
    c.activate(base)
    before = (base / c.EVENTS).read_bytes()
    with pytest.raises(ValueError, match="engineering"):
        c.reserve_registration(base)
    assert (base / c.EVENTS).read_bytes() == before
    binding = _science_inputs(base, contract)
    evidence = load_json(base / "research/laboratory/fixture-inputs.json")["gate_evidence"]
    for key in ("same_builder_dry_run", "readiness"):
        path = "research/laboratory/fixture-" + key + ".json"
        evidence[key] = {"path": path, "sha256": _write(base, path, {"fixture_check": key, "passed": True})}
    receipt = {"program_id": c.PROGRAM_ID, "contract_sha256": c.CONTRACT_SHA256, **binding,
               "status": "validated_ready", "release_checks": {key: True for key in c.RELEASE_CHECKS},
               "gate_evidence": evidence}
    for key in c.RELEASE_CHECKS:
        malformed = deepcopy(receipt)
        malformed["release_checks"][key] = False
        _write(base, "research/laboratory/not-ready.json", malformed)
        with pytest.raises(ValueError, match="six"):
            c.mark_ready(base, "research/laboratory/not-ready.json")
    assert c.status(base)["registration_attempts_used"] == 0


def test_one_paid_failure_consumed_without_b_change(tmp_path, monkeypatch):
    base, _, contract, _ = _fixture(tmp_path, monkeypatch)
    c.activate(base)
    _science_ready(base, contract)
    legacy = (base / "research/events.jsonl").read_bytes()
    assert c.scope_problems(base) == []
    assert c.reserve_registration(base) == 1
    assert c.scope_problems(base) == []  # same pending attempt can pass admission
    with pytest.raises(ValueError, match="consumed"):
        c.reserve_registration(base)
    c.mark_registration_failed(base, "fixture commit gate failed")
    value = c.status(base)
    assert value["registration_attempts_used"] == 1 and value["program_terminal"] is True
    assert value["experiment_id"] is None and c.scope_problems(base)
    with pytest.raises(ValueError):
        c.reserve_registration(base)
    with pytest.raises(ValueError):
        c.mark_registration_failed(base, "rescue")
    assert (base / "research/events.jsonl").read_bytes() == legacy


def test_registered_binding_resource_overruns_preserved_not_double_counted(tmp_path, monkeypatch):
    base, clock, contract, _ = _fixture(tmp_path, monkeypatch)
    c.activate(base)
    binding = _register(base, contract)
    assert c.scope_problems(base, "EXP-FIXTURE-0001") == [] and c.scope_problems(base)
    receipt = {**c._binding(), **binding, "experiment_id": "EXP-FIXTURE-0001",
               "full_worker_seconds": 9100., "supervised_fit_seconds": 3601.}
    _write(base, "research/laboratory/cost.json", receipt)
    clock[0] += timedelta(seconds=9200)
    c.record_scientific_cost(base, "research/laboratory/cost.json")
    value = c.status(base)
    assert value["total_seconds_charged"] == 9810  # 600 + 9210, not +9100+3601
    assert value["full_worker_seconds"] == 9100 and value["supervised_fit_seconds"] == 3601
    assert value["scoring_authorized"] is False and value["program_terminal"] is True
    with pytest.raises(ValueError):
        c.record_scientific_cost(base, "research/laboratory/cost.json")
    receipt["full_worker_seconds"] = 9099
    _write(base, "research/laboratory/refunded.json", receipt)
    with pytest.raises(ValueError):
        c.record_scientific_cost(base, "research/laboratory/refunded.json")


def test_authority_missing_hash_change_b_prefix_and_source_fail_closed(tmp_path, monkeypatch):
    base, _, _, _ = _fixture(tmp_path, monkeypatch)
    c.activate(base)
    for path in (c.AUTHORITY, c.CONTRACT, c.ENGINEERING, c.B_CONTRACT, "research/results/fixture-source.json"):
        target = base / path
        original = target.read_bytes()
        target.write_bytes(original + b" ")
        with pytest.raises(ValueError):
            c.status(base)
        target.write_bytes(original)
    target = base / c.AUTHORITY
    saved = target.read_bytes()
    target.unlink()
    with pytest.raises(FileNotFoundError):
        c.status(base)
    target.write_bytes(saved)
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_aux_fit_charged", "program_id": c.B_ID, "seconds": 1})
    with pytest.raises(ValueError, match="legacy B"):
        c.status(base)


def test_global_non_b_suffix_allowed_b_prefix_immutable(tmp_path, monkeypatch):
    base, _, _, _ = _fixture(tmp_path, monkeypatch)
    c.activate(base)
    append_jsonl(base / "research/events.jsonl", {"event": "fixture-plan-recorded", "program_id": c.PROGRAM_ID})
    assert c.status(base)["total_seconds_charged"] == 610
    target = base / "research/events.jsonl"
    original = target.read_bytes()
    target.write_bytes(original.replace(b"ticket", b"tacket", 1))
    with pytest.raises(ValueError, match="legacy B"):
        c.status(base)


def test_foreign_duplicate_reordered_and_nonfinite_events_rejected(tmp_path, monkeypatch):
    base, _, _, _ = _fixture(tmp_path, monkeypatch)
    c.activate(base)
    c.checkpoint(base, "fixture")
    path = base / c.EVENTS
    original = path.read_bytes()
    events = read_jsonl(path)
    for key, wrong in (("program_id", "foreign"), ("authority_sha256", "0" * 64),
                       ("sequence", True), ("sequence", 1), ("previous_event_sha256", None),
                       ("outer_elapsed_seconds", float("nan")), ("total_seconds_charged", 1),
                       ("liability_seconds", 0)):
        malformed = deepcopy(events)
        malformed[-1][key] = wrong
        path.write_text("".join(json.dumps(e) + "\n" for e in malformed), encoding="utf-8")
        with pytest.raises(ValueError):
            c.status(base)
        path.write_bytes(original)
    append_jsonl(path, events[-1])
    with pytest.raises(ValueError):
        c.status(base)


def test_nonfinite_caps_measurements_clock_and_exhaustion(tmp_path, monkeypatch):
    base, clock, contract, _ = _fixture(tmp_path, monkeypatch)
    c.activate(base)
    for value in (True, float("nan"), float("inf"), -1, 0, 43201):
        with pytest.raises(ValueError):
            c.auxiliary_reserve(base, "invalid", value)
    for value in (True, float("nan"), float("inf"), -1, 0):
        with pytest.raises(ValueError):
            c.add_liability(base, value, "missing.json")
    c.checkpoint(base, "at-ten")
    clock[0] -= timedelta(seconds=1)
    with pytest.raises(ValueError, match="backwards"):
        c.checkpoint(base, "refund")
    assert c.status(base)["total_seconds_charged"] == 610
    clock[0] = datetime(2026, 10, 8, 11, 32, tzinfo=timezone.utc)
    assert c.status(base)["total_seconds_charged"] == 43200
    assert c.status(base)["program_terminal"] is True
    clock[0] += timedelta(seconds=5)
    c.checkpoint(base, "actual-overrun")
    assert c.status(base)["total_seconds_charged"] == 43205
    with pytest.raises(ValueError):
        c.reserve_registration(base)


def test_liability_increases_without_refund_and_closure_stops_idle_clock(tmp_path, monkeypatch):
    base, clock, _, _ = _fixture(tmp_path, monkeypatch)
    c.activate(base)
    _write(base, "research/laboratory/debt.json", {"additional_proven_work_seconds": 25})
    c.add_liability(base, 25, "research/laboratory/debt.json")
    assert c.status(base)["total_seconds_charged"] == 635
    with pytest.raises(ValueError):
        c.add_liability(base, 25, "research/laboratory/debt.json")
    _write(base, "research/laboratory/close.json", {"program_id": c.PROGRAM_ID, "contract_sha256": c.CONTRACT_SHA256,
           "whole_goal_complete": False})
    c.close(base, "research/laboratory/close.json")
    clock[0] += timedelta(days=1)
    assert c.status(base)["total_seconds_charged"] == 635
    assert c.status(base)["scoring_authorized"] is False
    c.checkpoint(base, "late-publication-cost")
    assert c.status(base)["total_seconds_charged"] == 87035
    with pytest.raises(ValueError):
        c.close(base, "research/laboratory/close.json")


def test_exclusive_ledger_lock_rejects_racing_second_mutation(tmp_path, monkeypatch):
    base, _, _, _ = _fixture(tmp_path, monkeypatch)
    c.activate(base)
    with c._lock(base):
        with pytest.raises(ValueError, match="locked"):
            c.checkpoint(base, "racing")
    assert not (base / "research/tmp/c_ledger.lock").exists()


def test_prospective_admission_reads_real_prerequisites_without_ready_or_writes(tmp_path, monkeypatch):
    base, clock, contract, _ = _fixture(tmp_path, monkeypatch)
    c.activate(base)
    assert c.prospective_admission_problems(base)
    _science_inputs(base, contract)
    before = {path.relative_to(base).as_posix(): path.read_bytes() for path in base.rglob("*") if path.is_file()}
    assert c.prospective_admission_problems(base) == []
    assert c.scope_problems(base, prospective=True) == []
    assert c.scope_problems(base) and c.status(base)["scoring_authorized"] is False
    with pytest.raises(ValueError):
        c.reserve_registration(base)
    after = {path.relative_to(base).as_posix(): path.read_bytes() for path in base.rglob("*") if path.is_file()}
    assert before == after
    config = base / "config/research.toml"
    config.write_text(config.read_text().replace('benchmark_version="c_engineering_fixture_v1"',
                                                'benchmark_version="foreign_cohort"'), encoding="utf-8")
    assert c.prospective_admission_problems(base)
    config.write_bytes(before["config/research.toml"])
    clock[0] = datetime(2026, 10, 8, 11, 32, tzinfo=timezone.utc)
    assert c.prospective_admission_problems(base)


def test_prospective_artifact_missing_corrupt_same_size_mtime_and_foreign_receipt(tmp_path, monkeypatch):
    base, _, contract, _ = _fixture(tmp_path, monkeypatch)
    c.activate(base)
    _science_inputs(base, contract)
    receipt = load_json(base / "research/laboratory/fixture-inputs.json")
    for proof in receipt["gate_evidence"].values():
        path = base / proof["path"]
        original, stat = path.read_bytes(), path.stat()
        changed = bytearray(original)
        changed[0] = ord("[")
        path.write_bytes(changed)
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        assert path.stat().st_size == stat.st_size and path.stat().st_mtime_ns == stat.st_mtime_ns
        with pytest.raises(ValueError, match="evidence changed"):
            c.prospective_admission_problems(base)
        path.write_bytes(original)
        path.unlink()
        with pytest.raises(FileNotFoundError):
            c.prospective_admission_problems(base)
        path.write_bytes(original)
    path = base / "research/laboratory/fixture-inputs.json"
    path.write_text("{corrupt", encoding="utf-8")
    with pytest.raises(ValueError):
        c.prospective_admission_problems(base)
    binding = c._study_binding(read_jsonl(base / c.EVENTS))
    for key, value in (("program_id", "foreign"), ("contract_sha256", "0" * 64),
                       ("study_sha256", "0" * 64), ("cohort", "foreign")):
        wrong = deepcopy(receipt)
        wrong[key] = value
        _write(base, "research/laboratory/foreign-inputs.json", wrong)
        with pytest.raises(ValueError, match="four"):
            c._inputs_receipt(base, "research/laboratory/foreign-inputs.json", binding)


@pytest.mark.parametrize("error", [None, "Synthetic scientific worker failure"])
def test_scientific_finish_terminal_but_admin_outer_clock_keeps_charging(tmp_path, monkeypatch, error):
    base, clock, contract, _ = _fixture(tmp_path, monkeypatch)
    c.activate(base)
    binding = _register(base, contract)
    cost_path = "research/laboratory/fixture-terminal-cost.json"
    cost_digest = _write(base, cost_path, {**c._binding(), **binding, "experiment_id": "EXP-FIXTURE-0001",
                         "full_worker_seconds": 10., "supervised_fit_seconds": 3.})
    finish = {"program_id": c.PROGRAM_ID, "contract_sha256": c.CONTRACT_SHA256,
              "study_path": binding["study_path"], "study_sha256": binding["study_sha256"],
              "experiment_id": "EXP-FIXTURE-0001", "cost_receipt_path": cost_path,
              "cost_receipt_sha256": cost_digest, "full_worker_seconds": 10., "supervised_fit_seconds": 3.,
              "paid_retry_authorized": False, "whole_goal_complete": False, "error": error}
    finish_path = "research/laboratory/fixture-scientific-finished.json"
    _write(base, finish_path, finish)
    with pytest.raises(ValueError, match="prior costs"):
        c.mark_scientific_finished(base, finish_path)
    c.record_scientific_cost(base, cost_path)
    c.mark_scientific_finished(base, finish_path)
    initial = c.status(base)
    assert initial["scientific_phase_finished"] and initial["program_terminal"] and initial["study_terminal"]
    assert not initial["scoring_authorized"] and not initial["program_closed"] and not initial["paid_run_pending"]
    clock[0] += timedelta(seconds=40)
    assert c.status(base)["total_seconds_charged"] == initial["total_seconds_charged"] + 40
    c.checkpoint(base, "post-science-administration")
    assert c.scope_problems(base, "EXP-FIXTURE-0001")
    with pytest.raises(ValueError):
        c.reserve_registration(base)
    with pytest.raises(ValueError):
        c.mark_scientific_finished(base, finish_path)
    closure = "research/laboratory/fixture-last-closure.json"
    _write(base, closure, {"program_id": c.PROGRAM_ID, "contract_sha256": c.CONTRACT_SHA256, "whole_goal_complete": False})
    c.close(base, closure)
    closed_cost = c.status(base)["total_seconds_charged"]
    clock[0] += timedelta(seconds=50)
    assert c.status(base)["total_seconds_charged"] == closed_cost


def test_scientific_finish_foreign_cost_binding_and_refund_rejected(tmp_path, monkeypatch):
    base, _, contract, _ = _fixture(tmp_path, monkeypatch)
    c.activate(base)
    binding = _register(base, contract)
    cost_path = "research/laboratory/fixture-finish-cost.json"
    digest = _write(base, cost_path, {**c._binding(), **binding, "experiment_id": "EXP-FIXTURE-0001",
                                   "full_worker_seconds": 8., "supervised_fit_seconds": 2.})
    c.record_scientific_cost(base, cost_path)
    finish = {"program_id": c.PROGRAM_ID, "contract_sha256": c.CONTRACT_SHA256,
              "study_path": binding["study_path"], "study_sha256": binding["study_sha256"],
              "experiment_id": "EXP-FIXTURE-0001", "cost_receipt_path": cost_path, "cost_receipt_sha256": digest,
              "full_worker_seconds": 8., "supervised_fit_seconds": 2., "paid_retry_authorized": False,
              "whole_goal_complete": False, "error": None}
    before = (base / c.EVENTS).read_bytes()
    for key, bad in (("program_id", "foreign"), ("study_sha256", "0" * 64), ("experiment_id", "foreign"),
                     ("cost_receipt_sha256", "0" * 64), ("full_worker_seconds", 0),
                     ("supervised_fit_seconds", True), ("paid_retry_authorized", True)):
        wrong = {**finish, key: bad}
        _write(base, "research/laboratory/fixture-wrong-finish.json", wrong)
        with pytest.raises(ValueError):
            c.mark_scientific_finished(base, "research/laboratory/fixture-wrong-finish.json")
        assert (base / c.EVENTS).read_bytes() == before
