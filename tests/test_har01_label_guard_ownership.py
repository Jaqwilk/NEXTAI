"""Six prospective ownership cases; preserve all prior consumed costs."""
from copy import deepcopy
import shutil

import pytest

from nextai_autoresearch import research_program as program
from nextai_autoresearch.utils import project_root


@pytest.fixture
def exact_owned(tmp_path):
    documents = (program.HAR_REPLICATION_STUDY, program.HAR_PREPARATION_AUTHORITY,
                 program.HAR_IMPORT_EXIT_STUDY, program.HAR_IMPORT_EXIT_AUTHORITY,
                 program.HAR_LABEL_GUARD_STUDY, program.HAR_LABEL_GUARD_AUTHORITY)
    for path in documents:
        destination = tmp_path / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project_root() / path, destination)
    old = {"program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1",
           "study_path": program.HAR_REPLICATION_STUDY, "study_sha256": program.HAR_REPLICATION_SHA256,
           "authority_path": program.HAR_PREPARATION_AUTHORITY, "authority_sha256": program.HAR_PREPARATION_SHA256}
    previous = {"program_id": old["program_id"], "study_path": program.HAR_IMPORT_EXIT_STUDY,
                "study_sha256": program.HAR_IMPORT_EXIT_SHA256, "authority_path": program.HAR_IMPORT_EXIT_AUTHORITY,
                "authority_sha256": program.HAR_IMPORT_EXIT_AUTHORITY_SHA256}
    new = {"program_id": old["program_id"], "study_path": program.HAR_LABEL_GUARD_STUDY,
           "study_sha256": program.HAR_LABEL_GUARD_SHA256, "authority_path": program.HAR_LABEL_GUARD_AUTHORITY,
           "authority_sha256": program.HAR_LABEL_GUARD_AUTHORITY_SHA256}
    events = [{**old, "event": "research_program_scoped_preparation_authorized", "human_authorized": True,
               "stage_slot": 0, "cap": 1200, "whole_stage_cap": 6000}]
    for identity in program.HAR_OWN_AUXILIARY_IDS:
        events.extend([{**old, "event": "research_program_aux_fit_reserved", "charge_id": identity, "seconds_cap": 1200},
                       {**old, "event": "research_program_aux_fit_charged", "charge_id": identity, "seconds": 1200}])
    events.extend([{**previous, "event": "research_program_scoped_preparation_authorized", "human_authorized": True,
                    "stage_slot": 0, "cap": 600, "whole_stage_cap": 6000},
                   {**previous, "event": "research_program_aux_fit_reserved",
                    "charge_id": program.HAR_IMPORT_EXIT_AUXILIARY_ID, "seconds_cap": 600},
                   {**previous, "event": "research_program_aux_fit_charged",
                    "charge_id": program.HAR_IMPORT_EXIT_AUXILIARY_ID, "seconds": 600},
                   {**new, "event": "research_program_scoped_preparation_authorized", "human_authorized": True,
                    "stage_slot": 0, "cap": 600, "whole_stage_cap": 6000},
                   {**new, "event": "research_program_aux_fit_reserved",
                    "charge_id": program.HAR_LABEL_GUARD_AUXILIARY_ID, "seconds_cap": 600}])
    return tmp_path, events, new


def test_exact600_plus_prior3000_protected43400(exact_owned):
    base, events, binding = exact_owned
    assert program._har_replication_auxiliary(base, events)[0] == 2400
    assert program._har_import_exit_auxiliary(base, events)[0] == 3000
    total, actual = program._har_label_guard_auxiliary(base, events)
    assert total == 3600 and actual == binding
    tickets, protected = program._transfer_reserves({"independent_replication": 0,
        "frozen_fresh_final": 0, "prototype_evaluation": 0})
    assert protected - program._har_import_exit_auxiliary(base, events[:-2])[0] == 44000
    assert tickets == 7 and protected - total == 43400
    events.append({**binding, "event": "research_program_aux_fit_charged",
                   "charge_id": program.HAR_LABEL_GUARD_AUXILIARY_ID, "seconds": 600})
    assert program._har_label_guard_auxiliary(base, events)[0] == total
    assert program._har_import_exit_auxiliary(base, events)[0] == 3000


def test_missing_or_changed_hash_binding_rejected(exact_owned):
    base, events, _ = exact_owned
    for field in ("study_sha256", "authority_sha256"):
        for missing in (True, False):
            wrong = deepcopy(events)
            if missing:
                del wrong[-1][field]
            else:
                wrong[-1][field] = "0" * 64
            with pytest.raises(ValueError):
                program._har_label_guard_auxiliary(base, wrong)
    with pytest.raises(ValueError):
        program._har_label_guard_auxiliary(base, events[:-2] + events[-1:])
    path = base / program.HAR_LABEL_GUARD_STUDY
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="hash"):
        program._har_label_guard_auxiliary(base, events)


def test_foreign_charge_ID_rejected(exact_owned):
    base, events, _ = exact_owned
    for identity in ("HAR01-LABEL-GUARD-prefix-only", program.HAR_IMPORT_EXIT_AUXILIARY_ID):
        wrong = deepcopy(events)
        wrong[-1]["charge_id"] = identity
        with pytest.raises(ValueError):
            program._har_label_guard_auxiliary(base, wrong)
    wrong = deepcopy(events)
    wrong[-1]["program_id"] = "foreign"
    with pytest.raises(ValueError):
        program._har_label_guard_auxiliary(base, wrong)


def test_duplicate_reservation_or_charge_rejected(exact_owned):
    base, events, binding = exact_owned
    charge = {**binding, "event": "research_program_aux_fit_charged",
              "charge_id": program.HAR_LABEL_GUARD_AUXILIARY_ID, "seconds": 600}
    for wrong in (events + [deepcopy(events[-1])], events + [charge, deepcopy(charge)],
                  events + [deepcopy(events[-2])]):
        with pytest.raises(ValueError):
            program._har_label_guard_auxiliary(base, wrong)


def test_invalid_cap_nan_bool_negative_or_over600_rejected(exact_owned):
    base, events, binding = exact_owned
    for amount in (float("nan"), True, -1, 601):
        wrong = deepcopy(events)
        wrong[-1]["seconds_cap"] = amount
        with pytest.raises(ValueError):
            program._har_label_guard_auxiliary(base, wrong)
        wrong = deepcopy(events)
        wrong.append({**binding, "event": "research_program_aux_fit_charged",
                      "charge_id": program.HAR_LABEL_GUARD_AUXILIARY_ID, "seconds": amount})
        with pytest.raises(ValueError):
            program._har_label_guard_auxiliary(base, wrong)


def test_prior_consumed3000_cannot_refund_or_replace(exact_owned):
    base, events, binding = exact_owned
    for index in (2, 4, 7):
        wrong = deepcopy(events)
        wrong[index]["seconds"] -= 1
        with pytest.raises(ValueError):
            program._har_label_guard_auxiliary(base, wrong)
        with pytest.raises(ValueError):
            program._har_label_guard_auxiliary(base, events[:index] + events[index + 1:])
    events.append({**binding, "event": "research_program_aux_fit_charged",
                   "charge_id": program.HAR_LABEL_GUARD_AUXILIARY_ID, "seconds": 599})
    with pytest.raises(ValueError, match="conservative"):
        program._har_label_guard_auxiliary(base, events)
