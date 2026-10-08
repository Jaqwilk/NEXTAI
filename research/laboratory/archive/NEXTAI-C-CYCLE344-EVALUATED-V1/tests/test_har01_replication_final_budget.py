"""Final bounded wallet fixtures only; no native data or fit."""
from copy import deepcopy
import shutil

import pytest

from nextai_autoresearch import research_program as p
from nextai_autoresearch.utils import atomic_write_json, load_json, project_root, sha256_file


@pytest.fixture
def owned(tmp_path):
    rows = [(p.HAR_REPLICATION_STUDY, p.HAR_REPLICATION_SHA256, p.HAR_PREPARATION_AUTHORITY, p.HAR_PREPARATION_SHA256, dict.fromkeys(p.HAR_OWN_AUXILIARY_IDS, 1200)),
            (p.HAR_IMPORT_EXIT_STUDY, p.HAR_IMPORT_EXIT_SHA256, p.HAR_IMPORT_EXIT_AUTHORITY, p.HAR_IMPORT_EXIT_AUTHORITY_SHA256, {p.HAR_IMPORT_EXIT_AUXILIARY_ID: 600}),
            (p.HAR_LABEL_GUARD_STUDY, p.HAR_LABEL_GUARD_SHA256, p.HAR_LABEL_GUARD_AUTHORITY, p.HAR_LABEL_GUARD_AUTHORITY_SHA256, {p.HAR_LABEL_GUARD_AUXILIARY_ID: 600}),
            (p.HAR_PROCESS_LAUNCH_STUDY, p.HAR_PROCESS_LAUNCH_SHA256, p.HAR_PROCESS_LAUNCH_AUTHORITY, p.HAR_PROCESS_LAUNCH_AUTHORITY_SHA256, {p.HAR_PROCESS_LAUNCH_AUXILIARY_ID: 300}),
            (p.HAR_CONTINUATION_STUDY, p.HAR_CONTINUATION_SHA256, p.HAR_CONTINUATION_AUTHORITY, p.HAR_CONTINUATION_AUTHORITY_SHA256, p.HAR_CONTINUATION_AUXILIARY_CAPS),
            (p.HAR_FINAL_STUDY, p.HAR_FINAL_SHA256, p.HAR_FINAL_AUTHORITY, p.HAR_FINAL_AUTHORITY_SHA256, {"HAR01-REPLICATION-preparation-V3": 300})]
    events = []
    for index, (study, digest, authority, auth_digest, caps) in enumerate(rows):
        for path in (study, authority):
            dest = tmp_path / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(project_root() / path, dest)
        binding = {"program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1", "study_path": study,
                   "study_sha256": digest, "authority_path": authority, "authority_sha256": auth_digest}
        events.append({**binding, "event": "research_program_scoped_preparation_authorized", "human_authorized": True,
                       "stage_slot": 0, "cap": next(iter(caps.values())), "whole_stage_cap": 6000})
        for identity, cap in caps.items():
            events.append({**binding, "event": "research_program_aux_fit_reserved", "charge_id": identity, "seconds_cap": cap})
            if index < 5:
                events.append({**binding, "event": "research_program_aux_fit_charged", "charge_id": identity, "seconds": cap})
    return tmp_path, events, binding


def test_exact_credit_retains4950_and_protects_other41000(owned):
    base, events, binding = owned
    assert p._har_continuation_auxiliary(base, events)[0] == 4950
    total, actual = p._har_final_auxiliary(base, events)
    assert total == 5250 and actual == binding and total - 4950 == 300
    assert 47000 - total == 41750
    events.append({**binding, "event": "research_program_aux_fit_reserved", "charge_id": "HAR01-REPLICATION-controller-V3", "seconds_cap": 250})
    assert p._har_final_auxiliary(base, events)[0] == 5500 and 47000 - 5500 == 41500
    assert p._transfer_reserves({"independent_replication": 1, "frozen_fresh_final": 0, "prototype_evaluation": 0}) == (6, 41000)


def test_foreign_missing_changed_or_prefix_bindings_rejected(owned):
    base, events, _ = owned
    for key, value in (("study_sha256", "0" * 64), ("authority_sha256", "0" * 64), ("program_id", "foreign"),
                       ("study_path", "foreign.json"), ("charge_id", "HAR01-REPLICATION-prefix-V3")):
        wrong = deepcopy(events)
        wrong[-1][key] = value
        with pytest.raises(ValueError):
            p._har_final_auxiliary(base, wrong)
    wrong = deepcopy(events)
    del wrong[-1]["study_sha256"]
    with pytest.raises(ValueError):
        p._har_final_auxiliary(base, wrong)
    with pytest.raises(ValueError):
        p._har_final_auxiliary(base, events[:-2] + events[-1:])
    path = base / p.HAR_FINAL_STUDY
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="hash"):
        p._har_final_auxiliary(base, events)


def test_duplicate_authority_reservation_and_charge_rejected(owned):
    base, events, binding = owned
    charge = {**binding, "event": "research_program_aux_fit_charged", "charge_id": "HAR01-REPLICATION-preparation-V3", "seconds": 300}
    for wrong in (events + [deepcopy(events[-2])], events + [deepcopy(events[-1])], events + [charge, deepcopy(charge)]):
        with pytest.raises(ValueError):
            p._har_final_auxiliary(base, wrong)


