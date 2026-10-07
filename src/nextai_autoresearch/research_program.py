"""Hash-bound finite research authority; failed registrations spend real tickets."""
from datetime import datetime, timezone
import math
import re

from .config import load_config
from .ledger import append_jsonl, latest_plan_statuses, read_jsonl
from .utils import load_json, sha256_file, sha256_json, utc_now

AUTHORITY = "research/laboratory/MUC03-AUTONOMOUS-20261004-V1.json"
CONTRACT = "research/plans/MUC03-AUTONOMOUS-PROGRAM-V1.json"
FIRST_STUDY = "research/plans/MUC03-DIAG-UNDERTRAINING-V1.json"
CONTINUATION_AUTHORITY = "research/laboratory/NEXTAI-CONTINUATION-20261004-V1.json"
CONTINUATION_CONTRACT = "research/plans/NEXTAI-CONTINUATION-PROGRAM-V1.json"
TRANSFER_AUTHORITY = "research/laboratory/NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1.json"
TRANSFER_CONTRACT = "research/plans/NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-V1.json"
TRANSFER_SOURCE_AUTHORITY = "research/laboratory/NEXTAI-TRANSFER-PROTOTYPE-20261005-V1.json"
TRANSFER_STAGES = {"task_design": 0, "transfer_family_1_screen": 2, "transfer_family_2_screen": 2,
                   "independent_replication": 3, "frozen_fresh_final": 3,
                   "prototype_evaluation": 1, "repair_reserve": 1}
TRANSFER_RESERVES = {"independent_replication": {"attempts": 3, "seconds_per_attempt": 6000},
                     "frozen_fresh_final": {"attempts": 3, "seconds_per_attempt": 8000},
                     "prototype_evaluation": {"attempts": 1, "seconds_per_attempt": 5000}}
HAR_REPLICATION_STUDY = "research/plans/HAR01-INDEPENDENT-REPLICATION-V1.json"
HAR_REPLICATION_SHA256 = "d5567973e85b444d95ac13a70db9fe24b87c0ab3b672932e8322862c336ad12a"
HAR_PREPARATION_AUTHORITY = "research/laboratory/HAR01-REPLICATION-PREPARATION-AUTHORITY-V1.json"
HAR_PREPARATION_SHA256 = "036894388f89b4dfb5377c27fbde737f42853104c8a69f4d356fcb2734111fb6"
HAR_OWN_AUXILIARY_IDS = ("HAR01-REPLICATION-preparation-V1", "HAR01-REPLICATION-controller-V1")
HAR_IMPORT_EXIT_STUDY = "research/plans/HAR01-IMPORT-EXIT-CONFORMANCE-V1.json"
HAR_IMPORT_EXIT_SHA256 = "1b91ab6f3a22afeaa5122476555acfb03e6330d77f6b8251dda91e198ed384ea"
HAR_IMPORT_EXIT_AUTHORITY = "research/laboratory/HAR01-IMPORT-EXIT-AUTHORITY-V1.json"
HAR_IMPORT_EXIT_AUTHORITY_SHA256 = "2015359bbd07dd715b5deba6f37918eacdfe668900cd0d72a5d5bbe0031f45cc"
HAR_IMPORT_EXIT_AUXILIARY_ID = "HAR01-IMPORT-EXIT-preparation-V1"
HAR_LABEL_GUARD_STUDY = "research/plans/HAR01-LABEL-GUARD-CONFORMANCE-V1.json"
HAR_LABEL_GUARD_SHA256 = "243ee6fe7d8634440b92bb88fb8dd712d89761513f32663ee54c1bd226af651b"
HAR_LABEL_GUARD_AUTHORITY = "research/laboratory/HAR01-LABEL-GUARD-AUTHORITY-V1.json"
HAR_LABEL_GUARD_AUTHORITY_SHA256 = "04157dac2256884c782f259afeeb41e96d64fdc8d9fe183c13d84cee601691d7"
HAR_LABEL_GUARD_AUXILIARY_ID = "HAR01-LABEL-GUARD-preparation-V1"
HAR_PROCESS_LAUNCH_STUDY = "research/plans/HAR01-PROCESS-LAUNCH-CONFORMANCE-V1.json"
HAR_PROCESS_LAUNCH_SHA256 = "8747333468ea4cb03db5a47e862d5c42493845207594c65a02123c0e05c2ca3a"
HAR_PROCESS_LAUNCH_AUTHORITY = "research/laboratory/HAR01-PROCESS-LAUNCH-AUTHORITY-V1.json"
HAR_PROCESS_LAUNCH_AUTHORITY_SHA256 = "5239722efb53f015b43a6b14e47a78573822a525b874be67e31bb9b8d6833e69"
HAR_PROCESS_LAUNCH_AUXILIARY_ID = "HAR01-PROCESS-LAUNCH-preparation-V1"
HAR_CONTINUATION_STUDY = "research/plans/HAR01-INDEPENDENT-REPLICATION-V2.json"
HAR_CONTINUATION_SHA256 = "c1ffee7b7856851fc4dc2792f3aa0e6e8502bb465d2244ba0997fa43966f39aa"
HAR_CONTINUATION_AUTHORITY = "research/laboratory/HAR01-REPLICATION-CONTINUATION-AUTHORITY-V2.json"
HAR_CONTINUATION_AUTHORITY_SHA256 = "a2ffcca6567de58b5f71c219520bb1c344b748997411627d94a046ff7bc4b120"
HAR_CONTINUATION_AUXILIARY_CAPS = {"HAR01-REPLICATION-preparation-V2": 600,
                                   "HAR01-REPLICATION-controller-V2": 450}


