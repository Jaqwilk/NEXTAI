"""Synthetic apparatus tests only. Never train/score the PC-01 model or corpus."""
from __future__ import annotations

import copy
import hashlib
import json

import numpy as np
import pytest

from nextai_autoresearch import pc01
from nextai_autoresearch.utils import project_root


def uniform(inputs):
    return np.zeros((*inputs.shape, 256), dtype=np.float64)


def test_known_probability_controls_and_deliberately_wrong_targets():
    targets = np.array([7, 7, 7])
    loss, n = pc01.loss_sum(np.zeros((3, 256)), targets)
    assert loss/n/np.log(2) == pytest.approx(8, abs=1e-10)
    p = np.full((3, 256), 0.5/255)
    p[:, 7] = 0.5
    loss, n = pc01.loss_sum(np.log(p), targets)
    assert loss/n/np.log(2) == pytest.approx(1, abs=1e-10)
    p[:] = 0.01/255
    p[:, 7] = 0.99
    good, _ = pc01.loss_sum(np.log(p), targets)
    bad, _ = pc01.loss_sum(np.log(p), (targets+1) % 256)
    assert good/n/np.log(2) < 0.02
    assert bad/n/np.log(2) > 10


@pytest.mark.parametrize("size", [2, 255, 256, 257, 258, 513, 777])
def test_windows_cover_exactly_once_and_mask_tail(size):
    data = bytes(i % 256 for i in range(size))
    windows = list(pc01.byte_windows(data))
    assert b"".join(y for x, y in windows) == data[1:]
    assert all(len(x) == len(y) and all((a+1) % 256 == b for a, b in zip(x, y)) for x, y in windows)
    results = [pc01.evaluate_bytes(uniform, data, batch_size=b) for b in (1, 2, 64)]
    assert all(r["target_count"] == size-1 for r in results)
    assert all(r["bits_per_byte"] == pytest.approx(8, abs=1e-10) for r in results)


def test_partition_invariance_for_nonconstant_loss():
    data = bytes(range(256))*4+b"end"
    def logits(x):
        return np.sin(np.arange(256)[None, None, :]+x[:, :, None])
    reference = pc01.evaluate_bytes(logits, data, batch_size=1)
    assert pc01.evaluate_bytes(logits, data, batch_size=3)["bits_per_byte"] == pytest.approx(reference["bits_per_byte"], abs=1e-10)


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_nonfinite_metric_is_rejected(bad):
    logits = np.zeros((1, 256))
    logits[0, 1] = bad
    with pytest.raises(ValueError, match="nonfinite"):
        pc01.loss_sum(logits, np.array([1]))


def test_invalid_target_and_empty_mask_rejected():
    with pytest.raises(ValueError, match="targets"):
        pc01.loss_sum(np.zeros((1, 256)), np.array([256]))
    with pytest.raises(ValueError, match="targets"):
        pc01.loss_sum(np.zeros((1, 256)), np.array([1]), np.array([False]))


def test_corpus_hashes_without_quality_or_text_output():
    payload, manifest = pc01.verify_corpus()
    assert len(payload) == 1115394
    assert manifest["sha256"] == pc01.DATA_SHA256
    view = pc01.development_data()
    assert len(view.get("train", purpose="fit")) == 948084
    assert len(view.get("dev", purpose="evaluate")) == 55770
    assert not hasattr(view, "final")
    for purpose, split in (("fit", "final"), ("fit", "dev"), ("evaluate", "final"), ("final", "final")):
        with pytest.raises(ValueError, match="access denied"):
            view.get(split, purpose=purpose)
    broken = copy.deepcopy(manifest["splits"])
    broken["dev"]["start_inclusive"] -= 1
    with pytest.raises(ValueError, match="overlap"):
        pc01.verify_splits(payload, broken)
    with pytest.raises(ValueError, match="hash"):
        pc01.verify_splits(bytes([payload[0] ^ 1])+payload[1:], manifest["splits"])


def curve():
    return [{"update": update, "bits_per_byte": 0.0 if update == 0 else 3.0,
             "checkpoint_sha256": ("0" if update == 0 else "1")*64}
            for update in range(0, 5001, 250)]


