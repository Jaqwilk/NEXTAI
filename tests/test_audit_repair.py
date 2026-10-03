import json
import os
import socket
import sys
import time
from pathlib import Path

import psutil
import pytest

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.config import load_config
from nextai_autoresearch.data_access import require_data_access
from nextai_autoresearch.ledger import RunLock
from nextai_autoresearch.muc_contract import parse_question, parse_statement
from nextai_autoresearch.muc02_task import make_world, TRAIN_TUPLES, HELDOUT_TUPLES
from nextai_autoresearch.utils import atomic_write_json, load_json, project_root, sha256_file


@pytest.mark.parametrize("seed", [8, 9])
def test_excluded_recordings_are_denied_before_hash_native_load_or_open(tmp_path, seed):
    path = tmp_path / "research/data/wt_changepoints_v1/extracted/wt_changepoints_v1" / f"load_in_seed_{seed}.csv"
    for action in (require_data_access, sha256_file, lambda p: p.open("rb")):
        with pytest.raises(PermissionError, match="WT files 8-9"):
            action(path)
    from nextai_autoresearch.benchmarks.heldout_wt_changepoints_prequential_v1 import _load
    with pytest.raises(PermissionError, match="WT files 8-9"):
        _load(tmp_path, (seed,))


def test_aged_live_lock_cannot_be_stolen(tmp_path):
    with RunLock(tmp_path, stale_seconds=0):
        path = tmp_path / "research/run.lock"
        record = load_json(path)
        record["epoch"] = 0
        atomic_write_json(path, record)
        with pytest.raises(RuntimeError, match="active"):
            with RunLock(tmp_path, stale_seconds=0):
                pass
        assert path.exists()
    assert not path.exists()


def test_release_cannot_remove_someone_elses_token(tmp_path):
    with RunLock(tmp_path):
        path = tmp_path / "research/run.lock"
        record = load_json(path)
        record["token"] = "different-owner"
        atomic_write_json(path, record)
    assert path.exists()


def test_proven_dead_lock_is_archived_and_reclaimed(tmp_path):
    path = tmp_path / "research/run.lock"
    atomic_write_json(path, {"host": socket.gethostname(), "pid": os.getpid(),
                             "process_created_at": psutil.Process().create_time() - 100, "epoch": time.time()})
    with RunLock(tmp_path):
        assert load_json(path)["token"]
    assert len(list(path.parent.glob("run.lock.stale-*"))) == 1


@pytest.mark.parametrize("module", ["muc01_task", "muc02_task"])
def test_candidate_cannot_import_private_world_generator(tmp_path, module):
    target = tmp_path / "src/nextai_autoresearch/candidates/probe.py"
    target.parent.mkdir(parents=True)
    target.write_text(f"from nextai_autoresearch.{module} import make_world\nclass Candidate: pass\n", encoding="utf-8")
    result = audit_candidate("probe", load_config(project_root()), tmp_path)
    assert not result.ok and any("forbidden" in value for value in result.problems)


@pytest.mark.parametrize("k", [32, 128, 512])
@pytest.mark.parametrize("d", [1, 2, 4])
def test_v2_composition_labels_match_actual_relation_sequences(k, d):
    world = make_world(k, d, 98731, "F")
    groups = {False: [], True: []}
    for q in world.questions:
        start, relations = parse_question(q.text)
        assert q.unseen_composition == (relations not in TRAIN_TUPLES[d])
        groups[q.unseen_composition].append(q)
        if q.unknown:
            assert start == "EF999" and q.answer == "UNKNOWN"
    if d > 1:
        for group in groups.values():
            assert len(group) == 8
            assert sum(q.replacement_affected for q in group) == 3
            assert sum(q.unchanged_retention for q in group) == 4
            assert sum(q.unknown for q in group) == 1
    else:
        assert len(groups[False]) == 16 and not groups[True]


@pytest.mark.parametrize("answers", [[], ["x"], [None, "x"], "xx", ["x", "x", "x"]])
def test_answer_contract_rejects_missing_extra_and_non_string_answers(answers):
    from nextai_autoresearch.benchmarks.mutable_contact_ledger_v2 import checked_answers
    with pytest.raises(ValueError):
        checked_answers(answers, 2)