def _finite_seconds(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def _har_replication_auxiliary(base, events):
    """Credit only this exact human-authorized allocation, never a name prefix."""
    if (_bound_hash(base, HAR_REPLICATION_STUDY) != HAR_REPLICATION_SHA256
            or _bound_hash(base, HAR_PREPARATION_AUTHORITY) != HAR_PREPARATION_SHA256):
        raise ValueError("HAR scoped preparation study/authority hash mismatch")
    study = _document(base, HAR_REPLICATION_STUDY)
    authority = _document(base, HAR_PREPARATION_AUTHORITY)
    program_id = "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1"
    permissions = [e for e in events if e.get("event") == "research_program_scoped_preparation_authorized"
                   and e.get("study_path") == HAR_REPLICATION_STUDY]
    if (len(permissions) != 1 or authority["program_id"] != program_id
            or authority["study_path"] != HAR_REPLICATION_STUDY
            or authority["stage"] != "independent_replication" or type(authority["stage_slot"]) is not int
            or authority["stage_slot"] != 0 or authority["preparation_seconds_cap"] != 1200
            or authority["whole_stage_seconds_cap"] != 6000
            or study["auxiliary_charge_ownership"]["allowed_ids"] != list(HAR_OWN_AUXILIARY_IDS)):
        raise ValueError("HAR scoped preparation authority missing, repeated or changed")
    permission = permissions[0]
    expected = {"program_id": program_id, "study_path": HAR_REPLICATION_STUDY,
                "study_sha256": HAR_REPLICATION_SHA256, "authority_path": HAR_PREPARATION_AUTHORITY,
                "authority_sha256": HAR_PREPARATION_SHA256}
    if (any(permission.get(k) != v for k, v in expected.items())
            or permission.get("human_authorized") is not True or permission.get("stage_slot") != 0
            or type(permission.get("stage_slot")) is not int or permission.get("cap") != 1200
            or not _finite_seconds(permission.get("cap")) or permission.get("whole_stage_cap") != 6000):
        raise ValueError("HAR scoped preparation event binding changed")
    owned = [e for e in events if e.get("event") in {"research_program_aux_fit_reserved", "research_program_aux_fit_charged"}
             and (e.get("charge_id") in HAR_OWN_AUXILIARY_IDS or e.get("study_path") == HAR_REPLICATION_STUDY)]
    reservations, charges = {}, {}
    for event in owned:
        identity = event.get("charge_id")
        if identity not in HAR_OWN_AUXILIARY_IDS or any(event.get(k) != v for k, v in expected.items()):
            raise ValueError("Foreign or incomplete HAR auxiliary ownership binding")
        target = reservations if event["event"] == "research_program_aux_fit_reserved" else charges
        if identity in target:
            raise ValueError("Duplicate HAR auxiliary accounting")
        target[identity] = event
    if HAR_OWN_AUXILIARY_IDS[0] not in reservations or set(charges) - set(reservations):
        raise ValueError("Missing HAR preparation reservation or unreserved charge")
    total = 0.
    for identity, reservation in reservations.items():
        cap = reservation.get("seconds_cap")
        amount = charges.get(identity, {}).get("seconds", cap)
        if not _finite_seconds(cap) or not 0 < cap <= 1200 or not _finite_seconds(amount) or amount > cap:
            raise ValueError("Invalid HAR owned auxiliary cap or charge")
        total += amount
    if total > 2400:
        raise ValueError("HAR owned auxiliary allocation exceeded")
    return total, expected


def _har_import_exit_auxiliary(base, events):
    """Deduct only the exact new 600s allocation from the existing first slot."""
    if (_bound_hash(base, HAR_IMPORT_EXIT_STUDY) != HAR_IMPORT_EXIT_SHA256
            or _bound_hash(base, HAR_IMPORT_EXIT_AUTHORITY) != HAR_IMPORT_EXIT_AUTHORITY_SHA256):
        raise ValueError("HAR import/exit study or authority hash mismatch")
    study = _document(base, HAR_IMPORT_EXIT_STUDY)
    authority = _document(base, HAR_IMPORT_EXIT_AUTHORITY)
    prior, _ = _har_replication_auxiliary(base, events)
    prior_charges = [e for e in events if e.get("event") == "research_program_aux_fit_charged"
                     and e.get("charge_id") in HAR_OWN_AUXILIARY_IDS]
    if (prior != 2400 or len(prior_charges) != 2
            or any(not _finite_seconds(e.get("seconds")) or e["seconds"] != 1200 for e in prior_charges)):
        raise ValueError("Prior HAR consumed 2400s cannot be refunded or replaced")
    expected = {"program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1",
                "study_path": HAR_IMPORT_EXIT_STUDY, "study_sha256": HAR_IMPORT_EXIT_SHA256,
                "authority_path": HAR_IMPORT_EXIT_AUTHORITY,
                "authority_sha256": HAR_IMPORT_EXIT_AUTHORITY_SHA256}
    permissions = [e for e in events if e.get("event") == "research_program_scoped_preparation_authorized"
                   and e.get("study_path") == HAR_IMPORT_EXIT_STUDY]
    if (len(permissions) != 1 or any(permissions[0].get(k) != v for k, v in expected.items())
            or permissions[0].get("human_authorized") is not True
            or type(permissions[0].get("stage_slot")) is not int or permissions[0]["stage_slot"] != 0
            or not _finite_seconds(permissions[0].get("cap")) or permissions[0]["cap"] != 600
            or permissions[0].get("whole_stage_cap") != 6000
            or authority["program_id"] != expected["program_id"] or authority["study_path"] != HAR_IMPORT_EXIT_STUDY
            or authority["stage"] != "independent_replication" or type(authority["stage_slot"]) is not int
            or authority["stage_slot"] != 0 or authority["preparation_seconds_cap"] != 600
            or authority["prior_consumed_stage_seconds"] != 2400 or authority["whole_stage_seconds_cap"] != 6000
            or study["study_kind"] != "preparation_only" or study["registration_attempts_for_this_study_cap"] != 0
            or study["resources"]["fit_seconds_study_cap"] != 0
            or study["auxiliary_charge_ownership"]["allowed_ids"] != [HAR_IMPORT_EXIT_AUXILIARY_ID]):
        raise ValueError("HAR import/exit authority missing, repeated or changed")
    owned = [e for e in events if e.get("event") in {"research_program_aux_fit_reserved", "research_program_aux_fit_charged"}
             and (e.get("charge_id") == HAR_IMPORT_EXIT_AUXILIARY_ID or e.get("study_path") == HAR_IMPORT_EXIT_STUDY)]
    reservations, charges = [], []
    for event in owned:
        if event.get("charge_id") != HAR_IMPORT_EXIT_AUXILIARY_ID or any(event.get(k) != v for k, v in expected.items()):
            raise ValueError("Foreign or incomplete HAR import/exit ownership binding")
        (reservations if event["event"] == "research_program_aux_fit_reserved" else charges).append(event)
    if len(reservations) != 1 or len(charges) > 1:
        raise ValueError("Missing or duplicate HAR import/exit auxiliary accounting")
    cap = reservations[0].get("seconds_cap")
    amount = charges[0].get("seconds") if charges else cap
    if not _finite_seconds(cap) or cap != 600 or not _finite_seconds(amount) or amount != 600:
        raise ValueError("HAR import/exit allocation must retain its full conservative 600s charge")
    return prior + amount, expected


def _har_label_guard_auxiliary(base, events):
    """Carry the consumed 3000s and this one exact prospective 600s allocation."""
    if (_bound_hash(base, HAR_LABEL_GUARD_STUDY) != HAR_LABEL_GUARD_SHA256
            or _bound_hash(base, HAR_LABEL_GUARD_AUTHORITY) != HAR_LABEL_GUARD_AUTHORITY_SHA256):
        raise ValueError("HAR label-guard study or authority hash mismatch")
    study = _document(base, HAR_LABEL_GUARD_STUDY)
    authority = _document(base, HAR_LABEL_GUARD_AUTHORITY)
    prior, _ = _har_import_exit_auxiliary(base, events)
    prior_charges = [e for e in events if e.get("event") == "research_program_aux_fit_charged"
                     and e.get("charge_id") == HAR_IMPORT_EXIT_AUXILIARY_ID]
    if (prior != 3000 or len(prior_charges) != 1
            or not _finite_seconds(prior_charges[0].get("seconds")) or prior_charges[0]["seconds"] != 600):
        raise ValueError("Prior HAR consumed 3000s cannot be refunded or replaced")
    expected = {"program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1",
                "study_path": HAR_LABEL_GUARD_STUDY, "study_sha256": HAR_LABEL_GUARD_SHA256,
                "authority_path": HAR_LABEL_GUARD_AUTHORITY,
                "authority_sha256": HAR_LABEL_GUARD_AUTHORITY_SHA256}
    permissions = [e for e in events if e.get("event") == "research_program_scoped_preparation_authorized"
                   and e.get("study_path") == HAR_LABEL_GUARD_STUDY]
    if (len(permissions) != 1 or any(permissions[0].get(k) != v for k, v in expected.items())
            or permissions[0].get("human_authorized") is not True
            or type(permissions[0].get("stage_slot")) is not int or permissions[0]["stage_slot"] != 0
            or not _finite_seconds(permissions[0].get("cap")) or permissions[0]["cap"] != 600
            or permissions[0].get("whole_stage_cap") != 6000
            or authority["program_id"] != expected["program_id"] or authority["study_path"] != HAR_LABEL_GUARD_STUDY
            or authority["stage"] != "independent_replication" or type(authority["stage_slot"]) is not int
            or authority["stage_slot"] != 0 or authority["preparation_seconds_cap"] != 600
            or authority["prior_consumed_stage_seconds"] != 3000 or authority["whole_stage_seconds_cap"] != 6000
            or study["study_kind"] != "preparation_only" or study["registration_attempts_for_this_study_cap"] != 0
            or study["resources"]["fit_seconds_study_cap"] != 0
            or study["auxiliary_charge_ownership"]["allowed_ids"] != [HAR_LABEL_GUARD_AUXILIARY_ID]):
        raise ValueError("HAR label-guard authority missing, repeated or changed")
    owned = [e for e in events if e.get("event") in {"research_program_aux_fit_reserved", "research_program_aux_fit_charged"}
             and (e.get("charge_id") == HAR_LABEL_GUARD_AUXILIARY_ID or e.get("study_path") == HAR_LABEL_GUARD_STUDY)]
    reservations, charges = [], []
    for event in owned:
        if event.get("charge_id") != HAR_LABEL_GUARD_AUXILIARY_ID or any(event.get(k) != v for k, v in expected.items()):
            raise ValueError("Foreign or incomplete HAR label-guard ownership binding")
        (reservations if event["event"] == "research_program_aux_fit_reserved" else charges).append(event)
    if len(reservations) != 1 or len(charges) > 1:
        raise ValueError("Missing or duplicate HAR label-guard auxiliary accounting")
    cap = reservations[0].get("seconds_cap")
    amount = charges[0].get("seconds") if charges else cap
    if not _finite_seconds(cap) or cap != 600 or not _finite_seconds(amount) or amount != 600:
        raise ValueError("HAR label-guard allocation must retain its full conservative 600s charge")
    return prior + amount, expected


def _har_process_launch_auxiliary(base, events):
    """Retain the spent 3600s and the exact prospectively authorized 300s."""
    if (_bound_hash(base, HAR_PROCESS_LAUNCH_STUDY) != HAR_PROCESS_LAUNCH_SHA256
            or _bound_hash(base, HAR_PROCESS_LAUNCH_AUTHORITY) != HAR_PROCESS_LAUNCH_AUTHORITY_SHA256):
        raise ValueError("HAR process-launch study or authority hash mismatch")
    prior, _ = _har_label_guard_auxiliary(base, events)
    settled = [e for e in events if e.get("event") == "research_program_aux_fit_charged"
               and e.get("charge_id") == HAR_LABEL_GUARD_AUXILIARY_ID]
    if prior != 3600 or len(settled) != 1 or not _finite_seconds(settled[0].get("seconds")) or settled[0]["seconds"] != 600:
        raise ValueError("Prior HAR consumed 3600s cannot be refunded or replaced")
    expected = {"program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1",
                "study_path": HAR_PROCESS_LAUNCH_STUDY, "study_sha256": HAR_PROCESS_LAUNCH_SHA256,
                "authority_path": HAR_PROCESS_LAUNCH_AUTHORITY,
                "authority_sha256": HAR_PROCESS_LAUNCH_AUTHORITY_SHA256}
    permissions = [e for e in events if e.get("event") == "research_program_scoped_preparation_authorized"
                   and e.get("study_path") == HAR_PROCESS_LAUNCH_STUDY]
    if (len(permissions) != 1 or any(permissions[0].get(k) != v for k, v in expected.items())
            or permissions[0].get("human_authorized") is not True
            or type(permissions[0].get("stage_slot")) is not int or permissions[0]["stage_slot"] != 0
            or not _finite_seconds(permissions[0].get("cap")) or permissions[0]["cap"] != 300
            or permissions[0].get("whole_stage_cap") != 6000):
        raise ValueError("HAR process-launch authority missing, repeated or changed")
    owned = [e for e in events if e.get("event") in {"research_program_aux_fit_reserved", "research_program_aux_fit_charged"}
             and (e.get("charge_id") == HAR_PROCESS_LAUNCH_AUXILIARY_ID or e.get("study_path") == HAR_PROCESS_LAUNCH_STUDY)]
    reservations, charges = [], []
    for event in owned:
        if event.get("charge_id") != HAR_PROCESS_LAUNCH_AUXILIARY_ID or any(event.get(k) != v for k, v in expected.items()):
            raise ValueError("Foreign or incomplete HAR process-launch ownership binding")
        (reservations if event["event"] == "research_program_aux_fit_reserved" else charges).append(event)
    if len(reservations) != 1 or len(charges) > 1:
        raise ValueError("Missing or duplicate HAR process-launch auxiliary accounting")
    cap = reservations[0].get("seconds_cap")
    amount = charges[0].get("seconds") if charges else cap
    if not _finite_seconds(cap) or cap != 300 or not _finite_seconds(amount) or amount != 300:
        raise ValueError("HAR process-launch allocation must retain its full conservative 300s charge")
    return prior + amount, expected


def _har_continuation_auxiliary(base, events):
    """The new scientific allocation owns only 1050s; its consumed parent owns 3900s."""
    if (_bound_hash(base, HAR_CONTINUATION_STUDY) != HAR_CONTINUATION_SHA256
            or _bound_hash(base, HAR_CONTINUATION_AUTHORITY) != HAR_CONTINUATION_AUTHORITY_SHA256):
        raise ValueError("HAR continuation study or authority hash mismatch")
    prior, _ = _har_process_launch_auxiliary(base, events)
    settled = [e for e in events if e.get("event") == "research_program_aux_fit_charged"
               and e.get("charge_id") == HAR_PROCESS_LAUNCH_AUXILIARY_ID]
    if prior != 3900 or len(settled) != 1 or not _finite_seconds(settled[0].get("seconds")) or settled[0]["seconds"] != 300:
        raise ValueError("Prior HAR consumed 3900s cannot be refunded or replaced")
    expected = {"program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1",
                "study_path": HAR_CONTINUATION_STUDY, "study_sha256": HAR_CONTINUATION_SHA256,
                "authority_path": HAR_CONTINUATION_AUTHORITY,
                "authority_sha256": HAR_CONTINUATION_AUTHORITY_SHA256}
    permissions = [e for e in events if e.get("event") == "research_program_scoped_preparation_authorized"
                   and e.get("study_path") == HAR_CONTINUATION_STUDY]
    if (len(permissions) != 1 or any(permissions[0].get(k) != v for k, v in expected.items())
            or permissions[0].get("human_authorized") is not True
            or type(permissions[0].get("stage_slot")) is not int or permissions[0]["stage_slot"] != 0
            or not _finite_seconds(permissions[0].get("cap")) or permissions[0]["cap"] != 600
            or permissions[0].get("whole_stage_cap") != 6000):
        raise ValueError("HAR continuation authority missing, repeated or changed")
    owned = [e for e in events if e.get("event") in {"research_program_aux_fit_reserved", "research_program_aux_fit_charged"}
             and (e.get("charge_id") in HAR_CONTINUATION_AUXILIARY_CAPS or e.get("study_path") == HAR_CONTINUATION_STUDY)]
    reservations, charges = {}, {}
    for event in owned:
        identity = event.get("charge_id")
        if identity not in HAR_CONTINUATION_AUXILIARY_CAPS or any(event.get(k) != v for k, v in expected.items()):
            raise ValueError("Foreign or incomplete HAR continuation ownership binding")
        target = reservations if event["event"] == "research_program_aux_fit_reserved" else charges
        if identity in target:
            raise ValueError("Duplicate HAR continuation auxiliary accounting")
        target[identity] = event
    if "HAR01-REPLICATION-preparation-V2" not in reservations or set(charges) - set(reservations):
        raise ValueError("Missing HAR continuation preparation reservation or unreserved charge")
    total = 0.
    for identity, reservation in reservations.items():
        cap = reservation.get("seconds_cap")
        amount = charges.get(identity, {}).get("seconds", cap)
        if (not _finite_seconds(cap) or cap != HAR_CONTINUATION_AUXILIARY_CAPS[identity]
                or not _finite_seconds(amount) or amount != cap):
            raise ValueError("HAR continuation must retain its full conservative auxiliary allocations")
        total += amount
    return prior + total, expected


def _study_worker_recovery(base, events, plan, observed):
    if plan["research_program_protocol"].get("study_path") != HAR_CONTINUATION_STUDY:
        return _har_worker_recovery(base, events, plan, observed)
    recoveries = [e for e in events if e.get("event") == "research_program_worker_charge_recovery"
                  and e.get("experiment_id") == plan["experiment_id"]]
    if not recoveries:
        return 0.
    if len(recoveries) != 1 or plan["research_program_protocol"].get("study_sha256") != HAR_CONTINUATION_SHA256:
        raise ValueError("HAR continuation worker recovery repeated or outside exact study")
    event = recoveries[0]
    expected = {"program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1",
                "study_path": HAR_CONTINUATION_STUDY, "study_sha256": HAR_CONTINUATION_SHA256,
                "experiment_id": plan["experiment_id"]}
    receipt = _document(base, event["receipt_path"])
    total = event.get("worker_charge_total")
    if (any(event.get(k) != v or receipt.get(k) != v for k, v in expected.items())
            or _bound_hash(base, event["receipt_path"]) != event.get("receipt_sha256")
            or not _finite_seconds(total) or total > 1050 or receipt.get("worker_charge_total") != total):
        raise ValueError("HAR continuation worker recovery receipt or finite allocation changed")
    return max(0., total - observed)


def _har_worker_recovery(base, events, plan, observed):
    recoveries = [e for e in events if e.get("event") == "research_program_worker_charge_recovery"
                  and e.get("experiment_id") == plan["experiment_id"]]
    if not recoveries:
        return 0.
    protocol = plan["research_program_protocol"]
    if (len(recoveries) != 1 or protocol["study_path"] != HAR_REPLICATION_STUDY
            or protocol["study_sha256"] != HAR_REPLICATION_SHA256):
        raise ValueError("Worker recovery is repeated or outside exact HAR study")
    event = recoveries[0]
    expected = {"program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1",
                "study_path": HAR_REPLICATION_STUDY, "study_sha256": HAR_REPLICATION_SHA256,
                "experiment_id": plan["experiment_id"]}
    receipt = _document(base, event["receipt_path"])
    total = event.get("worker_charge_total")
    if (any(event.get(k) != v or receipt.get(k) != v for k, v in expected.items())
            or _bound_hash(base, event["receipt_path"]) != event.get("receipt_sha256")
            or not _finite_seconds(total) or total > 3600 or receipt.get("worker_charge_total") != total):
        raise ValueError("HAR worker recovery receipt or finite allocation changed")
    return max(0., total - observed)


def _document(base, relative):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        raise ValueError("Research program document missing or outside repository")
    return load_json(path)


def _bound_hash(base, relative):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        raise ValueError("Carry-forward evidence missing or outside repository")
    return sha256_file(path)


def _execution_fit(outcomes):
    total = 0.
    for item in outcomes:
        execution = item.get("execution") or {}
        value = execution.get("research_compute_seconds", execution.get("supervised_fit_seconds"))
        if value is None:
            value = execution.get("wall_seconds", 0.)
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid research fit charge")
        total += value
    return total


def _study_scope(study):
    resources = study["resources"]
    extra = ({"compute_charge_basis": resources["compute_charge_basis"],
              "task_contract_path": study["task_contract_path"], "task_contract_sha256": study["task_contract_sha256"]}
             if "compute_charge_basis" in resources else {})
    if study.get("study_kind") == "paired_view_transport_compression_adverse":
        replication = study["cohort"] == "paired_view_mutable_memory_v7"
        extra.update(classical_economic_contract_path="research/plans/PVM01-REPLICATION-CLASSICAL-ECONOMICS-V1.json" if replication else "research/plans/PVM01-TRANSPORT-CLASSICAL-ECONOMICS-V1.json",
                     classical_economic_contract_sha256="efab9dbb8e2fc19f6b3c163c4bc0eaa88009299f6bfbb524ea38cf1b21096c09" if replication else "06688b5c493c08d701a236fedcfb549e27489ec7596715c73535b8d04fe7a512")
    if study.get("study_kind") == "paired_view_dense_noise_robustness":
        extra.update(classical_economic_contract_path="research/plans/PVM01-ROBUSTNESS-CLASSICAL-ECONOMICS-V1.json",
                     classical_economic_contract_sha256="3d81817d5e1627bd16f5c12e9fbade1d0721431a09337c6a99888d2f1da57d64")
    if study.get("study_kind") == "paired_view_dense_noise_confirmation":
        extra.update(classical_economic_contract_path="research/plans/PVM01-CONFIRMATION-CLASSICAL-ECONOMICS-V1.json",
                     classical_economic_contract_sha256="ee666f18410417345fb75e48f8b720f388d71d8f52bf06bcce0a6cbbebfe9325",
                     resource_measurement_version="cumulative_cuda_phase_peaks_v1")
    if study.get("study_kind") == "paired_view_unaugmented_reference_confirmation":
        extra.update(classical_economic_contract_path="research/plans/PVM01-BASE-REFERENCE-CLASSICAL-ECONOMICS-V1.json",
                     classical_economic_contract_sha256="06adddd5263f6fcc1d60df00e74b41e906909413563e1333d0fb78f4edc25ee3",
                     resource_measurement_version="cumulative_cuda_phase_peaks_v1")
    if study.get("study_kind") == "paired_view_frozen_fresh_final":
        extra.update(classical_economic_contract_path="research/plans/PVM01-FRESH-FINAL-CLASSICAL-ECONOMICS-V1.json",
                     classical_economic_contract_sha256="5f6565713391799b8aeb2f1a54e9a0faa976d6bde5ec1645618284aabd8cc5fb",
                     resource_measurement_version="cumulative_cuda_phase_peaks_v1",
                     evaluation_data_role="frozen_fresh_final_v1")
    if study.get("study_kind") == "native_frozen_source_transfer":
        if study["cohort"] not in {"har01_native_memory_v1", "har01_native_memory_v2", "har01_native_memory_v3"}:
            raise ValueError("Native source-transfer recipe/cohort mismatch")
        if study["cohort"] == "har01_native_memory_v2" and study.get("id") != "HAR01-INDEPENDENT-REPLICATION-V1":
            raise ValueError("HAR v2 belongs only to the exact independent replication")
        if study["cohort"] == "har01_native_memory_v3" and study.get("id") != "HAR01-INDEPENDENT-REPLICATION-V2":
            raise ValueError("HAR v3 belongs only to the exact independent continuation")
    if study.get("study_kind") == "asm01_frozen_source_transfer":
        if study["cohort"] not in {"asm01_native_memory_v2", "asm01_native_memory_v3"}:
            raise ValueError("Canonical native pen source-transfer recipe/cohort mismatch")
    return {**extra, **{key: study[key] for key in ("roles", "recipe", "data", "diagnostics", "diagnosis_gates", "reference_gates")},
            "classical_baselines": study["candidates"], "deadline_at": study["study_deadline_at"],
            "fit_seconds_cap": resources["fit_seconds_per_role_cap"], "fit_seconds_total_cap": resources["fit_seconds_study_cap"],
            **{key: resources[key] for key in ("worker_seconds_cap", "max_rss_bytes", "max_cuda_reserved_bytes")}}


def _status_for(base, *, authority_path=None, contract_path=None, study_path=None,
                expected_caps=(20, 72000), authorization_event="research_program_authorized"):
    authority_path, contract_path = authority_path or AUTHORITY, contract_path or CONTRACT
    events = read_jsonl(base / "research/events.jsonl")
    starts = [e for e in events if e.get("event") == authorization_event]
    if not (base / authority_path).exists() and not starts:
        return None
    auth, contract = _document(base, authority_path), _document(base, contract_path)
    registration_cap, compute_cap = expected_caps
    if (len(starts) != 1 or starts[0].get("authority_sha256") != sha256_file(base / authority_path)
            or starts[0].get("contract_sha256") != sha256_file(base / contract_path)
            or auth["program_contract_sha256"] != sha256_file(base / contract_path)
            or auth["id"] != contract["id"] or starts[0].get("program_id") != contract["id"]
            or auth["program_contract_path"] != contract_path
            or auth["registration_attempts_cap"] != registration_cap or auth["fit_seconds_total_cap"] != compute_cap
            or contract["registration_attempts_cap"] != registration_cap or contract["fit_seconds_total_cap"] != compute_cap
            or contract["wt_files_8_9_access_authorized"] is not False
            or contract["external_model_api_authorized"] is not False
            or (authorization_event == "research_program_authorized"
                and sha256_file(base / contract["previous_result"]) != contract["previous_result_sha256"])):
        raise ValueError("Research authority or immutable prior evidence changed")
    program_id = contract["id"]
    events = [e for e in events if e.get("program_id") == program_id]
    study_path = study_path or load_config(base).raw.get("research_program", {}).get("study_path", FIRST_STUDY)
    study = _document(base, study_path)
    freezes = [e for e in events if e.get("event") == "research_program_study_frozen" and e.get("study_path") == study_path]
    if (len(freezes) != 1 or freezes[0]["study_sha256"] != sha256_file(base / study_path)
            or study["program_contract_sha256"] != sha256_file(base / contract_path)):
        raise ValueError("Current study must have one immutable prospective freeze")
    if study.get("task_contract_path") and _bound_hash(base, study["task_contract_path"]) != study["task_contract_sha256"]:
        raise ValueError("Frozen task contract changed")
    tickets = [e for e in events if e.get("event") == "research_program_registration_started"]
    if [e.get("ticket") for e in tickets] != list(range(1, len(tickets) + 1)) or len(tickets) > registration_cap:
        raise ValueError("Research registration accounting changed or exceeded")
    stage_caps = {s["id"]: s["registration_cap"] for s in contract["stages"]}
    stage_used = {name: 0 for name in stage_caps}
    for ticket in tickets:
        ticket_study = _document(base, ticket["study_path"])
        stage_used[ticket_study["stage"]] += 1
    if any(stage_used[name] > cap for name, cap in stage_caps.items()):
        raise ValueError("Research milestone registration cap exceeded")
    registered = [e for e in events if e.get("event") == "research_program_registered"]
    if len({e["ticket"] for e in registered}) != len(registered):
        raise ValueError("Research ticket registered repeatedly")
    if any(e.get("experiment_id") not in {r["experiment_id"] for r in registered}
           for e in events if e.get("event") == "research_program_worker_charge_recovery"):
        raise ValueError("Worker recovery references an unregistered experiment")
    preserved = [e for e in events if e.get("event") == "research_program_outcome_preserved"]
    if (len({e["experiment_id"] for e in preserved}) != len(preserved)
            or {e["experiment_id"] for e in preserved} - {e["experiment_id"] for e in registered}):
        raise ValueError("Repeated or unregistered preserved research outcome")
    result_hashes = {e["experiment_id"]: e["result_sha256"] for e in preserved}
    fit, fit_reserved = 0., 0.
    pending_registered = False
    current_plans = []
    for event in registered:
        if event["ticket"] not in {e["ticket"] for e in tickets}:
            raise ValueError("Unreserved research registration")
        plan = _document(base, event["plan_path"])
        if sha256_json(plan) != event["plan_sha256"]:
            raise ValueError("Research registered plan changed")
        protocol = plan["research_program_protocol"]
        bound_study = _document(base, protocol["study_path"])
        if (protocol["program_contract_sha256"] != sha256_file(base / contract_path)
                or protocol["study_sha256"] != sha256_file(base / protocol["study_path"])
                or plan["candidates"] != bound_study["candidates"] or plan["matrix"] != bound_study["matrix"]
                or any(protocol.get(key) != expected for key, expected in _study_scope(bound_study).items())
                or protocol["registration_ticket"] != event["ticket"]
                or event["study_path"] != protocol["study_path"]
                or protocol["authority_path"] != authority_path or protocol["program_contract_path"] != contract_path
                or plan["benchmark"] != bound_study["cohort"]):
            raise ValueError("Registered research scope differs from frozen study")
        if protocol["study_path"] == study_path:
            current_plans.append(plan)
        result = base / "research/results" / f"{plan['experiment_id']}.json"
        if plan["experiment_id"] in result_hashes and (not result.is_file() or sha256_file(result) != result_hashes[plan["experiment_id"]]):
            raise ValueError("Preserved completed research result changed; budget cannot be reset")
        if result.exists():
            observed = _execution_fit(load_json(result)["candidates"])
            fit += observed + _study_worker_recovery(base, events, plan, observed)
        else:
            supervisors = sorted((base / "research/tmp" / plan["experiment_id"]).glob("*.supervisor.json"))
            observed = _execution_fit(load_json(p) for p in supervisors)
            recovered = _study_worker_recovery(base, events, plan, observed)
            fit += observed + recovered
            recovery_terminal = any(e.get("event") == "research_program_worker_charge_recovery"
                                    and e.get("experiment_id") == plan["experiment_id"] for e in events)
            if plan["experiment_id"] not in latest_plan_statuses(base) and not recovery_terminal:
                pending_registered = True
                fit_reserved += max(0., protocol["fit_seconds_total_cap"] - observed)
    reserves = [e for e in events if e.get("event") == "research_program_aux_fit_reserved"]
    charges = [e for e in events if e.get("event") == "research_program_aux_fit_charged"]
    if len({e["charge_id"] for e in reserves}) != len(reserves) or len({e["charge_id"] for e in charges}) != len(charges):
        raise ValueError("Repeated auxiliary fit accounting")
    completed = {e["charge_id"]: e for e in charges}
    if set(completed) - {e["charge_id"] for e in reserves}:
        raise ValueError("Auxiliary fit without prior reservation")
    auxiliary = 0.
    for reservation in reserves:
        amount = completed.get(reservation["charge_id"], {}).get("seconds", reservation["seconds_cap"])
        if (not _finite_seconds(reservation["seconds_cap"]) or not _finite_seconds(amount)
                or not 0 <= amount <= reservation["seconds_cap"]):
            raise ValueError("Auxiliary fit reservation exceeded")
        auxiliary += amount
    current_tickets = [e for e in tickets if e["study_path"] == study_path]
    failed = [e for e in events if e.get("event") == "research_program_registration_failed" and e.get("study_path") == study_path]
    study_registration_cap = study.get("registration_attempts_for_this_study_cap")
    if study_registration_cap is None and study_path == HAR_REPLICATION_STUDY:
        _har_replication_auxiliary(base, read_jsonl(base / "research/events.jsonl"))
        study_registration_cap = 1
    if study_registration_cap is None and study_path == HAR_CONTINUATION_STUDY:
        _har_continuation_auxiliary(base, read_jsonl(base / "research/events.jsonl"))
        study_registration_cap = study["validation_contract"]["registration_cap"]
    if study_registration_cap is None and study.get("id") == "HAR01-FROZEN-SOURCE-SCREEN-V1":
        cap_addendum = _document(base, "research/plans/HAR01-PRESEED-CAP-CONFORMANCE-V1.json")
        if (study.get("study_kind") != "native_frozen_source_transfer"
                or study.get("cohort") != "har01_native_memory_v1"
                or cap_addendum["study_path"] != study_path
                or cap_addendum["study_sha256"] != _bound_hash(base, study_path)
                or cap_addendum["study_sha256"] != "9ec218451704762a128415204a1b4f7aa6e016bac4a56122368e975f6d9013eb"
                or cap_addendum["registration_attempts_for_this_study_cap"] != 1):
            raise ValueError("Native pre-seed registration cap addendum mismatch")
        study_registration_cap = 1
    if type(study_registration_cap) is not int or study_registration_cap < 0:
        raise ValueError("Study registration cap missing or invalid")
    if len(current_tickets) > study_registration_cap or len(current_plans) > 1:
        raise ValueError("Study registration cap exceeded")
    experiment_id = current_plans[0]["experiment_id"] if current_plans else None
    preparation_ends = [e for e in events if e.get("event") == "research_program_preparation_completed"
                        and e.get("study_path") == study_path]
    if (len(preparation_ends) > 1 or any(e["study_sha256"] != sha256_file(base / study_path)
            or e["receipt_sha256"] != _bound_hash(base, e["receipt_path"]) for e in preparation_ends)):
        raise ValueError("Preparation completion receipt changed or repeated")
    terminal = bool(failed or (experiment_id and ((base / "research/results" / f"{experiment_id}.json").exists()
                                                or experiment_id in latest_plan_statuses(base)
                                                or any(e.get("event") == "research_program_worker_charge_recovery"
                                                       and e.get("experiment_id") == experiment_id for e in events))) or preparation_ends)
    ready_events = [e for e in events if e.get("event") == "research_program_study_ready" and e.get("study_path") == study_path]
    if len(ready_events) > 1:
        raise ValueError("Research readiness repeated")
    if ready_events:
        ready = ready_events[0]
        if (ready["study_sha256"] != sha256_file(base / study_path)
                or ready["receipt_sha256"] != sha256_file(base / ready["receipt_path"])):
            raise ValueError("Research readiness receipt changed")
    expired = datetime.now(timezone.utc) >= datetime.fromisoformat(study["study_deadline_at"].replace("Z", "+00:00"))
    exhausted = (len(tickets) >= registration_cap and not pending_registered) or fit + auxiliary >= compute_cap
    closed = any(e.get("event") == "research_program_completed" for e in events)
    return {"id": program_id, "authority_path": authority_path, "contract_path": contract_path,
            "study_path": study_path, "cohort": study["cohort"], "ready": bool(ready_events),
            "study_terminal": terminal, "study_expired": expired, "program_terminal": closed or exhausted,
            "program_closed": closed,
            "registration_budget_exhausted": len(tickets) >= registration_cap, "paid_run_pending": pending_registered,
            "registration_attempts_used": len(tickets), "registration_attempts_cap": registration_cap,
            "stage_registration_attempts": stage_used, "stage_registration_caps": stage_caps,
            "experimental_fit_seconds": fit, "auxiliary_fit_seconds_conservative": auxiliary,
            "fit_seconds_charged": fit + auxiliary, "fit_seconds_remaining": max(0., compute_cap - fit - auxiliary),
            "pending_fit_reservation_seconds": fit_reserved,
            "unreserved_fit_seconds_remaining": max(0., compute_cap - fit - auxiliary - fit_reserved),
            "fit_seconds_cap": compute_cap, "experiment_id": experiment_id,
            "scoring_authorized": bool(ready_events) and study.get("study_kind") != "preparation_only"
                and not (terminal or expired or closed or fit + auxiliary >= compute_cap)}


def _continuation_status(base, *, study_path=None, include_raw_current=False):
    """A new authority carries immutable closed accounting; it never reopens it."""
    events = read_jsonl(base / "research/events.jsonl")
    starts = [e for e in events if e.get("event") == "research_program_continuation_authorized"]
    if not starts:  # A copied prospective document alone cannot activate a program.
        return _status_for(base, study_path=study_path)
    contract = _document(base, CONTINUATION_CONTRACT)
    carry = contract["carry_forward"]
    if (carry["authority_path"] != AUTHORITY or carry["contract_path"] != CONTRACT
            or contract["prior_budgets_reset"] is not False
            or any(_bound_hash(base, path) != digest for path, digest in carry["document_sha256"].items())
            or sha256_json([e for e in events if e.get("program_id") == carry["program_id"]]) != carry["program_events_sha256"]):
        raise ValueError("Immutable carry-forward evidence changed; old accounting cannot reset")
    prior = _status_for(base, study_path=carry["terminal_study_path"])
    if (not prior or prior["id"] != carry["program_id"] or not prior["program_closed"] or prior["paid_run_pending"]
            or prior["pending_fit_reservation_seconds"] != 0
            or any(prior[key] != carry[key] for key in ("registration_attempts_used", "experimental_fit_seconds",
                   "auxiliary_fit_seconds_conservative", "fit_seconds_charged"))):
        raise ValueError("Carry-forward counts differ from closed program; budget cannot reset")
    current = _status_for(base, authority_path=CONTINUATION_AUTHORITY, contract_path=CONTINUATION_CONTRACT,
                          study_path=study_path, expected_caps=(17, 69344),
                          authorization_event="research_program_continuation_authorized")
    return {**current, **({"_raw_current_program": current} if include_raw_current else {}),
            "prior_program_closed": True, "prior_program_id": prior["id"],
            "prior_registration_attempts_used": prior["registration_attempts_used"],
            "prior_compute_seconds_charged": prior["fit_seconds_charged"],
            "continuation_registration_attempts_used": current["registration_attempts_used"],
            "continuation_registration_attempts_cap": current["registration_attempts_cap"],
            "continuation_compute_seconds_charged": current["fit_seconds_charged"],
            "continuation_compute_seconds_cap": current["fit_seconds_cap"],
            **{key: prior[key] + current[key] for key in ("registration_attempts_used",
                "experimental_fit_seconds", "auxiliary_fit_seconds_conservative", "fit_seconds_charged")},
            "registration_attempts_cap": prior["registration_attempts_used"] + current["registration_attempts_cap"],
            "fit_seconds_cap": prior["fit_seconds_charged"] + current["fit_seconds_cap"]}


def _transfer_reserves(stage_used, planned_stage=None):
    remaining = {stage: row["attempts"] - stage_used[stage] - (stage == planned_stage)
                 for stage, row in TRANSFER_RESERVES.items()}
    return (sum(remaining.values()),
            sum(remaining[stage] * row["seconds_per_attempt"] for stage, row in TRANSFER_RESERVES.items()))


def _transfer_status(base, events):
    contract, auth = _document(base, TRANSFER_CONTRACT), _document(base, TRANSFER_AUTHORITY)
    source = _document(base, TRANSFER_SOURCE_AUTHORITY)
    carry = contract["carry_forward"]
    required = {CONTINUATION_AUTHORITY, CONTINUATION_CONTRACT, TRANSFER_SOURCE_AUTHORITY,
                carry["terminal_study_path"], carry["completion_receipt_path"],
                contract["source_result_path"], contract["source_state_publication_path"]}
    if (carry["authority_path"] != CONTINUATION_AUTHORITY or carry["contract_path"] != CONTINUATION_CONTRACT
            or contract["prior_budgets_reset"] is not False or contract["unspent_A_credit_added"] is not False
            or contract["schedule_change_authorized"] is not False or contract["no_retry"] is not True
            or contract["one_new_experiment_per_cycle"] is not True
            or auth["source_authority_path"] != TRANSFER_SOURCE_AUTHORITY
            or auth["source_authority_sha256"] != _bound_hash(base, TRANSFER_SOURCE_AUTHORITY)
            or source["stage_a_contract_path"] != CONTINUATION_CONTRACT
            or source["stage_b"]["additional_registration_attempts_cap"] != 12
            or source["stage_b"]["additional_compute_seconds_cap"] != 72000
            or source["stage_b"]["reserve_for_replication_and_fresh_final_required"] is not True
            or source["stage_b"]["all_fit_evaluation_tests_and_failures_charged"] is not True
            or {row["id"]: row["registration_cap"] for row in contract["stages"]} != TRANSFER_STAGES
            or contract["protected_allocations"] != TRANSFER_RESERVES
            or contract["deliverables"] != source["deliverables"]
            or contract["economic_claim_gates"] != _document(base, CONTINUATION_CONTRACT)["economic_claim_gates"]
            or not required <= set(carry["document_sha256"])
            or any(_bound_hash(base, path) != digest for path, digest in carry["document_sha256"].items())):
        raise ValueError("Transfer authority or immutable carry-forward evidence changed")
    previous_events = [event for event in events if event.get("program_id") == carry["program_id"]]
    ended = [event for event in previous_events if event.get("event") == "research_program_completed"]
    reserved = {event["charge_id"] for event in previous_events
                if event.get("event") == "research_program_aux_fit_reserved"}
    charged = {event["charge_id"] for event in previous_events
               if event.get("event") == "research_program_aux_fit_charged"}
    if (sha256_json(previous_events) != carry["program_events_sha256"] or len(ended) != 1
            or ended[0].get("receipt_path") != carry["completion_receipt_path"]
            or ended[0].get("receipt_sha256") != _bound_hash(base, carry["completion_receipt_path"])
            or reserved != charged):
        raise ValueError("Closed A events, completion or unresolved auxiliary reservations changed")
    previous = _continuation_status(base, study_path=carry["terminal_study_path"], include_raw_current=True)
    keys = ("registration_attempts_used", "experimental_fit_seconds",
            "auxiliary_fit_seconds_conservative", "fit_seconds_charged")
    if (not previous or previous["id"] != carry["program_id"] or not previous["program_closed"]
            or previous["paid_run_pending"] or previous["pending_fit_reservation_seconds"] != 0
            or any(previous[key] != carry[key] for key in keys)):
        raise ValueError("Transfer carry-forward counts differ from closed A; no budget reset")
    # Reuse the just-verified raw A wallet rather than parse every archived result twice.
    stage_a = previous.pop("_raw_current_program")
    if any(stage_a[key] != carry["stage_a_accounting"][key] for key in keys):
        raise ValueError("Stage A accounting differs from immutable transfer carry-forward")
    current = _status_for(base, authority_path=TRANSFER_AUTHORITY, contract_path=TRANSFER_CONTRACT,
                          expected_caps=(12, 72000), authorization_event="research_program_transfer_prototype_authorized")
    protected_tickets, protected_seconds = _transfer_reserves(current["stage_registration_attempts"])
    owned_auxiliary = 0.
    if (current["study_path"] == HAR_CONTINUATION_STUDY
            or any(e.get("study_path") == HAR_CONTINUATION_STUDY
                   or e.get("charge_id") in HAR_CONTINUATION_AUXILIARY_CAPS for e in events)):
        combined, _ = _har_continuation_auxiliary(base, events)
        owned_auxiliary = combined - 3900
        if not current["stage_registration_attempts"]["independent_replication"]:
            protected_seconds -= combined
    elif (current["study_path"] == HAR_PROCESS_LAUNCH_STUDY
            or any(e.get("study_path") == HAR_PROCESS_LAUNCH_STUDY
                   or e.get("charge_id") == HAR_PROCESS_LAUNCH_AUXILIARY_ID for e in events)):
        owned_auxiliary, _ = _har_process_launch_auxiliary(base, events)
        if not current["stage_registration_attempts"]["independent_replication"]:
            protected_seconds -= owned_auxiliary
    elif (current["study_path"] == HAR_LABEL_GUARD_STUDY
            or any(e.get("study_path") == HAR_LABEL_GUARD_STUDY
                   or e.get("charge_id") == HAR_LABEL_GUARD_AUXILIARY_ID for e in events)):
        owned_auxiliary, _ = _har_label_guard_auxiliary(base, events)
        if not current["stage_registration_attempts"]["independent_replication"]:
            protected_seconds -= owned_auxiliary
    elif (current["study_path"] == HAR_IMPORT_EXIT_STUDY
            or any(e.get("study_path") == HAR_IMPORT_EXIT_STUDY
                   or e.get("charge_id") == HAR_IMPORT_EXIT_AUXILIARY_ID for e in events)):
        owned_auxiliary, _ = _har_import_exit_auxiliary(base, events)
        if not current["stage_registration_attempts"]["independent_replication"]:
            protected_seconds -= owned_auxiliary
    elif current["study_path"] == HAR_REPLICATION_STUDY:
        owned_auxiliary, _ = _har_replication_auxiliary(base, events)
        current_tickets = [e for e in events if e.get("event") == "research_program_registration_started"
                           and e.get("program_id") == current["id"] and e.get("study_path") == HAR_REPLICATION_STUDY]
        if current["stage_registration_attempts"]["independent_replication"] != len(current_tickets):
            raise ValueError("HAR scoped preparation owns only first replication slot")
        if not current_tickets:
            protected_seconds -= owned_auxiliary
    return {**current, "prior_program_closed": True, "prior_program_id": previous["id"],
            "prior_registration_attempts_used": previous["registration_attempts_used"],
            "prior_compute_seconds_charged": previous["fit_seconds_charged"],
            "stage_a_accounting": stage_a,
            "current_program_registration_attempts_used": current["registration_attempts_used"],
            "stage_b_registration_attempts_used": current["registration_attempts_used"],
            "stage_b_registration_attempts_cap": 12,
            "stage_b_compute_seconds_charged": current["fit_seconds_charged"],
            "stage_b_compute_seconds_cap": 72000,
            "protected_future_registration_attempts": protected_tickets,
            "protected_future_compute_seconds": protected_seconds,
            "study_owned_auxiliary_seconds": owned_auxiliary,
            **{key: previous[key] + current[key] for key in keys},
            "registration_attempts_cap": previous["registration_attempts_used"] + 12,
            "fit_seconds_cap": previous["fit_seconds_charged"] + 72000}


def status(base):
    """Only an explicit hash-bound event can activate the approved next stage."""
    events = read_jsonl(base / "research/events.jsonl")
    if any(event.get("event") == "research_program_transfer_prototype_authorized" for event in events):
        return _transfer_status(base, events)
    return _continuation_status(base)


def _check_transfer_study_reserve(value, study):
    if "stage_b_registration_attempts_used" not in value:
        return
    tickets, seconds = _transfer_reserves(value["stage_registration_attempts"], study["stage"])
    resources = study["resources"]
    auxiliary_cap = resources["auxiliary_test_seconds_cap"]
    worker_cap = resources["fit_seconds_study_cap"]
    credit = value.get("study_owned_auxiliary_seconds", 0.) if value["study_path"] in {HAR_REPLICATION_STUDY, HAR_CONTINUATION_STUDY} else 0.
    if (not _finite_seconds(auxiliary_cap) or not _finite_seconds(worker_cap)
            or not _finite_seconds(credit) or credit > auxiliary_cap):
        raise ValueError("Invalid finite study resource cap or owned auxiliary credit")
    if (12 - value["stage_b_registration_attempts_used"] - 1 < tickets
            or value["unreserved_fit_seconds_remaining"] - worker_cap - (auxiliary_cap - credit) < seconds):
        raise ValueError("Study would consume protected replication, fresh-final or prototype reserves")


def scope_problems(base, experiment_id=None):
    value = status(base)
    if not value or not value["scoring_authorized"]:
        return ["Research study is not ready, expired or terminal; preregister a new bounded study within program caps"]
    if load_config(base).benchmark_version != value["cohort"]:
        return ["Research authority does not cover this cohort"]
    if experiment_id is None and value["experiment_id"]:
        return ["Current study already registered; no duplicate"]
    if experiment_id is not None and value["experiment_id"] != experiment_id:
        return ["Research authority does not cover this experiment"]
    return []


def auxiliary_reserve(base, charge_id, seconds_cap):
    value = status(base)
    if (not value or value["program_closed"] or type(seconds_cap) not in (int, float)
            or not math.isfinite(seconds_cap) or seconds_cap <= 0 or seconds_cap > value["unreserved_fit_seconds_remaining"]):
        raise ValueError("Insufficient research budget for auxiliary fit reservation")
    events = read_jsonl(base / "research/events.jsonl")
    binding = {}
    protected = value.get("protected_future_compute_seconds", 0)
    if charge_id in HAR_OWN_AUXILIARY_IDS:
        if value["study_path"] != HAR_REPLICATION_STUDY:
            raise ValueError("HAR auxiliary ID belongs only to its exact current study")
        credit, binding = _har_replication_auxiliary(base, events)
        if credit + seconds_cap > 2400:
            raise ValueError("HAR owned auxiliary allocation exceeded")
        protected = 41000
        if not value["stage_registration_attempts"]["independent_replication"]:
            _check_transfer_study_reserve(value, _document(base, HAR_REPLICATION_STUDY))
    elif charge_id in HAR_CONTINUATION_AUXILIARY_CAPS:
        if value["study_path"] != HAR_CONTINUATION_STUDY or seconds_cap != HAR_CONTINUATION_AUXILIARY_CAPS[charge_id]:
            raise ValueError("HAR continuation auxiliary reservation differs from exact study allocation")
        _, binding = _har_continuation_auxiliary(base, events)
        if not value["stage_registration_attempts"]["independent_replication"]:
            _check_transfer_study_reserve(value, _document(base, HAR_CONTINUATION_STUDY))
            protected -= seconds_cap
    if ("stage_b_registration_attempts_used" in value and
            seconds_cap > value["unreserved_fit_seconds_remaining"] - protected):
        raise ValueError("Auxiliary reservation would consume protected future research reserves")
    if any(e.get("charge_id") == charge_id for e in events):
        raise ValueError("Auxiliary fit ID already consumed")
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_aux_fit_reserved", "created_at": utc_now(),
                 "program_id": value["id"], "charge_id": charge_id, "seconds_cap": seconds_cap, **binding})


