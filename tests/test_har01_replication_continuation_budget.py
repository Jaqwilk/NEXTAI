"""Exact continuation wallet fixtures; no native acquisition or model fitting."""
from copy import deepcopy
import shutil

import pytest

from nextai_autoresearch import research_program as program
from nextai_autoresearch.utils import atomic_write_json, load_json, project_root, sha256_file


@pytest.fixture
def owned(tmp_path):
    scopes = [(program.HAR_REPLICATION_STUDY, program.HAR_REPLICATION_SHA256,
               program.HAR_PREPARATION_AUTHORITY, program.HAR_PREPARATION_SHA256, program.HAR_OWN_AUXILIARY_IDS, 1200),
              (program.HAR_IMPORT_EXIT_STUDY, program.HAR_IMPORT_EXIT_SHA256,
               program.HAR_IMPORT_EXIT_AUTHORITY, program.HAR_IMPORT_EXIT_AUTHORITY_SHA256, (program.HAR_IMPORT_EXIT_AUXILIARY_ID,), 600),
              (program.HAR_LABEL_GUARD_STUDY, program.HAR_LABEL_GUARD_SHA256,
               program.HAR_LABEL_GUARD_AUTHORITY, program.HAR_LABEL_GUARD_AUTHORITY_SHA256, (program.HAR_LABEL_GUARD_AUXILIARY_ID,), 600),
              (program.HAR_PROCESS_LAUNCH_STUDY, program.HAR_PROCESS_LAUNCH_SHA256,
               program.HAR_PROCESS_LAUNCH_AUTHORITY, program.HAR_PROCESS_LAUNCH_AUTHORITY_SHA256, (program.HAR_PROCESS_LAUNCH_AUXILIARY_ID,), 300),
              (program.HAR_CONTINUATION_STUDY, program.HAR_CONTINUATION_SHA256,
               program.HAR_CONTINUATION_AUTHORITY, program.HAR_CONTINUATION_AUTHORITY_SHA256, ("HAR01-REPLICATION-preparation-V2",), 600)]
    events = []
    for index, (study, digest, authority, authority_digest, identities, cap) in enumerate(scopes):
        for path in (study, authority):
            destination = tmp_path / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(project_root() / path, destination)
        binding = {"program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1", "study_path": study,
                   "study_sha256": digest, "authority_path": authority, "authority_sha256": authority_digest}
        events.append({**binding, "event": "research_program_scoped_preparation_authorized", "human_authorized": True,
                       "stage_slot": 0, "cap": cap, "whole_stage_cap": 6000})
        for identity in identities:
            events.append({**binding, "event": "research_program_aux_fit_reserved", "charge_id": identity, "seconds_cap": cap})
            if index < 4:
                events.append({**binding, "event": "research_program_aux_fit_charged", "charge_id": identity, "seconds": cap})
    return tmp_path, events, binding


def test_exact_new_credit_preserves_prior3900_and_remaining_slot(owned):
    base, events, binding = owned
    assert program._har_process_launch_auxiliary(base, events)[0] == 3900
    total, actual = program._har_continuation_auxiliary(base, events)
    assert total == 4500 and actual == binding and total - 3900 == 600
    _, protected = program._transfer_reserves({"independent_replication": 0, "frozen_fresh_final": 0, "prototype_evaluation": 0})
    assert protected - total == 42500
    events.append({**binding, "event": "research_program_aux_fit_reserved", "charge_id": "HAR01-REPLICATION-controller-V2", "seconds_cap": 450})
    assert program._har_continuation_auxiliary(base, events)[0] == 4950
    assert protected - 4950 == 42050
    assert program._transfer_reserves({"independent_replication": 1, "frozen_fresh_final": 0, "prototype_evaluation": 0}) == (6, 41000)


def test_missing_changed_foreign_or_prefix_binding_is_rejected(owned):
    base, events, _ = owned
    for field, value in (("study_sha256", "0" * 64), ("authority_sha256", "0" * 64),
                         ("program_id", "foreign"), ("study_path", "foreign.json"),
                         ("charge_id", "HAR01-REPLICATION-prefix-V2")):
        wrong = deepcopy(events)
        wrong[-1][field] = value
        with pytest.raises(ValueError):
            program._har_continuation_auxiliary(base, wrong)
    wrong = deepcopy(events)
    del wrong[-1]["study_sha256"]
    with pytest.raises(ValueError):
        program._har_continuation_auxiliary(base, wrong)
    with pytest.raises(ValueError):
        program._har_continuation_auxiliary(base, events[:-2] + events[-1:])
    path = base / program.HAR_CONTINUATION_STUDY
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="hash"):
        program._har_continuation_auxiliary(base, events)


def test_duplicate_authority_reservation_or_charge_is_rejected(owned):
    base, events, binding = owned
    charge = {**binding, "event": "research_program_aux_fit_charged", "charge_id": "HAR01-REPLICATION-preparation-V2", "seconds": 600}
    for wrong in (events + [deepcopy(events[-2])], events + [deepcopy(events[-1])], events + [charge, deepcopy(charge)]):
        with pytest.raises(ValueError):
            program._har_continuation_auxiliary(base, wrong)


