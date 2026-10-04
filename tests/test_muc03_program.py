"""Budget failures, paired namespace semantics, and unchanged reference identity."""
import hashlib
import inspect
import json
import shutil
import subprocess

import pytest

from nextai_autoresearch import research_program as program
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.utils import load_json, project_root, sha256_file
from nextai_autoresearch.muc03_task import fresh_worlds, iid_namespace, diagnostic_queries, world_seed


def fixture_program(tmp_path):
    root = project_root()
    for rel in ["config/research.toml", program.AUTHORITY, program.CONTRACT, program.FIRST_STUDY]:
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / rel, dst)
    import re
    config = tmp_path / "config/research.toml"
    fixture_study = load_json(tmp_path / program.FIRST_STUDY)
    config_text = re.sub(r'study_path = "[^"]+"', f'study_path = "{program.FIRST_STUDY}"', config.read_text(encoding="utf-8"))
    config_text = re.sub(r'benchmark_version = "[^"]+"', f'benchmark_version = "{fixture_study["cohort"]}"', config_text)
    config.write_text(config_text, encoding="utf-8")
    prior = tmp_path / "research/results/prior.json"
    prior.parent.mkdir(parents=True, exist_ok=True)
    prior.write_text('{}\n', encoding="utf-8")
    contract = load_json(tmp_path / program.CONTRACT)
    contract.update(previous_result="research/results/prior.json", previous_result_sha256=sha256_file(prior))
    (tmp_path / program.CONTRACT).write_text(json.dumps(contract), encoding="utf-8")
    auth = load_json(tmp_path / program.AUTHORITY)
    auth["program_contract_sha256"] = sha256_file(tmp_path / program.CONTRACT)
    (tmp_path / program.AUTHORITY).write_text(json.dumps(auth), encoding="utf-8")
    study = load_json(tmp_path / program.FIRST_STUDY)
    study.update(program_contract_sha256=sha256_file(tmp_path / program.CONTRACT), study_deadline_at="2099-01-01T00:00:00+00:00")
    (tmp_path / program.FIRST_STUDY).write_text(json.dumps(study), encoding="utf-8")
    receipt = tmp_path / "research/laboratory/ready.json"
    receipt.write_text('{}\n', encoding="utf-8")
    common = {"program_id": contract["id"]}
    append_jsonl(tmp_path / "research/events.jsonl", {**common, "event": "research_program_authorized",
                 "authority_sha256": sha256_file(tmp_path / program.AUTHORITY), "contract_sha256": sha256_file(tmp_path / program.CONTRACT)})
    append_jsonl(tmp_path / "research/events.jsonl", {**common, "event": "research_program_study_frozen",
                 "study_path": program.FIRST_STUDY, "study_sha256": sha256_file(tmp_path / program.FIRST_STUDY)})
    append_jsonl(tmp_path / "research/events.jsonl", {**common, "event": "research_program_study_ready", "study_path": program.FIRST_STUDY,
                 "study_sha256": sha256_file(tmp_path / program.FIRST_STUDY), "receipt_path": "research/laboratory/ready.json",
                 "receipt_sha256": sha256_file(receipt)})
    return tmp_path


def test_failed_registration_consumes_one_nonrefundable_ticket(tmp_path, monkeypatch):
    from nextai_autoresearch import gates
    base = fixture_program(tmp_path)
    monkeypatch.setattr(gates, "ensure_can_create_plan", lambda base: (_ for _ in ()).throw(ValueError("fixture gate fails")))
    with pytest.raises(ValueError, match="fixture gate"):
        program.create_plan(base)
    value = program.status(base)
    assert value["registration_attempts_used"] == 1 and value["study_terminal"]
    assert value["stage_registration_attempts"]["reference"] == 1
    with pytest.raises(ValueError, match="consumed"):
        program.create_plan(base)
    assert program.status(base)["registration_attempts_used"] == 1


def test_live_legacy_cli_routes_through_paid_program_without_side_effects(tmp_path, monkeypatch):
    from argparse import Namespace
    from nextai_autoresearch import cli
    base = fixture_program(tmp_path)
    called = []
    monkeypatch.setattr(cli, "project_root", lambda: base)
    monkeypatch.setattr(program, "create_plan", lambda root, requested: called.append((root, requested)) or "fixture-plan")
    before = (base / "research/events.jsonl").read_bytes()
    assert cli.command_plan_new(Namespace(candidates=["wrong_legacy_role"], budget="quick")) == 0
    assert called == [(base, {"candidates": ["wrong_legacy_role"], "budget": "quick", "pc01_phase": None})]
    assert (base / "research/events.jsonl").read_bytes() == before