def auxiliary_charge(base, charge_id, seconds):
    value = status(base)
    events = read_jsonl(base / "research/events.jsonl")
    if any(e.get("event") == "research_program_aux_fit_charged" and e.get("charge_id") == charge_id for e in events):
        raise ValueError("Repeated auxiliary fit accounting")
    reservations = [e for e in events if e.get("event") == "research_program_aux_fit_reserved" and e.get("charge_id") == charge_id]
    if (len(reservations) != 1 or type(seconds) not in (int, float) or not math.isfinite(seconds)
            or not 0 <= seconds <= reservations[0]["seconds_cap"]):
        raise ValueError("Auxiliary fit charge exceeds reservation or has no reservation")
    binding = {}
    if charge_id in HAR_OWN_AUXILIARY_IDS:
        _, binding = _har_replication_auxiliary(base, events)
    elif charge_id == HAR_IMPORT_EXIT_AUXILIARY_ID:
        _, binding = _har_import_exit_auxiliary(base, events)
        if seconds != 600:
            raise ValueError("HAR import/exit charge cannot release its conservative allocation")
    elif charge_id == HAR_LABEL_GUARD_AUXILIARY_ID:
        _, binding = _har_label_guard_auxiliary(base, events)
        if seconds != 600:
            raise ValueError("HAR label-guard charge cannot release its conservative allocation")
    elif charge_id == HAR_PROCESS_LAUNCH_AUXILIARY_ID:
        _, binding = _har_process_launch_auxiliary(base, events)
        if seconds != 300:
            raise ValueError("HAR process-launch charge cannot release its conservative allocation")
    elif charge_id in HAR_CONTINUATION_AUXILIARY_CAPS:
        _, binding = _har_continuation_auxiliary(base, events)
        if seconds != HAR_CONTINUATION_AUXILIARY_CAPS[charge_id]:
            raise ValueError("HAR continuation charge cannot release its conservative allocation")
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_aux_fit_charged", "created_at": utc_now(),
                 "program_id": value["id"], "charge_id": charge_id, "seconds": seconds, **binding})
    status(base)  # Validate the durable accounting, including failed test runs.