def test_checkpoint_selection_excludes_initialization_and_breaks_ties_on_dev():
    assert pc01.choose_checkpoint(curve(), split="dev")["update"] == 250
    with pytest.raises(ValueError, match="dev"):
        pc01.choose_checkpoint(curve(), split="final")
    with pytest.raises(ValueError, match="incomplete"):
        pc01.choose_checkpoint(curve()[:-1], split="dev")


def test_causality_control_rejects_future_sensitive_predictor():
    x = np.arange(32).reshape(2, 16)
    def causal(x):
        return np.repeat(x.cumsum(axis=1)[:, :, None], 256, axis=2)
    def leaky(x):
        return np.broadcast_to(x.sum(axis=1)[:, None, None], (*x.shape, 256))
    pc01.assert_causal(causal, x, cut=8)
    with pytest.raises(ValueError, match="future"):
        pc01.assert_causal(leaky, x, cut=8)


def test_learning_off_hash_control_uses_100_unchanged_steps():
    weights = np.arange(16, dtype=np.float64)
    digest = lambda: hashlib.sha256(weights.tobytes()).hexdigest()
    before, steps = digest(), []
    for _ in range(100):
        float(weights @ weights)  # forward only, no optimizer or training
        steps.append(digest())
    pc01.assert_learning_off(before, steps)
    steps[-1] = "a"*64
    with pytest.raises(ValueError, match="weights changed"):
        pc01.assert_learning_off(before, steps)


def usage():
    return {"fit_seconds": 100, "worker_seconds": 110, "rss_bytes": pc01.GIB,
            "cuda_allocated_bytes": pc01.GIB, "cuda_reserved_bytes": 2*pc01.GIB,
            "persisted_bytes": pc01.GIB, "disk_free_bytes": 20*pc01.GIB}


@pytest.mark.parametrize("field,value", [
    ("fit_seconds", 1201), ("worker_seconds", 1801), ("rss_bytes", 11*pc01.GIB),
    ("cuda_allocated_bytes", 11*pc01.GIB), ("cuda_reserved_bytes", 11*pc01.GIB),
    ("persisted_bytes", 3*pc01.GIB), ("disk_free_bytes", 9*pc01.GIB),
    ("worker_seconds", float("nan")), ("fit_seconds", -1),
])
def test_resource_controls_fail_closed(field, value):
    sample = usage()
    sample[field] = value
    with pytest.raises(ValueError):
        pc01.check_resources(sample)


def test_cooperative_guard_and_aggregate_budget():
    times = iter([0.0, 1.0, 101.0, 1202.0])
    guard = pc01.BudgetGuard(usage, clock=lambda: next(times))
    guard.begin_fit()
    assert guard.check()["fit_seconds"] == 100
    with pytest.raises(ValueError, match="fit_seconds"):
        guard.check()
    with pytest.raises(ValueError, match="aggregate"):
        pc01.check_resources(usage(), previous_fit_seconds=7150)


def expected_outputs():
    return {name: b"x"*(b*(256 if teacher else 1)) for name, (b, teacher) in pc01.SCENARIOS.items()}


def timing_fixture():
    now = 0
    def clock():
        nonlocal now
        now += 100
        return now
    return pc01.measure_scenarios(lambda xs, teacher: b"x"*(len(xs)*(256 if teacher else 1)),
                                  lambda: None, bytes(range(256))*32,
                                  expected_outputs=expected_outputs(), clock_ns=clock)


def test_timer_synchronization_boundary_output_and_batch_semantics():
    calls, now = [], 0
    def sync():
        calls.append("sync")
    def clock():
        nonlocal now
        calls.append("clock")
        now += 10
        return now
    def predict(xs, teacher):
        calls.append("predict")
        assert all(type(x) is bytes and len(x) == 256 for x in xs)
        return b"x"*(len(xs)*(256 if teacher else 1))
    timing = pc01.measure_scenarios(predict, sync, bytes(range(256))*32,
                                    expected_outputs=expected_outputs(), clock_ns=clock)
    assert calls == ["sync", "clock", "predict", "sync", "clock"]*(4*120)
    pc01.validate_timing(timing)
    assert timing["B1-next"]["output_bytes_per_repeat"] == 1
    assert timing["B32-teacher"]["output_bytes_per_repeat"] == 8192
    bad = copy.deepcopy(timing)
    bad["B1-next"]["samples_ns"].pop()
    with pytest.raises(ValueError, match="repeats"):
        pc01.validate_timing(bad)
    with pytest.raises(ValueError, match="CPU output"):
        pc01.measure_scenarios(lambda *args: None, sync, bytes(range(256))*32,
                               expected_outputs=expected_outputs(), clock_ns=clock)
    with pytest.raises(ValueError, match="differs from reference"):
        pc01.measure_scenarios(lambda xs, teacher: b"y"*(len(xs)*(256 if teacher else 1)),
                               sync, bytes(range(256))*32, expected_outputs=expected_outputs(), clock_ns=clock)