def test_factory_validates_schema_and_reserves_pending_worst_case_fit(tmp_path, monkeypatch):
    from nextai_autoresearch import gates, baseline_semantics, schemas
    base = fixture_program(tmp_path)
    manifest = base / "research/eval_manifest.json"
    shutil.copyfile(project_root() / "research/eval_manifest.json", manifest)
    monkeypatch.setattr(gates, "ensure_can_create_plan", lambda _: None)
    monkeypatch.setattr(baseline_semantics, "verify_required_baselines", lambda *a, **k: {})
    monkeypatch.setattr(baseline_semantics, "verify_preflight_certificate", lambda _: {})
    validate = schemas.validate_document
    monkeypatch.setattr(schemas, "validate_document", lambda name, doc, root: validate(name, doc, project_root()))
    path = program.create_plan(base)
    plan = load_json(path)
    assert plan["research_program_protocol"]["registration_ticket"] == 1
    assert plan["research_program_protocol"]["diagnostics"]["rejection_threshold"] == .5
    assert plan["research_program_protocol"]["fit_seconds_total_cap"] == 3500
    value = program.status(base)
    assert value["registration_attempts_used"] == 1 and not value["study_terminal"]
    assert value["pending_fit_reservation_seconds"] == 3500
    program.auxiliary_reserve(base, "closing", 600)
    assert program.status(base)["unreserved_fit_seconds_remaining"] == 67900
    with pytest.raises(ValueError, match="consumed"):
        program.create_plan(base)
    contract = load_json(base / program.CONTRACT)
    remaining = [(stage["id"], stage["registration_cap"] - (stage["id"] == "reference")) for stage in contract["stages"]]
    stages = [name for name, cap in remaining for _ in range(cap)]
    for ticket, stage in enumerate(stages, 2):
        relative = f"research/plans/consumed-fixture-{ticket}.json"
        study = load_json(base / program.FIRST_STUDY)
        study["stage"] = stage
        (base / relative).write_text(json.dumps(study), encoding="utf-8")
        append_jsonl(base / "research/events.jsonl", {"event": "research_program_registration_started", "program_id": value["id"],
                     "study_path": relative, "ticket": ticket})
    value = program.status(base)
    assert value["registration_budget_exhausted"] and value["paid_run_pending"] and not value["program_terminal"]
    assert program.scope_problems(base, plan["experiment_id"]) == []
    with pytest.raises(ValueError, match="exhausted"):
        program.create_plan(base)
    result = base / "research/results" / f"{plan['experiment_id']}.json"
    result.write_text(json.dumps({"candidates": [{"execution": {"supervised_fit_seconds": 17.}}]}), encoding="utf-8")
    append_jsonl(base / "research/events.jsonl", {"event": "research_program_outcome_preserved", "program_id": value["id"],
                 "experiment_id": plan["experiment_id"], "result_sha256": sha256_file(result)})
    assert program.status(base)["experimental_fit_seconds"] == 17
    assert not program.status(base)["paid_run_pending"] and program.status(base)["program_terminal"]
    result.write_text(json.dumps({"candidates": [{"execution": {"supervised_fit_seconds": 1.}}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="completed research result changed"):
        program.status(base)


def test_auxiliary_fit_is_reserved_and_charged_including_failure(tmp_path):
    base = fixture_program(tmp_path)
    program.auxiliary_reserve(base, "fixture-test", 600)
    assert program.status(base)["fit_seconds_remaining"] == 71400
    with pytest.raises(ValueError, match="already consumed"):
        program.auxiliary_reserve(base, "fixture-test", 600)
    program.auxiliary_charge(base, "fixture-test", 139)
    assert program.status(base)["fit_seconds_charged"] == 139
    with pytest.raises(ValueError, match="Insufficient"):
        program.auxiliary_reserve(base, "excessive", 72000)
    with pytest.raises(ValueError, match="Repeated"):
        program.auxiliary_charge(base, "fixture-test", 139)
    program.auxiliary_reserve(base, "second-test", 600)
    before = (base / "research/events.jsonl").read_bytes()
    with pytest.raises(ValueError, match="reservation"):
        program.auxiliary_charge(base, "second-test", 601)
    assert (base / "research/events.jsonl").read_bytes() == before


def test_last_registration_can_finish_execution_and_closing_checks(tmp_path):
    base = fixture_program(tmp_path)
    contract = load_json(base / program.CONTRACT)
    stages = [stage["id"] for stage in contract["stages"] for _ in range(stage["registration_cap"])]
    for ticket, stage in enumerate(stages, 1):
        path = f"research/plans/fixture-study-{ticket}.json"
        study = load_json(base / program.FIRST_STUDY)
        study["stage"] = stage
        (base / path).write_text(json.dumps(study), encoding="utf-8")
        append_jsonl(base / "research/events.jsonl", {"event": "research_program_registration_started",
                     "program_id": contract["id"], "ticket": ticket, "study_path": path})
    value = program.status(base)
    assert value["registration_attempts_used"] == 20 and value["program_terminal"]
    assert value["scoring_authorized"]  # No unpaid twenty-first registration is permitted.
    with pytest.raises(ValueError, match="exhausted"):
        program.create_plan(base)
    program.auxiliary_reserve(base, "closing-checks", 600)
    program.auxiliary_charge(base, "closing-checks", 1)
    assert program.status(base)["fit_seconds_charged"] == 1


def test_changed_authority_or_study_fails_closed(tmp_path):
    base = fixture_program(tmp_path)
    path = base / program.FIRST_STUDY
    study = load_json(path)
    study["roles"]["muc03_hard_768_s0"]["fit_steps"] = 769
    path.write_text(json.dumps(study), encoding="utf-8")
    with pytest.raises(ValueError, match="immutable"):
        program.status(base)


def test_execution_fit_charge_falls_back_conservatively():
    assert program._execution_fit([{"execution": {"wall_seconds": 43}}]) == 43
    assert program._execution_fit([{"execution": {"wall_seconds": 43, "supervised_fit_seconds": 8}}]) == 8
    with pytest.raises(ValueError, match="Invalid"):
        program._execution_fit([{"execution": {"supervised_fit_seconds": float("nan")}}])


def test_fresh_namespace_intervention_preserves_graph_and_gold():
    from nextai_autoresearch.candidates.muc02_core import SymbolicSystem
    from nextai_autoresearch.benchmarks.mutable_contact_ledger_hard_negatives_v1 import run_trial
    tag = "MUC03-UNIT-FIXTURE"
    worlds = fresh_worlds(tag, 809, "D", 32, 1, 15)
    world = worlds[0]
    iid = iid_namespace(world)
    assert iid_namespace(world) == iid and world != iid
    assert tuple(s.replace("ED", "ET") for s in world.statements) == iid.statements
    assert [q.answer.replace("ED", "ET") for q in world.questions] == [q.answer for q in iid.questions]
    original_queries = diagnostic_queries(tag, world, 809, 32, 1, 0)
    renamed_queries = diagnostic_queries(tag, iid, 809, 32, 1, 0)
    assert [(s.replace("ED", "ET"), r) for s, r in original_queries] == list(renamed_queries)
    assert renamed_queries[2][0] == "ET999" and renamed_queries[3][1] == "violet"
    with pytest.raises(ValueError, match="train/dev"):
        fresh_worlds(tag, 809, "F", 32, 1, 15)
    assert len({world_seed(tag, 809, split, 32, 1, i) for split in ("T", "D") for i in range(15)}) == 30
    system = SymbolicSystem(809, {})
    system.record_fit_resources(0, 0)
    trial = run_trial(system, 32, 1, 809, {}, False, worlds_provider=lambda: worlds)
    assert trial["accuracy"] == 1 and trial["query_count"] == 240
    assert len(trial["latency_samples_us"]) == 240 and len(trial["world_costs"]) == 15


def test_namespace_diagnostic_is_correct_before_gold_and_preserves_threshold():
    from nextai_autoresearch.benchmarks.muc03_undertraining_v1 import domain_diagnostic
    from nextai_autoresearch.benchmarks.mutable_contact_ledger_hard_negatives_v1 import diagnostic_metrics
    class ExactScores:
        def synchronize(self):
            pass
        def scores(self, query, keys):
            return [.9 if query == key else .1 for key in keys]
        class Model:
            length = 96
            def estimated_forward_flops(self, examples):
                return examples
        model = Model()
    world = fresh_worlds("MUC03-UNIT-FIXTURE", 813, "D", 32, 1, 1)[0]
    for variant in (world, iid_namespace(world)):
        group = domain_diagnostic("MUC03-UNIT-FIXTURE", ExactScores(), variant, 813, 32, 1, 0)
        with pytest.raises(ValueError, match="strata coverage"):
            diagnostic_metrics([group])
        m = diagnostic_metrics([group], worlds_expected=1)
        assert m["fact_top1_accuracy"] == m["dense_unknown_rejection"] == m["accepted_fact_accuracy"] == 1
        assert m["known_false_abstention"] == m["pair_false_negative_rate"] == 0
        assert group["estimated_flops"] > 0 and group["preparation_ops"] > 0


def test_reference_model_sampler_and_pairing_remain_unchanged():
    import torch
    from nextai_autoresearch.candidates.muc03_reference import Candidate
    from nextai_autoresearch.candidates.muc02_core import Reader
    source = subprocess.check_output(["git", "show", "a74dbce:src/nextai_autoresearch/candidates/muc02_core.py"], cwd=project_root()).decode()
    assert inspect.getsource(Reader).strip() == source[source.index("class Reader("):source.index("class BM25Index:")].strip()
    study = load_json(project_root() / program.FIRST_STUDY)
    protocol = {"recipe": study["recipe"], "fit_seconds_cap": 350}
    short = Candidate(817, {**protocol, "fit_steps_cap": 192})
    long = Candidate(817, {**protocol, "fit_steps_cap": 768})
    digest = lambda m: hashlib.sha256(b"".join(v.detach().cpu().numpy().tobytes() for v in m.state_dict().values())).hexdigest()
    assert digest(short.model) == digest(long.model)
    assert short.negative_sampling == long.negative_sampling == "hard"
    assert short.mode == long.mode == "bm25" and len(long.model.encoder.layers) == 6
    generator = torch.Generator().manual_seed(817)
    first = torch.randperm(4096, generator=generator)
    generator = torch.Generator().manual_seed(817)
    assert torch.equal(first, torch.randperm(4096, generator=generator))
