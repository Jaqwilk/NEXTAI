"""Closed budgets stay consumed; B cannot silently spend its final-study reserve."""
import shutil

import pytest

from nextai_autoresearch import research_program as program
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.utils import atomic_write_json, load_json, project_root, sha256_file, sha256_json
from test_research_continuation import continuation_fixture


def _select_study(base, path, study):
    config = base / "config/research.toml"
    import re
    config.write_text(re.sub(r'study_path = "[^"]+"', f'study_path = "{path}"',
                             config.read_text(encoding="utf-8")), encoding="utf-8")
    atomic_write_json(base / path, study)
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_study_frozen",
        "program_id": study["program_id"], "study_path": path, "study_sha256": sha256_file(base / path)})


def transfer_fixture(tmp_path, *, activate=True, leave_A_reservation=False):
    base = continuation_fixture(tmp_path)
    a_path = "research/plans/A-closed-reference.json"
    study = load_json(base / program.FIRST_STUDY)
    study.update(program_id="NEXTAI-CONTINUATION-20261004-V1", stage="reference_and_alternatives",
                 program_contract_sha256=sha256_file(base / program.CONTINUATION_CONTRACT))
    _select_study(base, a_path, study)
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_registration_started",
        "program_id": study["program_id"], "study_path": a_path, "ticket": 1})
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_registration_failed",
        "program_id": study["program_id"], "study_path": a_path, "ticket": 1, "error": "preserved A failure"})
    program.auxiliary_reserve(base, "A-failed-tests", 500)
    if not leave_A_reservation:
        program.auxiliary_charge(base, "A-failed-tests", 149)
    receipt_path = "research/laboratory/A-completion.json"
    atomic_write_json(base / receipt_path, {"status": "complete", "program_budget": program.status(base)})
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_completed",
        "program_id": study["program_id"], "receipt_path": receipt_path,
        "receipt_sha256": sha256_file(base / receipt_path)})
    old = program.status(base)
    source_path = base / program.TRANSFER_SOURCE_AUTHORITY
    source_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(project_root() / program.TRANSFER_SOURCE_AUTHORITY, source_path)
    source = load_json(source_path)
    artifact = "research/laboratory/source-state.json"
    atomic_write_json(base / artifact, {"fixture_only": True, "not_a_research_result": True})
    result = "research/results/prior.json"
    bound = [program.CONTINUATION_AUTHORITY, program.CONTINUATION_CONTRACT,
             program.TRANSFER_SOURCE_AUTHORITY, a_path, receipt_path, artifact, result]
    contract = {"id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1",
        "registration_attempts_cap": 12, "fit_seconds_total_cap": 72000,
        "prior_budgets_reset": False, "unspent_A_credit_added": False, "no_retry": True,
        "one_new_experiment_per_cycle": True, "schedule_change_authorized": False,
        "wt_files_8_9_access_authorized": False, "external_model_api_authorized": False,
        "stages": [{"id": key, "registration_cap": value} for key, value in program.TRANSFER_STAGES.items()],
        "protected_allocations": program.TRANSFER_RESERVES,
        "deliverables": source["deliverables"],
        "economic_claim_gates": load_json(base / program.CONTINUATION_CONTRACT)["economic_claim_gates"],
        "source_result_path": result, "source_state_publication_path": artifact,
        "carry_forward": {"program_id": old["id"], "authority_path": program.CONTINUATION_AUTHORITY,
            "contract_path": program.CONTINUATION_CONTRACT, "terminal_study_path": a_path,
            "completion_receipt_path": receipt_path,
            "document_sha256": {p: sha256_file(base / p) for p in bound},
            "program_events_sha256": sha256_json([e for e in read_jsonl(base / "research/events.jsonl")
                                                  if e.get("program_id") == old["id"]]),
            **{k: old[k] for k in ("registration_attempts_used", "experimental_fit_seconds",
                "auxiliary_fit_seconds_conservative", "fit_seconds_charged")},
            "stage_a_accounting": program._status_for(base, authority_path=program.CONTINUATION_AUTHORITY,
                contract_path=program.CONTINUATION_CONTRACT, study_path=a_path, expected_caps=(17, 69344),
                authorization_event="research_program_continuation_authorized")}}
    atomic_write_json(base / program.TRANSFER_CONTRACT, contract)
    authority = {"id": contract["id"], "program_contract_path": program.TRANSFER_CONTRACT,
        "program_contract_sha256": sha256_file(base / program.TRANSFER_CONTRACT),
        "registration_attempts_cap": 12, "fit_seconds_total_cap": 72000,
        "source_authority_path": program.TRANSFER_SOURCE_AUTHORITY,
        "source_authority_sha256": sha256_file(source_path)}
    atomic_write_json(base / program.TRANSFER_AUTHORITY, authority)
    if activate:
        path = "research/plans/B-preparation.json"
        prep = {"program_id": contract["id"], "cohort": "mutable_contact_ledger_v2",
            "program_contract_sha256": sha256_file(base / program.TRANSFER_CONTRACT),
            "study_kind": "preparation_only", "stage": "task_design",
            "registration_attempts_for_this_study_cap": 0, "study_deadline_at": "2099-01-01T00:00:00Z"}
        _select_study(base, path, prep)
        append_jsonl(base / "research/events.jsonl", {"event": "research_program_transfer_prototype_authorized",
            "program_id": contract["id"], "authority_sha256": sha256_file(base / program.TRANSFER_AUTHORITY),
            "contract_sha256": sha256_file(base / program.TRANSFER_CONTRACT)})
    return base