class _CounterFixture:
    def synchronize(self): pass
    def warmup(self, session): pass
    def new_session(self): return _CounterSession()
    def fit_cost_report(self):
        return {"fit_ops":270, "preprocessing_ops":135, "fit_seconds":0, "fit_peak_bytes":0,
                "ops_kind":"fixture exact counts", "counts_are_estimates":False}


class _CounterSession:
    last_replaced = False
    def __init__(self): self.mapping, self.inputs, self.queries = {}, 0, 0
    def ingest(self, text):
        _, subject, relation, target = parse_statement(text)
        self.mapping[subject, relation] = target
        self.inputs += 1
    def answer_batch(self, texts):
        self.queries += len(texts)
        answers = []
        for text in texts:
            current, relations = parse_question(text)
            for relation in relations:
                current = self.mapping.get((current, relation), "UNKNOWN")
            answers.append(current)
        return tuple(answers)
    def cost_report(self):
        return {"query_count":self.queries, "query_ops":self.queries*2, "input_ops":self.inputs,
                "search_ops":0, "update_ops":0, "build_ops":0, "preprocessing_ops":0, "warmup_ops":0,
                "state_bytes":len(self.mapping), "peak_state_bytes":len(self.mapping), "bytes_touched":self.queries,
                "parser_failures":0}


def test_world_costs_do_not_accumulate_across_cells_and_charge_full_fit():
    from nextai_autoresearch.benchmarks.mutable_contact_ledger_v2 import run_trial
    system = _CounterFixture()
    first = run_trial(system, 32, 1, 16, 12345, {})
    run_trial(system, 128, 4, 16, 12345, {})
    repeated = run_trial(system, 32, 1, 16, 12345, {})
    for metric in ("mean_query_ops", "mean_input_ops", "workload_ops_r1", "workload_ops_r16"):
        assert repeated[metric] == first[metric]
    assert first["accuracy"] == 1 and first["mean_query_ops"] == 2
    assert first["workload_ops_r1"] == 3 + 40 + 32  # fit+fit preparation, 40 inputs, 16 queries
    assert first["workload_ops_r16"] == 3 + 40 + 16*32


def test_actual_scorer_rejects_a_truncated_world_answer(monkeypatch):
    from nextai_autoresearch.benchmarks.mutable_contact_ledger_v2 import run_trial
    monkeypatch.setattr(_CounterSession, "answer_batch", lambda *_: ())
    with pytest.raises(ValueError, match="exactly 1"):
        run_trial(_CounterFixture(), 32, 1, 16, 12345, {})


def test_pooled_latency_percentile_is_not_mean_of_cell_percentiles():
    from nextai_autoresearch.metrics import aggregate_trials
    row = {"status":"complete", "knowledge_size":32, "reasoning_depth":1, "seed":1,
           "query_count":20, "accuracy":1, "warm_accuracy":1, "mean_query_ops":1, "mean_warm_query_ops":1,
           "p50_latency_us":1, "p95_latency_us":1, "fit_seconds":0, "state_bytes":1, "update_ops":0,
           "update_latency_us":0, "continual_retention":1, "latency_samples_us":[1.] * 20}
    other = {**row, "knowledge_size":128, "p50_latency_us":100, "p95_latency_us":100, "latency_samples_us":[100.] * 20}
    assert aggregate_trials([row, other])["p95_latency_us"] == 100
    broken = {**other, "latency_samples_us":[100.]}
    with pytest.raises(ValueError, match="coverage"):
        aggregate_trials([row, broken])