def test_cuda_fixture_checks_sync_and_causality_without_training():
    torch = pytest.importorskip("torch")
    if not torch.cuda.is_available():
        pytest.skip("CUDA unavailable; never silently claim GPU validation")
    device = "cuda"
    q = torch.arange(32, device=device, dtype=torch.float32).reshape(1, 1, 8, 4)/32
    altered = q.clone()
    altered[:, :, 4:] += 1
    with torch.no_grad():
        expected = torch.nn.functional.scaled_dot_product_attention(q, q, q, is_causal=True)
        actual = torch.nn.functional.scaled_dot_product_attention(altered, altered, altered, is_causal=True)
        torch.cuda.synchronize()
        assert torch.allclose(expected[:, :, :4], actual[:, :, :4], atol=1e-5, rtol=1e-5)
        broken = torch.nn.functional.scaled_dot_product_attention(altered, altered, altered, is_causal=False)
        assert not torch.allclose(expected[:, :, :4], broken[:, :, :4], atol=1e-5, rtol=1e-5)


def replica(index=1):
    """Fabricated envelope to unit-test gates; never persisted as a result."""
    return {
        "schema_version": 1, "kind": "pc01_local_calibration_replica", "phase": "final", "status": "complete",
        "experiment_id": f"EXP-20990101-{index:04}", "seed": 10000+index,
        "contract_sha256": pc01.CONTRACT_SHA256, "data_sha256": pc01.DATA_SHA256,
        **{key: "a"*64 for key in ("evaluator_sha256", "candidate_sha256", "recipe_sha256", "series_sha256")},
        "initial_weights_sha256": "0"*64, "frozen_weights_sha256": "0"*64, "trained_weights_sha256": "1"*64,
        "updates": 5000, "target_count": 111539, "trained_bpb": 3.0, "frozen_bpb": 8.0,
        "unigram_bpb": 4.0, "bigram_bpb": 3.0, "fp32_dev_bpb": 3.0, "bf16_dev_bpb": 3.001,
        "dev_curve": curve(), "controls": {name: True for name in pc01.CONTROL_NAMES},
        "resources": usage(), "timing": timing_fixture(), "architecture_promoted": False,
        "evidence_scope": "local_single_corpus_diagnostic",
    }


def test_final_gate_separates_learning_economics_and_transfer():
    decision = pc01.series_decision([replica(i) for i in (1, 2, 3)])
    assert decision["decision"] == "positive_control_pass"
    assert decision["lower_95pct_t"] == 5
    assert not decision["architecture_promoted"]
    assert not decision["economic_advantage_established"]
    assert not decision["transfer_established"]


@pytest.mark.parametrize("field,value", [
    ("seed", 10001), ("experiment_id", "EXP-20990101-0001"),
    ("candidate_sha256", "b"*64), ("evaluator_sha256", "b"*64),
    ("recipe_sha256", "b"*64), ("series_sha256", "b"*64), ("data_sha256", "b"*64),
    ("updates", 4999), ("status", "crash"), ("phase", "dev"),
    ("trained_bpb", float("nan")), ("frozen_weights_sha256", "b"*64),
    ("trained_weights_sha256", "0"*64), ("target_count", 111538),
    ("bf16_dev_bpb", 3.2), ("architecture_promoted", True),
])
def test_final_gate_rejects_broken_records(field, value):
    records = [replica(i) for i in (1, 2, 3)]
    records[1][field] = value
    assert pc01.series_decision(records)["decision"] == "inconclusive"


