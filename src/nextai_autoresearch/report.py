from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .config import load_config
from .metrics import aggregate_trials
from .scientific_validity import invalid_experiment_ids
from .pareto import is_privileged_candidate, pareto_front
from .utils import load_json, project_root, utc_now


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}g}"
    return str(value)


def collect_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    invalid = invalid_experiment_ids(root)
    for path in sorted((root / "research" / "results").glob("EXP-*.json")):
        result = load_json(path)
        plan_path = root / str(result["plan_path"])
        plan = load_json(plan_path) if plan_path.is_file() else {}
        matrix = result.get("evaluation_matrix")
        if matrix is None:
            matrix = plan.get("matrix", {})
        integrity_ok = bool(result.get("integrity_after", {}).get("ok"))
        for candidate in result.get("candidates", []):
            summary = candidate.get("summary", {})
            derived = aggregate_trials(candidate.get("trials", []))
            display_summary = {**derived, **summary}
            rows.append(
                {
                    "experiment_id": result["experiment_id"],
                    "hypothesis_id": result["hypothesis_id"],
                    "benchmark": result["benchmark"],
                    "budget": result["budget"],
                    "candidate": candidate["candidate"],
                    "candidate_status": candidate["status"],
                    "is_privileged": is_privileged_candidate(str(candidate["candidate"])),
                    "matrix_seed_count": len(matrix.get("seeds", ())),
                    "matrix_knowledge_points": len(matrix.get("knowledge_sizes", ())),
                    "matrix_depth_points": len(matrix.get("reasoning_depths", ())),
                    "primary_metrics": tuple(plan.get("primary_metrics", ())),
                    "metric_directions": dict(plan.get("metric_directions", {})),
                    "integrity_ok": integrity_ok,
                    "scientifically_valid": result["experiment_id"] not in invalid,
                    **display_summary,
                }
            )
    return rows


def write_report(root: Path | None = None) -> Path:
    base = (root or project_root()).resolve()
    config = load_config(base)
    rows = collect_rows(base)
    invalid_ids = invalid_experiment_ids(base)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["benchmark"]), str(row["budget"]))].append(row)
    lines = [
        "# Research report",
        "",
        f"Generated: {utc_now()}",
        "",
        "Only results from the same benchmark version and budget tier are compared.",
        "The implementable Pareto frontier excludes privileged support controls and is capability-gated.",
        "Pareto axes come from the frozen benchmark contract; incomplete rows cannot remove an axis or enter the frontier.",
        f"Append-only scientific-validity corrections exclude {len(invalid_ids)} result(s) from every frontier and evidential comparison.",
        "",
    ]
    if not grouped:
        lines.extend(["No completed experiment results yet.", ""])
    metrics = config.raw["metrics"]
    minimum_accuracy = float(config.raw["decision"]["minimum_screen_accuracy"])
    for (benchmark, budget), cohort in sorted(grouped.items()):
        eligible = [
            row
            for row in cohort
            if row.get("integrity_ok")
            and row.get("scientifically_valid", True)
            and row.get("candidate_status") == "complete"
            and row.get("status") == "complete"
            and float(row.get("accuracy") or 0.0) >= minimum_accuracy
            and not row["is_privileged"]
        ]
        declared_sets = [set(row["primary_metrics"]) for row in cohort if row["primary_metrics"]]
        declared = set.intersection(*declared_sets) if declared_sets else set()
        maximize_requested = [
            metric for metric in metrics["maximize"] if metric in declared
        ]
        minimize_requested = [
            metric for metric in metrics["minimize"] if metric in declared
        ]
        minimum_points = int(config.raw["decision"].get("minimum_scaling_points", 3))
        if any(
            int(row.get("knowledge_compute_slope_points") or row.get("matrix_knowledge_points") or 0)
            < minimum_points
            for row in eligible
        ):
            minimize_requested = [
                metric
                for metric in minimize_requested
                if metric != "knowledge_compute_slope"
            ]
        if any(
            int(row.get("depth_compute_slope_points") or row.get("matrix_depth_points") or 0)
            < minimum_points
            for row in eligible
        ):
            minimize_requested = [
                metric for metric in minimize_requested if metric != "depth_compute_slope"
            ]
        maximize, minimize = maximize_requested, minimize_requested
        eligible = [row for row in eligible if all(row.get(metric) is not None for metric in [*maximize, *minimize])]
        frontier = {
            (row["experiment_id"], row["candidate"])
            for row in (
                pareto_front(eligible, maximize, minimize)
                if maximize or minimize
                else []
            )
        }
        lines.extend(
            [
                f"## {benchmark} / {budget}",
                "",
                f"Pareto axes: maximize `{', '.join(maximize) or 'none'}`; minimize `{', '.join(minimize) or 'none'}`.",
                "",
                "| Experiment | Candidate | Role | Status | Acc. | Seeds | Ops/query | Input ops | Bytes touched | R16 workload | K slope (points) | State bytes | Pareto |",
                "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|",
            ]
        )
        for row in cohort:
            marker = "yes" if (row["experiment_id"], row["candidate"]) in frontier else ""
            role = (
                "scientifically invalid"
                if not row.get("scientifically_valid", True)
                else "privileged support control" if row["is_privileged"] else "implementable"
            )
            slope_points = row.get("knowledge_compute_slope_points")
            if slope_points is None:
                slope_points = row.get("matrix_knowledge_points")
            slope = row.get("knowledge_compute_slope")
            if int(slope_points or 0) < minimum_points:
                slope = row.get("knowledge_compute_slope_screening", slope)
                slope_rendered = f"{_fmt(slope)} ({slope_points}; screening)"
            else:
                slope_rendered = f"{_fmt(slope)} ({slope_points})"
            lines.append(
                "| {experiment_id} | {candidate} | {role} | {candidate_status} | {accuracy} | "
                "{seeds} | {mean_query_ops} | {mean_input_ops} | {mean_bytes_touched} | "
                "{workload_ops_r16} | {knowledge_compute_slope} | {state_bytes} | {marker} |".format(
                    experiment_id=row["experiment_id"],
                    candidate=row["candidate"],
                    role=role,
                    candidate_status=(
                        "scientifically_invalid"
                        if not row.get("scientifically_valid", True)
                        else row["candidate_status"]
                    ),
                    accuracy=_fmt(row.get("accuracy")),
                    seeds=row.get("seed_count") or row.get("matrix_seed_count") or "-",
                    mean_query_ops=_fmt(row.get("mean_query_ops")),
                    mean_input_ops=_fmt(row.get("mean_input_ops")),
                    mean_bytes_touched=_fmt(row.get("mean_bytes_touched")),
                    workload_ops_r16=_fmt(row.get("workload_ops_r16")),
                    knowledge_compute_slope=slope_rendered,
                    state_bytes=_fmt(row.get("state_bytes"), 6),
                    marker=marker,
                )
            )
        lines.append("")
    path = base / "research" / "REPORT.md"
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return path