@pytest.mark.parametrize("name", ["STOP", "PAUSE"])
def test_running_generic_worker_obeys_stop_files(tmp_path, monkeypatch, name):
    import subprocess
    from nextai_autoresearch import runner
    from nextai_autoresearch.audit import AuditResult
    from nextai_autoresearch.ledger import ensure_layout
    ensure_layout(tmp_path)
    real_popen = subprocess.Popen
    code = f"import pathlib,time; pathlib.Path({str(tmp_path / name)!r}).write_text('stop'); time.sleep(30)"
    monkeypatch.setattr(runner.subprocess, "Popen", lambda command, **options: real_popen([sys.executable, "-c", code], **options))
    candidate_file = tmp_path / "probe.py"
    candidate_file.write_text("class Candidate: pass\n")
    outcome = runner._run_candidate("probe", tmp_path / "plan.json", {"experiment_id":"EXP-stop", "budget":"quick"},
                                    load_config(project_root()), tmp_path,
                                    AuditResult(True, "probe", candidate_file, "a"*64, ()))
    assert outcome["status"] == "stopped"
    assert outcome["execution"]["termination_reason"] == "stopped"


def test_partial_trial_journal_survives_worker_exception(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from nextai_autoresearch import worker
    def broken(candidate, plan, trial_sink):
        trial_sink({"status":"failed", "knowledge_size":32, "reasoning_depth":1, "error":"saved first cell"})
        raise RuntimeError("late failure")
    monkeypatch.setattr(worker.importlib, "import_module", lambda *args: SimpleNamespace(BENCHMARK_VERSION="fixture", run_suite=broken))
    path = tmp_path / "plan.json"
    atomic_write_json(path, {"benchmark":"fixture"})
    assert worker.run_worker(path, "probe", tmp_path / "result.json") == 1
    result = load_json(tmp_path / "result.json")
    assert result["error"] == "late failure" and len(result["trials"]) == 1


@pytest.mark.parametrize("fault,reason", [("cuda", "cuda_limit"), ("fit", "fit_timeout"), ("malformed", "telemetry_failure")])
def test_parent_enforces_fit_cuda_and_telemetry_limits(tmp_path, monkeypatch, fault, reason):
    from nextai_autoresearch import worker_resources as resources
    output = tmp_path / "probe.json"
    limits = {"fit_seconds_cap":10, "max_cuda_reserved_bytes":100}
    atomic_write_json(output.with_suffix(".device.json"), {"allocated":0, "reserved":101 if fault == "cuda" else 0})
    atomic_write_json(output.with_suffix(".phase.json"), {"phase":"invalid" if fault == "malformed" else "fit", "fit_started":time.monotonic()-20, "fit_elapsed":0})
    assert resources.resource_problem(output, limits, time.monotonic()-30, time.monotonic())[0] == reason


def test_evaluation_time_does_not_inflate_fit_budget(tmp_path):
    from nextai_autoresearch.worker_resources import WorkerResources
    resource = WorkerResources(tmp_path / "probe.json", {"fit_seconds_cap":10}, tmp_path / "plan.json")
    resource.fit_started = time.monotonic() - 20
    resource.fit_elapsed = 1
    resource.phase_name = "evaluation"
    resource.phase("complete")
    assert resource.fit_elapsed == 1


@pytest.mark.parametrize("fault", ["missing_phase", "missing_device", "stale_device"])
def test_parent_requires_both_phase_and_live_device_telemetry(tmp_path, fault):
    from nextai_autoresearch.worker_resources import resource_problem
    output = tmp_path / "probe.json"
    device = output.with_suffix(".device.json")
    if fault != "missing_device":
        atomic_write_json(device, {"allocated": 0, "reserved": 0})
        if fault == "stale_device":
            old = time.time() - 10
            os.utime(device, (old, old))
    if fault != "missing_phase":
        atomic_write_json(output.with_suffix(".phase.json"),
                          {"phase": "initializing", "fit_started": None, "fit_elapsed": 0})
    now = time.monotonic()
    assert resource_problem(output, {"fit_seconds_cap": 10, "max_cuda_reserved_bytes": 100},
                            now - 60, now - 31)[0] == "telemetry_failure"


def test_parent_recovers_gap_only_after_valid_phase_and_fresh_device(tmp_path):
    from nextai_autoresearch.worker_resources import resource_problem
    output = tmp_path / "probe.json"
    atomic_write_json(output.with_suffix(".device.json"), {"allocated": 0, "reserved": 0})
    atomic_write_json(output.with_suffix(".phase.json"),
                      {"phase": "initializing", "fit_started": None, "fit_elapsed": 0})
    now = time.monotonic()
    reason, gap = resource_problem(output, {"fit_seconds_cap": 10, "max_cuda_reserved_bytes": 100},
                                   now - 60, now - 31)
    assert reason is None and gap >= now


def test_short_worker_exit_before_monitor_attachment_keeps_valid_output(tmp_path, monkeypatch):
    import subprocess
    from nextai_autoresearch import runner
    from nextai_autoresearch.audit import AuditResult
    from nextai_autoresearch.ledger import ensure_layout
    ensure_layout(tmp_path)
    output = tmp_path / "research/tmp/EXP-attach/probe.json"
    payload = {"candidate": "probe", "status": "complete", "trials": [], "summary": {}}
    script = f"import pathlib; pathlib.Path({str(output)!r}).write_text({json.dumps(payload)!r})"
    real_popen = subprocess.Popen
    def launch(command, **options):
        process = real_popen([sys.executable, "-c", script], **options)
        process.wait(timeout=5)
        return process
    monkeypatch.setattr(runner.subprocess, "Popen", launch)
    def unavailable(pid):
        raise psutil.NoSuchProcess(pid)
    monkeypatch.setattr(runner.psutil, "Process", unavailable)
    path = tmp_path / "probe.py"
    path.write_text("class Candidate: pass\n")
    result = runner._run_candidate("probe", tmp_path / "plan.json",
                                  {"experiment_id": "EXP-attach", "budget": "quick"},
                                  load_config(project_root()), tmp_path,
                                  AuditResult(True, "probe", path, "a" * 64, ()))
    assert result["status"] == "complete" and result["execution"]["return_code"] == 0


def test_parent_interrupt_cleans_up_running_child(tmp_path, monkeypatch):
    import subprocess
    from nextai_autoresearch import runner
    from nextai_autoresearch.audit import AuditResult
    from nextai_autoresearch.ledger import ensure_layout
    ensure_layout(tmp_path)
    real_popen = subprocess.Popen
    launched = []
    def launch(command, **options):
        process = real_popen([sys.executable, "-c", "import time; time.sleep(30)"], **options)
        launched.append(process)
        return process
    monkeypatch.setattr(runner.subprocess, "Popen", launch)
    monkeypatch.setattr(runner.time, "sleep", lambda _: (_ for _ in ()).throw(KeyboardInterrupt()))
    path = tmp_path / "probe.py"
    path.write_text("class Candidate: pass\n")
    with pytest.raises(KeyboardInterrupt):
        runner._run_candidate("probe", tmp_path / "plan.json", {"experiment_id":"EXP-interrupt", "budget":"quick"},
                              load_config(project_root()), tmp_path, AuditResult(True, "probe", path, "a"*64, ()))
    assert launched and launched[0].poll() is not None


def test_repository_compression_report_uses_frozen_loss_identity(tmp_path, monkeypatch):
    from nextai_autoresearch import report
    from nextai_autoresearch.comparison_contract import passes_quality, quality_contract
    rows = [r for r in report.collect_rows(project_root()) if r["experiment_id"] == "EXP-20260901-0062"]
    assert any(r.get("bits_per_byte") for r in rows)
    assert all(passes_quality(r, r["eligibility_contract"]) for r in rows if r["candidate_status"] == "complete")
    assert not passes_quality({"accuracy":.9}, quality_contract({"benchmark":"fixture", "eligibility_contract":{"metric":"accuracy", "minimum":.99}}))
    (tmp_path / "research").mkdir()
    monkeypatch.setattr(report, "collect_rows", lambda _: rows)
    monkeypatch.setattr(report, "invalid_experiment_ids", lambda _: set())
    monkeypatch.setattr(report, "load_config", lambda _: load_config(project_root()))
    rendered = report.write_report(tmp_path).read_text(encoding="utf-8")
    assert "| bpb |" in rendered and any(line.endswith("| yes |") for line in rendered.splitlines() if "ppm" in line)
