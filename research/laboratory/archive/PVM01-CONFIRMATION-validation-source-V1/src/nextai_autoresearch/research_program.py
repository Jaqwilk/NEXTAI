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
            fit += _execution_fit(load_json(result)["candidates"])
        else:
            supervisors = sorted((base / "research/tmp" / plan["experiment_id"]).glob("*.supervisor.json"))
            observed = _execution_fit(load_json(p) for p in supervisors)
            fit += observed
            if plan["experiment_id"] not in latest_plan_statuses(base):
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
        if not 0 <= amount <= reservation["seconds_cap"]:
            raise ValueError("Auxiliary fit reservation exceeded")
        auxiliary += amount
    current_tickets = [e for e in tickets if e["study_path"] == study_path]
    failed = [e for e in events if e.get("event") == "research_program_registration_failed" and e.get("study_path") == study_path]
    if len(current_tickets) > study["registration_attempts_for_this_study_cap"] or len(current_plans) > 1:
        raise ValueError("Study registration cap exceeded")
    experiment_id = current_plans[0]["experiment_id"] if current_plans else None
    preparation_ends = [e for e in events if e.get("event") == "research_program_preparation_completed"
                        and e.get("study_path") == study_path]
    if (len(preparation_ends) > 1 or any(e["study_sha256"] != sha256_file(base / study_path)
            or e["receipt_sha256"] != _bound_hash(base, e["receipt_path"]) for e in preparation_ends)):
        raise ValueError("Preparation completion receipt changed or repeated")
    terminal = bool(failed or (experiment_id and ((base / "research/results" / f"{experiment_id}.json").exists()
                                                or experiment_id in latest_plan_statuses(base))) or preparation_ends)
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


def status(base):
    """A new authority carries immutable closed accounting; it never reopens it."""
    events = read_jsonl(base / "research/events.jsonl")
    starts = [e for e in events if e.get("event") == "research_program_continuation_authorized"]
    if not starts:  # A copied prospective document alone cannot activate a program.
        return _status_for(base)
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
                          expected_caps=(17, 69344), authorization_event="research_program_continuation_authorized")
    return {**current, "prior_program_closed": True, "prior_program_id": prior["id"],
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
    if (not value or value["program_closed"] or not isinstance(seconds_cap, (int, float))
            or not math.isfinite(seconds_cap) or seconds_cap <= 0 or seconds_cap > value["unreserved_fit_seconds_remaining"]):
        raise ValueError("Insufficient research budget for auxiliary fit reservation")
    events = read_jsonl(base / "research/events.jsonl")
    if any(e.get("charge_id") == charge_id for e in events):
        raise ValueError("Auxiliary fit ID already consumed")
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_aux_fit_reserved", "created_at": utc_now(),
                 "program_id": value["id"], "charge_id": charge_id, "seconds_cap": seconds_cap})


def auxiliary_charge(base, charge_id, seconds):
    value = status(base)
    events = read_jsonl(base / "research/events.jsonl")
    if any(e.get("event") == "research_program_aux_fit_charged" and e.get("charge_id") == charge_id for e in events):
        raise ValueError("Repeated auxiliary fit accounting")
    reservations = [e for e in events if e.get("event") == "research_program_aux_fit_reserved" and e.get("charge_id") == charge_id]
    if (len(reservations) != 1 or not isinstance(seconds, (int, float)) or not math.isfinite(seconds)
            or not 0 <= seconds <= reservations[0]["seconds_cap"]):
        raise ValueError("Auxiliary fit charge exceeds reservation or has no reservation")
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_aux_fit_charged", "created_at": utc_now(),
                 "program_id": value["id"], "charge_id": charge_id, "seconds": seconds})
    status(base)  # Validate the durable accounting, including failed test runs.


def verify_pvm01_fresh_realization(base, seeds, nonces, *, include_latest=False, include_transport=False, include_replication=False, include_dense_noise=False):
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
    ticket = value.get("continuation_registration_attempts_used", value["registration_attempts_used"]) + 1
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_registration_started", "created_at": utc_now(),
                 "program_id": value["id"], "study_path": value["study_path"], "ticket": ticket})
    try:
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
        paired_view = study["cohort"] in ("paired_view_mutable_memory_v1", "paired_view_mutable_memory_v2", "paired_view_mutable_memory_v3", "paired_view_mutable_memory_v4", "paired_view_mutable_memory_v5", "paired_view_mutable_memory_v6", "paired_view_mutable_memory_v7", "paired_view_mutable_memory_v8", "paired_view_mutable_memory_v9")
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
