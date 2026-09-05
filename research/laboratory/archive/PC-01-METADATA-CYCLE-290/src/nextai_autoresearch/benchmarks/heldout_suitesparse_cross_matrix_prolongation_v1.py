from __future__ import annotations

import importlib
import math
import time
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import numpy as np
import pyamg
from pyamg.relaxation import smoothing
from scipy.io import mmread
from scipy.sparse.linalg import cg

from ..utils import load_json, project_root, sha256_file


BENCHMARK_VERSION = "heldout_suitesparse_cross_matrix_prolongation_v1"
DATASET_ID = "suitesparse_real_pde_v1"
ROOT = Path("research/data/suitesparse_real_pde_v1")
RTOL = 1e-7
MAXITER = 2000
HORIZONS = (1, 4, 16)
TARGET_SIZES = (9801, 10605, 81920)
CONTROL_NAMES = (
    "target_standard_sa_v1",
    "target_adaptive_sa_v1",
    "source_frozen_hierarchy_v1",
    "fixed_pr_numeric_refresh_v1",
    "unpreconditioned_cg_v1",
)
ROLE = {
    "shared_anonymous_prolongation_v1": "shared",
    "independent_anonymous_prolongation_v1": "independent",
    "cross_family_only_anonymous_prolongation_v1": "cross_family_only",
    "support_only_anonymous_prolongation_v1": "support_only",
}
BASE_IMPLEMENTATION = {
    name: "shared_anonymous_prolongation_v1" for name in ROLE
}
SOURCE_IDENTICAL_CONTRACT = (
    "anonymous_csr_numeric_operator_core_constants_fit_build_output_and_accounting_"
    "identical_except_preregistered_source_matrix_scope_v1"
)
TRACKED_HASHES = {
    "acquisition_manifest.json": "2049008d17bcf1f23168886c86b9066813658212756732770d9ca81fcca8a6df",
    "audit.json": "8f4e2c023f12fbf2a04e8f0fa111a5386e67c7bded0d997c634a2e5f44776ed2",
    "recycling_sequence_manifest.json": "c2f2527aae6063e29c4a1d085223f7348c7a24b83ee13617b3aeb19a8f635ef4",
    "recycling_audit.json": "82bac4874eac4cf94e89be5eeeae68b2011e20b658072482fdefd926bd824ea3",
    "recycling_sequence_receipt.json": "350c385847465ce7a7a0a3bdfa8b37e9383dc2f70d6b89c750e9e61631bbb3cc",
}


@dataclass(frozen=True)
class AnonymousSparseOperator:
    shape: tuple[int, int]
    indptr: np.ndarray
    indices: np.ndarray
    data: np.ndarray


def _root() -> Path:
    return project_root() / ROOT


def _documents() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    base = _root()
    return (
        load_json(base / "acquisition_manifest.json"),
        load_json(base / "audit.json"),
        load_json(base / "recycling_sequence_manifest.json"),
        load_json(base / "recycling_audit.json"),
    )


def _records() -> tuple[dict[str, dict[str, Any]], tuple[dict[str, Any], ...]]:
    acquisition, base_audit, sequences, sequence_audit = _documents()
    hashes = {record["name"]: record for record in base_audit["records"]}
    hashes.update({record["source"]: record for record in sequence_audit["records"]})
    hashes.update({record["target"]: record for record in sequence_audit["records"]})
    base_names = tuple(item["name"] for item in acquisition["matrices"])
    pairs = tuple(
        {
            "slot": item["sequence_slot"],
            "source": item["matrices"][0]["name"],
            "target": item["matrices"][1]["name"],
            "size": int(item["dimension"]),
        }
        for item in sequences["sequences"]
    )
    return {"hashes": hashes, "base_names": base_names}, pairs


def _matrix_hash(record: dict[str, Any], name: str) -> str:
    if record.get("name") == name:
        return str(record["matrix_sha256"])
    key = "source_matrix_sha256" if record.get("source") == name else "target_matrix_sha256"
    return str(record[key])


def _matrix_path(name: str) -> Path:
    return _root() / "extracted" / name / f"{name}.mtx"


def _load_matrix(name: str) -> Any:
    records, _ = _records()
    record = records["hashes"][name]
    path = _matrix_path(name)
    if not path.is_file() or sha256_file(path) != _matrix_hash(record, name):
        raise RuntimeError(f"SuiteSparse payload hash mismatch: {name}")
    matrix = mmread(path, spmatrix=True).tocsr().astype(np.float64)
    matrix.sum_duplicates()
    return matrix


def anonymous(matrix: Any) -> AnonymousSparseOperator:
    arrays = tuple(np.array(value, copy=True) for value in (matrix.indptr, matrix.indices, matrix.data))
    for value in arrays:
        value.flags.writeable = False
    return AnonymousSparseOperator(tuple(matrix.shape), *arrays)


