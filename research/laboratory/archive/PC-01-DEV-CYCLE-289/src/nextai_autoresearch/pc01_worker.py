"""Trusted PC-01 torch recipe and evaluator. No candidate architecture lives here.

Candidate must export Candidate(model_config=...) -> torch.nn.Module, forward
(integer BxT tokens) -> BxTx256 logits. No targets, dev/final buffers or paths are
passed to the model. The evaluator owns optimizer, sampling, selection and timing.
This is an audited Python boundary, not an inaccessible/OS-isolated holdout.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib
import math
from pathlib import Path
import random
import shutil
import subprocess
import time
import traceback

import numpy as np

from . import pc01
from .pc01_execution import (ATTEMPTS, audit_bundle, new_json, validate_plan,
                             verify_certificate, verify_series)
from .ledger import read_jsonl, registered_plan_hash
from .pc01_telemetry import write_device_sample
from .gates import ensure_can_run_plan
from .utils import atomic_write_json, load_json, project_root, sha256_json


def scalar_baselines(train: bytes):
    """Add-one marginal/transition counts see exactly the same legal train bytes."""
    values = np.frombuffer(train, dtype=np.uint8).astype(np.int64)
    unigram = np.bincount(values, minlength=256).astype(np.float64)+1
    unigram = np.log(unigram/unigram.sum())
    bigram = np.bincount(values[:-1]*256+values[1:], minlength=256*256).reshape(256, 256).astype(np.float64)+1
    bigram = np.log(bigram/bigram.sum(axis=1, keepdims=True))
    return (lambda x: np.broadcast_to(unigram, (*x.shape, 256))), (lambda x: bigram[x])


def numerical_controls() -> None:
    targets = np.array([7, 7, 7], dtype=np.int64)
    uniform, uniform_n = pc01.loss_sum(np.zeros((3, 256)), targets)
    pc01.require(abs(uniform/uniform_n/math.log(2)-8) < 1e-10, "uniform byte scale control")
    p = np.full((3, 256), 0.5/255)
    p[:, 7] = 0.5
    loss, n = pc01.loss_sum(np.log(p), targets)
    pc01.require(abs(loss/n/math.log(2)-1) < 1e-10, "known loss control")
    wrong, _ = pc01.loss_sum(np.log(p), (targets+1) % 256)
    pc01.require(wrong > loss+10, "wrong target control")
    fixture = bytes(range(256))*3+b"tail"
    windows = list(pc01.byte_windows(fixture))
    pc01.require(b"".join(y for _, y in windows) == fixture[1:], "target alignment")
    view = pc01.DevelopmentData(b"train", b"dev")
    try:
        view.get("final", purpose="fit")
    except ValueError:
        pass
    else:
        raise ValueError("holdout access control failed")


def learning_rate(update: int) -> float:
    pc01.require(type(update) is int and 0 <= update < 5000, "invalid update")
    if update < 100:
        return 0.001*update/100
    ratio = (update-100)/(5000-100)
    return 0.0001+0.5*(1+math.cos(math.pi*ratio))*(0.001-0.0001)


def weights_digest(model) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        array = value.detach().cpu().contiguous().numpy()
        digest.update(name.encode())
        digest.update(str(array.dtype).encode())
        digest.update(str(array.shape).encode())
        digest.update(array.tobytes())
    return digest.hexdigest()


def verify_model_layout(model, specification: dict) -> None:
    """Enforce the conventional nanoGPT layout, not just a coincidental parameter count."""
    import torch
    from torch import nn
    pc01.require(isinstance(model, nn.Module), "Candidate must be a torch module")
    expected = {"transformer.wte.weight": (256, 384), "transformer.wpe.weight": (256, 384),
                "transformer.ln_f.weight": (384,)}
    for index in range(6):
        for suffix, shape in {"ln_1.weight": (384,), "ln_2.weight": (384,),
                              "attn.c_attn.weight": (1152, 384), "attn.c_proj.weight": (384, 384),
                              "mlp.c_fc.weight": (1536, 384), "mlp.c_proj.weight": (384, 1536)}.items():
            expected[f"transformer.h.{index}.{suffix}"] = shape
    actual = {name: tuple(parameter.shape) for name, parameter in model.named_parameters()}
    pc01.require(actual == expected, "model parameter layout/bias/tied-weight mismatch")
    pc01.require(model.lm_head.weight is model.transformer.wte.weight, "embeddings must be tied")
    pc01.require(sum(p.numel() for p in model.parameters()) == specification["expected_unique_parameter_count"], "parameter count")
    pc01.require(all(p.requires_grad and p.dtype == torch.float32 for p in model.parameters()), "all parameters must train in FP32")
    norms = [m for m in model.modules() if isinstance(m, nn.LayerNorm)]
    dropouts = [m for m in model.modules() if isinstance(m, nn.Dropout)]
    activations = [m for m in model.modules() if isinstance(m, nn.GELU)]
    pc01.require(len(norms) == 13 and all(m.eps == 1e-5 and m.bias is None for m in norms), "LayerNorm recipe mismatch")
    pc01.require(len(dropouts) == 19 and all(m.p == 0.2 for m in dropouts), "dropout recipe mismatch")
    pc01.require(len(activations) == 6 and all(m.approximate == "none" for m in activations), "GELU recipe mismatch")
    pc01.require(all(getattr(block.attn, "n_head", None) == 6 for block in model.transformer.h), "attention head count")


def validate_runtime(runtime_path: Path, root: Path) -> dict:
    runtime = load_json(runtime_path)
    plan = runtime["plan"]
    validate_plan(plan, root)
    ensure_can_run_plan(plan["experiment_id"], root)
    verify_certificate(root)
    pc01.require(registered_plan_hash(plan["experiment_id"], root) == sha256_json(plan), "unregistered worker plan")
    pc01.require(runtime_path.resolve() == (root / "research/tmp" / plan["experiment_id"] / "pc01-runtime.json").resolve(),
                 "noncanonical worker runtime")
    starts = [e for e in read_jsonl(root / ATTEMPTS) if e.get("experiment_id") == plan["experiment_id"]]
    pc01.require(len(starts) == 1 and starts[0]["event"] == "started" and starts[0]["runtime_sha256"] == sha256_json(runtime),
                 "worker runtime unregistered or already terminal")
    pc01.require(runtime["audit"] == audit_bundle(plan["candidate"], root), "worker source changed")
    if plan["phase"] == "dev":
        pc01.require(runtime["seed"] == 1103 and plan["series_sha256"] is None, "wrong dev seed/series")
    else:
        pc01.require(10000 <= runtime["seed"] <= 2147483647, "wrong final seed")
        pc01.require(plan["series_sha256"] == sha256_json(verify_series(root)), "unfrozen final access")
    return runtime


def run(runtime_path: Path, root: Path) -> None:
    runtime = validate_runtime(runtime_path, root)  # Before importing torch or exposing any data.
    import torch
    from torch.nn import functional as F

    plan, seed = runtime["plan"], runtime["seed"]
    work = runtime_path.parent
    design = pc01.contract(root)
    numerical_controls()
    pc01.require(torch.cuda.is_available() and torch.cuda.is_bf16_supported(), "contract requires CUDA BF16")
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.cuda.set_per_process_memory_fraction(10*pc01.GIB/torch.cuda.get_device_properties(0).total_memory, 0)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.cuda.reset_peak_memory_stats()
    load_started = time.monotonic()
    module = importlib.import_module(f"nextai_autoresearch.candidates.{plan['candidate']}")
    model = module.Candidate(model_config=dict(design["model"]))
    verify_model_layout(model, design["model"])
    # nanoGPT initialization is evaluator-owned. Names c_proj identify residual projections.
    projections = 0
    for item in model.modules():
        if isinstance(item, (torch.nn.Linear, torch.nn.Embedding)):
            torch.nn.init.normal_(item.weight, mean=0, std=0.02)
            if getattr(item, "bias", None) is not None:
                torch.nn.init.zeros_(item.bias)
        elif isinstance(item, torch.nn.LayerNorm):
            torch.nn.init.ones_(item.weight)
            if item.bias is not None:
                torch.nn.init.zeros_(item.bias)
    for name, parameter in model.named_parameters():
        if name.endswith("c_proj.weight"):
            torch.nn.init.normal_(parameter, mean=0, std=0.02/math.sqrt(12))
            projections += 1
    pc01.require(projections == 12, "expected twelve residual projections")
    model = model.float().cuda()
    load_seconds = time.monotonic()-load_started
    view = pc01.development_data(root)
    train, dev = view.get("train", purpose="fit"), view.get("dev", purpose="evaluate")
    # Final data is acquired only for a previously frozen final-series runtime.
    evaluation = dev
    if plan["phase"] == "final":
        payload, manifest = pc01.verify_corpus(root)
        part = manifest["splits"]["final"]
        evaluation = payload[part["start_inclusive"]:part["end_exclusive"]]
        del payload
    unigram, bigram = scalar_baselines(train)

    def sample_device():
        torch.cuda.synchronize()
        row = {"allocated": torch.cuda.max_memory_allocated(), "reserved": torch.cuda.max_memory_reserved()}
        write_device_sample(work / "device.json", row, root)
        pc01.require(row["allocated"] <= 10*pc01.GIB and row["reserved"] <= 10*pc01.GIB, "CUDA memory cap")

    def predict(x, *, fp32=False):
        model.eval()
        with torch.no_grad(), (contextlib.nullcontext() if fp32 else torch.autocast("cuda", dtype=torch.bfloat16)):
            logits = model(torch.as_tensor(np.array(x, copy=True), dtype=torch.long, device="cuda"))
            pc01.require(isinstance(logits, torch.Tensor) and tuple(logits.shape) == (*x.shape, 256), "model output shape")
            return logits.float().cpu().numpy()

    fixture = np.frombuffer(dev[:512], dtype=np.uint8).astype(np.int64).reshape(2, 256)
    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU, torch.profiler.ProfilerActivity.CUDA]) as profile:
        predict(fixture)
        torch.cuda.synchronize()
    attention_events = sorted({event.key for event in profile.key_averages() if "scaled_dot_product" in event.key})
    pc01.require(attention_events, "candidate did not use the frozen SDPA attention recipe")
    pc01.assert_causal(predict, fixture, cut=128)
    batch_one = pc01.evaluate_bytes(predict, dev[:1025], batch_size=1)
    batch_many = pc01.evaluate_bytes(predict, dev[:1025], batch_size=3)
    pc01.require(abs(batch_one["bits_per_byte"]-batch_many["bits_per_byte"]) <= 0.02, "batch partition numerical drift")
    initial = weights_digest(model)
    off = []
    for _ in range(100):
        predict(fixture)  # No optimizer step; the same source stays frozen.
        off.append(weights_digest(model))
    pc01.assert_learning_off(initial, off)
    frozen_bpb = pc01.evaluate_bytes(predict, evaluation)["bits_per_byte"]
    frozen = weights_digest(model)
    pc01.require(initial == frozen, "initial evaluation mutated weights")
    baseline_unigram = pc01.evaluate_bytes(unigram, evaluation)["bits_per_byte"]
    baseline_bigram = pc01.evaluate_bytes(bigram, evaluation)["bits_per_byte"]
    parameters = list(model.parameters())
    optimizer = torch.optim.AdamW([
        {"params": [p for p in parameters if p.ndim >= 2], "weight_decay": 0.1},
        {"params": [p for p in parameters if p.ndim < 2], "weight_decay": 0.0},
    ], lr=0.001, betas=(0.9, 0.99), eps=1e-8, fused=False, foreach=False)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    training = torch.from_numpy(np.frombuffer(train, dtype=np.uint8).copy().astype(np.int64))
    payload_dir = root / "research/pc01_payload" / plan["experiment_id"]
    payload_dir.mkdir(parents=True, exist_ok=False)
    checkpoint = payload_dir / "best.pt"
    curve, best = [], math.inf
    new_json(work / "fit-request.json", {"ready": True})
    while not (work / "fit-granted.json").exists():
        time.sleep(0.01)  # Parent starts deadline BEFORE granting; worker itself is supervised.
    fit_started = time.monotonic()

    def evaluate_checkpoint(update):
        nonlocal best
        value = pc01.evaluate_bytes(predict, dev)["bits_per_byte"]
        digest = weights_digest(model)
        curve.append({"update": update, "bits_per_byte": value, "checkpoint_sha256": digest})
        atomic_write_json(work / "dev-curve.json", {"curve": curve})
        if update > 0 and value < best:
            best = value
            torch.save(model.state_dict(), checkpoint)
        sample_device()

    evaluate_checkpoint(0)
    for update in range(5000):
        pc01.require(time.monotonic()-fit_started <= 1200, "fit timeout")
        model.train()
        offsets = torch.randint(len(training)-256, (64,), generator=generator)
        x = torch.stack([training[i:i+256] for i in offsets]).cuda()
        y = torch.stack([training[i+1:i+257] for i in offsets]).cuda()
        for group in optimizer.param_groups:
            group["lr"] = learning_rate(update)
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            logits = model(x)
            loss = F.cross_entropy(logits.float().reshape(-1, 256), y.reshape(-1))
        pc01.require(bool(torch.isfinite(loss)), "nonfinite train loss")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
        optimizer.step()
        sample_device()
        if (update+1) % 250 == 0:
            evaluate_checkpoint(update+1)
    selected = pc01.choose_checkpoint(curve, split="dev")
    model.load_state_dict(torch.load(checkpoint, map_location="cuda", weights_only=True))
    trained = weights_digest(model)
    pc01.require(trained == selected["checkpoint_sha256"] and trained != initial, "selected weights mismatch/unchanged")
    sample_device()
    new_json(work / "fit-finished.json", {"updates": 5000, "selected_update": selected["update"]})
    pc01.assert_causal(predict, fixture, cut=128)
    trained_bpb = pc01.evaluate_bytes(predict, evaluation)["bits_per_byte"]
    bf16_dev_bpb = pc01.evaluate_bytes(predict, dev)["bits_per_byte"]
    fp32_dev_bpb = pc01.evaluate_bytes(lambda x: predict(x, fp32=True), dev)["bits_per_byte"]
    pc01.precision_gate(fp32_dev_bpb, bf16_dev_bpb)

    def predict_bytes(prompts, teacher):
        # Byte conversion/H2D/logits/argmax/D2H are all inside the timed callback.
        x = np.stack([np.frombuffer(p, dtype=np.uint8).astype(np.int64) for p in prompts])
        model.eval()
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
            logits = model(torch.as_tensor(x, device="cuda"))
            chosen = logits.argmax(dim=-1) if teacher else logits[:, -1].argmax(dim=-1)
            return chosen.to(dtype=torch.uint8).cpu().numpy().tobytes()

    reference = {}
    for name, (batch, teacher) in pc01.SCENARIOS.items():
        x = np.frombuffer(dev[:batch*256], dtype=np.uint8).astype(np.int64).reshape(batch, 256)
        logits = predict(x)
        chosen = logits.argmax(axis=-1) if teacher else logits[:, -1].argmax(axis=-1)
        reference[name] = chosen.astype(np.uint8).tobytes()
    timing = pc01.measure_scenarios(predict_bytes, torch.cuda.synchronize, dev, expected_outputs=reference)
    sample_device()
    # Parent supplies actual supervisor resource measurements; no placeholder zero metrics.
    resources = None
    measurement = {"schema_version": 1, "kind": "pc01_local_calibration_replica", "phase": plan["phase"],
        "status": "complete", "experiment_id": plan["experiment_id"], "seed": seed,
        "contract_sha256": pc01.CONTRACT_SHA256, "data_sha256": pc01.DATA_SHA256,
        "evaluator_sha256": plan["evaluator_sha256"], "candidate_sha256": runtime["audit"]["sha256"],
        "recipe_sha256": plan["recipe_sha256"], "series_sha256": plan["series_sha256"],
        "initial_weights_sha256": initial, "frozen_weights_sha256": frozen, "trained_weights_sha256": trained,
        "updates": 5000, "target_count": len(evaluation)-1, "trained_bpb": trained_bpb, "frozen_bpb": frozen_bpb,
        "unigram_bpb": baseline_unigram, "bigram_bpb": baseline_bigram, "fp32_dev_bpb": fp32_dev_bpb,
        "bf16_dev_bpb": bf16_dev_bpb, "dev_curve": curve, "controls": {n: True for n in pc01.CONTROL_NAMES},
        "resources": resources, "timing": timing, "architecture_promoted": False,
        "evidence_scope": "local_single_corpus_diagnostic"}
    from .runner import environment_fingerprint
    driver = None
    executable = shutil.which("nvidia-smi")
    if executable:
        probe = subprocess.run([executable, "--query-gpu=driver_version,name,clocks.sm,clocks.mem,utilization.gpu,memory.used",
                                "--format=csv,noheader"], capture_output=True, text=True, timeout=5, check=False)
        if probe.returncode == 0:
            driver = probe.stdout.strip()
    new_json(work / "environment.json", {**environment_fingerprint(root), "torch": torch.__version__, "cuda": torch.version.cuda,
        "device": torch.cuda.get_device_name(), "load_seconds": load_seconds,
        "attention_events": attention_events, "gpu_driver_clocks_load_snapshot": driver,
        "tf32": False, "compile": False, "energy_measured": False,
        "timing_scope": "B1 next-byte latency and teacher-forced throughput; not autoregressive throughput"})
    # These are matmul estimates, not full measured algorithmic operation counts.
    def macs(batch, context=256):
        return batch*(6*(12*context*384**2+2*context**2*384)+context*384*256)
    new_json(work / "cost-boundary.json", {
        "uniform_reference_bpb": 8.0, "parameter_count": sum(p.numel() for p in model.parameters()),
        "matmul_forward_macs_estimate": {name: macs(batch) for name, (batch, _) in pc01.SCENARIOS.items()},
        "training_matmul_flops_estimate": 3*2*macs(64)*5000,
        "estimate_excludes": ["normalization", "GELU", "softmax", "optimizer", "data copies"],
        "complete_measured_boundary": "parent worker_seconds includes process startup, data verification, controls, fit, selection, evaluation, timing and serialization",
        "acquisition_and_service_cost": "separate immutable PC-01 acquisition and service receipts; not assumed zero",
        "amortized_repeated_workload_seconds": {str(r): r*sum(timing["B1-next"]["samples_ns"])/1e9 for r in (1, 10, 100)},
        "reuse_unit": "one complete 100-request batch=1 next-byte workload; add one-time worker preparation/fit/load separately",
        "economic_advantage_established": False, "energy_measured": False})
    new_json(work / "measurement.json", measurement)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        run(args.runtime.resolve(), project_root().resolve())
        return 0
    except BaseException:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
