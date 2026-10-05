"""New authority cannot reopen closed evidence or refund consumed computation."""
import pytest
import shutil

from nextai_autoresearch import research_program as program
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.utils import atomic_write_json, load_json, project_root, sha256_file, sha256_json
from test_muc03_program import fixture_program


def continuation_fixture(tmp_path):
    base = fixture_program(tmp_path)
    for ticket in range(1, 4):
        path = f"research/plans/closed-ticket-{ticket}.json"
        atomic_write_json(base / path, load_json(base / program.FIRST_STUDY))
        append_jsonl(base / "research/events.jsonl", {"event": "research_program_registration_started",
            "program_id": "MUC03-AUTONOMOUS-20261004-V1", "ticket": ticket, "study_path": path})
        append_jsonl(base / "research/events.jsonl", {"event": "research_program_registration_failed",
            "program_id": "MUC03-AUTONOMOUS-20261004-V1", "ticket": ticket, "study_path": path, "error": "preserved fixture failure"})
    program.auxiliary_reserve(base, "historical-tests", 1439)
    program.auxiliary_charge(base, "historical-tests", 1439)
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_completed", "program_id": "MUC03-AUTONOMOUS-20261004-V1"})
    prior = program.status(base)
    contract = load_json(project_root() / program.CONTINUATION_CONTRACT)
    carry = contract["carry_forward"]
    carry.update(terminal_study_path=program.FIRST_STUDY,
        document_sha256={p: sha256_file(base / p) for p in (program.AUTHORITY, program.CONTRACT, program.FIRST_STUDY, "research/results/prior.json")},
        program_events_sha256=sha256_json(read_jsonl(base / "research/events.jsonl")),
        **{key: prior[key] for key in ("registration_attempts_used", "experimental_fit_seconds", "auxiliary_fit_seconds_conservative", "fit_seconds_charged")})
    atomic_write_json(base / program.CONTINUATION_CONTRACT, contract)
    auth = load_json(project_root() / program.CONTINUATION_AUTHORITY)
    auth["program_contract_sha256"] = sha256_file(base / program.CONTINUATION_CONTRACT)
    atomic_write_json(base / program.CONTINUATION_AUTHORITY, auth)
    study_path = contract["first_study_path"]
    study = load_json(project_root() / study_path)
    study.update(program_contract_sha256=sha256_file(base / program.CONTINUATION_CONTRACT), study_deadline_at="2099-01-01T00:00:00Z")
    atomic_write_json(base / study_path, study)
    config = base / "config/research.toml"
    config.write_text(config.read_text(encoding="utf-8").replace(program.FIRST_STUDY, study_path), encoding="utf-8")
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_continuation_authorized", "program_id": contract["id"],
        "authority_sha256": sha256_file(base / program.CONTINUATION_AUTHORITY), "contract_sha256": sha256_file(base / program.CONTINUATION_CONTRACT)})
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_study_frozen", "program_id": contract["id"],
        "study_path": study_path, "study_sha256": sha256_file(base / study_path)})
    return base


def test_continuation_keeps_closed_tickets_and_compute(tmp_path):
    base = continuation_fixture(tmp_path)
    value = program.status(base)
    assert value["prior_program_closed"] and not value["program_closed"] and not value["program_terminal"]
    assert value["registration_attempts_used"] == 3 and value["registration_attempts_cap"] == 20
    assert value["continuation_registration_attempts_used"] == 0 and value["continuation_registration_attempts_cap"] == 17
    assert value["fit_seconds_charged"] == 1439 and value["fit_seconds_remaining"] == 69344
    assert value["fit_seconds_cap"] == 1439 + 69344
    assert program._status_for(base, study_path=program.FIRST_STUDY)["program_closed"]
    before = (base / "research/events.jsonl").read_bytes()
    with pytest.raises(ValueError, match="Preparation-only"):
        program.create_plan(base)
    assert (base / "research/events.jsonl").read_bytes() == before
    assert not value["scoring_authorized"]


@pytest.mark.parametrize("path", [program.AUTHORITY, program.CONTRACT, program.FIRST_STUDY, "research/results/prior.json"])
def test_changed_old_evidence_fails_closed(tmp_path, path):
    base = continuation_fixture(tmp_path)
    with (base / path).open("a", encoding="utf-8") as handle:
        handle.write("\n")
    with pytest.raises(ValueError, match="carry-forward"):
        program.status(base)


def test_old_event_append_and_count_reset_are_rejected(tmp_path):
    base = continuation_fixture(tmp_path)
    path = base / program.CONTINUATION_CONTRACT
    contract = load_json(path)
    contract["carry_forward"]["registration_attempts_used"] = 0
    atomic_write_json(path, contract)
    with pytest.raises(ValueError, match="counts"):
        program.status(base)
    contract["carry_forward"]["registration_attempts_used"] = 3
    atomic_write_json(path, contract)
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_aux_fit_charged", "program_id": "MUC03-AUTONOMOUS-20261004-V1",
        "charge_id": "hidden-old-charge", "seconds": 1})
    with pytest.raises(ValueError, match="carry-forward"):
        program.status(base)


