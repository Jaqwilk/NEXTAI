from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable


Fact = tuple[int, int]


class UnsupportedScale(RuntimeError):
    """Raised when a candidate declares a preregistered scale unsupported."""


@dataclass(frozen=True)
class CandidateMetadata:
    name: str
    family: str
    description: str


class CandidateBase(ABC):
    metadata: CandidateMetadata

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed
        self.last_ops = 0
        self.fit_ops = 0
        self.update_ops = 0

    @abstractmethod
    def fit(self, facts: Iterable[Fact], universe_size: int, max_depth: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def query(self, source: int, steps: int) -> int | None:
        raise NotImplementedError

    @abstractmethod
    def update(self, source: int, target: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def state_bytes(self) -> int:
        raise NotImplementedError

