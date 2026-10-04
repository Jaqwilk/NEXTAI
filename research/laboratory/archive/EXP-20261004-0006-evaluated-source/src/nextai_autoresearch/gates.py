from __future__ import annotations

import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .config import ResearchConfig, load_config
from .integrity import verify_manifest
from .ledger import (
    latest_plan_statuses,
    read_jsonl,
    research_dir,
)
from .scientific_validity import invalid_experiment_ids, problems as validity_problems
from .baseline_semantics import required_baseline_names
from .pareto import complete_metric_axes, is_privileged_candidate, pareto_front
from .utils import load_json, project_root, sha256_json
from .report import report_provenance_problems
from .laboratory import laboratory_problems, pc01_scope_problems


class GateViolation(RuntimeError):
    """Raised when a durable research-policy gate blocks a mutation or score."""


def stop_gate_problems(root: Path | None = None) -> list[str]:
    base = (root or project_root()).resolve()
    return [
        f"{name} gate is present"
        for name in ("STOP", "PAUSE")
        if (base / name).exists()
    ]


def plan_status(experiment_id: str, root: Path | None = None) -> str:
    base = (root or project_root()).resolve()
    if (research_dir(base) / "results" / f"{experiment_id}.json").is_file():
        return "complete"
    event = latest_plan_statuses(base).get(experiment_id)
    return str(event["status"]) if event else "planned"


def pending_plan_ids(root: Path | None = None) -> list[str]:
    base = (root or project_root()).resolve()
    return [
        path.stem
        for path in sorted((research_dir(base) / "plans").glob("EXP-*.json"))
        if plan_status(path.stem, base) == "planned"
    ]


def _review_gate_problems(
    state: dict[str, Any], config: ResearchConfig
) -> list[str]:
    completed = int(state.get("completed_experiments", 0))
    codex = config.raw["codex"]
    checks = (
        (
            "reflection",
            "last_reflection_completed_experiments",
            int(codex["reflection_every_completed_experiments"]),
        ),
        (
            "literature review",
            "last_literature_review_completed_experiments",
            int(codex["literature_review_every_completed_experiments"]),
        ),
    )
    problems: list[str] = []
    for label, field, cadence in checks:
        last = int(state.get(field, 0))
        if completed - last >= cadence:
            problems.append(
                f"{label} is due: {completed - last} completed experiments since the last review (cadence {cadence})"
            )
    return problems


def lifecycle_problems(root: Path | None = None) -> list[str]:
    base = (root or project_root()).resolve()
    research = research_dir(base)
    problems: list[str] = []
    problems.extend(validity_problems(base))

    registry_events = read_jsonl(research / "plan_registry.jsonl")
    registry: dict[str, str] = {}
    for event in registry_events:
        experiment_id = str(event.get("experiment_id", ""))
        digest = str(event.get("plan_sha256", ""))
        if experiment_id in registry:
            problems.append(f"plan registered more than once: {experiment_id}")
        registry[experiment_id] = digest

    plans: dict[str, dict[str, Any]] = {}
    for path in sorted((research / "plans").glob("EXP-*.json")):
        plan = load_json(path)
        experiment_id = str(plan.get("experiment_id", ""))
        plans[experiment_id] = plan
        if path.stem != experiment_id:
            problems.append(f"plan filename/id mismatch: {path.name}")
        expected = registry.get(experiment_id)
        if expected is None:
            problems.append(f"unregistered plan: {path.name}")
        elif expected != sha256_json(plan):
            problems.append(f"changed preregistered plan: {path.name}")
    for experiment_id in registry:
        if experiment_id not in plans:
            problems.append(f"registered plan file is missing: {experiment_id}")
    if any(p.get("kind") == "pc01_diagnostic_plan" for p in plans.values()):
        try:
            from .pc01_execution import attempt_history
            attempts = attempt_history(base)
            unfinished = [attempt["experiment_id"] for attempt in attempts if not attempt["complete"]]
            live = False
            lock_path = research / "run.lock"
            state_path = research / "state.json"
            if len(unfinished) == 1 and lock_path.exists() and state_path.exists():
                import psutil
                import socket
                lock = load_json(lock_path)
                live = (load_json(state_path).get("active_experiment_id") == unfinished[0]
                        and lock.get("host") == socket.gethostname() and psutil.pid_exists(int(lock.get("pid", -1))))
            if unfinished and not live:
                problems.append("PC-01 has an unresolved started attempt; preserve its reservation and request recovery")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            problems.append(f"PC-01 attempt provenance: {exc}")

    status_events = latest_plan_statuses(base)
    for experiment_id, event in status_events.items():
        if experiment_id not in plans:
            problems.append(f"plan status references missing plan: {experiment_id}")
        if event.get("status") != "invalidated" or not str(event.get("reason", "")).strip():
            problems.append(f"invalid plan status event: {experiment_id}")

    results: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted((research / "results").glob("EXP-*.json")):
        result = load_json(path)
        experiment_id = str(result.get("experiment_id", ""))
        results.append((path, result))
        if experiment_id in status_events:
            problems.append(f"invalidated plan has a result: {experiment_id}")
        plan = plans.get(experiment_id)
        if plan is None:
            problems.append(f"result has no plan: {path.name}")
            continue
        digest = sha256_json(plan)
        if result.get("plan_sha256") != digest or registry.get(experiment_id) != digest:
            problems.append(f"result/plan hash mismatch: {experiment_id}")
        if not (research / "analyses" / f"{experiment_id}.md").is_file():
            problems.append(f"result lacks required analysis: {experiment_id}")

    pending = pending_plan_ids(base)
    if len(pending) > 1:
        problems.append(f"multiple pending plans: {', '.join(pending)}")

    state_path = research / "state.json"
    if state_path.is_file():
        state = load_json(state_path)
        if int(state.get("completed_experiments", -1)) != len(results):
            problems.append(
                "state completed_experiments differs from immutable result count"
            )
        active = state.get("active_experiment_id")
        if active is not None and active not in pending:
            problems.append(f"state points to a non-pending active experiment: {active}")
        if results:
            newest = max(results, key=lambda item: str(item[1].get("completed_at", "")))[1]
            if state.get("last_experiment_id") != newest.get("experiment_id"):
                problems.append("state last_experiment_id differs from newest result")
        try:
            problems.extend(_review_gate_problems(state, load_config(base)))
        except (KeyError, TypeError, ValueError) as exc:
            problems.append(f"review cadence cannot be evaluated: {exc}")

    if results:
        problems.extend(report_provenance_problems(base))
    return problems


