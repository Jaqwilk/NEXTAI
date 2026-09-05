from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ByteFile:
    slot: int
    data: tuple[int, ...]


@dataclass(frozen=True)
class CompressionTraining:
    train_files: tuple[ByteFile, ...]
    validation_files: tuple[ByteFile, ...]
    acquisition_ops: int


@dataclass(frozen=True)
class ByteContext:
    slot: int
    history: tuple[int, ...]


@dataclass(frozen=True)
class PrivilegedByteContext:
    public: ByteContext
    file_histogram: tuple[int, ...]