def verify_pvm01_fresh_realization(base, seeds, nonces, *, include_latest=False, include_transport=False, include_replication=False, include_dense_noise=False, include_confirmation=False, include_base_reference=False):
    """Reject consumed PVM units before any newly realized arrays or fit."""
    if (len(seeds) != 5 or len(set(seeds)) != 5 or len(nonces) != 5
            or len(set(nonces)) != 5 or any(not re.fullmatch(r"[0-9a-f]{64}", n) for n in nonces)):
        raise ValueError("PVM01 unit realization must contain five independent seeds/nonces")
    previous = {
        "EXP-20261004-0004": "research/laboratory/archive/EXP-20261004-0004-runtime/research/tmp/EXP-20261004-0004",
        "EXP-20261004-0005": "research/laboratory/archive/EXP-20261004-0005-runtime",
        "EXP-20261004-0006": "research/laboratory/archive/EXP-20261004-0006-runtime/research/tmp/EXP-20261004-0006",
        "EXP-20261004-0007": "research/laboratory/archive/EXP-20261004-0007-runtime/research/tmp/EXP-20261004-0007",
    }
    if include_latest:
        previous["EXP-20261004-0008"] = "research/laboratory/archive/EXP-20261004-0008-runtime/research/tmp/EXP-20261004-0008"
    if include_transport:
        if not include_latest:
            raise ValueError("Transport history requires capacity-exposure history")
        previous["EXP-20261005-0001"] = "research/laboratory/archive/EXP-20261005-0001-runtime/research/tmp/EXP-20261005-0001"
    if include_replication:
        if not include_latest or not include_transport:
            raise ValueError("Replication history requires all earlier PVM histories")
        previous["EXP-20261005-0002"] = "research/laboratory/archive/EXP-20261005-0002-runtime/research/tmp/EXP-20261005-0002"
    if include_dense_noise:
        if not include_latest or not include_transport or not include_replication:
            raise ValueError("Dense-noise confirmation requires all earlier PVM histories")
        previous["EXP-20261005-0003"] = "research/laboratory/archive/EXP-20261005-0003-runtime/research/tmp/EXP-20261005-0003"
    if include_confirmation:
        if not all((include_latest, include_transport, include_replication, include_dense_noise)):
            raise ValueError("Base-reference comparison requires all earlier PVM histories")
        previous["EXP-20261005-0004"] = "research/laboratory/archive/EXP-20261005-0004-runtime/research/tmp/EXP-20261005-0004"
    if include_base_reference:
        if not all((include_latest, include_transport, include_replication, include_dense_noise, include_confirmation)):
            raise ValueError("Frozen fresh final requires all earlier PVM histories")
        previous["EXP-20261005-0005"] = "research/laboratory/archive/EXP-20261005-0005-runtime/research/tmp/EXP-20261005-0005"
    for identity, relative in previous.items():
        directory = base / relative
        runtime = load_json(directory / "runtime-plan.json")
        private_path = directory / "pvm01-private-data.json"
        private = load_json(private_path)
        if (private["experiment_id"] != identity or runtime["experiment_id"] != identity
                or sha256_file(private_path) != runtime["pvm01_private_data_sha256"]):
            raise ValueError("Preserved PVM01 realization binding changed")
        if set(seeds) & set(runtime["matrix"]["seeds"]) or set(nonces) & set(private["unit_nonces"]):
            raise ValueError("Consumed PVM01 seed/data collision; no replacement or retry")


