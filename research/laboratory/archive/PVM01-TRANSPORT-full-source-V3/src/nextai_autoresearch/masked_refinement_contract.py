from __future__ import annotations

from dataclasses import dataclass


MASK = 256


@dataclass(frozen=True)
class ByteFile:
    slot: int
    data: tuple[int, ...]


@dataclass(frozen=True)
class MaskedTraining:
    train_files: tuple[ByteFile, ...]
    validation_files: tuple[ByteFile, ...]
    acquisition_ops: int


@dataclass(frozen=True)
class MaskedQuery:
    slot: int
    snapshot: tuple[int, ...]
    masked_positions: tuple[int, ...]
    round_index: int
    maximum_rounds: int


@dataclass(frozen=True)
class PrivilegedMaskedQuery:
    public: MaskedQuery
    target: tuple[int, ...]