def _raise_if(problems: list[str], action: str) -> None:
    if problems:
        raise GateViolation(f"{action} blocked: " + "; ".join(problems))


def ensure_can_create_plan(root: Path | None = None, *, pc01_candidate: str | None = None,
                           pc01_phase: str | None = None, pc01_series_freeze: bool = False) -> None:
    base = (root or project_root()).resolve()
    config = load_config(base)
    problems = [*stop_gate_problems(base), *lifecycle_problems(base), *laboratory_problems(base, scoring=True)]
    if config.protocol_version >= 3:
        problems.extend(pc01_scope_problems(base, candidate=pc01_candidate, phase=pc01_phase,
                                            series_freeze=pc01_series_freeze))
    if config.benchmark_status != "active":
        problems.append(
            f"benchmark {config.benchmark_version!r} is {config.benchmark_status!r}, not active"
        )
    benchmark_path = (
        base
        / "src"
        / "nextai_autoresearch"
        / "benchmarks"
        / f"{config.benchmark_version}.py"
    )
    if not benchmark_path.is_file():
        problems.append(f"benchmark module is missing: {config.benchmark_version}")
    integrity = verify_manifest(base)
    if not integrity["ok"]:
        problems.extend(f"integrity: {value}" for value in integrity["problems"])
    pending = pending_plan_ids(base)
    if pending:
        problems.append(f"pending plan must be run or invalidated first: {pending[0]}")
    _raise_if(problems, "plan creation")


def ensure_can_run_plan(experiment_id: str, root: Path | None = None) -> None:
    base = (root or project_root()).resolve()
    config = load_config(base)
    problems = [*stop_gate_problems(base), *lifecycle_problems(base), *laboratory_problems(base, scoring=True)]
    if config.protocol_version >= 3:
        problems.extend(pc01_scope_problems(base, experiment_id=experiment_id))
    if config.benchmark_status != "active":
        problems.append(
            f"benchmark {config.benchmark_version!r} is {config.benchmark_status!r}, not active"
        )
    benchmark_path = (
        base
        / "src"
        / "nextai_autoresearch"
        / "benchmarks"
        / f"{config.benchmark_version}.py"
    )
    if not benchmark_path.is_file():
        problems.append(f"benchmark module is missing: {config.benchmark_version}")
    if plan_status(experiment_id, base) != "planned":
        problems.append(f"plan {experiment_id} is {plan_status(experiment_id, base)}")
    pending = pending_plan_ids(base)
    if pending != [experiment_id]:
        problems.append(
            f"the only pending plan must be {experiment_id}; found {pending or 'none'}"
        )
    plan_path = research_dir(base) / "plans" / f"{experiment_id}.json"
    if plan_path.is_file():
        plan = load_json(plan_path)
        if "seeds" in plan.get("matrix", {}) and not bool(
            config.raw["execution"].get("allow_legacy_fixed_seed_plans", False)
        ):
            problems.append("legacy plan exposes scoring seeds before candidate freeze")

    _raise_if(problems, "scored run")