@pytest.mark.parametrize("control", pc01.CONTROL_NAMES)
def test_every_required_control_must_pass(control):
    records = [replica(i) for i in (1, 2, 3)]
    records[0]["controls"][control] = False
    assert pc01.series_decision(records)["decision"] == "inconclusive"


def test_valid_negative_is_not_crash_and_partial_series_is_inconclusive():
    records = [replica(i) for i in (1, 2, 3)]
    records[0]["trained_bpb"] = 3.6
    assert pc01.series_decision(records)["decision"] == "valid_negative"
    assert pc01.series_decision(records[:2])["decision"] == "inconclusive"
    records[0]["controls"].pop(pc01.CONTROL_NAMES[0])
    assert pc01.series_decision(records)["decision"] == "inconclusive"


def test_progress_resolves_verified_completion_and_cap_without_authorizing_scoring(tmp_path, monkeypatch):
    from nextai_autoresearch import laboratory
    from nextai_autoresearch.utils import sha256_file
    initial = json.loads((project_root() / laboratory.CONTRACT_PATH).read_text())
    monkeypatch.setattr(laboratory, "laboratory_contract", lambda root: initial)
    directory = tmp_path / "research"
    directory.mkdir()
    proof = directory / "proof.json"
    proof.write_text('{"fixture":true}')
    def event(attempt):
        return {"event": "lab_milestone_progress", "restart_id": initial["restart_id"], "milestone_id": "PC-01",
                "attempt": attempt, "training_performed": False, "scoring_performed": False,
                "cumulative_budget": {"service_cycles_used": attempt, "service_cycles_cap": 2,
                                      "service_minutes_conservatively_charged": attempt*30,
                                      "total_fit_seconds_used": 0, "development_attempts_used": 0},
                "status": "design_contract_completed" if attempt == 1 else "preparation_blocked",
                "next_action_id": "PC-01-HARNESS" if attempt == 1 else "PC-01-DECISION",
                "next_action": "Synthetic fixture, not an actual milestone completion.",
                "artifact_sha256": {"research/proof.json": sha256_file(proof)}}
    events = directory / "events.jsonl"
    assert laboratory.laboratory_progress(tmp_path)["next_action_id"] == "PC-01-CONTRACT"
    events.write_text(json.dumps(event(1))+"\n")
    assert laboratory.laboratory_progress(tmp_path)["next_action_id"] == "PC-01-HARNESS"
    events.write_text(json.dumps(event(1))+"\n"+json.dumps(event(2))+"\n")
    status = laboratory.laboratory_progress(tmp_path)
    assert status["service_budget_exhausted"] and status["user_decision_required"]
    assert status["next_action_id"] == "PC-01-DECISION"
    proof.write_text('{"fixture":"tampered"}')
    with pytest.raises(ValueError, match="artifact"):
        laboratory.laboratory_progress(tmp_path)
    events.write_text(json.dumps(event(1))+"\n"+json.dumps(event(1))+"\n")
    with pytest.raises(ValueError, match="resets"):
        laboratory.laboratory_progress(tmp_path)
    bad = event(1)
    bad["next_action_id"] = "TRAIN-NOW"
    events.write_text(json.dumps(bad)+"\n")
    with pytest.raises(ValueError, match="transition"):
        laboratory.laboratory_progress(tmp_path)
    bad = event(1)
    bad["artifact_sha256"] = {"../escape.json": "a"*64}
    events.write_text(json.dumps(bad)+"\n")
    with pytest.raises(ValueError, match="artifact"):
        laboratory.laboratory_progress(tmp_path)


def test_candidate_cannot_import_the_private_pc01_evaluator(tmp_path):
    from nextai_autoresearch.audit import audit_candidate
    from nextai_autoresearch.config import load_config
    path = tmp_path / "src/nextai_autoresearch/candidates/pc01_bad_fixture.py"
    path.parent.mkdir(parents=True)
    (path.parent.parent / "pc01.py").write_text("# Private evaluator fixture; never executed.\n")
    path.write_text("from nextai_autoresearch.pc01 import verify_corpus\nclass Candidate:\n    pass\n")
    report = audit_candidate("pc01_bad_fixture", load_config(project_root()), tmp_path)
    assert not report.ok
    assert any("crosses evaluator boundary" in problem for problem in report.problems)
