from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pyamg
from scipy.io import mmread
from scipy.sparse.linalg import cg

CG_RTOL = 1e-7
CG_MAXITER = 2000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def solve_diagnostic(solver: object, matrix: object, rhs: np.ndarray) -> dict[str, object]:
    residuals: list[float] = []
    started = time.perf_counter()
    solution = solver.solve(
        rhs,
        x0=np.zeros_like(rhs),
        tol=1e-8,
        maxiter=100,
        residuals=residuals,
    )
    ratio = float(residuals[-1] / residuals[0]) if residuals and residuals[0] else 0.0
    return {
        "finite": bool(np.isfinite(solution).all()),
        "iterations": max(0, len(residuals) - 1),
        "relative_residual": ratio,
        "solve_seconds_diagnostic": time.perf_counter() - started,
    }


def cg_diagnostic(solver: object, matrix: object, rhs: np.ndarray) -> dict[str, object]:
    iterations = 0

    def count_iteration(_: np.ndarray) -> None:
        nonlocal iterations
        iterations += 1

    started = time.perf_counter()
    solution, info = cg(
        matrix,
        rhs,
        x0=np.zeros_like(rhs),
        M=solver.aspreconditioner(),
        rtol=CG_RTOL,
        atol=0.0,
        maxiter=CG_MAXITER,
        callback=count_iteration,
    )
    relative_residual = float(np.linalg.norm(rhs - matrix @ solution) / np.linalg.norm(rhs))
    return {
        "converged": info == 0,
        "finite": bool(np.isfinite(solution).all()),
        "iterations": iterations,
        "relative_residual": relative_residual,
        "solve_seconds_diagnostic": time.perf_counter() - started,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = root / "acquisition_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records: list[dict[str, object]] = []

    for item in manifest["matrices"]:
        group = item["group"]
        name = item["name"]
        archive = root / "archive" / f"{group}__{name}.tar.gz"
        matrix_path = root / "extracted" / name / f"{name}.mtx"
        matrix = mmread(matrix_path, spmatrix=True).tocsr().astype(np.float64)
        matrix.sum_duplicates()
        difference = matrix - matrix.T
        symmetry_max_abs = (
            float(np.max(np.abs(difference.data))) if difference.nnz else 0.0
        )
        diagonal = matrix.diagonal()
        rhs_primary = np.asarray(matrix @ np.ones(matrix.shape[0])).reshape(-1)
        rhs_reuse = np.asarray(
            matrix @ np.linspace(-1.0, 1.0, matrix.shape[0], dtype=np.float64)
        ).reshape(-1)

        started = time.perf_counter()
        standard = pyamg.smoothed_aggregation_solver(matrix, symmetry="symmetric")
        standard_build_seconds = time.perf_counter() - started
        standard_primary = solve_diagnostic(standard, matrix, rhs_primary)
        standard_cg_primary = cg_diagnostic(standard, matrix, rhs_primary)

        started = time.perf_counter()
        adaptive, adaptive_work = pyamg.aggregation.adaptive_sa_solver(
            matrix,
            symmetry="symmetric",
            pdef=True,
            num_candidates=1,
            candidate_iters=5,
            max_levels=10,
            max_coarse=50,
        )
        adaptive_build_seconds = time.perf_counter() - started
        adaptive_primary = solve_diagnostic(adaptive, matrix, rhs_primary)
        adaptive_reused_rhs = solve_diagnostic(adaptive, matrix, rhs_reuse)
        adaptive_cg_primary = cg_diagnostic(adaptive, matrix, rhs_primary)
        adaptive_cg_reused_rhs = cg_diagnostic(adaptive, matrix, rhs_reuse)

        records.append(
            {
                "group": group,
                "name": name,
                "family_slot": item["family_slot"],
                "scale_slot": item["scale_slot"],
                "archive_bytes": archive.stat().st_size,
                "archive_sha256": sha256(archive),
                "matrix_bytes": matrix_path.stat().st_size,
                "matrix_sha256": sha256(matrix_path),
                "shape": list(matrix.shape),
                "stored_entries": int(matrix.nnz),
                "numerical_nnz": int(np.count_nonzero(matrix.data)),
                "explicit_zero_entries": int(np.count_nonzero(matrix.data == 0)),
                "finite_values": bool(np.isfinite(matrix.data).all()),
                "symmetry_max_abs": symmetry_max_abs,
                "diagonal_min": float(diagonal.min()),
                "diagonal_positive_fraction": float(np.mean(diagonal > 0)),
                "standard_sa": {
                    "levels": len(standard.levels),
                    "build_seconds_diagnostic": standard_build_seconds,
                    "primary_rhs": standard_primary,
                    "preconditioned_cg_primary_rhs": standard_cg_primary,
                },
                "adaptive_sa": {
                    "levels": len(adaptive.levels),
                    "reported_setup_work": float(adaptive_work),
                    "build_seconds_diagnostic": adaptive_build_seconds,
                    "primary_rhs": adaptive_primary,
                    "reused_hierarchy_second_rhs": adaptive_reused_rhs,
                    "preconditioned_cg_primary_rhs": adaptive_cg_primary,
                    "preconditioned_cg_reused_hierarchy_second_rhs": adaptive_cg_reused_rhs,
                },
            }
        )

    algebraic_pass = all(
        record["shape"] == [item["rows"], item["cols"]]
        and record["numerical_nnz"] == item["nnz"]
        and record["finite_values"]
        and record["symmetry_max_abs"] <= 1e-12
        and record["diagonal_positive_fraction"] == 1.0
        for record, item in zip(records, manifest["matrices"], strict=True)
    )
    adaptive_runnable = all(
        record["adaptive_sa"]["preconditioned_cg_primary_rhs"]["converged"]
        and record["adaptive_sa"]["preconditioned_cg_primary_rhs"]["finite"]
        and record["adaptive_sa"]["preconditioned_cg_primary_rhs"]["relative_residual"] <= 1e-7
        and record["adaptive_sa"]["preconditioned_cg_reused_hierarchy_second_rhs"]["converged"]
        and record["adaptive_sa"]["preconditioned_cg_reused_hierarchy_second_rhs"]["finite"]
        and record["adaptive_sa"]["preconditioned_cg_reused_hierarchy_second_rhs"]["relative_residual"] <= 1e-7
        for record in records
    )
    payload = {
        "schema_version": 1,
        "dataset_id": manifest["dataset_id"],
        "manifest_sha256": sha256(manifest_path),
        "pyamg_version": pyamg.__version__,
        "numpy_version": np.__version__,
        "preconditioned_cg_contract": {
            "rtol": CG_RTOL,
            "atol": 0.0,
            "maxiter": CG_MAXITER,
        },
        "matrix_count": len(records),
        "algebraic_metadata_pass": algebraic_pass,
        "adaptive_sa_runnable_all_matrices": adaptive_runnable,
        "records": records,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not algebraic_pass or not adaptive_runnable:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