def test_invalid_caps_and_partial_refund_rejected(owned):
    base, events, binding = owned
    for amount in (True, float("nan"), float("inf"), -1, 299, 301):
        wrong = deepcopy(events)
        wrong[-1]["seconds_cap"] = amount
        with pytest.raises(ValueError):
            p._har_final_auxiliary(base, wrong)
        with pytest.raises(ValueError):
            p._har_final_auxiliary(base, events + [{**binding, "event": "research_program_aux_fit_charged", "charge_id": "HAR01-REPLICATION-preparation-V3", "seconds": amount}])
    for amount in (True, float("nan"), -1, 251, 300):
        with pytest.raises(ValueError):
            p._har_final_auxiliary(base, events + [{**binding, "event": "research_program_aux_fit_reserved", "charge_id": "HAR01-REPLICATION-controller-V3", "seconds_cap": amount}])


def test_each_prior_allocation_must_remain_settled(owned):
    base, events, _ = owned
    for index, event in enumerate(events):
        if event["event"] == "research_program_aux_fit_charged":
            wrong = deepcopy(events)
            wrong[index]["seconds"] -= 1
            with pytest.raises(ValueError):
                p._har_final_auxiliary(base, wrong)
            with pytest.raises(ValueError):
                p._har_final_auxiliary(base, events[:index] + events[index + 1:])


def test_registration_guard_uses_only_new550_at_exact_boundary(owned):
    base, _, _ = owned
    study = load_json(base / p.HAR_FINAL_STUDY)
    value = {"study_path": p.HAR_FINAL_STUDY, "stage_b_registration_attempts_used": 1,
             "stage_registration_attempts": {"independent_replication": 0, "frozen_fresh_final": 0, "prototype_evaluation": 0},
             "unreserved_fit_seconds_remaining": 41750, "study_owned_auxiliary_seconds": 300}
    p._check_transfer_study_reserve(value, study)
    value["unreserved_fit_seconds_remaining"] -= .01
    with pytest.raises(ValueError, match="protected"):
        p._check_transfer_study_reserve(value, study)
    value.update(unreserved_fit_seconds_remaining=41500, study_owned_auxiliary_seconds=550)
    p._check_transfer_study_reserve(value, study)
    value["study_owned_auxiliary_seconds"] = 5250
    with pytest.raises(ValueError, match="credit"):
        p._check_transfer_study_reserve(value, study)


def test_failure_controller_reservation_keeps_worker500(owned, monkeypatch):
    base, events, _ = owned
    value = {"id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1", "study_path": p.HAR_FINAL_STUDY, "program_closed": False,
             "stage_b_registration_attempts_used": 1, "unreserved_fit_seconds_remaining": 41780.4497598,
             "protected_future_compute_seconds": 41750, "study_owned_auxiliary_seconds": 300,
             "stage_registration_attempts": {"independent_replication": 0, "frozen_fresh_final": 0, "prototype_evaluation": 0}}
    monkeypatch.setattr(p, "status", lambda _: value)
    monkeypatch.setattr(p, "read_jsonl", lambda _: events)
    monkeypatch.setattr(p, "append_jsonl", lambda _, event: events.append(event))
    p.auxiliary_reserve(base, "HAR01-REPLICATION-controller-V3", 250)
    p.auxiliary_charge(base, "HAR01-REPLICATION-controller-V3", 250)
    assert p._har_final_auxiliary(base, events)[0] == 5500
    with pytest.raises(ValueError, match="Repeated"):
        p.auxiliary_charge(base, "HAR01-REPLICATION-controller-V3", 250)


def test_exact_v4_retains_parent_scientific_recipe(owned):
    base, _, _ = owned
    study = load_json(base / p.HAR_FINAL_STUDY)
    parent = load_json(project_root() / study["parent_study_path"])
    scope = p._study_scope(study)
    for field in ("roles", "recipe", "diagnostics", "diagnosis_gates", "reference_gates"):
        assert scope[field] == parent[field]
    assert scope["fit_seconds_total_cap"] == 500
    study["id"] = "foreign"
    with pytest.raises(ValueError, match="exact"):
        p._study_scope(study)


def test_exact500_worker_recovery_no_discount_or_double_count(owned):
    base, _, binding = owned
    identity = "EXP-20990101-0001"
    plan = {"experiment_id": identity, "research_program_protocol": binding}
    receipt = {k: v for k, v in binding.items() if k in {"program_id", "study_path", "study_sha256"}}
    receipt.update(experiment_id=identity, worker_charge_total=500)
    path = "research/reviews/final-recovery-fixture.json"
    atomic_write_json(base / path, receipt)
    event = {**receipt, "event": "research_program_worker_charge_recovery", "receipt_path": path, "receipt_sha256": sha256_file(base / path)}
    assert p._final_study_worker_recovery(base, [event], plan, 200) == 300
    assert p._final_study_worker_recovery(base, [event], plan, 550) == 0
    with pytest.raises(ValueError, match="repeated"):
        p._final_study_worker_recovery(base, [event, event], plan, 200)
    for key, value in (("study_sha256", "0" * 64), ("program_id", "foreign"), ("receipt_sha256", "0" * 64),
                       ("worker_charge_total", True), ("worker_charge_total", float("nan")), ("worker_charge_total", 501)):
        wrong = deepcopy(event)
        wrong[key] = value
        with pytest.raises(ValueError):
            p._final_study_worker_recovery(base, [wrong], plan, 200)
