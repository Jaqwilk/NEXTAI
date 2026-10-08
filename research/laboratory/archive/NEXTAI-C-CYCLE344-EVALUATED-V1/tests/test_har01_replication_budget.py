"""Exact-owned allocation fixtures only; no native access or model fitting."""
from copy import deepcopy
import shutil

import pytest

from nextai_autoresearch import research_program as program
from nextai_autoresearch.utils import atomic_write_json, load_json, project_root, sha256_file


@pytest.fixture
def owned(tmp_path):
    for path in (program.HAR_REPLICATION_STUDY, program.HAR_PREPARATION_AUTHORITY):
        destination = tmp_path / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project_root() / path, destination)
    binding = {"program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1",
               "study_path": program.HAR_REPLICATION_STUDY, "study_sha256": program.HAR_REPLICATION_SHA256,
               "authority_path": program.HAR_PREPARATION_AUTHORITY, "authority_sha256": program.HAR_PREPARATION_SHA256}
    events = [{**binding, "event": "research_program_scoped_preparation_authorized",
               "human_authorized": True, "stage_slot": 0, "cap": 1200, "whole_stage_cap": 6000},
              {**binding, "event": "research_program_aux_fit_reserved",
               "charge_id": program.HAR_OWN_AUXILIARY_IDS[0], "seconds_cap": 1200}]
    return tmp_path, events, binding


def test_reserved_or_charged_credit_never_refunds_spent_history(owned):
    base, events, binding = owned
    assert program._har_replication_auxiliary(base, events)[0] == 1200
    events.append({**binding, "event": "research_program_aux_fit_charged",
                   "charge_id": program.HAR_OWN_AUXILIARY_IDS[0], "seconds": 800})
    assert program._har_replication_auxiliary(base, events)[0] == 800
    events.append({**binding, "event": "research_program_aux_fit_reserved",
                   "charge_id": program.HAR_OWN_AUXILIARY_IDS[1], "seconds_cap": 1200})
    assert program._har_replication_auxiliary(base, events)[0] == 2000


@pytest.mark.parametrize("fault", ["foreign-id", "foreign-program", "wrong-study", "wrong-study-hash",
    "missing-study", "wrong-auth-hash", "duplicate", "missing-reservation", "missing-authority",
    "duplicate-authority", "false-human", "bool-cap", "nan-cap", "infinite-cap", "negative-charge",
    "bool-charge", "excess-charge"], ids=lambda fault: fault)
def test_wrong_ownership_never_provides_credit(owned, fault):
    base, events, binding = owned
    row = events[1]
    if fault == "foreign-id":
        row["charge_id"] = "HAR01-REPLICATION-other-V1"
    elif fault == "foreign-program":
        row["program_id"] = "foreign"
    elif fault == "wrong-study":
        row["study_path"] = "research/plans/foreign.json"
    elif fault == "wrong-study-hash":
        row["study_sha256"] = "0" * 64
    elif fault == "missing-study":
        del row["study_path"]
    elif fault == "wrong-auth-hash":
        row["authority_sha256"] = "0" * 64
    elif fault == "duplicate":
        events.append(deepcopy(row))
    elif fault == "missing-reservation":
        events.pop()
    elif fault == "missing-authority":
        events.pop(0)
    elif fault == "duplicate-authority":
        events.append(deepcopy(events[0]))
    elif fault == "false-human":
        events[0]["human_authorized"] = False
    elif fault in {"bool-cap", "nan-cap", "infinite-cap"}:
        row["seconds_cap"] = {"bool-cap": True, "nan-cap": float("nan"), "infinite-cap": float("inf")}[fault]
    else:
        events.append({**binding, "event": "research_program_aux_fit_charged", "charge_id": row["charge_id"],
                       "seconds": {"negative-charge": -1, "bool-charge": True, "excess-charge": 1201}[fault]})
    with pytest.raises(ValueError):
        program._har_replication_auxiliary(base, events)


