from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OnlineObservation:
    slot: int
    values: tuple[float, ...]


@dataclass(frozen=True)
class LabeledObservation:
    observation: OnlineObservation
    target: float


@dataclass(frozen=True)
class MetaStream:
    slot: int
    sequence: tuple[LabeledObservation, ...]


@dataclass(frozen=True)
class OnlineTraining:
    streams: tuple[MetaStream, ...]
    acquisition_ops: int


@dataclass(frozen=True)
class PrivilegedTraining:
    public: OnlineTraining


@dataclass(frozen=True)
class PrivilegedObservation:
    public: OnlineObservation
    mechanism: str
    first: tuple[float, ...]
    second: tuple[float, ...]

