"""Separate, inclusive-wall C authority; its events never debit legacy B.

Nested component measurements describe resources, not additional wallet charges.
Only explicit activation and a subsequently frozen scientific study permit C.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import math
import os
from pathlib import Path

from .config import load_config
from .ledger import append_jsonl, read_jsonl
from .utils import load_json, sha256_json

CONTRACT = "research/plans/NEXTAI-C-STABILIZATION-ASM-SCREEN-V1.json"
CONTRACT_SHA256 = "4a95f8bef9cdfef23abf27c3b0dbee74cb9b9b1796b822c6eb2b0edca7a47f41"
AUTHORITY = "research/laboratory/NEXTAI-C-HUMAN-AUTHORITY-20261008.md"
AUTHORITY_SHA256 = "fbd30ba3d9b72746ca8407103e62517b650547b10642140921ee5cfe2d6d586e"
ENGINEERING = "research/plans/NEXTAI-C-ENGINEERING-PREREGISTRATION-V1.json"
ENGINEERING_SHA256 = "bb1d7aa30041edf7b11d2ed7dcb93f02584a0dce7675b3affa73d35dc6f6a56a"
EVENTS = "research/c_events.jsonl"
PROGRAM_ID = "NEXTAI-C-STABILIZATION-ASM-SCREEN-20261008-V1"
B_ID = "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1"
B_CONTRACT = "research/plans/NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-V1.json"
RELEASE_CHECKS = ("complete1830_native_intake", "all_conformance", "same_builder_dry_run",
                  "source_and_data_hash_freeze", "preflight", "readiness")
INPUT_CHECKS = tuple(key for key in RELEASE_CHECKS if key not in {"same_builder_dry_run", "readiness"})
_EVENT_TYPES = {"activated", "scientific_study_frozen", "ready", "registration_started",
                "registered", "registration_failed", "checkpoint", "scientific_cost",
                "auxiliary_reserved", "auxiliary_measured", "liability_increased", "closed", "inputs_ready",
                "scientific_finished"}


def _now():
    return datetime.now(timezone.utc)


def _date(value):
    if not isinstance(value, str):
        raise ValueError("C timestamp must be an explicit UTC string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("C timestamp must specify UTC")
    return parsed


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def _path(base, relative):
    if not isinstance(relative, str) or not relative:
        raise ValueError("Missing C document path")
    target = (Path(base) / relative).resolve()
    if Path(relative).is_absolute() or not target.is_relative_to(Path(base).resolve()):
        raise ValueError("C evidence must remain inside this checkout")
    return target


def _hash(path, length=None):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        remaining = length
        while remaining is None or remaining:
            chunk = handle.read(1024 * 1024 if remaining is None else min(1024 * 1024, remaining))
            if not chunk:
                if remaining:
                    raise ValueError("Preserved legacy event prefix was truncated")
                break
            digest.update(chunk)
            if remaining is not None:
                remaining -= len(chunk)
    return digest.hexdigest()


def _binding():
    return {"program_id": PROGRAM_ID, "contract_path": CONTRACT,
            "contract_sha256": CONTRACT_SHA256, "authority_path": AUTHORITY,
            "authority_sha256": AUTHORITY_SHA256, "engineering_path": ENGINEERING,
            "engineering_sha256": ENGINEERING_SHA256}


def _documents(base):
    for path, expected in ((CONTRACT, CONTRACT_SHA256), (AUTHORITY, AUTHORITY_SHA256),
                           (ENGINEERING, ENGINEERING_SHA256)):
        if _hash(_path(base, path)) != expected:
            raise ValueError("C authority, contract or engineering preregistration changed")
    contract = load_json(_path(base, CONTRACT))
    engineering = load_json(_path(base, ENGINEERING))
    liability = contract["historical_admin_liability"]
    preserved = contract["B_preserved"]
    caps = {"total_seconds_cap": 43200, "scientific_registration_attempts_cap": 1,
            "scientific_full_workers_seconds_cap": 9000, "scientific_supervised_fit_seconds_cap": 3600}
    if (contract["id"] != PROGRAM_ID or contract["authority_copy_path"] != AUTHORITY
            or contract["authority_sha256"] != AUTHORITY_SHA256
            or contract["engineering_plan_path"] != ENGINEERING
            or engineering["parent_contract_path"] != CONTRACT
            or contract["work_started_at"] != "2026-10-07T23:42:00Z"
            or contract["wall_deadline_at"] != "2026-10-08T11:42:00Z"
            or contract["effective_budget_deadline_at_with_initial600_debt"] != "2026-10-08T11:32:00Z"
            or any(not _finite(contract.get(key)) or contract[key] != amount for key, amount in caps.items())
            or liability["initial_conservative_settlement_seconds"] != 600
            or not _finite(liability["initial_conservative_settlement_seconds"])
            or liability["upper_bound_verified"] is not False
            or liability["unmeasured_later_work_is_not_zero"] is not True
            or liability["additional_proven_liability_must_increase_C_charge"] is not True
            or preserved["registration_attempts_used"] != 2
            or preserved["compute_seconds_charged"] != 30999.55024020007
            or preserved["protected_registration_attempts"] != 6
            or preserved["protected_seconds"] != 41000 or preserved["C_credit_added_to_B"] is not False
            or tuple(contract["scientific_release_gates"]) != RELEASE_CHECKS):
        raise ValueError("C finite authority or preserved B allocation does not match")
    evidence = liability["evidence_path"]
    if _hash(_path(base, evidence)) != liability["evidence_sha256"]:
        raise ValueError("Historical unpaid administration evidence changed")
    if _hash(_path(base, B_CONTRACT)) != preserved["contract_sha256"]:
        raise ValueError("Preserved B contract changed")
    return contract


def is_active(base):
    """A document or config alone cannot activate C; corrupt C never falls into B."""
    values = read_jsonl(_path(base, EVENTS))
    if not values:
        return False
    if values[0].get("event") != "activated":
        raise ValueError("C ledger exists without its sole activation")
    return True


def _legacy_subset(base):
    return [event for event in read_jsonl(_path(base, "research/events.jsonl"))
            if event.get("program_id") == B_ID]


def _preservation(base, contract, activation=None):
    global_path = _path(base, "research/events.jsonl")
    if activation is None:
        length = global_path.stat().st_size
        if _hash(global_path) != contract["B_preserved"]["events_prefix_sha256"]:
            raise ValueError("C activation requires the frozen original global event prefix")
        old_contract = load_json(_path(base, B_CONTRACT))
        required = {old_contract["source_result_path"], old_contract["source_state_publication_path"],
                    old_contract["carry_forward"]["completion_receipt_path"]}
        anchors = {path: old_contract["carry_forward"]["document_sha256"][path] for path in required}
        return {"B_events_prefix_bytes": length, "B_events_prefix_sha256": _hash(global_path),
                "B_program_events_sha256": sha256_json(_legacy_subset(base)),
                "preserved_evidence_sha256": anchors}
    length = activation.get("B_events_prefix_bytes")
    if (type(length) is not int or length < 1
            or activation.get("B_events_prefix_sha256") != contract["B_preserved"]["events_prefix_sha256"]
            or _hash(global_path, length) != activation["B_events_prefix_sha256"]
            or sha256_json(_legacy_subset(base)) != activation.get("B_program_events_sha256")):
        raise ValueError("C altered legacy B history or its original event prefix")
    anchors = activation.get("preserved_evidence_sha256")
    old_contract = load_json(_path(base, B_CONTRACT))
    required = {old_contract["source_result_path"], old_contract["source_state_publication_path"],
                old_contract["carry_forward"]["completion_receipt_path"]}
    expected = {path: old_contract["carry_forward"]["document_sha256"][path] for path in required}
    if anchors != expected or any(_hash(_path(base, path)) != digest for path, digest in expected.items()):
        raise ValueError("Preserved source result, fitted-state publication or A closure changed")


def _read(base):
    contract = _documents(base)
    events = read_jsonl(_path(base, EVENTS))
    if not events:
        return contract, []
    previous_hash, previous_total, previous_elapsed, liability = None, 0., 0., 600.
    counts = {}
    auxiliary = {}
    worker, fit = 0., 0.
    frozen = None
    cost_receipts = set()
    for index, event in enumerate(events, 1):
        name = event.get("event")
        if (name not in _EVENT_TYPES or any(event.get(k) != v for k, v in _binding().items())
                or type(event.get("sequence")) is not int or event["sequence"] != index
                or event.get("previous_event_sha256") != previous_hash
                or index == 1 and name != "activated"):
            raise ValueError("Foreign, missing, repeated or reordered C event")
        counts[name] = counts.get(name, 0) + 1
        if name in {"activated", "scientific_study_frozen", "inputs_ready", "ready", "registration_started", "registered",
                    "registration_failed", "scientific_finished", "closed"} and counts[name] != 1:
            raise ValueError("Repeated C milestone or paid scientific retry")
        if name == "liability_increased":
            if (not _finite(event.get("additional_seconds")) or event["additional_seconds"] <= 0
                    or _hash(_path(base, event["receipt_path"])) != event["receipt_sha256"]):
                raise ValueError("Additional C liability requires positive, preserved evidence")
            liability += event["additional_seconds"]
        elapsed, total = event.get("outer_elapsed_seconds"), event.get("total_seconds_charged")
        event_time = _date(event.get("created_at"))
        expected_elapsed = (event_time - _date(contract["work_started_at"])).total_seconds()
        if (not _finite(elapsed) or elapsed < previous_elapsed or abs(elapsed - expected_elapsed) > 1e-6
                or not _finite(total) or total < previous_total
                or event.get("liability_seconds") != liability or abs(total - elapsed - liability) > 1e-6):
            raise ValueError("C outer timing or liability was reset, refunded or double charged")
        if name == "scientific_study_frozen":
            if (event.get("study_path") != contract["scientific_plan_path"]
                    or _hash(_path(base, event["study_path"])) != event.get("study_sha256")):
                raise ValueError("C scientific study freeze changed")
            frozen = event
        if name in {"inputs_ready", "ready", "registration_started", "registered", "registration_failed", "scientific_cost", "scientific_finished"}:
            if not frozen or any(event.get(k) != frozen.get(k) for k in ("study_path", "study_sha256", "cohort", "stage")):
                raise ValueError("C scientific milestone lacks exact frozen study binding")
        if name in {"registered", "registration_failed"}:
            if counts.get("registration_started") != 1 or counts.get("registered", 0) + counts.get("registration_failed", 0) != 1:
                raise ValueError("C outcome has no unique paid attempt")
        if name == "registration_started" and (event.get("registration_ticket") != 1
                or type(event.get("registration_ticket")) is not int):
            raise ValueError("C owns exactly ticket one")
        if name == "registered" and (_hash(_path(base, event["plan_path"])) != event["plan_file_sha256"]
                or sha256_json(load_json(_path(base, event["plan_path"]))) != event["plan_sha256"]):
            raise ValueError("Registered C plan changed")
        if name == "ready":
            if counts.get("inputs_ready") != 1:
                raise ValueError("C final readiness must follow independently verified inputs")
            _readiness_receipt(base, event["receipt_path"], frozen, event["receipt_sha256"])
        if name == "inputs_ready":
            _inputs_receipt(base, event["receipt_path"], frozen, event["receipt_sha256"])
        if name in {"auxiliary_reserved", "auxiliary_measured"}:
            identity = event.get("charge_id")
            if not isinstance(identity, str) or not identity or event.get("nested_not_added_to_total") is not True:
                raise ValueError("Malformed C nested auxiliary identity")
            if name == "auxiliary_reserved":
                if identity in auxiliary or not _finite(event.get("seconds_cap")) or event["seconds_cap"] <= 0:
                    raise ValueError("Duplicate or nonfinite C auxiliary reservation")
                auxiliary[identity] = event
            else:
                if identity not in auxiliary or auxiliary[identity].get("measured") or not _finite(event.get("seconds")):
                    raise ValueError("Missing or repeated C auxiliary measurement")
                auxiliary[identity] = {**auxiliary[identity], "measured": True}
        if name == "scientific_cost":
            registered = next((e for e in events[:index] if e["event"] == "registered"), None)
            if (not registered or event.get("experiment_id") != registered["experiment_id"]
                    or event.get("receipt_sha256") in cost_receipts
                    or _hash(_path(base, event["receipt_path"])) != event["receipt_sha256"]):
                raise ValueError("C worker cost requires unique evidence for its registered EXP")
            receipt = load_json(_path(base, event["receipt_path"]))
            if any(receipt.get(k) != event.get(k) for k in (*_binding(), "study_path", "study_sha256", "experiment_id",
                                                          "full_worker_seconds", "supervised_fit_seconds")):
                raise ValueError("C scientific cost receipt binding differs")
            new_worker, new_fit = event.get("full_worker_seconds"), event.get("supervised_fit_seconds")
            if (not _finite(new_worker) or not _finite(new_fit) or new_worker < worker or new_fit < fit or new_fit > new_worker):
                raise ValueError("C actual cumulative resource cost cannot decrease or be clipped")
            worker, fit = new_worker, new_fit
            cost_receipts.add(event["receipt_sha256"])
        if name == "scientific_finished":
            registered = next((e for e in events[:index] if e["event"] == "registered"), None)
            costs = [e for e in events[:index] if e["event"] == "scientific_cost"]
            if not registered or not costs or event.get("experiment_id") != registered["experiment_id"]:
                raise ValueError("C scientific terminality requires recorded registered worker costs")
            _finished_receipt(base, event["receipt_path"], frozen, registered, costs[-1], event["receipt_sha256"])
        if name == "closed" and _hash(_path(base, event["receipt_path"])) != event["receipt_sha256"]:
            raise ValueError("C closure receipt changed")
        previous_hash, previous_total, previous_elapsed = sha256_json(event), total, elapsed
    _preservation(base, contract, events[0])
    if events[0].get("B_preserved") != contract["B_preserved"]:
        raise ValueError("C activation changed preserved B wallet counts")
    return contract, events


@contextmanager
def _lock(base):
    path = _path(base, "research/tmp/c_ledger.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise ValueError("C ledger mutation already locked; do not retry scientific registration") from exc
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        os.fsync(descriptor)
        yield
    finally:
        os.close(descriptor)
        path.unlink()


def _append(base, contract, events, name, **fields):
    now = _now()
    elapsed = (now - _date(contract["work_started_at"])).total_seconds()
    previous = events[-1] if events else None
    liability = previous["liability_seconds"] if previous else 600.
    if name == "liability_increased":
        liability += fields["additional_seconds"]
    if elapsed < 0 or previous and elapsed < previous["outer_elapsed_seconds"]:
        raise ValueError("C clock moved backwards; cannot refund work")
    event = {**_binding(), "event": name, "sequence": len(events) + 1,
             "previous_event_sha256": sha256_json(previous) if previous else None,
             "created_at": now.isoformat(), "outer_elapsed_seconds": elapsed,
             "liability_seconds": liability, "total_seconds_charged": elapsed + liability, **fields}
    append_jsonl(_path(base, EVENTS), event)
    return event


def activate(base):
    """Root calls once; hashes and the B snapshot are checked before any event."""
    with _lock(base):
        contract, events = _read(base)
        if events:
            raise ValueError("C has already been activated; no accounting reset")
        preservation = _preservation(base, contract)
        # Check actual anchor bytes before committing the preservation receipt.
        for path, digest in preservation["preserved_evidence_sha256"].items():
            if _hash(_path(base, path)) != digest:
                raise ValueError("C source/closure preservation anchor differs")
        _append(base, contract, events, "activated", **preservation,
                historical_liability_upper_bound_verified=False, B_preserved=contract["B_preserved"])
    return status(base)


def current_study(base):
    contract, events = _read(base)
    return _current_study(base, contract, events)


def _current_study(base, contract, events):
    if not events:
        raise ValueError("C is not activated")
    path = load_config(base).raw.get("research_program_c", {}).get("study_path", ENGINEERING)
    if path == ENGINEERING:
        study = {**load_json(_path(base, path)), "study_kind": "preparation_only", "stage": "engineering",
                 "cohort": load_config(base).benchmark_version, "registration_attempts_for_this_study_cap": 0}
        study["study_deadline_at"] = datetime.fromtimestamp(
            _date(contract["work_started_at"]).timestamp() + study["engineering_phase_seconds_max"],
            timezone.utc).isoformat()
    elif path == contract["scientific_plan_path"]:
        frozen = next((e for e in events if e["event"] == "scientific_study_frozen"), None)
        if not frozen or _hash(_path(base, path)) != frozen["study_sha256"]:
            raise ValueError("Configured C science lacks its prospective frozen hash")
        study = load_json(_path(base, path))
    else:
        raise ValueError("C authority does not cover the configured study")
    return path, study


def _study_binding(events):
    frozen = next((e for e in events if e["event"] == "scientific_study_frozen"), None)
    if not frozen:
        raise ValueError("C scientific plan is not frozen")
    return {key: frozen[key] for key in ("study_path", "study_sha256", "cohort", "stage")}


def freeze_scientific_study(base, path=None):
    with _lock(base):
        contract, events = _read(base)
        if not events or any(e["event"] in {"scientific_study_frozen", "closed", "registration_started"} for e in events):
            raise ValueError("C study cannot be changed or frozen after execution")
        path = path or contract["scientific_plan_path"]
        if path != contract["scientific_plan_path"]:
            raise ValueError("C permits only its prospectively named ASM scientific study")
        study = load_json(_path(base, path))
        resources = study.get("resources", {})
        if (study.get("study_kind") == "preparation_only" or not isinstance(study.get("cohort"), str)
                or not isinstance(study.get("stage"), str) or study.get("registration_attempts_for_this_study_cap") != 1
                or type(study.get("registration_attempts_for_this_study_cap")) is not int
                or resources.get("fit_seconds_study_cap") != 9000
                or not _finite(resources.get("fit_seconds_study_cap"))
                or resources.get("supervised_fit_seconds_study_cap") != 3600
                or not _finite(resources.get("supervised_fit_seconds_study_cap"))):
            raise ValueError("C scientific ticket/full-worker/fit scope differs from authority")
        _append(base, contract, events, "scientific_study_frozen", study_path=path,
                study_sha256=_hash(_path(base, path)), cohort=study["cohort"], stage=study["stage"])


def _readiness_receipt(base, path, study_binding, digest=None):
    if digest and _hash(_path(base, path)) != digest:
        raise ValueError("C readiness receipt changed")
    receipt = load_json(_path(base, path))
    expected = {"program_id": PROGRAM_ID, "contract_sha256": CONTRACT_SHA256,
                **{key: study_binding[key] for key in ("study_path", "study_sha256", "cohort", "stage")}}
    if (any(receipt.get(k) != v for k, v in expected.items()) or receipt.get("status") != "validated_ready"
            or receipt.get("release_checks") != {key: True for key in RELEASE_CHECKS}
            or any(type(v) is not bool for v in receipt.get("release_checks", {}).values())
            or not isinstance(receipt.get("gate_evidence"), dict)
            or set(receipt["gate_evidence"]) != set(RELEASE_CHECKS)):
        raise ValueError("C readiness lacks all six exact frozen release gates")
    for proof in receipt["gate_evidence"].values():
        if (not isinstance(proof, dict) or set(proof) != {"path", "sha256"}
                or _hash(_path(base, proof["path"])) != proof["sha256"]):
            raise ValueError("C final readiness evidence changed")
    return receipt


def _inputs_receipt(base, path, study_binding, digest=None):
    if digest and _hash(_path(base, path)) != digest:
        raise ValueError("C prospective prerequisite receipt changed")
    receipt = load_json(_path(base, path))
    expected = {"program_id": PROGRAM_ID, "contract_sha256": CONTRACT_SHA256,
                **{key: study_binding[key] for key in ("study_path", "study_sha256", "cohort", "stage")}}
    evidence = receipt.get("gate_evidence")
    if (any(receipt.get(k) != v for k, v in expected.items())
            or receipt.get("status") != "validated_prospective_inputs"
            or receipt.get("release_checks") != {key: True for key in INPUT_CHECKS}
            or any(type(v) is not bool for v in receipt.get("release_checks", {}).values())
            or not isinstance(evidence, dict) or set(evidence) != set(INPUT_CHECKS)):
        raise ValueError("C prospective verification needs all four real input prerequisites")
    for proof in evidence.values():
        if (not isinstance(proof, dict) or set(proof) != {"path", "sha256"}
                or _hash(_path(base, proof["path"])) != proof["sha256"]):
            raise ValueError("C prospective intake/conformance/source/preflight evidence changed")
    return receipt


def mark_inputs_ready(base, receipt_path):
    """Bind independently completed inputs for read-only validation, never scoring."""
    with _lock(base):
        contract, events = _read(base)
        binding = _study_binding(events)
        if any(e["event"] in {"inputs_ready", "ready", "registration_started", "closed"} for e in events):
            raise ValueError("C prospective inputs cannot be repeated or rescued after execution")
        _inputs_receipt(base, receipt_path, binding)
        _append(base, contract, events, "inputs_ready", **binding, receipt_path=receipt_path,
                receipt_sha256=_hash(_path(base, receipt_path)), scoring_authorized=False)


def mark_ready(base, receipt_path):
    with _lock(base):
        contract, events = _read(base)
        binding = _study_binding(events)
        if any(e["event"] in {"ready", "registration_started", "closed"} for e in events):
            raise ValueError("C readiness cannot be repeated or rescued after a paid attempt")
        if not any(e["event"] == "inputs_ready" for e in events):
            raise ValueError("C final readiness requires verified input prerequisites")
        _readiness_receipt(base, receipt_path, binding)
        _append(base, contract, events, "ready", **binding, receipt_path=receipt_path,
                receipt_sha256=_hash(_path(base, receipt_path)))


def status(base):
    contract, events = _read(base)
    if not events:
        return None
    path, study = _current_study(base, contract, events)
    live_elapsed = (_now() - _date(contract["work_started_at"])).total_seconds()
    closed = any(e["event"] == "closed" for e in events)
    elapsed = events[-1]["outer_elapsed_seconds"] if closed else max(events[-1]["outer_elapsed_seconds"], live_elapsed)
    liability = events[-1]["liability_seconds"]
    total = elapsed + liability
    exhausted = total >= contract["total_seconds_cap"] or _now() >= _date(contract["wall_deadline_at"])
    used = sum(e["event"] == "registration_started" for e in events)
    registered = next((e for e in events if e["event"] == "registered"), None)
    failed = any(e["event"] == "registration_failed" for e in events)
    scientific_finished = any(e["event"] == "scientific_finished" for e in events)
    measurements = [e for e in events if e["event"] == "scientific_cost"]
    worker = measurements[-1]["full_worker_seconds"] if measurements else 0.
    fit = measurements[-1]["supervised_fit_seconds"] if measurements else 0.
    resource_exhausted = worker >= 9000 or fit >= 3600
    stage = study["stage"]
    preparation = study.get("study_kind") == "preparation_only"
    study_deadline = study.get("study_deadline_at", contract["effective_budget_deadline_at_with_initial600_debt"])
    study_expired = exhausted or _now() >= _date(study_deadline)
    ready = any(e["event"] == "ready" for e in events) and not preparation
    terminal = failed or scientific_finished or closed or exhausted or resource_exhausted
    remaining = max(0., contract["total_seconds_cap"] - total)
    return {"id": PROGRAM_ID, "program_id": PROGRAM_ID, "authority_path": AUTHORITY,
            "contract_path": CONTRACT, "program_contract_sha256": CONTRACT_SHA256,
            "study_path": path, "study_sha256": _hash(_path(base, path)), "cohort": study["cohort"], "stage": stage,
            "ready": ready, "scoring_authorized": ready and not terminal and not study_expired and live_elapsed >= events[-1]["outer_elapsed_seconds"],
            "study_terminal": terminal or study_expired, "program_terminal": terminal, "program_closed": closed,
            "expired": exhausted, "study_expired": study_expired, "study_deadline_at": study_deadline,
            "registration_budget_exhausted": used >= 1,
            "registration_attempts_cap": 1, "registration_attempts_used": used,
            "current_program_registration_attempts_used": used,
            "stage_registration_attempts": {stage: used if not preparation else 0},
            "stage_registration_caps": {stage: 0 if preparation else 1},
            "experiment_id": registered["experiment_id"] if registered else None,
            "paid_run_pending": bool(used and not failed and not scientific_finished and not closed),
            "scientific_phase_finished": scientific_finished,
            "outer_elapsed_seconds": elapsed, "historical_liability_seconds": liability,
            "historical_liability_upper_bound_verified": False,
            "total_seconds_charged": total, "fit_seconds_charged": total,
            "fit_seconds_cap": 43200, "fit_seconds_remaining": remaining,
            "unreserved_fit_seconds_remaining": remaining,
            "pending_fit_reservation_seconds": 0., "experimental_fit_seconds": fit,
            "auxiliary_fit_seconds_conservative": 0., "full_worker_seconds": worker,
            "supervised_fit_seconds": fit, "full_worker_total_cap": 9000,
            "supervised_fit_total_cap": 3600, "full_worker_seconds_remaining": max(0., 9000 - worker),
            "supervised_fit_seconds_remaining": max(0., 3600 - fit),
            "wall_deadline_at": contract["wall_deadline_at"],
            "effective_budget_deadline_at": datetime.fromtimestamp(
                _date(contract["wall_deadline_at"]).timestamp() - liability, timezone.utc).isoformat(),
            "B_preserved": contract["B_preserved"], "nested_measurements_added_to_total": False}


def prospective_admission_problems(base):
    value = status(base)
    if (not value or value["program_terminal"] or value["study_expired"] or value["registration_attempts_used"]
            or value["cohort"] != load_config(base).benchmark_version):
        return ["C prospective validation lacks available exact study authority"]
    _, events = _read(base)
    if not any(e["event"] == "inputs_ready" for e in events):
        return ["C prospective validation lacks verified intake/conformance/source/preflight evidence"]
    if _current_study(base, _documents(base), events)[1].get("study_kind") == "preparation_only":
        return ["C engineering has no prospective scientific plan"]
    return []


def scope_problems(base, experiment_id=None, *, prospective=False):
    if prospective:
        if experiment_id is not None:
            return ["C prospective admission cannot execute an experiment"]
        return prospective_admission_problems(base)
    value = status(base)
    if not value or not value["scoring_authorized"]:
        return ["C study is not ready, expired or terminal"]
    if load_config(base).benchmark_version != value["cohort"]:
        return ["C authority does not cover this cohort"]
    if experiment_id is None and value["experiment_id"]:
        return ["C paid attempt is already consumed; no scientific retry"]
    if experiment_id is not None and value["experiment_id"] != experiment_id:
        return ["C authority does not cover this experiment"]
    return []


def science_budget_protocol(base):
    value = status(base)
    if not value:
        raise ValueError("C is inactive")
    return {"program_id": PROGRAM_ID, "full_worker_total_cap": 9000,
            "fit_seconds_total_cap": 9000, "supervised_fit_total_cap": 3600,
            "C_outer_seconds_remaining_at_plan": value["unreserved_fit_seconds_remaining"],
            "C_work_started_at": "2026-10-07T23:42:00Z", "C_liability_seconds": value["historical_liability_seconds"],
            "C_wall_deadline_at": value["wall_deadline_at"]}


def reserve_registration(base):
    with _lock(base):
        contract, events = _read(base)
        value = status(base)
        if value and _current_study(base, contract, events)[1].get("study_kind") == "preparation_only":
            raise ValueError("C engineering has no scientific registration authority")
        if (not value or not value["scoring_authorized"] or value["program_terminal"]
                or value["registration_attempts_used"]):
            raise ValueError("C actual scientific attempt is terminal, exhausted or already consumed")
        # Admission/commit gates run AFTER this durable paid ticket.
        _append(base, contract, events, "registration_started", **_study_binding(events), registration_ticket=1)
    return 1


def mark_registered(base, plan, path, digest):
    with _lock(base):
        contract, events = _read(base)
        binding = _study_binding(events)
        protocol = plan.get("research_program_protocol", {})
        expected = {"authority_path": AUTHORITY, "program_contract_path": CONTRACT,
                    "program_contract_sha256": CONTRACT_SHA256, "registration_ticket": 1,
                    "study_path": binding["study_path"], "study_sha256": binding["study_sha256"]}
        if (sum(e["event"] == "registration_started" for e in events) != 1
                or any(e["event"] in {"registered", "registration_failed", "closed"} for e in events)
                or any(protocol.get(k) != v for k, v in expected.items())
                or type(protocol.get("registration_ticket")) is not int
                or plan.get("benchmark") != binding["cohort"]
                or not isinstance(plan.get("experiment_id"), str) or not plan["experiment_id"]
                or sha256_json(plan) != digest or sha256_json(load_json(_path(base, path))) != digest):
            raise ValueError("C registration has no unique ticket or exact frozen protocol/plan")
        _append(base, contract, events, "registered", **binding, registration_ticket=1,
                experiment_id=plan["experiment_id"], plan_path=path, plan_sha256=digest,
                plan_file_sha256=_hash(_path(base, path)))


def mark_registration_failed(base, error):
    with _lock(base):
        contract, events = _read(base)
        if (sum(e["event"] == "registration_started" for e in events) != 1
                or any(e["event"] in {"registered", "registration_failed", "closed"} for e in events)):
            raise ValueError("C failure cannot invent, reset or retry a paid ticket")
        _append(base, contract, events, "registration_failed", **_study_binding(events),
                registration_ticket=1, error=str(error), retry_authorized=False)


def checkpoint(base, label):
    with _lock(base):
        contract, events = _read(base)
        if not events or not isinstance(label, str) or not label:
            raise ValueError("C checkpoint requires active authority and a label")
        return _append(base, contract, events, "checkpoint", label=label)


def record_scientific_cost(base, receipt_path):
    """Record cumulative actual worker/fit (including failure); never clip overruns."""
    with _lock(base):
        contract, events = _read(base)
        registered = next((e for e in events if e["event"] == "registered"), None)
        binding = _study_binding(events)
        receipt = load_json(_path(base, receipt_path))
        expected = {**_binding(), **binding, "experiment_id": registered["experiment_id"] if registered else None}
        worker, fit = receipt.get("full_worker_seconds"), receipt.get("supervised_fit_seconds")
        old = [e for e in events if e["event"] == "scientific_cost"]
        digest = _hash(_path(base, receipt_path))
        if (not registered or any(receipt.get(k) != v for k, v in expected.items())
                or not _finite(worker) or not _finite(fit) or fit > worker
                or old and (worker < old[-1]["full_worker_seconds"] or fit < old[-1]["supervised_fit_seconds"])
                or any(e["receipt_sha256"] == digest for e in old)):
            raise ValueError("Invalid, refunded or duplicate C cumulative scientific cost")
        _append(base, contract, events, "scientific_cost", **binding, experiment_id=registered["experiment_id"],
                receipt_path=receipt_path, receipt_sha256=digest, full_worker_seconds=worker,
                supervised_fit_seconds=fit, nested_not_added_to_total=True,
                resource_cap_exceeded=worker > 9000 or fit > 3600)


def _finished_receipt(base, path, study_binding, registered, cost, digest=None):
    if digest and _hash(_path(base, path)) != digest:
        raise ValueError("C scientific completion receipt changed")
    receipt = load_json(_path(base, path))
    expected = {"program_id": PROGRAM_ID, "contract_sha256": CONTRACT_SHA256,
                "study_path": study_binding["study_path"], "study_sha256": study_binding["study_sha256"],
                "experiment_id": registered["experiment_id"], "cost_receipt_path": cost["receipt_path"],
                "cost_receipt_sha256": cost["receipt_sha256"],
                "full_worker_seconds": cost["full_worker_seconds"],
                "supervised_fit_seconds": cost["supervised_fit_seconds"]}
    if (any(receipt.get(key) != value for key, value in expected.items())
            or not _finite(receipt.get("full_worker_seconds")) or not _finite(receipt.get("supervised_fit_seconds"))
            or receipt.get("paid_retry_authorized") is not False or receipt.get("whole_goal_complete") is not False
            or "error" not in receipt or receipt["error"] is not None and not isinstance(receipt["error"], str)):
        raise ValueError("C scientific completion lacks exact EXP/study/cost receipt binding")
    return receipt


def mark_scientific_finished(base, receipt_path):
    """End the sole science attempt; archive/report/publication wall keeps accruing."""
    with _lock(base):
        contract, events = _read(base)
        registered = next((e for e in events if e["event"] == "registered"), None)
        costs = [e for e in events if e["event"] == "scientific_cost"]
        if (not registered or not costs
                or any(e["event"] in {"scientific_finished", "closed"} for e in events)):
            raise ValueError("C scientific finish requires one registered attempt and prior costs, no retry")
        binding = _study_binding(events)
        receipt = _finished_receipt(base, receipt_path, binding, registered, costs[-1])
        _append(base, contract, events, "scientific_finished", **binding,
                experiment_id=registered["experiment_id"], receipt_path=receipt_path,
                receipt_sha256=_hash(_path(base, receipt_path)),
                scientific_outcome="failed" if receipt["error"] is not None else "finished",
                scoring_authorized=False, outer_work_window_closed=False)


def auxiliary_reserve(base, charge_id, seconds_cap):
    with _lock(base):
        contract, events = _read(base)
        value = status(base)
        if (not value or value["program_closed"] or not isinstance(charge_id, str) or not charge_id
                or not _finite(seconds_cap) or seconds_cap <= 0 or seconds_cap > value["fit_seconds_remaining"]
                or any(e.get("charge_id") == charge_id for e in events)):
            raise ValueError("Invalid or repeated C descriptive auxiliary reservation")
        _append(base, contract, events, "auxiliary_reserved", charge_id=charge_id,
                seconds_cap=seconds_cap, nested_not_added_to_total=True)


def auxiliary_charge(base, charge_id, seconds):
    with _lock(base):
        contract, events = _read(base)
        reserved = [e for e in events if e["event"] == "auxiliary_reserved" and e["charge_id"] == charge_id]
        if (len(reserved) != 1 or not _finite(seconds)
                or any(e["event"] == "auxiliary_measured" and e["charge_id"] == charge_id for e in events)):
            raise ValueError("Missing, repeated or nonfinite C auxiliary measurement")
        _append(base, contract, events, "auxiliary_measured", charge_id=charge_id, seconds=seconds,
                nested_not_added_to_total=True, reservation_exceeded=seconds > reserved[0]["seconds_cap"])


def add_liability(base, additional_seconds, receipt_path):
    if not _finite(additional_seconds) or additional_seconds <= 0:
        raise ValueError("C inherited liability may only increase")
    with _lock(base):
        contract, events = _read(base)
        if not events or any(e.get("receipt_path") == receipt_path for e in events):
            raise ValueError("C liability requires new preserved evidence")
        _append(base, contract, events, "liability_increased", additional_seconds=additional_seconds,
                receipt_path=receipt_path, receipt_sha256=_hash(_path(base, receipt_path)))


def close(base, receipt_path):
    """Closing halts science; later archive/publication checkpoints still charge wall."""
    with _lock(base):
        contract, events = _read(base)
        receipt = load_json(_path(base, receipt_path))
        if (not events or any(e["event"] == "closed" for e in events)
                or receipt.get("program_id") != PROGRAM_ID or receipt.get("contract_sha256") != CONTRACT_SHA256
                or receipt.get("whole_goal_complete") is not False):
            raise ValueError("C closure is missing, repeated or claims unproved whole-goal completion")
        _append(base, contract, events, "closed", receipt_path=receipt_path,
                receipt_sha256=_hash(_path(base, receipt_path)), scoring_authorized=False)
