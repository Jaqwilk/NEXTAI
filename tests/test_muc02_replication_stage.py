"""Zero-fit fixtures for the separate replication authority and preserved B scope."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import os
import shutil

import pytest

from nextai_autoresearch import muc02_replication_stage as stage
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json, load_json, project_root, sha256_file, sha256_json


@pytest.fixture
def scope(tmp_path, monkeypatch):
    source = project_root()
    contract = load_json(source / stage.PLAN)
    frozen_now = datetime.fromisoformat(contract["stage_started_at"].replace("Z", "+00:00")) + timedelta(minutes=1)
    class DuringStage(datetime):
        @classmethod
        def now(cls, tz=None):
            return frozen_now
    monkeypatch.setattr(stage, "datetime", DuringStage)
    references = [stage.PLAN, stage.AUTHORITY, contract["parent_contract_path"], contract["prior_completion_path"],
                  f"research/results/{contract['prior_experiment']}.json", *contract["unchanged_implementation_files"]]
    for relative in references:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if relative.startswith("research/results/"):
            # Immutable old result is read only in every fixture; avoid 25 large copies.
            os.link(source / relative, destination)
        else:
            shutil.copy2(source / relative, destination)
    # Only immutable result/plan metadata are copied; no native data or world generator runs.
    old_plan = source / "research/plans" / f"{contract['prior_experiment']}.json"
    shutil.copy2(old_plan, tmp_path / "research/plans" / old_plan.name)
    config = deepcopy(load_json(source / "research/laboratory/restart.json"))
    for relative in ["schemas/laboratory_restart.schema.json", *config["required_documents"]]:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, destination)
    atomic_write_json(tmp_path / "research/laboratory/restart.json", config)
    (tmp_path / "config").mkdir()
    (tmp_path / "config/research.toml").write_text(
        'schema_version = 1\n[project]\nprotocol_version = 3\nbenchmark_version = "' + stage.COHORT
        + '"\nbenchmark_status = "maintenance"\n[muc02_replication]\nactive = true\n[laboratory]\n'
        + 'contract_path = "research/laboratory/restart.json"\nrestart_id = "' + config["restart_id"] + '"\n'
        + ''.join(f'[budgets.{tier}]\ndevelopment_seeds = [1]\nscoring_seed_count = 5\n' for tier in ("quick", "screen", "deep")),
        encoding="utf-8")
    append_jsonl(tmp_path / "research/events.jsonl", {"event": "muc02_replication_authorized", "stage_id": stage.ID,
        "authorization_path": stage.AUTHORITY, "authorization_sha256": sha256_file(tmp_path / stage.AUTHORITY),
        "plan_path": stage.PLAN, "plan_sha256": stage.PLAN_SHA256})
    from nextai_autoresearch import research_program
    preserved = {"id": "preserved-B-fixture", "fit_seconds_charged": 20000., "registration_attempts_used": 1,
                 "protected_future_tickets": 7, "protected_future_seconds": 47000., "scoring_authorized": False,
                 "cohort": "asm01_native_memory_v3"}
    monkeypatch.setattr(research_program, "status", lambda base: deepcopy(preserved))
    return tmp_path, preserved


def ready(base):
    relative = "research/reviews/replication-fixture-ready.json"
    atomic_write_json(base / relative, {"status": "validated_ready", "plan_sha256": stage.PLAN_SHA256,
        "cohort": stage.COHORT, "required_checks_passed": True, "scoring_seed_draws": 0,
        "fit_seconds_charged": 0, "clone_package_origin_verified": True})
    append_jsonl(base / "research/events.jsonl", {"event": "muc02_replication_ready", "stage_id": stage.ID,
        "plan_sha256": stage.PLAN_SHA256, "receipt_path": relative, "receipt_sha256": sha256_file(base / relative)})
    return relative


def register(base, identifier="EXP-20990101-0001", transform=None):
    plan = {"experiment_id": identifier, "benchmark": stage.COHORT, "budget": "quick", "candidates": list(stage.ROLES)}
    names = ("fact_top1_accuracy", "dense_unknown_rejection", "accuracy", "continual_retention",
             "mean_query_ops", "p95_latency_us", "state_bytes", "fit_ops", "preprocessing_ops")
    stage.configure_plan(plan, SimpleNamespace(candidates=list(stage.ROLES), budget="quick"), base,
                         {name: "maximize" if "accuracy" in name or name == "dense_unknown_rejection" else "minimize" for name in names})
    if transform:
        transform(plan)
    atomic_write_json(base / "research/plans" / f"{identifier}.json", plan)
    append_jsonl(base / "research/plan_registry.jsonl", {"experiment_id": identifier, "plan_sha256": sha256_json(plan)})
    return plan


def test_preparation_readiness_and_underlying_wallet_are_separate(scope):
    base, preserved = scope
    events_hash = sha256_file(base / "research/events.jsonl")
    value = stage.status(base)
    assert not value["ready"] and not value["scoring_authorized"]
    assert value["registrations_used"] == value["executions_started"] == value["fit_seconds_charged"] == 0
    assert value["preserved_research_program"] == preserved
    assert sha256_file(base / "research/events.jsonl") == events_hash
    ready(base)
    assert stage.status(base)["scoring_authorized"] and not stage.scope_problems(base)


@pytest.mark.parametrize("failure", ("authority", "event", "source", "contract"), ids=("auth-hash", "repeat-auth", "core-hash", "plan-hash"))
def test_changed_or_repeated_authority_and_historical_sources_fail(scope, failure):
    base, _ = scope
    if failure == "event":
        append_jsonl(base / "research/events.jsonl", load_json(base / stage.AUTHORITY) | {"event": "muc02_replication_authorized"})
    else:
        relative = {"authority": stage.AUTHORITY, "source": "src/nextai_autoresearch/candidates/muc02_core.py", "contract": stage.PLAN}[failure]
        with (base / relative).open("ab") as handle:
            handle.write(b"\n ")
    with pytest.raises(ValueError, match="changed|repeated|authority"):
        stage.status(base)


@pytest.mark.parametrize("failure", ("hash", "fit", "checks", "repeat"), ids=("ready-hash", "fixture-fit", "missing-check", "repeat-ready"))
def test_readiness_is_one_hash_bound_zero_fit_proof(scope, failure):
    base, _ = scope
    relative = ready(base)
    events = base / "research/events.jsonl"
    if failure == "repeat":
        import json
        event = json.loads(events.read_text(encoding="utf-8").splitlines()[-1])
        append_jsonl(events, event)
    else:
        receipt = load_json(base / relative)
        receipt["fit_seconds_charged" if failure == "fit" else "required_checks_passed"] = 1 if failure == "fit" else False
        atomic_write_json(base / relative, receipt)
        if failure != "hash":
            import json
            rows = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
            rows[-1]["receipt_sha256"] = sha256_file(base / relative)
            events.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    with pytest.raises(ValueError, match="readiness|receipt|zero-fit"):
        stage.status(base)


def test_registration_is_single_exact_recipe_and_history_bound(scope):
    base, preserved = scope
    ready(base)
    plan = register(base)
    value = stage.status(base)
    assert not stage.scope_problems(base, plan["experiment_id"])
    assert stage.scope_problems(base) and stage.scope_problems(base, "EXP-20990101-9999")
    assert value["preserved_research_program"] == preserved and value["registrations_used"] == 1
    bound = plan["muc02_negatives_protocol"]
    assert bound["data_tag"] == stage.ID and bound["historical_seeds"]
    assert bound["fit_steps_cap"] == 192 and bound["recipe"]["training_pairs"] == 4096
    register(base, "EXP-20990101-0002")
    with pytest.raises(ValueError, match="single registration"):
        stage.status(base)


@pytest.mark.parametrize("mutation", ("steps", "sampling", "matrix", "hist-seeds"), ids=("steps", "sampler", "matrix", "history"))
def test_registered_scope_cannot_be_widened(scope, mutation):
    base, _ = scope
    ready(base)
    def transform(plan):
        if mutation == "matrix":
            plan["matrix"]["knowledge_sizes"] = [32]
        else:
            bound = plan["muc02_negatives_protocol"]
            if mutation == "steps":
                bound["fit_steps_cap"] = 193
            elif mutation == "sampling":
                bound["negative_sampling"]["hard"] = "different distribution"
            else:
                bound["historical_seeds"] = [1]
    register(base, transform=transform)
    with pytest.raises(ValueError, match="scope|seed list"):
        stage.status(base)


@pytest.mark.parametrize("ending", ("result", "invalidated", "postseed", "preparation"), ids=("result", "invalidated", "runner-failure", "fixture-failure"))
def test_every_terminal_outcome_stops_unstarted_scope_without_retry(scope, ending):
    base, preserved = scope
    ready(base)
    plan = register(base)
    identifier = plan["experiment_id"]
    if ending == "result":
        atomic_write_json(base / "research/results" / f"{identifier}.json", {"candidates": [{"execution": {"supervised_fit_seconds": 12.}}]})
    elif ending == "invalidated":
        append_jsonl(base / "research/plan_status_events.jsonl", {"experiment_id": identifier, "status": "invalidated", "reason": "fixture"})
    elif ending == "postseed":
        append_jsonl(base / "research/events.jsonl", {"event": "experiment_runner_postseed_failure", "experiment_id": identifier})
    else:
        relative = "research/reviews/replication-fixture-failure.json"
        atomic_write_json(base / relative, {"status": "failed"})
        append_jsonl(base / "research/events.jsonl", {"event": "muc02_replication_preparation_failed", "stage_id": stage.ID,
            "plan_sha256": stage.PLAN_SHA256, "receipt_path": relative, "receipt_sha256": sha256_file(base / relative)})
    value = stage.status(base)
    assert value["terminal"] and not value["scoring_authorized"] and stage.scope_problems(base, identifier)
    assert value["preserved_research_program"] == preserved


def test_first_start_is_consumed_and_cannot_resume(scope):
    base, _ = scope
    ready(base)
    plan = register(base)
    old = set(plan["muc02_negatives_protocol"]["historical_seeds"])
    fixture_seeds = [seed for seed in range(1111111, 1111120) if seed not in old][:5]
    event = {"event": "experiment_scoring_started", "experiment_id": plan["experiment_id"],
             "plan_sha256": sha256_json(plan), "scoring_seeds": fixture_seeds}
    append_jsonl(base / "research/events.jsonl", event)
    value = stage.status(base)
    assert value["started"] and value["executions_started"] == 1 and not value["scoring_authorized"]
    assert stage.scope_problems(base, plan["experiment_id"])
    append_jsonl(base / "research/events.jsonl", event)
    with pytest.raises(ValueError, match="repeated"):
        stage.status(base)


def test_deadline_and_fit_budget_are_preserved_hard_stops(scope, monkeypatch):
    base, _ = scope
    ready(base)
    class AfterDeadline(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2099, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(stage, "datetime", AfterDeadline)
    assert stage.status(base)["expired"] and stage.scope_problems(base)
    monkeypatch.setattr(stage, "datetime", datetime)
    plan = register(base)
    result = base / "research/results" / f"{plan['experiment_id']}.json"
    atomic_write_json(result, {"candidates": [{"execution": {"supervised_fit_seconds": 3600.}}]})
    assert stage.status(base)["fit_seconds_remaining"] == 0
    atomic_write_json(result, {"candidates": [{"execution": {"supervised_fit_seconds": 3601.}}]})
    with pytest.raises(ValueError, match="fit accounting"):
        stage.status(base)


def test_explicit_overlay_does_not_reopen_historical_scope(scope):
    base, _ = scope
    config = base / "config/research.toml"
    original = config.read_text(encoding="utf-8")
    config.write_text(original.replace("active = true", "active = false").replace(stage.COHORT, "asm01_native_memory_v3"), encoding="utf-8")
    assert stage.status(base) is None
    config.write_text(original.replace(stage.COHORT, "asm01_native_memory_v3"), encoding="utf-8")
    with pytest.raises(ValueError, match="only its own"):
        stage.status(base)


def test_laboratory_overlay_allows_only_new_stage_and_preserves_backing_program(scope, monkeypatch):
    from nextai_autoresearch import laboratory
    base, preserved = scope
    monkeypatch.setattr(laboratory, "_historical_laboratory_progress", lambda root: {"history_fixture": True})
    progress = laboratory.laboratory_progress(base)
    assert progress["muc02_negatives"]["id"] == stage.ID and "research_program" not in progress
    assert progress["preserved_research_program"] == preserved
    assert not progress["scoring_authorized"] and not progress["user_decision_required"]
    assert laboratory.laboratory_contract(base)["maintenance_plan"] == stage.PLAN
    assert laboratory.laboratory_problems(base) == []
    assert laboratory.laboratory_problems(base, scoring=True)
    assert laboratory.pc01_scope_problems(base, candidate="pc01_byte_gpt_v1", phase="dev")
    ready(base)
    assert laboratory.laboratory_contract(base)["scoring_authorized"]
    assert laboratory.laboratory_problems(base, scoring=True) == []
    assert laboratory.pc01_scope_problems(base) == []
    plan = register(base)
    assert laboratory.pc01_scope_problems(base, experiment_id=plan["experiment_id"]) == []
    assert laboratory.pc01_scope_problems(base, series_freeze=True)