def _training_names(role: str, pair: dict[str, Any]) -> tuple[str, ...]:
    records, pairs = _records()
    paired = str(pair["source"])
    sources = tuple(str(item["source"]) for item in pairs)
    base = tuple(str(name) for name in records["base_names"])
    if role in {"independent", "support_only"}:
        return (paired,)
    if role == "cross_family_only":
        return tuple(name for name in (*base, *sources) if name != paired)
    if role == "shared":
        return (*base, *sources)
    raise ValueError(f"unknown role: {role}")


def _build(kind: str, matrix: Any) -> Any:
    if kind == "adaptive":
        return pyamg.aggregation.adaptive_sa_solver(
            matrix, symmetry="symmetric", pdef=True, num_candidates=1,
            candidate_iters=5, max_levels=10, max_coarse=50,
        )[0]
    return pyamg.smoothed_aggregation_solver(matrix, symmetry="symmetric")


def _refresh(solver: Any, target: Any) -> None:
    solver.levels[0].A = target
    smoothing.rebuild_smoother(solver.levels[0])
    for index in range(len(solver.levels) - 1):
        fine, coarse = solver.levels[index], solver.levels[index + 1]
        coarse.A = (fine.R @ fine.A @ fine.P).tocsr()
        if index + 1 < len(solver.levels) - 1:
            smoothing.rebuild_smoother(coarse)


def _solver_bytes(solver: Any | None) -> int:
    if solver is None:
        return 0
    total = 0
    for level in solver.levels:
        for key in ("A", "P", "R"):
            value = getattr(level, key, None)
            if value is not None:
                total += int(value.data.nbytes + value.indices.nbytes + value.indptr.nbytes)
    return total


def _solver_nnz(solver: Any | None) -> int:
    if solver is None:
        return 0
    return sum(int(getattr(level, "A").nnz) for level in solver.levels)


def _control(name: str, source: Any, target: Any) -> tuple[Any | None, float, float, float]:
    started = time.perf_counter()
    update_ops = 0.0
    if name == "unpreconditioned_cg_v1":
        return None, 0.0, 0.0, 0.0
    if name == "target_standard_sa_v1":
        solver = _build("standard", target)
    elif name == "target_adaptive_sa_v1":
        solver = _build("adaptive", target)
    elif name == "source_frozen_hierarchy_v1":
        solver = _build("standard", source)
        solver.change_solve_matrix(target)
        update_ops = float(target.nnz)
    elif name == "fixed_pr_numeric_refresh_v1":
        solver = _build("standard", source)
        _refresh(solver, target)
        update_ops = float(_solver_nnz(solver))
    else:
        raise ValueError(f"unknown control: {name}")
    seconds = time.perf_counter() - started
    setup_ops = float(_solver_nnz(solver))
    return solver, setup_ops, update_ops, seconds


def _learned(name: str, training: tuple[Any, ...], target: Any, seed: int) -> tuple[Any, float, float, float, int]:
    module = importlib.import_module(
        f"nextai_autoresearch.candidates.{BASE_IMPLEMENTATION[name]}"
    )
    candidate = module.Candidate(seed=seed)
    started = time.perf_counter()
    candidate.fit(tuple(anonymous(item) for item in training))
    solver = candidate.build(anonymous(target))
    seconds = time.perf_counter() - started
    return (
        solver,
        float(getattr(candidate, "fit_ops", 0.0)),
        float(getattr(candidate, "build_ops", 0.0)),
        seconds,
        int(getattr(candidate, "state_bytes", lambda: _solver_bytes(solver))()),
    )


def _solve(solver: Any | None, matrix: Any, seed: int) -> tuple[int, float, float]:
    truth = np.random.default_rng(seed).standard_normal(matrix.shape[0])
    rhs = np.asarray(matrix @ truth).reshape(-1)
    count = 0
    def callback(_: Any) -> None:
        nonlocal count
        count += 1
    started = time.perf_counter()
    solution, _ = cg(
        matrix, rhs, M=None if solver is None else solver.aspreconditioner(),
        rtol=RTOL, atol=0.0, maxiter=MAXITER, callback=callback,
    )
    seconds = time.perf_counter() - started
    residual = float(np.linalg.norm(matrix @ solution - rhs) / max(np.linalg.norm(rhs), 1e-30))
    return count, residual, seconds