def _candidate_seed_cv(candidate: dict[str, Any]) -> tuple[int, float | None, float]:
    by_seed: dict[int, list[float]] = defaultdict(list)
    cell_accuracies: list[float] = []
    for trial in candidate.get("trials", []):
        if trial.get("status") != "complete" or "accuracy" not in trial:
            continue
        accuracy = float(trial["accuracy"])
        by_seed[int(trial["seed"])].append(accuracy)
        cell_accuracies.append(accuracy)
    seed_means = [statistics.fmean(values) for values in by_seed.values()]
    mean = statistics.fmean(seed_means) if seed_means else 0.0
    cv = statistics.pstdev(seed_means) / mean if len(seed_means) > 1 and mean else None
    minimum = min(cell_accuracies) if cell_accuracies else 0.0
    return len(seed_means), cv, minimum


def _implementable_front(result: dict[str, Any], config: ResearchConfig) -> set[str]:
    stored = result.get("pareto_front_implementable")
    if stored is not None:
        return {str(value) for value in stored}
    threshold = float(config.raw["decision"]["minimum_screen_accuracy"])
    rows = []
    for item in result.get("candidates", []):
        summary = item.get("summary", {})
        if (
            item.get("status") == "complete"
            and not is_privileged_candidate(str(item.get("candidate", "")))
            and float(summary.get("accuracy") or 0.0) >= threshold
        ):
            rows.append({"candidate": item["candidate"], **summary})
    maximize, minimize = complete_metric_axes(
        rows,
        config.raw["metrics"]["maximize"],
        config.raw["metrics"]["minimize"],
    )
    if not maximize and not minimize:
        return set()
    return {
        str(row["candidate"])
        for row in pareto_front(rows, maximize=maximize, minimize=minimize)
    }


def _continuous_transfer_promotion_problems(
    result: dict[str, Any], plan: dict[str, Any], candidate_name: str
) -> list[str]:
    if result.get("benchmark") not in {
        "heldout_three_family_continuous_transfer_v2",
        "heldout_three_family_continuous_transfer_v3",
        "heldout_three_family_continuous_transfer_v4",
        "heldout_three_family_continuous_transfer_v5",
        "heldout_three_family_continuous_transfer_v6",
        "heldout_three_family_continuous_transfer_v7",
        "heldout_three_family_continuous_transfer_v8",
    }:
        return []
    protocol = plan.get("continuous_transfer_protocol", {})
    shared = str(protocol.get("shared_candidate", ""))
    if candidate_name != shared:
        return ["three-family v2-v6 can promote only its shared candidate"]
    candidates = {str(item.get("candidate")): item for item in result.get("candidates", ())}
    metric_sources = {
        "shared_vs_independent_gain": shared,
        "cross_family_transfer_gain": str(protocol.get("cross_family_only_ablation", "")),
    }
    problems = []
    for metric in protocol.get("causal_promotion_gates", ()):
        source = candidates.get(metric_sources.get(str(metric), ""), {})
        value = source.get("summary", {}).get(metric)
        if source.get("status") != "complete" or value is None or float(value) <= 0.0:
            problems.append(f"causal promotion gate {metric} must be positive in every family")
    return problems


