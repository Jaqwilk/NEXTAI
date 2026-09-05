"""PC-01 measurement primitives. No training, model, runner bypass or promotion.

These routines are tested on synthetic fixtures. A complete supervised execution
adapter is still required before this preparation module can support an EXP.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import statistics
import time
from typing import Callable, Iterator

import numpy as np
from jsonschema.exceptions import ValidationError

from .utils import load_json, project_root, sha256_file


CONTRACT_PATH = "research/plans/PC-01-CONTRACT-V1.json"
CONTRACT_SHA256 = "f9e3d889485ff5e63c9f74caae3118f2f44c3872b91400931e72c8e1ce67a280"
ACQUISITION_SHA256 = "e2ef831342838921588e6699ea501cdc911ffe869323714907fc13b48fb9931f"
DATA_SHA256 = "86c4e6aa9db7c042ec79f339dcb96d42b0075e16b8fc2e86bf0ca57e2dc565ed"
COHORT = "pc01_byte_lm_learning_measurement_v1"
TELEMETRY_COHORT = "pc01_byte_lm_learning_measurement_v2"
COHORTS = (COHORT, TELEMETRY_COHORT)
GIB = 1024**3
CONTROL_NAMES = (
    "float64_known_probability_loss", "deliberately_wrong_target_fixture",
    "learning_off_parameter_hash", "causal_suffix_perturbation",
    "split_overlap_and_target_alignment", "holdout_access_denial_during_fit",
    "batch_partition_invariance", "checkpoint_selection_uses_dev_only",
    "timing_synchronization_and_real_output", "budget_and_seed_series_enforcement",
)
SCENARIOS = {"B1-next": (1, False), "B1-teacher": (1, True),
             "B8-teacher": (8, True), "B32-teacher": (32, True)}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def finite_nonnegative(value: object, name: str) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{name}: not numeric")
    number = float(value)
    require(math.isfinite(number) and number >= 0, f"{name}: nonfinite or negative")
    return number


def contract(root: Path | None = None) -> dict:
    base = root or project_root()
    require(sha256_file(base / CONTRACT_PATH) == CONTRACT_SHA256, "PC-01 contract hash mismatch")
    return load_json(base / CONTRACT_PATH)


def verify_corpus(root: Path | None = None) -> tuple[bytes, dict]:
    base = (root or project_root()).resolve()
    design = contract(base)
    relative = design["data_manifest"]
    require(sha256_file(base / relative) == ACQUISITION_SHA256, "acquisition manifest changed")
    manifest = load_json(base / relative)
    path = (base / manifest["path"]).resolve()
    require(path.is_relative_to(base), "corpus path escapes repository")
    payload = path.read_bytes()
    require(len(payload) == manifest["bytes"], "corpus size mismatch")
    require(hashlib.sha256(payload).hexdigest() == manifest["sha256"], "corpus hash mismatch")
    verify_splits(payload, manifest["splits"])
    return payload, manifest


def verify_splits(payload: bytes, splits: dict) -> None:
    require(set(splits) == {"train", "dev", "final"}, "unexpected splits")
    end = 0
    for name in ("train", "dev", "final"):
        part = splits[name]
        a, b = part["start_inclusive"], part["end_exclusive"]
        require(type(a) is int and type(b) is int and a == end and a < b <= len(payload), "split overlap/gap/range")
        require(b-a == part["bytes"], "split byte count")
        require(hashlib.sha256(payload[a:b]).hexdigest() == part["sha256"], "split hash")
        end = b
    require(end == len(payload), "unassigned corpus bytes")


@dataclass(frozen=True)
class DevelopmentData:
    """The development interface deliberately contains no final buffer or path.

    Not an OS sandbox; the caller loading corpus bytes is a trusted evaluator.
    """
    train: bytes
    dev: bytes

    def get(self, split: str, *, purpose: str) -> bytes:
        require((purpose, split) in {("fit", "train"), ("evaluate", "dev")}, "data access denied")
        return self.train if split == "train" else self.dev


def development_data(root: Path | None = None) -> DevelopmentData:
    payload, manifest = verify_corpus(root)
    parts = manifest["splits"]
    return DevelopmentData(*(payload[parts[n]["start_inclusive"]:parts[n]["end_exclusive"]]
                             for n in ("train", "dev")))


def byte_windows(data: bytes, context: int = 256) -> Iterator[tuple[bytes, bytes]]:
    require(type(context) is int and context > 0 and len(data) >= 2, "invalid window input")
    for start in range(0, len(data)-1, context):
        count = min(context, len(data)-1-start)
        yield data[start:start+count], data[start+1:start+1+count]


def loss_sum(logits: np.ndarray, targets: np.ndarray, mask: np.ndarray | None = None) -> tuple[float, int]:
    """Stable float64 NLL sum; pad targets never contribute to the denominator."""
    logits, targets = np.asarray(logits), np.asarray(targets)
    require(logits.ndim >= 2 and logits.shape[-1] == 256 and logits.shape[:-1] == targets.shape, "logit/target shape")
    require(np.issubdtype(targets.dtype, np.integer), "targets must be integer bytes")
    if mask is None:
        mask = np.ones(targets.shape, dtype=bool)
    mask = np.asarray(mask)
    require(mask.shape == targets.shape and mask.dtype == np.bool_, "invalid mask")
    selected = targets[mask]
    require(selected.size > 0 and np.all((selected >= 0) & (selected < 256)), "empty/invalid targets")
    rows = np.asarray(logits[mask], dtype=np.float64)
    require(bool(np.isfinite(rows).all()), "nonfinite logits")
    # Subtract the maximum BEFORE summing; do not lose small differences to a huge offset.
    shifted = rows - rows.max(axis=-1, keepdims=True)
    nll = np.log(np.exp(shifted).sum(axis=-1)) - shifted[np.arange(selected.size), selected]
    require(bool(np.isfinite(nll).all()), "nonfinite loss")
    return math.fsum(nll.tolist()), int(selected.size)


def evaluate_bytes(predict_logits: Callable, data: bytes, *, batch_size: int = 64) -> dict:
    """Evaluator owns targets; the predictor receives only causal input bytes."""
    require(type(batch_size) is int and batch_size > 0, "invalid batch size")
    windows = list(byte_windows(data))
    sums, count = [], 0
    for start in range(0, len(windows), batch_size):
        batch = windows[start:start+batch_size]
        x = np.zeros((len(batch), 256), dtype=np.int64)
        y = np.full_like(x, -1)
        mask = np.zeros(x.shape, dtype=bool)
        for i, (inputs, targets) in enumerate(batch):
            n = len(inputs)
            x[i, :n] = np.frombuffer(inputs, dtype=np.uint8)
            y[i, :n] = np.frombuffer(targets, dtype=np.uint8)
            mask[i, :n] = True
        nll, n = loss_sum(predict_logits(x), y, mask)
        sums.append(nll)
        count += n
    require(count == len(data)-1, "target accounting mismatch")
    return {"bits_per_byte": math.fsum(sums)/count/math.log(2), "target_count": count}


def choose_checkpoint(curve: list[dict], *, split: str) -> dict:
    require(split == "dev", "checkpoint selection requires dev, never final")
    require(len(curve) == 21, "incomplete learning curve")
    require([r["update"] for r in curve] == list(range(0, 5001, 250)), "updates incomplete/repeated/out of order")
    for row in curve:
        finite_nonnegative(row["bits_per_byte"], "checkpoint loss")
        digest = row["checkpoint_sha256"]
        require(isinstance(digest, str) and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest), "checkpoint digest")
    return min(curve[1:], key=lambda row: (row["bits_per_byte"], row["update"]))


def assert_causal(predict_logits: Callable, inputs: np.ndarray, *, cut: int) -> None:
    require(inputs.ndim == 2 and 0 < cut < inputs.shape[1], "causal fixture shape/cut")
    altered = inputs.copy()
    altered[:, cut:] = (altered[:, cut:] + 127) % 256
    before, after = np.asarray(predict_logits(inputs)), np.asarray(predict_logits(altered))
    require(before.shape == after.shape == (*inputs.shape, 256), "causal logits shape")
    require(bool(np.isfinite(before).all() and np.isfinite(after).all()), "nonfinite causal logits")
    require(bool(np.allclose(before[:, :cut], after[:, :cut], atol=1e-5, rtol=1e-5)), "future information leaked")


def assert_learning_off(before: str, steps: list[str]) -> None:
    require(len(steps) == 100 and all(digest == before for digest in steps), "learning-off weights changed/missing steps")


def precision_gate(fp32_bpb: float, bf16_bpb: float) -> None:
    a = finite_nonnegative(fp32_bpb, "fp32_bpb")
    b = finite_nonnegative(bf16_bpb, "bf16_bpb")
    require(abs(a-b) <= 0.02, "precision-inconclusive")


def check_resources(usage: dict, *, previous_fit_seconds: float = 0) -> None:
    limits = {"fit_seconds": 1200, "worker_seconds": 1800, "rss_bytes": 10*GIB,
              "cuda_allocated_bytes": 10*GIB, "cuda_reserved_bytes": 10*GIB,
              "persisted_bytes": 2*GIB}
    for key, maximum in limits.items():
        require(finite_nonnegative(usage[key], key) <= maximum, f"budget exceeded: {key}")
    require(usage["fit_seconds"] <= usage["worker_seconds"], "fit outside worker boundary")
    require(usage["cuda_allocated_bytes"] <= usage["cuda_reserved_bytes"], "CUDA allocation accounting")
    require(finite_nonnegative(usage["disk_free_bytes"], "disk_free_bytes") >= 10*GIB, "disk reserve")
    require(finite_nonnegative(previous_fit_seconds, "previous fit") + usage["fit_seconds"] <= 7200, "aggregate fit budget")


class BudgetGuard:
    """Cooperative per-update guard; NOT a replacement for the parent watchdog."""
    def __init__(self, sample_resources: Callable, *, clock: Callable = time.monotonic,
                 previous_fit_seconds: float = 0):
        self.sample_resources, self.clock = sample_resources, clock
        self.started = clock()
        self.fit_started: float | None = None
        self.previous_fit_seconds = previous_fit_seconds

    def begin_fit(self) -> None:
        require(self.fit_started is None, "fit may only start once")
        self.fit_started = self.clock()

    def check(self) -> dict:
        now = self.clock()
        usage = dict(self.sample_resources())
        usage["worker_seconds"] = now-self.started
        usage["fit_seconds"] = 0 if self.fit_started is None else now-self.fit_started
        check_resources(usage, previous_fit_seconds=self.previous_fit_seconds)
        return usage


def percentile(values: list[int], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered)-1)*fraction
    left, right = math.floor(position), math.ceil(position)
    return ordered[left] + (ordered[right]-ordered[left])*(position-left)


def measure_scenarios(predict_bytes: Callable, synchronize: Callable, dev: bytes,
                      *, expected_outputs: dict[str, bytes],
                      clock_ns: Callable = time.perf_counter_ns) -> dict:
    """Time bytes->CPU bytes, including preprocessing and transfers in callback.

    The real adapter must supply CUDA synchronize and keep the model resident.
    Injected clocks/callbacks are for unit tests, never real-system evidence.
    """
    require(len(dev) >= 32*256, "insufficient dev timing context")
    require(set(expected_outputs) == set(SCENARIOS), "independent reference outputs required")
    samples = {name: [] for name in SCENARIOS}
    warmup = {name: [] for name in SCENARIOS}
    inputs = {name: tuple(dev[i*256:(i+1)*256] for i in range(batch))
              for name, (batch, _) in SCENARIOS.items()}

    def one(name: str) -> int:
        batch, teacher = SCENARIOS[name]
        synchronize()
        start = clock_ns()
        output = predict_bytes(inputs[name], teacher)
        synchronize()
        elapsed = clock_ns()-start
        require(type(output) is bytes and len(output) == batch*(256 if teacher else 1), "missing/incorrect CPU output")
        require(output == expected_outputs[name], "timed output differs from reference")
        require(type(elapsed) is int and elapsed > 0, "invalid synchronized timing")
        return elapsed

    order = list(SCENARIOS)
    for name in order:
        warmup[name] = [one(name) for _ in range(20)]
    for block in (order, list(reversed(order))):
        for name in block:
            samples[name].extend(one(name) for _ in range(50))
    return {name: {
        "samples_ns": samples[name], "warmup_ns": warmup[name],
        "input_bytes_per_repeat": SCENARIOS[name][0]*256,
        "output_bytes_per_repeat": SCENARIOS[name][0]*(256 if SCENARIOS[name][1] else 1),
        "input_sha256": hashlib.sha256(b"".join(inputs[name])).hexdigest(),
        "p50_ns": percentile(samples[name], 0.5), "p95_ns": percentile(samples[name], 0.95),
        "output_bytes_per_second": 100*SCENARIOS[name][0]*(256 if SCENARIOS[name][1] else 1)*1e9/sum(samples[name]),
    } for name in order}


def validate_timing(timing: dict) -> None:
    require(set(timing) == set(SCENARIOS), "timing scenarios missing/extra")
    for name, (batch, teacher) in SCENARIOS.items():
        row = timing[name]
        for key, expected in (("samples_ns", 100), ("warmup_ns", 20)):
            require(len(row[key]) == expected and all(type(n) is int and n > 0 for n in row[key]), "timing repeats invalid")
        require(row["input_bytes_per_repeat"] == batch*256, "timing input count")
        require(row["output_bytes_per_repeat"] == batch*(256 if teacher else 1), "timing output count")
        for key, q in (("p50_ns", 0.5), ("p95_ns", 0.95)):
            require(row[key] == percentile(row["samples_ns"], q), "timing percentile mismatch")
        expected_rate = 100*row["output_bytes_per_repeat"]*1e9/sum(row["samples_ns"])
        require(math.isclose(row["output_bytes_per_second"], expected_rate, rel_tol=1e-12), "throughput denominator mismatch")


def series_decision(records: list[dict], *, root: Path | None = None) -> dict:
    """Pure claim gate. The runner must establish authenticity and completeness.

    Supplying self-authored records is not scientific evidence. No ledger writes.
    """
    from .schemas import validate_document
    try:
        require(len(records) == 3, "three complete replicas required; cannot omit failed runs")
        identities = ("contract_sha256", "data_sha256", "evaluator_sha256", "candidate_sha256", "recipe_sha256", "series_sha256")
        seeds, experiments, deltas, losses, contextual = set(), set(), [], [], []
        for record in records:
            validate_document("pc01_replica", record, root)
            require(record["status"] == "complete", "failed replica is inconclusive")
            require(record["contract_sha256"] == CONTRACT_SHA256, "wrong design contract")
            require(record["data_sha256"] == DATA_SHA256, "wrong corpus identity")
            require(all(record[k] == records[0][k] for k in identities), "recipe/data/evaluator changed across final series")
            require(record["seed"] not in seeds and record["experiment_id"] not in experiments, "duplicate seed or experiment")
            seeds.add(record["seed"])
            experiments.add(record["experiment_id"])
            require(record["updates"] == 5000, "incomplete training is budget-inconclusive")
            require(set(record["controls"]) == set(CONTROL_NAMES) and all(v is True for v in record["controls"].values()), "measurement control failed/missing")
            require(record["initial_weights_sha256"] == record["frozen_weights_sha256"], "frozen weights changed")
            require(record["trained_weights_sha256"] != record["initial_weights_sha256"], "trained weights unchanged")
            chosen = choose_checkpoint(record["dev_curve"], split="dev")
            require(chosen["checkpoint_sha256"] == record["trained_weights_sha256"], "wrong selected checkpoint")
            check_resources(record["resources"])
            validate_timing(record["timing"])
            precision_gate(record["fp32_dev_bpb"], record["bf16_dev_bpb"])
            trained = finite_nonnegative(record["trained_bpb"], "trained loss")
            frozen = finite_nonnegative(record["frozen_bpb"], "frozen loss")
            unigram = finite_nonnegative(record["unigram_bpb"], "unigram loss")
            finite_nonnegative(record["bigram_bpb"], "bigram loss")
            losses.append(trained)
            require(math.isfinite(frozen-trained) and math.isfinite(unigram-trained), "nonfinite contrast")
            deltas.append(frozen-trained)
            contextual.append(unigram-trained)
        mean = statistics.mean(deltas)
        sd = statistics.stdev(deltas)
        lower = mean - 4.3026527299*sd/math.sqrt(3)
        passed = all(x <= 3.5 for x in losses) and min(deltas) >= 1.0 and lower > 0
        return {"decision": "positive_control_pass" if passed else "valid_negative",
                "paired_deltas": deltas, "mean_delta": mean, "sample_sd": sd,
                "delta_range": [min(deltas), max(deltas)], "lower_95pct_t": lower,
                "contextual_secondary_pass": min(contextual) >= 0.1,
                "runner_authenticity_checked": False, "scientific_result_created": False,
                "independent_corpus_count": 1, "architecture_promoted": False,
                "economic_advantage_established": False, "transfer_established": False}
    except (ValueError, KeyError, TypeError, ValidationError, OverflowError) as exc:
        return {"decision": "inconclusive", "reason": str(exc), "architecture_promoted": False,
                "runner_authenticity_checked": False, "scientific_result_created": False}
