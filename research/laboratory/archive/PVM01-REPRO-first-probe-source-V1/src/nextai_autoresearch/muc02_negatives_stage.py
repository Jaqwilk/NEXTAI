"""Finite user-authorized development comparison; old authority stays consumed."""
from datetime import datetime, timezone

from .ledger import latest_plan_statuses, read_jsonl
from .utils import load_json, sha256_file, sha256_json

AUTHORITY = "research/laboratory/MUC02-HARD-NEGATIVES-20261003-V1.json"
PLAN = "research/plans/MUC02-HARD-NEGATIVES-20261003-V1.json"
DATA_ADDENDUM = "research/plans/MUC02-HARD-NEGATIVES-DATA-CONFORMANCE-V1.json"
ORIGINAL_COHORT = "mutable_contact_ledger_hard_negatives_v1"
COHORT = "mutable_contact_ledger_hard_negatives_v2"
PRESEED_ADDENDUM = "research/plans/MUC02-HARD-NEGATIVES-PRESEED-CONFORMANCE-V1.json"
ROLES = tuple(f"muc02_{arm}_neg_s{i}" for i in range(5) for arm in ("random", "hard")) + ("symbolic_last_write_graph_v2",)


def status(base):
    path = base / AUTHORITY
    events = read_jsonl(base / "research/events.jsonl")
    starts = [e for e in events if e.get("event") == "muc02_hard_negatives_authorized"]
    if not path.exists() and not starts:
        return None
    if not path.is_file() or len(starts) != 1 or starts[0].get("authorization_sha256") != sha256_file(path):
        raise ValueError("Hard-negative authority missing, changed or repeated")
    auth, contract = load_json(path), load_json(base / PLAN)
    corrections = [e for e in events if e.get("event") == "muc02_hard_negatives_preseed_conformance_frozen"]
    corrected = bool(corrections)
    if corrected:
        correction = load_json(base / PRESEED_ADDENDUM)
        if (len(corrections) != 1 or corrections[0].get("addendum_path") != PRESEED_ADDENDUM
                or corrections[0].get("addendum_sha256") != sha256_file(base / PRESEED_ADDENDUM)
                or correction["parent_contract_sha256"] != sha256_file(base / PLAN)
                or correction["corrected_cohort"] != COHORT or correction["executed_experiment_attempts_cap"] != 1
                or correction["registrations_total_cap_including_invalidated"] != 2
                or correction["deadline_at"] != contract["deadline_at"] or correction["fit_seconds_total_cap"] != 3600
                or correction["automatic_retry"] is not False):
            raise ValueError("Pre-seed correction missing/changed/repeated or widens execution")
        original = correction["prior_registration"]
        if (sha256_json(load_json(base / "research/plans" / f"{original}.json")) != correction["prior_registration_sha256"]
                or (base / "research/results" / f"{original}.json").exists()
                or latest_plan_statuses(base).get(original, {}).get("status") != "invalidated"
                or any(e.get("experiment_id") == original and e.get("event") in {"experiment_scoring_started", "experiment_runner_postseed_failure"} for e in events)):
            raise ValueError("Pre-seed correction cannot replace an executed or live experiment")
    supplements = [e for e in events if e.get("event") == "muc02_hard_negatives_data_conformance_frozen"]
    if (len(supplements) != 1 or supplements[0].get("addendum_path") != DATA_ADDENDUM
            or supplements[0].get("addendum_sha256") != sha256_file(base / DATA_ADDENDUM)
            or load_json(base / DATA_ADDENDUM)["parent_contract_sha256"] != sha256_file(base / PLAN)):
        raise ValueError("Prospective structural data-conformance addendum missing/changed/repeated")
    if (auth.get("plan_path") != PLAN or auth.get("plan_sha256") != sha256_file(base / PLAN)
            or starts[0].get("plan_sha256") != auth["plan_sha256"]
            or contract["new_cohort"] != ORIGINAL_COHORT or tuple(contract["candidates"]) != ROLES
            or contract["paired_seeds"] != 5 or contract["experiment_registrations_cap"] != 1
            or contract["automatic_retry"] is not False or contract["wt_files_8_9_access_authorized"] is not False
            or contract["new_architectures_authorized"] is not False
            or sha256_file(base / "research/results/EXP-20261002-0001.json") != contract["prior_result_sha256"]):
        raise ValueError("Hard-negative prospective scope or prior evidence changed")
    registered = [load_json(p) for p in sorted((base / "research/plans").glob("EXP-*.json"))
                  if load_json(p).get("benchmark") in {ORIGINAL_COHORT, COHORT}]
    originals = [p for p in registered if p["benchmark"] == ORIGINAL_COHORT]
    replacements = [p for p in registered if p["benchmark"] == COHORT]
    if len(originals) > 1 or len(replacements) > int(corrected) or (corrected and len(originals) != 1):
        raise ValueError("Hard-negative original/corrected registration cap exceeded")
    for p in registered:
        if tuple(p["candidates"]) != ROLES or p.get("muc02_negatives_protocol") != protocol(base, p["benchmark"] == COHORT):
            raise ValueError("Hard-negative registered scope changed")
    current = replacements if corrected else originals
    experiment_id = current[0]["experiment_id"] if current else None
    terminal = bool(experiment_id and ((base / "research/results" / f"{experiment_id}.json").exists()
                                      or experiment_id in latest_plan_statuses(base)))
    ready = [e for e in events if e.get("event") == "muc02_hard_negatives_harness_ready"]
    if len(ready) > 1 or (ready and (ready[0].get("plan_sha256") != auth["plan_sha256"]
                                   or sha256_file(base / ready[0]["receipt_path"]) != ready[0]["receipt_sha256"])):
        raise ValueError("Hard-negative harness readiness missing/changed/repeated")
    repaired_ready = [e for e in events if e.get("event") == "muc02_hard_negatives_preseed_repair_ready"]
    if len(repaired_ready) > 1 or (repaired_ready and (not corrected
            or repaired_ready[0].get("addendum_sha256") != sha256_file(base / PRESEED_ADDENDUM)
            or sha256_file(base / repaired_ready[0]["receipt_path"]) != repaired_ready[0]["receipt_sha256"])):
        raise ValueError("Corrected pre-seed harness readiness missing/changed/repeated")
    is_ready = bool(ready) and (bool(repaired_ready) if corrected else True)
    expired = datetime.now(timezone.utc) >= datetime.fromisoformat(contract["deadline_at"].replace("Z", "+00:00"))
    return {"id": auth["id"], "ready": is_ready, "terminal": terminal, "expired": expired,
            "deadline_at": contract["deadline_at"], "experiment_id": experiment_id,
            "registrations_used": len(registered), "registrations_cap": 2 if corrected else 1,
            "original_registration_preserved": originals[0]["experiment_id"] if originals else None,
            "current_registrations_used": len(current), "executed_attempts_cap": 1, "paired_seeds": 5,
            "fit_seconds_total_cap": 3600, "scoring_authorized": is_ready and not terminal and not expired}