def enforce_hypothesis_transition(
    previous: dict[str, Any],
    status: str,
    evidence_ids: list[str],
    candidate_name: str | None,
    root: Path | None = None,
) -> None:
    base = (root or project_root()).resolve()
    config = load_config(base)
    invalid_ids = invalid_experiment_ids(base)
    invalid = [value for value in evidence_ids if value in invalid_ids]
    _raise_if(
        [f"scientifically invalid evidence is forbidden: {value}" for value in invalid],
        "hypothesis update",
    )
    if status == "falsified":
        if not evidence_ids:
            raise GateViolation("falsified requires at least one scored evidence ID")
        missing = [
            experiment_id
            for experiment_id in evidence_ids
            if not (research_dir(base) / "results" / f"{experiment_id}.json").is_file()
            or not (research_dir(base) / "analyses" / f"{experiment_id}.md").is_file()
        ]
        _raise_if(
            [f"missing scored result and analysis for {value}" for value in missing],
            "falsification",
        )
        return
    if status not in {"promising", "promoted"}:
        return
    if not candidate_name:
        raise GateViolation(f"{status} requires --candidate")
    if is_privileged_candidate(candidate_name):
        raise GateViolation("privileged support controls cannot be promoted")
    decision = config.raw["decision"]
    if decision.get("promotion_requires_prior_art_check", True) and not previous.get(
        "prior_art"
    ):
        raise GateViolation("promotion requires a recorded prior-art check")
    if decision.get("promotion_requires_prior_art_check", True):
        primary_urls = {
            str(source.get("url"))
            for source in read_jsonl(research_dir(base) / "sources.jsonl")
            if source.get("primary_source")
        }
        if not any(
            str(item.get("url")) in primary_urls for item in previous.get("prior_art", [])
        ):
            raise GateViolation(
                "promotion prior art must reference a checked primary source in research/sources.jsonl"
            )

    all_ids = list(dict.fromkeys([*previous.get("evidence_experiment_ids", []), *evidence_ids]))
    qualifying: list[dict[str, Any]] = []
    failures: list[str] = []
    for experiment_id in all_ids:
        if experiment_id in invalid_ids:
            failures.append(f"{experiment_id} is scientifically invalid")
            continue
        result_path = research_dir(base) / "results" / f"{experiment_id}.json"
        if not result_path.is_file():
            continue
        result = load_json(result_path)
        plan_path = base / str(result.get("plan_path", ""))
        plan = load_json(plan_path) if plan_path.is_file() else {}
        if plan:
            mandatory = required_baseline_names(plan)
            statuses = {
                str(item.get("candidate")): str(item.get("status"))
                for item in result.get("candidates", ())
            }
            unavailable = [name for name in mandatory if statuses.get(name) != "complete"]
            if unavailable:
                failures.append(
                    f"{experiment_id} mandatory control did not complete: {', '.join(unavailable)}"
                )
                continue
        if result.get("hypothesis_id") != previous.get("hypothesis_id"):
            continue
        if result.get("budget") not in {"screen", "deep"}:
            continue
        if not result.get("integrity_before", {}).get("ok") or not result.get(
            "integrity_after", {}
        ).get("ok"):
            failures.append(f"{experiment_id} has an integrity violation")
            continue
        if not (research_dir(base) / "analyses" / f"{experiment_id}.md").is_file():
            failures.append(f"{experiment_id} lacks an analysis")
            continue
        item = next(
            (
                value
                for value in result.get("candidates", [])
                if value.get("candidate") == candidate_name
            ),
            None,
        )
        if item is None or item.get("status") != "complete":
            continue
        causal_problems = _continuous_transfer_promotion_problems(
            result, plan, candidate_name
        )
        if causal_problems:
            failures.extend(f"{experiment_id} {problem}" for problem in causal_problems)
            continue
        seed_count, seed_cv, minimum_accuracy = _candidate_seed_cv(item)
        required_seeds = int(decision["minimum_replication_seeds"])
        if seed_count < required_seeds:
            failures.append(
                f"{experiment_id} has {seed_count} seeds; {required_seeds} required"
            )
            continue
        if seed_cv is None or seed_cv > float(decision["maximum_relative_seed_cv"]):
            failures.append(f"{experiment_id} seed CV is {seed_cv}")
            continue
        if minimum_accuracy < float(decision["minimum_screen_accuracy"]):
            failures.append(
                f"{experiment_id} minimum cell accuracy is {minimum_accuracy:.4f}"
            )
            continue
        if candidate_name not in _implementable_front(result, config):
            failures.append(f"{experiment_id} is not on the implementable Pareto front")
            continue
        qualifying.append(result)

    required_results = 1 if status == "promising" else int(
        decision.get("minimum_promotion_results", 2)
    )
    if len(qualifying) < required_results:
        detail = "; ".join(failures) if failures else "no qualifying screen result"
        raise GateViolation(
            f"{status} needs {required_results} qualifying replicated result(s): {detail}"
        )
    if status == "promoted":
        if decision.get("promotion_requires_deep", True) and not any(
            result.get("budget") == "deep" for result in qualifying
        ):
            raise GateViolation("promoted requires at least one deep result")
        if decision.get("promotion_requires_adversarial_variant", True):
            benchmarks = {str(result.get("benchmark")) for result in qualifying}
            if len(benchmarks) < 2:
                raise GateViolation(
                    "promoted requires qualifying evidence from an adversarial or transfer cohort"
                )