def _rebind_B(base, contract):
    atomic_write_json(base / program.TRANSFER_CONTRACT, contract)
    auth = load_json(base / program.TRANSFER_AUTHORITY)
    auth["program_contract_sha256"] = sha256_file(base / program.TRANSFER_CONTRACT)
    atomic_write_json(base / program.TRANSFER_AUTHORITY, auth)
    events = read_jsonl(base / "research/events.jsonl")
    for event in events:
        if event.get("event") == "research_program_transfer_prototype_authorized":
            event.update(authority_sha256=sha256_file(base / program.TRANSFER_AUTHORITY),
                         contract_sha256=sha256_file(base / program.TRANSFER_CONTRACT))
    (base / "research/events.jsonl").write_text("".join(__import__('json').dumps(e)+"\n" for e in events), encoding="utf-8")


def _paid_study(base, stage="transfer_family_1_screen", path="research/plans/B-screen.json", cap=3500):
    study = load_json(base / program.FIRST_STUDY)
    study.update(program_id="NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1", stage=stage,
                 program_contract_sha256=sha256_file(base / program.TRANSFER_CONTRACT))
    study["resources"].update(fit_seconds_study_cap=cap, auxiliary_test_seconds_cap=100)
    _select_study(base, path, study)
    return study


def test_copied_B_document_does_not_activate_or_reopen_A(tmp_path):
    base = transfer_fixture(tmp_path, activate=False)
    value = program.status(base)
    assert value["id"] == "NEXTAI-CONTINUATION-20261004-V1" and value["program_closed"]
    assert "stage_b_registration_attempts_used" not in value


def test_B_keeps_both_closed_budgets_and_exact_new_wallet(tmp_path):
    base = transfer_fixture(tmp_path)
    value = program.status(base)
    assert value["prior_program_closed"] and value["stage_a_accounting"]["program_closed"]
    assert value["registration_attempts_used"] == 4 and value["registration_attempts_cap"] == 16
    assert value["fit_seconds_charged"] == 1588 and value["fit_seconds_remaining"] == 72000
    assert value["stage_b_registration_attempts_used"] == 0 and value["stage_b_compute_seconds_charged"] == 0
    assert value["protected_future_registration_attempts"] == 7
    assert value["protected_future_compute_seconds"] == 47000
    before = (base / "research/events.jsonl").read_bytes()
    with pytest.raises(ValueError, match="Preparation-only"):
        program.create_plan(base)
    assert (base / "research/events.jsonl").read_bytes() == before
    assert not value["scoring_authorized"]


@pytest.mark.parametrize("path", [program.CONTINUATION_AUTHORITY, program.CONTINUATION_CONTRACT,
    program.TRANSFER_SOURCE_AUTHORITY, "research/laboratory/A-completion.json",
    "research/laboratory/source-state.json", "research/results/prior.json"])
