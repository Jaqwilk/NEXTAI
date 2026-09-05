from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pair:
    source: int
    target: int


@dataclass(frozen=True)
class TrainingWorld:
    support: tuple[Pair, ...]
    examples: tuple[Pair, ...]


@dataclass(frozen=True)
class TestWorld:
    slot: int
    support: tuple[Pair, ...]


@dataclass(frozen=True)
class PublicTraining:
    training_worlds: tuple[TrainingWorld, ...]
    test_worlds: tuple[TestWorld, ...]
    acquisition_ops: int


@dataclass(frozen=True)
class PublicQuery:
    slot: int
    source: int


@dataclass(frozen=True)
class PublicUpdate:
    query: PublicQuery
    target: int


@dataclass(frozen=True)
class PrivilegedTraining:
    public: PublicTraining


@dataclass(frozen=True)
class PrivilegedQuery:
    public: PublicQuery
    target: int


@dataclass(frozen=True)
class PrivilegedUpdate:
    public: PublicUpdate

