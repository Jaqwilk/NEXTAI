"""Frozen public auxiliary arrays; no private research task or scored data."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "research/plans/PVM01-REPRO-PREPARATION-V1.json"
PLAN_SHA = "54bb174dc4cc6f01b5e4229f0da377c096d526a26f5925258d950f1748ac59ea"


def fixed_arrays():
    rng = np.random.default_rng(730119)
    def identities(count):
        rows = rng.standard_normal((count, 64)).astype(np.float32)
        return rows / np.linalg.norm(rows, axis=-1, keepdims=True)
    writes, validation = identities(128), identities(32)
    queries, validation_queries = np.roll(writes, 1, -1), np.roll(validation, 1, -1)
    sets = {}
    for size in (32, 128):
        support, question, labels = [], [], []
        for _ in range(8):
            keys = identities(size)
            known = rng.choice(size, 6, replace=False)
            query_keys = np.concatenate([keys[known], identities(2)])
            support.append(keys)
            question.append(np.roll(query_keys, 1, -1))
            labels.append(np.concatenate([known, [size, size]]))
        sets[size] = (np.stack(support), np.stack(question), np.stack(labels).astype(np.int64))
    digest = hashlib.sha256()
    for array in (writes, queries, validation, validation_queries, *(a for group in sets.values() for a in group)):
        digest.update(str((array.shape, array.dtype.str)).encode())
        digest.update(array.tobytes())
    return writes, queries, validation, validation_queries, sets, digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--repeat", type=int, required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert hashlib.sha256(PLAN.read_bytes()).hexdigest() == PLAN_SHA
    frozen = json.loads(PLAN.read_text())["cuda_fixture"]
    assert args.seed in frozen["model_seeds"] and args.repeat in (0, 1)
    assert args.arm in frozen["arms"] and args.profile in frozen["profiles"]
    assert not args.output.exists()
    started = time.perf_counter()
    import torch
    from torch.profiler import profile, ProfilerActivity
    from nextai_autoresearch.candidates.pvm01_core import Candidate as Dense, parameter_hash
    from nextai_autoresearch.candidates.pvm01_optimized_core import Candidate as Cached
    from nextai_autoresearch.candidates.pvm01_repro_core import Candidate as Repro
    from nextai_autoresearch.utils import atomic_write_json
    assert torch.cuda.is_available()
    torch.use_deterministic_algorithms(False)
    torch.cuda.reset_peak_memory_stats()
    arrays = fixed_arrays()
    writes, queries, validation, validation_queries, sets, fixture_hash = arrays
    cls = Repro if args.profile == "deterministic_math" else Dense if args.arm == "dense" else Cached
    model = cls(args.seed, args.arm, frozen["recipe"])
    initial_encoder, initial_decoder = parameter_hash(model.model), parameter_hash(model.decoder)
    settings_before = {"deterministic": torch.are_deterministic_algorithms_enabled(),
                       "warn_only": torch.is_deterministic_algorithms_warn_only_enabled(),
                       "math": torch.backends.cuda.math_sdp_enabled(),
                       "flash": torch.backends.cuda.flash_sdp_enabled(),
                       "efficient": torch.backends.cuda.mem_efficient_sdp_enabled(),
                       "cudnn": torch.backends.cuda.cudnn_sdp_enabled()}
    tick = time.perf_counter()
    with profile(activities=[ProfilerActivity.CPU]) as dispatch:
        fit_report = model.fit(writes, queries, validation, validation_queries, sets)
    profiled_fit_wall = time.perf_counter() - tick
    operators = {row.key: row.count for row in dispatch.key_averages() if "scaled_dot_product" in row.key}
    session = model.new_session(32)
    keys, initial_queries, _ = sets[32]
    for handle, key in enumerate(keys[0]):
        session.ingest((0, handle, key, handle % 16))
    def observe(question):
        handle, score, value = session.read(question)
        return {"handle": handle, "score": score, "value": value,
                "answer": value if score >= model.threshold else -1}
    observations = [observe(question) for question in initial_queries[0]]
    for handle in (0, 1):
        session.ingest((1, handle, validation[handle], 15 - handle))
    after = np.concatenate([initial_queries[0], validation_queries[:2], np.roll(keys[0, :2], 1, -1)])
    observations.extend(observe(question) for question in after)
    model.synchronize()
    report = {"seed": args.seed, "repeat": args.repeat, "arm": args.arm, "profile": args.profile,
              "plan_raw_sha256": PLAN_SHA, "fixture_sha256": fixture_hash,
              "initial_encoder_sha256": initial_encoder, "initial_decoder_sha256": initial_decoder,
              "final_encoder_sha256": parameter_hash(model.model), "final_decoder_sha256": parameter_hash(model.decoder),
              "fit_report": fit_report, "dispatch_operators": operators,
              "settings_before": settings_before, "deterministic_setting_after": torch.are_deterministic_algorithms_enabled(),
              "torch_version": torch.__version__, "cuda_runtime": torch.version.cuda,
              "device": torch.cuda.get_device_name(0), "precision": "float32", "threads": torch.get_num_threads(),
              "cuda_peak_allocated_bytes": torch.cuda.max_memory_allocated(),
              "cuda_peak_reserved_bytes": torch.cuda.max_memory_reserved(),
              "profiled_fit_wall_seconds": profiled_fit_wall, "child_work_wall_seconds": time.perf_counter() - started,
              "observations": observations, "research_data_scoring_or_claim": False}
    atomic_write_json(args.output, report)
    print(json.dumps({"output": str(args.output), "profile": args.profile, "arm": args.arm, "seed": args.seed,
                      "fit_wall": profiled_fit_wall, "dispatch": operators}))


if __name__ == "__main__":
    main()
