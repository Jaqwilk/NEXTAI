from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .utils import project_root


@dataclass(frozen=True)
class Budget:
    name: str
    wall_seconds_per_candidate: int
    max_rss_mb: int
    knowledge_sizes: tuple[int, ...]
    reasoning_depths: tuple[int, ...]
    queries_per_cell: int
    development_seeds: tuple[int, ...]
    scoring_seed_count: int
    legacy_scoring_seeds: tuple[int, ...]


@dataclass(frozen=True)
class ResearchConfig:
    raw: dict[str, Any]
    path: Path

    @property
    def benchmark_version(self) -> str:
        return str(self.raw["project"]["benchmark_version"])

    @property
    def benchmark_status(self) -> str:
        return str(self.raw["project"].get("benchmark_status", "active"))

    @property
    def protocol_version(self) -> int:
        return int(self.raw["project"].get("protocol_version", 1))

    def budget(self, name: str) -> Budget:
        try:
            data = self.raw["budgets"][name]
        except KeyError as exc:
            raise ValueError(f"Unknown budget tier: {name}") from exc
        return Budget(
            name=name,
            wall_seconds_per_candidate=int(data["wall_seconds_per_candidate"]),
            max_rss_mb=int(data["max_rss_mb"]),
            knowledge_sizes=tuple(int(value) for value in data["knowledge_sizes"]),
            reasoning_depths=tuple(int(value) for value in data["reasoning_depths"]),
            queries_per_cell=int(data["queries_per_cell"]),
            development_seeds=tuple(
                int(value)
                for value in data.get("development_seeds", data.get("seeds", ()))
            ),
            scoring_seed_count=int(
                data.get("scoring_seed_count", len(data.get("seeds", ())))
            ),
            legacy_scoring_seeds=tuple(int(value) for value in data.get("seeds", ())),
        )

    @property
    def allowed_import_roots(self) -> frozenset[str]:
        return frozenset(self.raw["execution"]["allowed_import_roots"])

    @property
    def forbidden_builtins(self) -> frozenset[str]:
        return frozenset(self.raw["execution"]["forbidden_builtins"])


def load_config(root: Path | None = None) -> ResearchConfig:
    base = root or project_root()
    path = base / "config" / "research.toml"
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    if raw.get("schema_version") != 1:
        raise ValueError("config/research.toml has an unsupported schema_version")
    for tier in ("quick", "screen", "deep"):
        if tier not in raw.get("budgets", {}):
            raise ValueError(f"Missing budget tier: {tier}")
        budget = raw["budgets"][tier]
        development_seeds = budget.get("development_seeds", budget.get("seeds", ()))
        scoring_seed_count = int(
            budget.get("scoring_seed_count", len(budget.get("seeds", ())))
        )
        if not development_seeds:
            raise ValueError(f"Budget {tier!r} needs at least one development seed")
        if scoring_seed_count < 1:
            raise ValueError(f"Budget {tier!r} needs at least one scoring seed")
    status = str(raw.get("project", {}).get("benchmark_status", "active"))
    if status not in {"active", "retired", "maintenance"}:
        raise ValueError(f"Unsupported benchmark_status: {status!r}")
    return ResearchConfig(raw=raw, path=path)