def test_changed_A_or_source_evidence_fails_closed(tmp_path, path):
    base = transfer_fixture(tmp_path)
    with (base / path).open("a", encoding="utf-8") as handle:
        handle.write("\n")
    with pytest.raises(ValueError, match="carry-forward|authority"):
        program.status(base)


@pytest.mark.parametrize("change", ["append_A_event", "missing_A_end", "duplicate_A_end", "changed_A_count", "changed_A_raw_count"])
def test_closed_A_event_or_count_manipulation_is_rejected(tmp_path, change):
    base = transfer_fixture(tmp_path)
    contract = load_json(base / program.TRANSFER_CONTRACT)
    if change == "append_A_event":
        append_jsonl(base / "research/events.jsonl", {"event": "research_program_cycle_completed",
            "program_id": "NEXTAI-CONTINUATION-20261004-V1"})
    elif change == "changed_A_count":
        contract["carry_forward"]["registration_attempts_used"] = 0
        _rebind_B(base, contract)
    elif change == "changed_A_raw_count":
        contract["carry_forward"]["stage_a_accounting"]["registration_attempts_used"] = 0
        _rebind_B(base, contract)
    else:
        events = read_jsonl(base / "research/events.jsonl")
        end = next(e for e in events if e.get("event") == "research_program_completed"
                   and e.get("program_id") == "NEXTAI-CONTINUATION-20261004-V1")
        if change == "missing_A_end":
            events.remove(end)
        else:
            events.append(end)
        (base / "research/events.jsonl").write_text("".join(__import__('json').dumps(e)+"\n" for e in events), encoding="utf-8")
        contract["carry_forward"]["program_events_sha256"] = sha256_json([e for e in events
            if e.get("program_id") == "NEXTAI-CONTINUATION-20261004-V1"])
        _rebind_B(base, contract)
    with pytest.raises(ValueError, match="Closed A|counts|Stage A accounting"):
        program.status(base)


def test_unresolved_A_test_reservation_blocks_B(tmp_path):
    base = transfer_fixture(tmp_path, leave_A_reservation=True)
    with pytest.raises(ValueError, match="unresolved auxiliary"):
        program.status(base)


@pytest.mark.parametrize("field", ["unspent_A_credit_added", "prior_budgets_reset", "schedule_change_authorized"])
def test_unused_A_credit_or_forbidden_scope_cannot_be_enabled(tmp_path, field):
    base = transfer_fixture(tmp_path)
    contract = load_json(base / program.TRANSFER_CONTRACT);contract[field] = True
    _rebind_B(base, contract)
    with pytest.raises(ValueError, match="Transfer authority"):
        program.status(base)


@pytest.mark.parametrize("change", ["reserve", "deliverable", "economic_gate", "stage_cap"])
def test_rebound_contract_cannot_weaken_frozen_requirements(tmp_path, change):
    base = transfer_fixture(tmp_path)
    contract = load_json(base / program.TRANSFER_CONTRACT)
    if change == "reserve":
        contract["protected_allocations"]["frozen_fresh_final"]["seconds_per_attempt"] = 1
    elif change == "deliverable":
        contract["deliverables"]["independent_task_families"] = 1
    elif change == "economic_gate":
        contract["economic_claim_gates"]["candidate_quality_difference_simultaneous_lower_min"] = -.2
    else:
        contract["stages"][1]["registration_cap"] = 3
    _rebind_B(base, contract)
    with pytest.raises(ValueError, match="Transfer authority"):
        program.status(base)


def test_B_reservations_failures_and_no_retry_remain_paid(tmp_path, monkeypatch):
    from nextai_autoresearch import gates
    base = transfer_fixture(tmp_path)
    program.auxiliary_reserve(base, "B-tests-fail", 600)
    assert program.status(base)["stage_b_compute_seconds_charged"] == 600
    program.auxiliary_charge(base, "B-tests-fail", 17)
    assert program.status(base)["fit_seconds_charged"] == 1605
    with pytest.raises(ValueError, match="Repeated"):
        program.auxiliary_charge(base, "B-tests-fail", 17)
    _paid_study(base)
    monkeypatch.setattr(gates, "ensure_can_create_plan", lambda _: (_ for _ in ()).throw(ValueError("fixture gate")))
    with pytest.raises(ValueError, match="fixture gate"):
        program.create_plan(base)
    assert program.status(base)["stage_b_registration_attempts_used"] == 1
    assert program.status(base)["registration_attempts_used"] == 5
    with pytest.raises(ValueError, match="consumed"):
        program.create_plan(base)


