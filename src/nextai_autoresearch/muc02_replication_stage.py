"""Separate single-attempt MUC v2 replication; historical wallets stay closed."""
from datetime import datetime, timezone
import math

from .config import load_config
from .ledger import latest_plan_statuses, read_jsonl, registered_plan_hash
from .utils import load_json, sha256_file, sha256_json

ID = "MUC02-NEGATIVES-REPLICATION-20261006-V1"
AUTHORITY = f"research/laboratory/{ID}.json"
PLAN = f"research/plans/{ID}.json"
PLAN_SHA256 = "cbde3b9e16bc6a8b59139249d065a9faaa2cbad41c2891293b3156d5ae7ef4a4"
COHORT = "mutable_contact_ledger_negatives_replication_v1"
ROLES = tuple(f"muc02_{arm}_neg_s{i}" for i in range(5) for arm in ("random", "hard")) + ("symbolic_last_write_graph_v2",)
MATRIX = {"knowledge_sizes": [32, 128, 512], "reasoning_depths": [1, 2, 4], "queries_per_cell": 16,
          "seed_policy": {"method": "runner_random_v1", "count": 5, "minimum": 1000000, "maximum": 2147483647}}


def _document(base, relative):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        raise ValueError("Replication evidence is missing or outside its checkout")
    return load_json(path)


