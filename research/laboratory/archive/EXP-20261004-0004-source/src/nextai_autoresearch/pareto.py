from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def is_oracle_candidate(candidate: str) -> bool:
    normalized = candidate.lower()
    return (
        normalized == "oracle"
        or normalized.startswith("oracle_")
        or normalized.endswith("_oracle")
        or "_oracle_" in normalized
    )


def is_privileged_candidate(candidate: str) -> bool:
    normalized = candidate.lower()
    return is_oracle_candidate(candidate) or normalized.startswith("privileged_")


def complete_metric_axes(
    rows: list[Mapping[str, Any]],
    maximize: Iterable[str],
    minimize: Iterable[str],
) -> tuple[list[str], list[str]]:
    """Keep only preregistered axes measured for every row in a cohort."""
    maximize_list = [
        metric
        for metric in maximize
        if rows and all(row.get(metric) is not None for row in rows)
    ]
    minimize_list = [
        metric
        for metric in minimize
        if rows and all(row.get(metric) is not None for row in rows)
    ]
    return maximize_list, minimize_list


def dominates(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    maximize: Iterable[str],
    minimize: Iterable[str],
) -> bool:
    """Return True when left is no worse everywhere and better somewhere."""
    no_worse = True
    strictly_better = False
    compared = False
    for metric in maximize:
        a, b = left.get(metric), right.get(metric)
        if a is None or b is None:
            return False
        compared = True
        if a < b:
            no_worse = False
        elif a > b:
            strictly_better = True
    for metric in minimize:
        a, b = left.get(metric), right.get(metric)
        if a is None or b is None:
            return False
        compared = True
        if a > b:
            no_worse = False
        elif a < b:
            strictly_better = True
    return compared and no_worse and strictly_better


def pareto_front(
    rows: list[dict[str, Any]], maximize: Iterable[str], minimize: Iterable[str]
) -> list[dict[str, Any]]:
    front: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if any(
            dominates(other, row, maximize, minimize)
            for other_index, other in enumerate(rows)
            if other_index != index
        ):
            continue
        front.append(row)
    return front
