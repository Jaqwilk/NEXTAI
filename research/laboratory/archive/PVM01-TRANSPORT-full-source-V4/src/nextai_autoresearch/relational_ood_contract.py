"""Candidate-visible contract for anonymous relational OOD evaluation.

Only public observations, training targets, and anonymous relations cross this
boundary.  Generator state, evaluation targets, nuisance labels, permutations,
and oracle information remain evaluator-private.
"""

from __future__ import annotations

from dataclasses import dataclass


COST_FIELDS = (
    "acquisition_ops",
    "acquisition_bytes",
    "relation_construction_ops",
    "relation_synchronization_ops",
    "preprocessing_ops",
    "fit_ops",
    "query_ops",
    "update_ops",
    "bytes_touched",
    "state_bytes",
    "peak_bytes",
    "wall_time_seconds",
    "workload_ops_r1",
    "workload_ops_r4",
    "workload_ops_r16",
)


@dataclass(frozen=True)
class RelationalTrainingBatch:
    """Immutable public training payload shared by every evaluator role."""

    records: tuple[tuple[float, ...], ...]
    targets: tuple[float, ...]
    relation_edges: tuple[tuple[int, int], ...]
    relation_mask: tuple[bool, ...]
    batch_order: tuple[int, ...]

    def active_relations(self) -> tuple[tuple[int, int], ...]:
        return tuple(
            edge for edge, active in zip(self.relation_edges, self.relation_mask) if active
        )


@dataclass(frozen=True)
class RelationalQueryBatch:
    """Public query payload; evaluation targets are intentionally absent."""

    records: tuple[tuple[float, ...], ...]


def empty_cost_record() -> dict[str, float]:
    """Return the complete cost schema without implying measured work."""

    return {field: 0.0 for field in COST_FIELDS}