def test_auxiliary_reservation_is_counted_before_charge_and_failures_cost_time(tmp_path):
    base = continuation_fixture(tmp_path)
    program.auxiliary_reserve(base, "failed-fixture-tests", 600)
    value = program.status(base)
    assert value["continuation_compute_seconds_charged"] == 600
    assert value["fit_seconds_remaining"] == 69344 - 600
    program.auxiliary_charge(base, "failed-fixture-tests", 13)
    assert program.status(base)["fit_seconds_charged"] == 1439 + 13
    with pytest.raises(ValueError, match="Repeated"):
        program.auxiliary_charge(base, "failed-fixture-tests", 13)
    with pytest.raises(ValueError, match="Insufficient"):
        program.auxiliary_reserve(base, "overspend", 69344)


def test_preparation_completion_is_bound_and_does_not_close_program(tmp_path):
    base = continuation_fixture(tmp_path)
    value = program.status(base)
    receipt = base / "research/laboratory/preparation-complete.json"
    atomic_write_json(receipt, {"status": "complete", "scoring": False})
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_preparation_completed", "program_id": value["id"],
        "study_path": value["study_path"], "study_sha256": sha256_file(base / value["study_path"]),
        "receipt_path": receipt.relative_to(base).as_posix(), "receipt_sha256": sha256_file(receipt)})
    completed = program.status(base)
    assert completed["study_terminal"] and not completed["program_terminal"] and not completed["scoring_authorized"]
    receipt.write_text('{}', encoding="utf-8")
    with pytest.raises(ValueError, match="completion receipt"):
        program.status(base)


def test_one_failed_recipe_does_not_close_the_new_program(tmp_path, monkeypatch):
    from nextai_autoresearch import gates
    base = continuation_fixture(tmp_path)
    old_path = load_json(base / program.CONTINUATION_CONTRACT)["first_study_path"]
    study_path = "research/plans/new-reference.json"
    study = load_json(base / program.FIRST_STUDY)
    study.update(stage="reference_and_alternatives", program_contract_sha256=sha256_file(base / program.CONTINUATION_CONTRACT))
    atomic_write_json(base / study_path, study)
    config = base / "config/research.toml"
    config.write_text(config.read_text(encoding="utf-8").replace(old_path, study_path), encoding="utf-8")
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_study_frozen", "program_id": "NEXTAI-CONTINUATION-20261004-V1",
        "study_path": study_path, "study_sha256": sha256_file(base / study_path)})
    monkeypatch.setattr(gates, "ensure_can_create_plan", lambda _: (_ for _ in ()).throw(ValueError("new fixture gate failure")))
    with pytest.raises(ValueError, match="fixture gate"):
        program.create_plan(base)
    value = program.status(base)
    assert value["registration_attempts_used"] == 4 and value["continuation_registration_attempts_used"] == 1
    assert value["study_terminal"] and not value["program_terminal"]
    with pytest.raises(ValueError, match="consumed"):
        program.create_plan(base)
    assert program.status(base)["registration_attempts_used"] == 4


def test_last_paid_continuation_ticket_can_run_without_a_free_extra_ticket(tmp_path, monkeypatch):
    from nextai_autoresearch import baseline_semantics, gates, integrity
    base = continuation_fixture(tmp_path)
    shutil.copytree(project_root() / "schemas", base / "schemas")
    contract = load_json(base / program.CONTINUATION_CONTRACT)
    stages = [stage["id"] for stage in contract["stages"] for _ in range(stage["registration_cap"])]
    current_path = "research/plans/final-paid-reference.json"
    for ticket, stage in enumerate(stages, 1):
        path = current_path if ticket == 17 else f"research/plans/new-failed-ticket-{ticket}.json"
        study = load_json(base / program.FIRST_STUDY)
        study.update(stage=stage, program_contract_sha256=sha256_file(base / program.CONTINUATION_CONTRACT))
        atomic_write_json(base / path, study)
        if ticket < 17:
            append_jsonl(base / "research/events.jsonl", {"event": "research_program_registration_started", "program_id": contract["id"],
                "ticket": ticket, "study_path": path})
            append_jsonl(base / "research/events.jsonl", {"event": "research_program_registration_failed", "program_id": contract["id"],
                "ticket": ticket, "study_path": path, "error": "preserved failure"})
    config = base / "config/research.toml"
    config.write_text(config.read_text(encoding="utf-8").replace(contract["first_study_path"], current_path), encoding="utf-8")
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_study_frozen", "program_id": contract["id"],
        "study_path": current_path, "study_sha256": sha256_file(base / current_path)})
    receipt = base / "research/laboratory/ready.json"
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_study_ready", "program_id": contract["id"],
        "study_path": current_path, "study_sha256": sha256_file(base / current_path),
        "receipt_path": receipt.relative_to(base).as_posix(), "receipt_sha256": sha256_file(receipt)})
    manifest = base / "research/eval_manifest.json"
    atomic_write_json(manifest, {"evaluator_sha256": "0" * 64})
    monkeypatch.setattr(gates, "ensure_can_create_plan", lambda _: None)
    monkeypatch.setattr(integrity, "manifest_path", lambda _: manifest)
    monkeypatch.setattr(baseline_semantics, "verify_preflight_certificate", lambda _: {})
    monkeypatch.setattr(baseline_semantics, "verify_required_baselines", lambda *a, **k: {})
    program.create_plan(base)
    value = program.status(base)
    assert value["registration_attempts_used"] == 20 and value["continuation_registration_attempts_used"] == 17
    assert value["paid_run_pending"] and value["scoring_authorized"] and not value["program_terminal"]
    assert value["pending_fit_reservation_seconds"] == 3500
    with pytest.raises(ValueError, match="exhausted"):
        program.create_plan(base)
