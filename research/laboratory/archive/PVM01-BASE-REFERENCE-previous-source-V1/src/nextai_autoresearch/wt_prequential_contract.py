from __future__ import annotations

from dataclasses import dataclass


Matrix = tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class WTEpisode:
    history: Matrix
    control: float
    target: Matrix


@dataclass(frozen=True)
class WTTraining:
    episodes: tuple[WTEpisode, ...]
    acquisition_ops: int
    preprocessing_ops: int


@dataclass(frozen=True)
class WTQuery:
    slot: int
    history: Matrix
    control: float
    horizon: int


@dataclass(frozen=True)
class WTReveal:
    slot: int
    history: Matrix
    control: float
    target: Matrix


@dataclass(frozen=True)
class PredictionArtifact:
    slot: int
    shape: tuple[int, int]
    sha256: str