def test_prefix_only_historical_cost_is_paid_without_credit(owned):
    base, events, _ = owned
    events.append({"event": "research_program_aux_fit_reserved", "program_id": "foreign-history",
                   "charge_id": "HAR01-REPLICATION-prefix-only", "seconds_cap": 999})
    assert program._har_replication_auxiliary(base, events)[0] == 1200


def test_registration_reserve_deducts_only_remaining_own_auxiliary(owned):
    base, events, _ = owned
    study = load_json(base / program.HAR_REPLICATION_STUDY)
    value = {"study_path": program.HAR_REPLICATION_STUDY, "stage_b_registration_attempts_used": 1,
             "stage_registration_attempts": {"independent_replication": 0, "frozen_fresh_final": 0,
                                             "prototype_evaluation": 0},
             "unreserved_fit_seconds_remaining": 45830.4497598,
             "study_owned_auxiliary_seconds": program._har_replication_auxiliary(base, events)[0]}
    program._check_transfer_study_reserve(value, study)
    value["unreserved_fit_seconds_remaining"] = 45799.99
    with pytest.raises(ValueError, match="protected"):
        program._check_transfer_study_reserve(value, study)
    value["unreserved_fit_seconds_remaining"] = 45830.4497598
    value["study_owned_auxiliary_seconds"] = 0
    with pytest.raises(ValueError, match="protected"):
        program._check_transfer_study_reserve(value, study)


@pytest.mark.parametrize("amount", [True, float("nan"), float("inf"), -1],
                         ids=["boolean", "nan", "infinite", "negative"])
def test_invalid_resource_caps_are_rejected_before_reserve(owned, amount):
    base, _, _ = owned
    study = load_json(base / program.HAR_REPLICATION_STUDY)
    study["resources"]["fit_seconds_study_cap"] = amount
    value = {"study_path": program.HAR_REPLICATION_STUDY, "stage_b_registration_attempts_used": 1,
             "stage_registration_attempts": {"independent_replication": 0, "frozen_fresh_final": 0,
                                             "prototype_evaluation": 0},
             "unreserved_fit_seconds_remaining": 72000, "study_owned_auxiliary_seconds": 1200}
    with pytest.raises(ValueError, match="finite"):
        program._check_transfer_study_reserve(value, study)


def test_new_cohort_keeps_exact_parent_scientific_recipe(owned):
    base, _, _ = owned
    study = load_json(base / program.HAR_REPLICATION_STUDY)
    parent = load_json(project_root() / study["parent_study_path"])
    scope = program._study_scope(study)
    for field in ("roles", "recipe", "diagnostics", "diagnosis_gates", "reference_gates"):
        assert scope[field] == parent[field]
    assert scope["classical_baselines"] == parent["candidates"]
    assert scope["fit_seconds_total_cap"] == 3600


def test_worker_recovery_charges_only_missing_cost_without_refund(owned):
    base, _, binding = owned
    identity = "EXP-20990101-0001"
    plan = {"experiment_id": identity, "research_program_protocol": binding}
    receipt = {k: v for k, v in binding.items() if k in {"program_id", "study_path", "study_sha256"}}
    receipt.update(experiment_id=identity, worker_charge_total=3600)
    relative = "research/reviews/recovery-fixture.json"
    atomic_write_json(base / relative, receipt)
    event = {**receipt, "event": "research_program_worker_charge_recovery",
             "receipt_path": relative, "receipt_sha256": sha256_file(base / relative)}
    assert program._har_worker_recovery(base, [event], plan, 700) == 2900
    assert program._har_worker_recovery(base, [event], plan, 3601) == 0
    with pytest.raises(ValueError, match="repeated"):
        program._har_worker_recovery(base, [event, event], plan, 700)
    event["receipt_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="receipt"):
        program._har_worker_recovery(base, [event], plan, 700)