def _contract(base):
    if sha256_file(base / PLAN) != PLAN_SHA256:
        raise ValueError("Replication prospective contract changed")
    c = _document(base, PLAN)
    parent = _document(base, c["parent_contract_path"])
    resources = c["resources"]
    start = datetime.fromisoformat(c["stage_started_at"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(c["deadline_at"].replace("Z", "+00:00"))
    if (c["id"] != ID or c["new_cohort"] != COHORT or tuple(c["candidates"]) != ROLES
            or c["paired_seeds"] != 5 or c["experiment_registrations_cap"] != 1
            or c["automatic_retry"] is not False or c["new_architectures_authorized"] is not False
            or c["wt_files_8_9_access_authorized"] is not False
            or resources["work_seconds_cap"] != 14400 or (end - start).total_seconds() != 14400
            or resources["fit_seconds_total_cap"] != 3600 or resources["fit_seconds_per_learned_role"] != 350
            or resources["worker_seconds_per_role"] != 1800
            or c["recipe"]["training_pairs"] != 4096 or c["recipe"]["updates"] != 192
            or any(c[key] != parent[key] for key in ("recipe", "metrics", "decision_gates", "negative_sampling"))):
        raise ValueError("Replication frozen model, metrics, thresholds or caps differ")
    references = {c["parent_contract_path"]: c["parent_contract_sha256"],
                  c["prior_completion_path"]: c["prior_completion_sha256"],
                  f"research/results/{c['prior_experiment']}.json": c["prior_result_sha256"],
                  **c["unchanged_implementation_files"]}
    if any(sha256_file(base / path) != digest for path, digest in references.items()):
        raise ValueError("Replication changed preserved MUC evidence or implementation")
    return c


def historical_metadata(base):
    """Registration-only metadata binding: no world, fixture or scoring seed draw."""
    seeds, references = set(), {}
    for path in sorted((base / "research/plans").glob("EXP-*.json")):
        plan = load_json(path)
        benchmark = str(plan.get("benchmark", ""))
        if not benchmark.startswith(("mutable_contact_ledger", "muc03_")) or benchmark == COHORT:
            continue
        result_path = base / "research/results" / path.name
        if not result_path.is_file():
            continue
        result = load_json(result_path)
        values = result.get("evaluation_matrix", {}).get("seeds", [])
        if any(type(seed) is not int for seed in values):
            raise ValueError("Historical MUC seed metadata is malformed")
        seeds.update(values)
        references[result_path.relative_to(base).as_posix()] = sha256_file(result_path)
    return sorted(seeds), references


def protocol(base, *, historical_seeds=None, historical_results_sha256=None):
    c = _contract(base)
    if historical_seeds is None and historical_results_sha256 is None:
        historical_seeds, historical_results_sha256 = historical_metadata(base)
    if (not historical_seeds or historical_seeds != sorted(set(historical_seeds))
            or any(type(seed) is not int for seed in historical_seeds) or not historical_results_sha256):
        raise ValueError("Explicit historical MUC seed/result bindings are required")
    bound_seeds = set()
    for path, digest in historical_results_sha256.items():
        if not path.startswith("research/results/EXP-") or not path.endswith(".json"):
            raise ValueError("Historical seed binding must reference an immutable result")
        result = _document(base, path)
        if sha256_file(base / path) != digest:
            raise ValueError("Historical MUC seed evidence changed")
        if not str(result.get("benchmark", "")).startswith(("mutable_contact_ledger", "muc03_")) or result.get("benchmark") == COHORT:
            raise ValueError("Historical seed evidence is outside the preserved MUC history")
        values = result.get("evaluation_matrix", {}).get("seeds", [])
        if any(type(seed) is not int for seed in values):
            raise ValueError("Historical MUC seed metadata is malformed")
        bound_seeds.update(values)
    if sorted(bound_seeds) != historical_seeds:
        raise ValueError("Historical MUC seed list differs from its immutable result bindings")
    return {"authority_path": AUTHORITY, "contract_path": PLAN, "contract_sha256": PLAN_SHA256,
            "data_tag": ID, "historical_seeds": historical_seeds,
            "historical_results_sha256": historical_results_sha256,
            "classical_baselines": list(ROLES), "fit_steps_cap": 192,
            "fit_seconds_cap": 350, "fit_seconds_total_cap": 3600, "worker_seconds_cap": 1800,
            "deadline_at": c["deadline_at"], "max_rss_bytes": c["resources"]["max_rss_bytes"],
            "max_cuda_reserved_bytes": c["resources"]["max_cuda_reserved_bytes"],
            **{key: c[key] for key in ("roles", "recipe", "data", "metrics", "decision_gates", "negative_sampling", "measurement")}}


def _receipt(base, event):
    if event.get("stage_id") != ID or event.get("plan_sha256") != PLAN_SHA256:
        raise ValueError("Replication receipt event changed stage or prospective binding")
    value = _document(base, event["receipt_path"])
    if sha256_file(base / event["receipt_path"]) != event["receipt_sha256"]:
        raise ValueError("Replication receipt changed")
    return value


def status(base):
    config = load_config(base)
    if config.raw.get("muc02_replication", {}).get("active") is not True:
        if config.benchmark_version == COHORT:
            raise ValueError("Replication cohort requires its explicit authority overlay")
        return None
    if config.benchmark_version != COHORT:
        raise ValueError("Replication overlay may activate only its own fresh cohort")
    c = _contract(base)
    events = read_jsonl(base / "research/events.jsonl")
    authorized = [e for e in events if e.get("event") == "muc02_replication_authorized"]
    auth = _document(base, AUTHORITY)
    if (len(authorized) != 1 or authorized[0].get("stage_id") != ID
            or authorized[0].get("authorization_path") != AUTHORITY
            or authorized[0].get("authorization_sha256") != sha256_file(base / AUTHORITY)
            or authorized[0].get("plan_path") != PLAN or authorized[0].get("plan_sha256") != PLAN_SHA256
            or auth["id"] != ID or auth["plan_path"] != PLAN or auth["plan_sha256"] != PLAN_SHA256
            or auth["registration_cap"] != 1 or auth["execution_attempt_cap"] != 1
            or auth["work_seconds_cap"] != 14400 or auth["fit_seconds_cap"] != 3600
            or any(auth[key] is not False for key in ("automatic_retry", "WT8_9", "architecture_change", "external_model_API",
                                                     "schedule_change", "consumes_or_changes_B_wallet", "reopens_old_authority"))
            or auth["separate_budget"] is not True):
        raise ValueError("Replication authority missing, changed, repeated or widens scope")
    plans = [load_json(p) for p in sorted((base / "research/plans").glob("EXP-*.json"))
             if load_json(p).get("benchmark") == COHORT]
    if len(plans) > 1:
        raise ValueError("Replication single registration is already consumed")
    for p in plans:
        bound = p["muc02_negatives_protocol"]
        if (p["candidates"] != list(ROLES) or p["matrix"] != MATRIX or p["budget"] != "quick"
                or registered_plan_hash(p["experiment_id"], base) != sha256_json(p)
                or bound != protocol(base, historical_seeds=bound["historical_seeds"],
                                     historical_results_sha256=bound["historical_results_sha256"])):
            raise ValueError("Replication registered scope or historical bindings changed")
    experiment_id = plans[0]["experiment_id"] if plans else None
    relevant = [e for e in events if experiment_id and e.get("experiment_id") == experiment_id]
    starts = [e for e in relevant if e.get("event") == "experiment_scoring_started"]
    if len(starts) > 1 or any(e.get("plan_sha256") != sha256_json(plans[0]) for e in starts):
        raise ValueError("Replication execution was repeated or changed")
    if starts:
        realized = starts[0].get("scoring_seeds", [])
        if (len(realized) != 5 or len(set(realized)) != 5 or any(type(seed) is not int for seed in realized)
                or set(realized) & set(plans[0]["muc02_negatives_protocol"]["historical_seeds"])):
            raise ValueError("Replication scoring seed coverage or freshness failed")
    readiness = [e for e in events if e.get("event") == "muc02_replication_ready"]
    if len(readiness) > 1:
        raise ValueError("Replication readiness repeated")
    if readiness:
        ready = _receipt(base, readiness[0])
        if (ready.get("status") != "validated_ready" or ready.get("plan_sha256") != PLAN_SHA256
                or ready.get("cohort") != COHORT or ready.get("required_checks_passed") is not True
                or ready.get("scoring_seed_draws") != 0 or ready.get("fit_seconds_charged") != 0
                or ready.get("clone_package_origin_verified") is not True):
            raise ValueError("Replication readiness does not establish frozen zero-fit clone conformance")
    failures = [e for e in events if e.get("event") == "muc02_replication_preparation_failed"]
    if len(failures) > 1:
        raise ValueError("Replication preparation failure repeated")
    for event in failures:
        _receipt(base, event)
    result_path = base / "research/results" / f"{experiment_id}.json"
    result_exists = bool(experiment_id and result_path.is_file())
    terminal = bool(failures or (experiment_id and (result_exists or experiment_id in latest_plan_statuses(base)))
                    or any(e.get("event") == "experiment_runner_postseed_failure" for e in relevant))
    outcomes = (load_json(result_path)["candidates"] if result_exists else
                [load_json(p) for p in sorted((base / "research/tmp" / str(experiment_id)).glob("*.supervisor.json"))] if experiment_id else [])
    fit = sum((row.get("execution") or {}).get("supervised_fit_seconds", 0.) for row in outcomes)
    if not math.isfinite(fit) or not 0 <= fit <= 3600:
        raise ValueError("Replication supervised fit accounting is invalid or exhausted")
    expired = datetime.now(timezone.utc) >= datetime.fromisoformat(c["deadline_at"].replace("Z", "+00:00"))
    # Underlying B is still independently validated, without registration or cost events in its wallet.
    from .research_program import status as program_status
    preserved = program_status(base)
    return {"id": ID, "authority_path": AUTHORITY, "contract_path": PLAN, "cohort": COHORT,
            "ready": bool(readiness), "terminal": terminal, "expired": expired, "started": bool(starts),
            "deadline_at": c["deadline_at"], "stage_started_at": c["stage_started_at"], "work_seconds_cap": 14400,
            "experiment_id": experiment_id, "registrations_used": len(plans), "registrations_cap": 1,
            "current_registrations_used": len(plans), "executed_attempts_cap": 1, "executions_started": len(starts),
            "paired_seeds": 5, "fit_seconds_total_cap": 3600, "fit_seconds_charged": fit,
            "fit_seconds_remaining": 3600 - fit, "separate_budget": True,
            "preserved_research_program": preserved,
            "scoring_authorized": bool(readiness) and not (terminal or expired or starts or fit >= 3600)}


def scope_problems(base, experiment_id=None):
    value = status(base)
    if value is None or not value["scoring_authorized"]:
        return ["Replication is not ready, terminal, started or expired; no retry"]
    if experiment_id is None and value["registrations_used"]:
        return ["Replication single registration already consumed"]
    if experiment_id is not None and value["experiment_id"] != experiment_id:
        return ["Replication authority does not cover this experiment"]
    return []


def configure_plan(plan, args, base, directions):
    if tuple(args.candidates) != ROLES or args.budget != "quick":
        raise ValueError("Replication requires all ten paired roles and symbolic control")
    seeds, references = historical_metadata(base)
    plan["matrix"] = {**MATRIX, "seed_policy": dict(MATRIX["seed_policy"])}
    metrics = ["fact_top1_accuracy", "dense_unknown_rejection", "accuracy", "continual_retention",
               "mean_query_ops", "p95_latency_us", "state_bytes", "fit_ops", "preprocessing_ops"]
    plan["primary_metrics"] = metrics
    plan["metric_directions"] = {name: directions[name] for name in metrics}
    plan["muc02_negatives_protocol"] = protocol(base, historical_seeds=seeds, historical_results_sha256=references)
    plan["eligibility_contract"] = {"metric": "accuracy", "minimum": 0.85}