def test_unprotected_auxiliary_work_cannot_take_final_funds(tmp_path):
    base = transfer_fixture(tmp_path)
    before = (base / "research/events.jsonl").read_bytes()
    with pytest.raises(ValueError, match="protected"):
        program.auxiliary_reserve(base, "steal-final", 25001)
    assert (base / "research/events.jsonl").read_bytes() == before
    program.auxiliary_reserve(base, "max-preparation", 25000)
    assert program.status(base)["fit_seconds_remaining"] == 47000


@pytest.mark.parametrize("field,value", [("registration_attempts_cap", 13), ("fit_seconds_total_cap", 72001)])
def test_expanded_B_caps_are_rejected_even_with_matching_hashes(tmp_path, field, value):
    base = transfer_fixture(tmp_path)
    contract = load_json(base / program.TRANSFER_CONTRACT);contract[field] = value
    _rebind_B(base, contract)
    auth = load_json(base / program.TRANSFER_AUTHORITY);auth[field] = value
    atomic_write_json(base / program.TRANSFER_AUTHORITY, auth)
    _rebind_B(base, contract)
    with pytest.raises(ValueError, match="Research authority"):
        program.status(base)


def test_overlarge_paid_study_is_charged_a_ticket_but_cannot_take_final_funds(tmp_path):
    base = transfer_fixture(tmp_path)
    _paid_study(base, cap=24901)
    with pytest.raises(ValueError, match="protected"):
        program.create_plan(base)
    value = program.status(base)
    assert value["stage_b_registration_attempts_used"] == 1 and value["study_terminal"]
    assert value["protected_future_compute_seconds"] == 47000


def test_last_B_paid_ticket_keeps_current_number_and_pending_run(tmp_path, monkeypatch):
    from nextai_autoresearch import baseline_semantics, gates, integrity
    base = transfer_fixture(tmp_path)
    shutil.copytree(project_root() / "schemas", base / "schemas")
    stages = [stage for stage, cap in program.TRANSFER_STAGES.items() for _ in range(cap)]
    for ticket, stage in enumerate(stages, 1):
        path = f"research/plans/B-ticket-{ticket}.json"
        _paid_study(base, stage, path)
        if ticket < 12:
            append_jsonl(base / "research/events.jsonl", {"event": "research_program_registration_started",
                "program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1", "study_path": path, "ticket": ticket})
            append_jsonl(base / "research/events.jsonl", {"event": "research_program_registration_failed",
                "program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1", "study_path": path,
                "ticket": ticket, "error": "fixture failure preserved"})
    receipt = "research/laboratory/ready.json"
    study_path = "research/plans/B-ticket-12.json"
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_study_ready",
        "program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1", "study_path": study_path,
        "study_sha256": sha256_file(base / study_path), "receipt_path": receipt,
        "receipt_sha256": sha256_file(base / receipt)})
    manifest = base / "research/eval_manifest.json"
    atomic_write_json(manifest, {"evaluator_sha256": "0" * 64})
    monkeypatch.setattr(gates, "ensure_can_create_plan", lambda _: None)
    monkeypatch.setattr(integrity, "manifest_path", lambda _: manifest)
    monkeypatch.setattr(baseline_semantics, "verify_preflight_certificate", lambda _: {})
    monkeypatch.setattr(baseline_semantics, "verify_required_baselines", lambda *a, **k: {})
    plan = load_json(program.create_plan(base))
    assert plan["research_program_protocol"]["registration_ticket"] == 12
    value = program.status(base)
    assert value["stage_b_registration_attempts_used"] == 12 and value["registration_attempts_used"] == 16
    assert value["paid_run_pending"] and not value["program_terminal"] and value["scoring_authorized"]
    assert value["pending_fit_reservation_seconds"] == 3500
    with pytest.raises(ValueError, match="exhausted"):
        program.create_plan(base)
