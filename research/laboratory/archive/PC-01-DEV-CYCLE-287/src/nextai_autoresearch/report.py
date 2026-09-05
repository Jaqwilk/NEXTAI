from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .config import load_config
from .metrics import aggregate_trials
from .ledger import read_jsonl
from .scientific_validity import invalid_experiment_ids
from .pareto import is_privileged_candidate, pareto_front
from .utils import atomic_write_json, load_json, project_root, sha256_file, sha256_json, utc_now


def report_inputs(root: Path) -> dict[str, Any]:
    """Content identity of every report input; unrelated events and mtimes do not count."""
    documents: dict[str, str | None] = {}
    for path in sorted((root / "research" / "results").glob("EXP-*.json")):
        result = load_json(path)
        documents[path.relative_to(root).as_posix()] = sha256_json(result)
        relative = str(result["plan_path"])
        plan = root / relative
        documents[relative] = sha256_json(load_json(plan)) if plan.is_file() else None
    corrections = [
        event for event in read_jsonl(root / "research" / "events.jsonl")
        if event.get("event") == "experiment_scientific_validity_correction"
    ]
    # Use the executing renderer, including for report unit-test fixtures.
    code = Path(__file__).resolve().parent
    renderer = {
        name: sha256_file(code / name)
        for name in ("report.py", "metrics.py", "pareto.py", "scientific_validity.py", "utils.py", "ledger.py", "config.py")
    }
    return {
        "documents": documents,
        "config_sha256": sha256_json(load_config(root).raw),
        "validity_sha256": sha256_json(corrections),
        "renderer": renderer,
    }


def report_provenance_problems(root: Path) -> list[str]:
    report = root / "research" / "REPORT.md"
    receipt = root / "research" / "REPORT.provenance.json"
    if not report.is_file() or not receipt.is_file():
        return ["research/REPORT.md needs a content provenance receipt; run nextai report"]
    try:
        stored = load_json(receipt)
        if stored.get("schema_version") != 1:
            return ["research/REPORT.provenance.json has an unsupported schema"]
        problems = []
        if stored.get("inputs") != report_inputs(root):
            problems.append("research/REPORT.md is stale relative to its content inputs")
        if stored.get("report_sha256") != sha256_file(report):
            problems.append("research/REPORT.md content differs from its provenance receipt")
        return problems
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return [f"report provenance cannot be verified: {exc}"]


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}g}"
    return str(value)


def _is_loss_benchmark(benchmark: str) -> bool:
    return benchmark.startswith(("heldout_parallel_masked_", "heldout_wt_changepoints_"))


def _cohort_pareto_contract(
    cohort: list[dict[str, Any]],
) -> tuple[list[str], list[str], str | None]:
    by_experiment: dict[str, Any] = {}
    for row in cohort:
        if row.get("scientifically_valid", True):
            by_experiment[str(row["experiment_id"])] = row.get("pareto_metrics")
    if not by_experiment:
        return [], [], "no scientifically valid immutable result"
    missing = sorted(
        experiment_id
        for experiment_id, contract in by_experiment.items()
        if not isinstance(contract, dict)
    )
    if missing:
        return [], [], "immutable result lacks pareto_metrics: " + ", ".join(missing)
    contracts: dict[tuple[tuple[str, ...], tuple[str, ...]], list[str]] = defaultdict(list)
    for experiment_id, contract in by_experiment.items():
        signature = (
            tuple(str(value) for value in contract.get("maximize", ())),
            tuple(str(value) for value in contract.get("minimize", ())),
        )
        contracts[signature].append(experiment_id)
    if len(contracts) != 1:
        return [], [], "inconsistent immutable pareto_metrics across experiments"
    (maximize, minimize), _ = next(iter(contracts.items()))
    return list(maximize), list(minimize), None


def collect_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    invalid = invalid_experiment_ids(root)
    for path in sorted((root / "research" / "results").glob("EXP-*.json")):
        result = load_json(path)
        plan_path = root / str(result["plan_path"])
        if result.get("kind") == "pc01_diagnostic_result":
            continue  # Diagnostic envelopes never supply architecture/Pareto rows.
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
                    "pareto_metrics": result.get("pareto_metrics"),
                    "promotion_gates": tuple(
                        plan.get("continuous_transfer_protocol", {}).get(
                            "causal_promotion_gates", ()
                        )
                    ),
                    "integrity_ok": integrity_ok,
                    "scientifically_valid": result["experiment_id"] not in invalid,
                    **display_summary,
                }
            )
    return rows


def write_report(root: Path | None = None) -> Path:
    base = (root or project_root()).resolve()
    inputs = report_inputs(base)
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
    minimum_accuracy = float(config.raw["decision"]["minimum_screen_accuracy"])
    for (benchmark, budget), cohort in sorted(grouped.items()):
        loss_cohort = _is_loss_benchmark(benchmark)
        eligible = [
            row
            for row in cohort
            if row.get("integrity_ok")
            and row.get("scientifically_valid", True)
            and row.get("candidate_status") == "complete"
            and row.get("status") == "complete"
            and row.get("accuracy") is not None
            and (loss_cohort or float(row["accuracy"]) >= minimum_accuracy)
            and not row["is_privileged"]
        ]
        maximize, minimize, contract_problem = _cohort_pareto_contract(cohort)
        minimum_points = int(config.raw["decision"].get("minimum_scaling_points", 3))
        if contract_problem:
            eligible = []
        eligible = [row for row in eligible if all(row.get(metric) is not None for metric in [*maximize, *minimize])]
        frontier = {
            (row["experiment_id"], row["candidate"])
            for row in (
                pareto_front(eligible, maximize, minimize)
                if maximize or minimize
                else []
            )
        }
        axes_line = (
            f"Pareto axes unavailable: {contract_problem}."
            if contract_problem
            else f"Pareto axes: maximize `{', '.join(maximize) or 'none'}`; minimize `{', '.join(minimize) or 'none'}`."
        )
        promotion_gates = list(dict.fromkeys(
            str(gate) for row in cohort for gate in row.get("promotion_gates", ())
        ))
        lines.extend([f"## {benchmark} / {budget}", "", axes_line, ""])
        if promotion_gates:
            lines.extend([
                f"Promotion-only gates (not Pareto axes): `{', '.join(promotion_gates)}`.",
                "",
            ])
        lines.extend(
            [
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
    if report_inputs(base) != inputs:
        raise RuntimeError("Report inputs changed during rendering; retry without overlapping writes")
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    atomic_write_json(base / "research" / "REPORT.provenance.json", {
        "schema_version": 1,
        "inputs": inputs,
        "report_sha256": sha256_file(path),
    })
    return path
