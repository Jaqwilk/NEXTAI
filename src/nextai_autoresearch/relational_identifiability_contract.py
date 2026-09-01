"""Generic public payload for an anonymous relational evaluation."""

from __future__ import annotations

from dataclasses import dataclass


RID_COST_FIELDS = (
    "acquisition_ops",
    "acquisition_bytes",
    "relation_construction_ops",
    "relation_synchronization_ops",
    "preprocessing_ops",
    "spectral_ops",
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
class AnonymousRelationalBatch:
    records: tuple[tuple[float, ...], ...]
    targets: tuple[float, ...]
    label_mask: tuple[bool, ...]
    relation_edges: tuple[tuple[int, int], ...]
    relation_mask: tuple[bool, ...]
    batch_order: tuple[int, ...]

    def active_relations(self) -> tuple[tuple[int, int], ...]:
        return tuple(
            edge
            for edge, active in zip(self.relation_edges, self.relation_mask)
            if active
        )


@dataclass(frozen=True)
class AnonymousQueryBatch:
    records: tuple[tuple[float, ...], ...]


def empty_rid_cost_record() -> dict[str, float]:
    return {field: 0.0 for field in RID_COST_FIELDS}