def _run(name: str, pair: dict[str, Any], seed: int) -> dict[str, Any]:
    source, target = _load_matrix(pair["source"]), _load_matrix(pair["target"])
    training_names = _training_names(ROLE[name], pair) if name in ROLE else (pair["source"],)
    training = tuple(_load_matrix(item) for item in training_names)
    acquisition = float(target.nnz + sum(item.nnz for item in training))
    if name in CONTROL_NAMES:
        solver, setup_ops, update_ops, fit_seconds = _control(name, source, target)
        fit_ops, state = 0.0, _solver_bytes(solver)
    else:
        solver, fit_ops, setup_ops, fit_seconds, state = _learned(name, training, target, seed)
        update_ops = setup_ops
    iterations, residual, solve_seconds = _solve(solver, target, seed)
    hierarchy_nnz = _solver_nnz(solver)
    query_ops = float(iterations * (2 * target.nnz + 2 * hierarchy_nnz))
    bytes_per_iteration = float(target.data.nbytes + target.indices.nbytes + target.indptr.nbytes + state)
    base = acquisition + fit_ops + setup_ops + update_ops
    quality = float(math.isfinite(residual) and residual <= RTOL)
    return {
        "status": "complete", "world_family": f"slot_{pair['size']}",
        "knowledge_size": int(pair["size"]), "reasoning_depth": 1, "seed": seed,
        "query_count": 1, "accuracy": quality, "warm_accuracy": quality,
        "continual_retention": 1.0, "relative_residual": residual,
        "solver_iterations": float(iterations), "fit_seconds": fit_seconds,
        "fit_ops": fit_ops, "meta_fit_ops": fit_ops,
        "data_acquisition_ops": acquisition, "preprocessing_ops": setup_ops,
        "adaptation_ops": update_ops, "mean_query_ops": query_ops,
        "mean_warm_query_ops": query_ops, "p50_latency_us": solve_seconds * 1e6,
        "p95_latency_us": solve_seconds * 1e6, "state_bytes": float(state),
        "peak_state_bytes": float(state), "mean_input_ops": float(target.nnz),
        "mean_bytes_touched": bytes_per_iteration * iterations,
        "update_ops": update_ops, "update_latency_us": 0.0,
        "workload_ops": base + query_ops, "workload_ops_r1": base + query_ops,
        "workload_ops_r4": base + 4 * query_ops,
        "workload_ops_r16": base + 16 * query_ops,
    }


def verify_static_contract(root: Path | None = None) -> dict[str, Any]:
    base = (root or project_root()) / ROOT
    for relative, expected in TRACKED_HASHES.items():
        if sha256_file(base / relative) != expected:
            raise RuntimeError(f"frozen SuiteSparse contract mismatch: {relative}")
    records, pairs = _records()
    train = set(records["base_names"]) | {item["source"] for item in pairs}
    test = {item["target"] for item in pairs}
    if len(train) != 12 or len(test) != 3 or train & test:
        raise RuntimeError("SuiteSparse train/test split is not disjoint 12/3")
    for name in train | test:
        _load_matrix(str(name))
    return {"train": len(train), "test": len(test), "targets": sorted(item["size"] for item in pairs)}


def contract_audit() -> dict[str, Any]:
    static = verify_static_contract()
    _, _, _, recycling = _documents()
    records = {item["sequence_slot"]: item for item in recycling["records"]}
    generic = records["generic_2d3d"]
    generic_reuse = [
        generic["controls"][kind][mode]["solve"]["converged"]
        for kind in ("standard_sa", "adaptive_sa")
        for mode in ("frozen_hierarchy_reuse", "fixed_prolongation_numeric_refresh")
    ]
    checks = {
        "static_split_and_hashes": static == {"train": 12, "test": 3, "targets": list(TARGET_SIZES)},
        "anonymous_boundary": tuple(item.name for item in fields(AnonymousSparseOperator)) == ("shape", "indptr", "indices", "data"),
        "source_identical_roles": len(set(BASE_IMPLEMENTATION.values())) == 1 and len(ROLE) == 4,
        "controls_frozen": len(CONTROL_NAMES) == 5,
        "matched_residual_contract": recycling["cg_contract"] == {"rtol": RTOL, "atol": 0.0, "maxiter": MAXITER},
        "all_rebuilds_complete": bool(recycling["all_target_rebuilds_complete"]),
        "generic_reuse_is_complete_low_quality": not any(generic_reuse),
    }
    return {
        "benchmark": BENCHMARK_VERSION, "pass": all(checks.values()),
        "checks": checks, "controls": list(CONTROL_NAMES), "roles": dict(ROLE),
        "runner_random_scoring_seed_realized": False, "scoring_performed": False,
    }


def development_smoke() -> dict[str, Any]:
    _, pairs = _records()
    pair = next(item for item in pairs if item["size"] == 10605)
    row = _run("target_standard_sa_v1", pair, 1103)
    return {"pass": row["accuracy"] == 1.0, "iterations": row["solver_iterations"], "relative_residual": row["relative_residual"]}


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    if not contract_audit()["pass"]:
        raise RuntimeError("SuiteSparse evaluator contract failed")
    if candidate_name not in {*CONTROL_NAMES, *ROLE}:
        raise ValueError(f"candidate has no frozen SuiteSparse role: {candidate_name}")
    protocol = plan["suitesparse_transfer_protocol"]
    if protocol["source_identical_contract"] != SOURCE_IDENTICAL_CONTRACT:
        raise ValueError("source-identical contract mismatch")
    _, pairs = _records()
    by_size = {int(item["size"]): item for item in pairs}
    matrix = plan["matrix"]
    if tuple(sorted(int(value) for value in matrix["knowledge_sizes"])) != TARGET_SIZES:
        raise ValueError("target size matrix differs from frozen cohort")
    return [
        _run(candidate_name, by_size[int(size)], int(seed))
        for seed in matrix["seeds"] for size in matrix["knowledge_sizes"]
    ]