def scope_problems(base, experiment_id=None):
    value = status(base)
    if value is None or not value["scoring_authorized"]:
        return ["Hard-negative stage is preparation-only, expired or terminal; no retry"]
    if experiment_id is None and value["current_registrations_used"]:
        return ["Hard-negative single registration already consumed"]
    if experiment_id is not None and value["experiment_id"] != experiment_id:
        return ["Hard-negative authority does not cover this experiment"]
    return []


def protocol(base, corrected=None):
    c = load_json(base / PLAN)
    value = {"authority_path": AUTHORITY, "contract_path": PLAN, "contract_sha256": sha256_file(base / PLAN),
            "data_conformance_addendum_path": DATA_ADDENDUM, "data_conformance_addendum_sha256": sha256_file(base / DATA_ADDENDUM),
            "roles": c["roles"], "classical_baselines": list(ROLES), "recipe": c["recipe"],
            "fit_steps_cap": 192, "fit_seconds_cap": 350, "fit_seconds_total_cap": 3600,
            "worker_seconds_cap": 1800, "deadline_at": c["deadline_at"],
            "max_rss_bytes": c["resources"]["max_rss_bytes"], "max_cuda_reserved_bytes": c["resources"]["max_cuda_reserved_bytes"],
            "data": c["data"], "metrics": c["metrics"], "decision_gates": c["decision_gates"],
            "negative_sampling": c["negative_sampling"], "measurement": c["measurement"]}
    if corrected is None:
        corrected = (base / PRESEED_ADDENDUM).exists()
    if corrected:
        value.update(preseed_conformance_addendum_path=PRESEED_ADDENDUM,
                     preseed_conformance_addendum_sha256=sha256_file(base / PRESEED_ADDENDUM))
    return value


def configure_plan(plan, args, base, directions):
    if tuple(args.candidates) != ROLES or args.budget != "quick":
        raise ValueError("Hard-negative comparison requires all 10 paired roles and symbolic control")
    plan["matrix"] = {"knowledge_sizes": [32, 128, 512], "reasoning_depths": [1, 2, 4], "queries_per_cell": 16,
                      "seed_policy": {"method": "runner_random_v1", "count": 5, "minimum": 1000000, "maximum": 2147483647}}
    metrics = ["fact_top1_accuracy", "dense_unknown_rejection", "accuracy", "continual_retention",
               "mean_query_ops", "p95_latency_us", "state_bytes", "fit_ops", "preprocessing_ops"]
    plan["primary_metrics"] = metrics
    plan["metric_directions"] = {name: directions[name] for name in metrics}
    plan["muc02_negatives_protocol"] = protocol(base)
    plan["eligibility_contract"] = {"metric": "accuracy", "minimum": 0.85}