def test_nonfinite_boolean_wrong_caps_and_refund_are_rejected(owned):
    base, events, binding = owned
    for amount in (True, float("nan"), float("inf"), -1, 599, 601):
        wrong = deepcopy(events)
        wrong[-1]["seconds_cap"] = amount
        with pytest.raises(ValueError):
            program._har_continuation_auxiliary(base, wrong)
        wrong = deepcopy(events)
        wrong.append({**binding, "event": "research_program_aux_fit_charged", "charge_id": "HAR01-REPLICATION-preparation-V2", "seconds": amount})
        with pytest.raises(ValueError):
            program._har_continuation_auxiliary(base, wrong)
    for amount in (True, float("nan"), -1, 451, 600):
        with pytest.raises(ValueError):
            program._har_continuation_auxiliary(base, events + [{**binding, "event": "research_program_aux_fit_reserved",
                "charge_id": "HAR01-REPLICATION-controller-V2", "seconds_cap": amount}])


def test_every_prior_consumed_allocation_remains_settled(owned):
    base, events, _ = owned
    for index, event in enumerate(events):
        if event["event"] != "research_program_aux_fit_charged":
            continue
        wrong = deepcopy(events)
        wrong[index]["seconds"] -= 1
        with pytest.raises(ValueError):
            program._har_continuation_auxiliary(base, wrong)
        with pytest.raises(ValueError):
            program._har_continuation_auxiliary(base, events[:index] + events[index + 1:])


def test_registration_guard_credits_only_new_auxiliary_at_exact_boundary(owned):
    base, _, _ = owned
    study = load_json(base / program.HAR_CONTINUATION_STUDY)
    value = {"study_path": program.HAR_CONTINUATION_STUDY, "stage_b_registration_attempts_used": 1,
             "stage_registration_attempts": {"independent_replication": 0, "frozen_fresh_final": 0, "prototype_evaluation": 0},
             "unreserved_fit_seconds_remaining": 42500, "study_owned_auxiliary_seconds": 600}
    program._check_transfer_study_reserve(value, study)
    value["unreserved_fit_seconds_remaining"] -= .01
    with pytest.raises(ValueError, match="protected"):
        program._check_transfer_study_reserve(value, study)
    value.update(unreserved_fit_seconds_remaining=42050, study_owned_auxiliary_seconds=1050)
    program._check_transfer_study_reserve(value, study)
    value["study_owned_auxiliary_seconds"] = 4500
    with pytest.raises(ValueError, match="credit"):
        program._check_transfer_study_reserve(value, study)


def test_failure_controller_reservation_preserves_worker_and_other_tickets(owned, monkeypatch):
    base, events, _ = owned
    value = {"id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1", "study_path": program.HAR_CONTINUATION_STUDY,
             "program_closed": False, "stage_b_registration_attempts_used": 1, "unreserved_fit_seconds_remaining": 42530.4497598,
             "protected_future_compute_seconds": 42500, "study_owned_auxiliary_seconds": 600,
             "stage_registration_attempts": {"independent_replication": 0, "frozen_fresh_final": 0, "prototype_evaluation": 0}}
    monkeypatch.setattr(program, "status", lambda _: value)
    monkeypatch.setattr(program, "read_jsonl", lambda _: events)
    monkeypatch.setattr(program, "append_jsonl", lambda _, event: events.append(event))
    program.auxiliary_reserve(base, "HAR01-REPLICATION-controller-V2", 450)
    assert program._har_continuation_auxiliary(base, events)[0] == 4950
    program.auxiliary_charge(base, "HAR01-REPLICATION-controller-V2", 450)
    with pytest.raises(ValueError, match="Repeated"):
        program.auxiliary_charge(base, "HAR01-REPLICATION-controller-V2", 450)


def test_exact_v3_scope_keeps_parent_scientific_recipe(owned):
    base, _, _ = owned
    study = load_json(base / program.HAR_CONTINUATION_STUDY)
    parent = load_json(project_root() / study["parent_study_path"])
    scope = program._study_scope(study)
    for field in ("roles", "recipe", "diagnostics", "diagnosis_gates", "reference_gates"):
        assert scope[field] == parent[field]
    assert scope["fit_seconds_total_cap"] == 1050
    study["id"] = "foreign"
    with pytest.raises(ValueError, match="exact"):
        program._study_scope(study)


def test_exact1050_worker_recovery_never_discounts_or_double_counts(owned):
    base, _, binding = owned
    identity = "EXP-20990101-0001"
    plan = {"experiment_id": identity, "research_program_protocol": binding}
    receipt = {k: v for k, v in binding.items() if k in {"program_id", "study_path", "study_sha256"}}
    receipt.update(experiment_id=identity, worker_charge_total=1050)
    path = "research/reviews/continuation-recovery-fixture.json"
    atomic_write_json(base / path, receipt)
    event = {**receipt, "event": "research_program_worker_charge_recovery", "receipt_path": path, "receipt_sha256": sha256_file(base / path)}
    assert program._study_worker_recovery(base, [event], plan, 200) == 850
    assert program._study_worker_recovery(base, [event], plan, 1100) == 0
    with pytest.raises(ValueError, match="repeated"):
        program._study_worker_recovery(base, [event, event], plan, 200)
    for field, wrong in (("study_sha256", "0" * 64), ("program_id", "foreign"), ("receipt_sha256", "0" * 64),
                         ("worker_charge_total", True), ("worker_charge_total", float("nan")), ("worker_charge_total", 1051)):
        changed = deepcopy(event)
        changed[field] = wrong
        with pytest.raises(ValueError):
            program._study_worker_recovery(base, [changed], plan, 200)