def create_plan(base, requested=None):
    """Called only by the audited CLI; reserve before every attempted validation."""
    from .gates import ensure_can_create_plan
    from .ledger import next_experiment_id, register_plan
    from .schemas import validate_document
    from .integrity import manifest_path
    from .baseline_semantics import verify_preflight_certificate, verify_required_baselines
    from .utils import atomic_write_json
    from .runner import _git_value
    value = status(base)
    if not value or value["program_terminal"] or value["registration_budget_exhausted"]:
        raise ValueError("Research program absent or exhausted")
    study = _document(base, value["study_path"])
    if study.get("study_kind") == "preparation_only":
        raise ValueError("Preparation-only study cannot register or score an experiment")
    if value["stage_registration_attempts"][study["stage"]] >= value["stage_registration_caps"][study["stage"]]:
        raise ValueError("Research milestone registration budget exhausted")
    events = read_jsonl(base / "research/events.jsonl")
    if any(e.get("event") == "research_program_registration_started" and e.get("study_path") == value["study_path"] for e in events):
        raise ValueError("Study ticket already consumed; do not retry")
    ticket = value.get("current_program_registration_attempts_used",
                       value.get("continuation_registration_attempts_used", value["registration_attempts_used"])) + 1
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_registration_started", "created_at": utc_now(),
                 "program_id": value["id"], "study_path": value["study_path"], "ticket": ticket})
    try:
        _check_transfer_study_reserve(value, study)
        if requested is not None and (requested.get("candidates") != study["candidates"]
                or requested.get("budget") != "quick" or requested.get("pc01_phase") is not None):
            raise ValueError("Legacy request differs from frozen research study; use program register")
        ensure_can_create_plan(base)
        if study["resources"]["fit_seconds_study_cap"] > value["unreserved_fit_seconds_remaining"]:
            raise ValueError("Study worst-case fit exceeds remaining global fit budget")
        experiment_id = next_experiment_id(base)
        protocol = {"authority_path": value["authority_path"], "program_contract_path": value["contract_path"],
                    "program_contract_sha256": sha256_file(base / value["contract_path"]), "study_path": value["study_path"],
                    "study_sha256": sha256_file(base / value["study_path"]), "registration_ticket": ticket,
                    **_study_scope(study)}
        metrics = ["accuracy", "fact_top1_accuracy", "dense_unknown_rejection", "mean_query_ops", "p95_latency_us", "state_bytes", "fit_ops", "preprocessing_ops"]
        paired_view = study["cohort"] in ("paired_view_mutable_memory_v1", "paired_view_mutable_memory_v2", "paired_view_mutable_memory_v3", "paired_view_mutable_memory_v4", "paired_view_mutable_memory_v5", "paired_view_mutable_memory_v6", "paired_view_mutable_memory_v7", "paired_view_mutable_memory_v8", "paired_view_mutable_memory_v9", "paired_view_mutable_memory_v10", "paired_view_mutable_memory_v11")
        plan = {"schema_version": 1, "experiment_id": experiment_id, "parent_experiment_id": None, "created_at": utc_now(),
                "status": "planned", "hypothesis_id": "HYP-0012", "title": study["id"], "research_question": study["question"],
                "architecture_family": "paired_view_learning_reference" if paired_view else "muc_v2_reference_diagnostic", "candidates": study["candidates"], "benchmark": study["cohort"],
                "evaluator_sha256": load_json(manifest_path(base))["evaluator_sha256"], "budget": "quick", "matrix": study["matrix"],
                "primary_metrics": metrics, "metric_directions": {m: "maximize" if m in metrics[:3] else "minimize" for m in metrics},
                "predicted_outcome": ("Legal trained alignment may improve ranking/absence over untrained and shuffled controls; classical transport may suffice; no predetermined success." if paired_view else "More hard-negative steps may improve fit; paired namespace probes discriminate generalization; no predetermined success."),
                "falsification_criteria": ["Stable-reference gates fail, or all outcomes are invalid/partial; retain every outcome."],
                "promotion_criteria": ["None: diagnostic only; economic prototype needs fresh replicated final and classical non-domination."],
                "alternative_explanations": ["Observation alignment, rejection and ranking failures are measured separately." if paired_view else "Undertraining, rejection, namespace shift and ranking failures are measured separately."],
                "confounds": ["Visible synthetic development; five combined seed/data units; no externally blinded final; update labels are not reasoning depth." if paired_view else "Visible synthetic development; five combined seed/data units; steps change training cost intentionally."],
                "outcome_policy": {"positive": study["decision_policy"], "null": study["decision_policy"], "negative": study["decision_policy"]},
                "eligibility_contract": {"metric": "accuracy", "minimum": .90}, "research_program_protocol": protocol,
                "git_before": {"commit": _git_value(base, "rev-parse", "HEAD"), "branch": _git_value(base, "branch", "--show-current"),
                               "dirty": bool(_git_value(base, "status", "--porcelain"))}}
        if study.get("study_kind") in {"paired_view_delta_memory", "paired_view_compact_feature_memory", "paired_view_capacity_exposure"}:
            common = [m for m in metrics if m != "fact_top1_accuracy"]
            plan.update(architecture_family="learned_transport_classical_delta_memory",
                primary_metrics=common,
                metric_directions={m: "maximize" if m in {"accuracy", "dense_unknown_rejection"} else "minimize" for m in common},
                predicted_outcome="Local delta may improve replacement while retaining facts; compact capacity and absence may fail, and strong classical retrieval may dominate.",
                falsification_criteria=["Any of the four preregistered simultaneous primary or competence gates fails; preserve valid narrow effects and exact tested scope."],
                alternative_explanations=["Classical RFF/LMS update, retrieval, finite capacity, representation learning and deployment overhead are distinct explanations."])
            if study["study_kind"] == "paired_view_compact_feature_memory":
                plan.update(architecture_family="learned_compact_features_classical_delta_memory",
                    predicted_outcome="Feature learning may improve matched512 capacity over frozen/shuffled maps; compact capacity and absence may fail, and classical retrieval may dominate.",
                    falsification_criteria=["Any frozen compact feature primary or competence gate fails; preserve narrow effects, all outcomes and exact recipe."])
            if study["study_kind"] == "paired_view_capacity_exposure":
                plan.update(architecture_family="learned_compact_features_capacity_exposure",
                    predicted_outcome="K512 optimizer exposure may improve the fixed512-feature memory beyond small/frozen/shuffled controls; larger fitting work is charged and strong classics may dominate.",
                    falsification_criteria=["Any frozen exposure primary or competence gate fails; preserve narrow effects and exact tested recipe."])
        if study.get("study_kind") == "paired_view_transport_compression_adverse":
            common = [m for m in metrics if m != "fact_top1_accuracy"]
            plan.update(architecture_family="learned_transport_compression_adverse",
                primary_metrics=common,
                metric_directions={m: "maximize" if m in {"accuracy", "dense_unknown_rejection"} else "minimize" for m in common},
                predicted_outcome="Write-only PCA may preserve learned transport quality under noise0.02/0.04; classical controls may dominate; no predetermined success.",
                falsification_criteria=["Any frozen eight primary or competence gate fails; invalid fit identity makes comparison inconclusive."],
                alternative_explanations=["Classical transport/PCA/exact retrieval, nonlinear representation and deployment overhead remain distinct explanations."])
        if study.get("study_kind") in {"native_frozen_source_transfer", "asm01_frozen_source_transfer"}:
            plan.update(architecture_family="frozen_source_features_native_sensor_memory",
                predicted_outcome="Actual frozen source weights may add useful native information beyond preserved untrained/shuffled states under identical target readout; native classical retrieval may suffice; no predetermined success.",
                falsification_criteria=["Any frozen source-information primary gate fails; failed reference or source/data/resource integrity yields an inconclusive qualified comparison, not architectural falsification."],
                alternative_explanations=["Target readout alone, native similarity, PCA/kernel/temporal alignment and hardware overhead must be separated from source information."],
                confounds=["Visible public physical subjects; overlapping training windows are not independent units. Five disjoint evaluation subjects/source-seed pairs; no external blind holdout. Latest-write logic is hand-written; update rounds are not reasoning depth."])
        validate_document("experiment_plan", plan, base)
        verify_required_baselines(plan, base, run_tests=False)
        verify_preflight_certificate(base)
        path = base / "research/plans" / f"{experiment_id}.json"
        if path.exists():
            raise FileExistsError("Research plan already exists")
        atomic_write_json(path, plan)
        digest = register_plan(plan, path, base)
        append_jsonl(base / "research/events.jsonl", {"event": "research_program_registered", "created_at": utc_now(),
                     "program_id": value["id"], "ticket": ticket, "study_path": value["study_path"],
                     "experiment_id": experiment_id, "plan_path": path.relative_to(base).as_posix(), "plan_sha256": digest})
        return path
    except Exception as exc:
        append_jsonl(base / "research/events.jsonl", {"event": "research_program_registration_failed", "created_at": utc_now(),
                     "program_id": value["id"], "ticket": ticket, "study_path": value["study_path"], "error": str(exc)})
        raise
