from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pyamg
from audit_suitesparse_real_pde import CG_MAXITER, CG_RTOL, cg_diagnostic, sha256
from pyamg.relaxation import smoothing
from scipy.io import mmread


def build_solver(matrix: object, kind: str) -> tuple[object, float]:
    started = time.perf_counter()
    if kind == "standard_sa":
        solver = pyamg.smoothed_aggregation_solver(matrix, symmetry="symmetric")
    else:
        solver = pyamg.aggregation.adaptive_sa_solver(
            matrix,
            symmetry="symmetric",
            pdef=True,
            num_candidates=1,
            candidate_iters=5,
            max_levels=10,
            max_coarse=50,
        )[0]
    return solver, time.perf_counter() - started


def refresh_numeric_hierarchy(solver: object, target: object) -> float:
    started = time.perf_counter()
    solver.levels[0].A = target
    smoothing.rebuild_smoother(solver.levels[0])
    for index in range(len(solver.levels) - 1):
        fine = solver.levels[index]
        coarse = solver.levels[index + 1]
        coarse.A = (fine.R @ fine.A @ fine.P).tocsr()
        if index + 1 < len(solver.levels) - 1:
            smoothing.rebuild_smoother(coarse)
    return time.perf_counter() - started


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = root / "recycling_sequence_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records: list[dict[str, object]] = []

    for sequence in manifest["sequences"]:
        source_item, target_item = sequence["matrices"]
        source_name = source_item["name"]
        target_name = target_item["name"]
        source_path = root / "extracted" / source_name / f"{source_name}.mtx"
        target_path = root / "extracted" / target_name / f"{target_name}.mtx"
        source = mmread(source_path, spmatrix=True).tocsr().astype(np.float64)
        target = mmread(target_path, spmatrix=True).tocsr().astype(np.float64)
        source.sum_duplicates()
        target.sum_duplicates()
        same_pattern = np.array_equal(source.indptr, target.indptr) and np.array_equal(
            source.indices, target.indices
        )
        value_relative_change = float(
            np.linalg.norm(source.data - target.data) / max(np.linalg.norm(source.data), 1e-30)
        )
        rhs = np.asarray(
            target @ np.linspace(-1.0, 1.0, target.shape[0], dtype=np.float64)
        ).reshape(-1)
        controls: dict[str, object] = {}

        for kind in ("standard_sa", "adaptive_sa"):
            rebuilt, rebuilt_setup = build_solver(target, kind)
            rebuilt_solve = cg_diagnostic(rebuilt, target, rhs)

            frozen, source_setup = build_solver(source, kind)
            started = time.perf_counter()
            frozen.change_solve_matrix(target)
            frozen_update = time.perf_counter() - started
            frozen_solve = cg_diagnostic(frozen, target, rhs)

            refreshed, refreshed_source_setup = build_solver(source, kind)
            refreshed_update = refresh_numeric_hierarchy(refreshed, target)
            refreshed_solve = cg_diagnostic(refreshed, target, rhs)

            controls[kind] = {
                "target_rebuild": {
                    "setup_seconds_diagnostic": rebuilt_setup,
                    "solve": rebuilt_solve,
                },
                "frozen_hierarchy_reuse": {
                    "source_setup_seconds_diagnostic": source_setup,
                    "target_update_seconds_diagnostic": frozen_update,
                    "solve": frozen_solve,
                },
                "fixed_prolongation_numeric_refresh": {
                    "source_setup_seconds_diagnostic": refreshed_source_setup,
                    "target_update_seconds_diagnostic": refreshed_update,
                    "solve": refreshed_solve,
                },
            }

        rebuild_complete = all(
            controls[kind]["target_rebuild"]["solve"]["converged"]
            for kind in controls
        )
        recycling_complete = any(
            controls[kind][mode]["solve"]["converged"]
            for kind in controls
            for mode in ("frozen_hierarchy_reuse", "fixed_prolongation_numeric_refresh")
        )
        records.append(
            {
                "sequence_slot": sequence["sequence_slot"],
                "kind": sequence["kind"],
                "source": source_name,
                "target": target_name,
                "shape": list(source.shape),
                "same_stored_sparsity_pattern": bool(same_pattern),
                "value_relative_change": value_relative_change,
                "source_archive_sha256": sha256(
                    root / "archive" / f"{source_item['group']}__{source_name}.tar.gz"
                ),
                "target_archive_sha256": sha256(
                    root / "archive" / f"{target_item['group']}__{target_name}.tar.gz"
                ),
                "source_matrix_sha256": sha256(source_path),
                "target_matrix_sha256": sha256(target_path),
                "target_rebuild_complete": rebuild_complete,
                "classical_cross_matrix_recycling_complete": recycling_complete,
                "controls": controls,
            }
        )

    payload = {
        "schema_version": 1,
        "sequence_contract_id": manifest["sequence_contract_id"],
        "manifest_sha256": sha256(manifest_path),
        "pyamg_version": pyamg.__version__,
        "cg_contract": {"rtol": CG_RTOL, "atol": 0.0, "maxiter": CG_MAXITER},
        "sequence_count": len(records),
        "all_patterns_identical_within_sequence": all(
            record["same_stored_sparsity_pattern"] for record in records
        ),
        "all_target_rebuilds_complete": all(
            record["target_rebuild_complete"] for record in records
        ),
        "all_classical_cross_matrix_recycling_complete": all(
            record["classical_cross_matrix_recycling_complete"] for record in records
        ),
        "records": records,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not payload["all_patterns_identical_within_sequence"] or not payload[
        "all_target_rebuilds_complete"
    ]:
        raise SystemExit(2)
    if not payload["all_classical_cross_matrix_recycling_complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
