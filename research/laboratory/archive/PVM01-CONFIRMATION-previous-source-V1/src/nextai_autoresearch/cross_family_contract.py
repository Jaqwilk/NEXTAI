from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Any


SUPPORT_WIDTH = 65_536
QUERY_WIDTH = 2_048
OUTPUT_WIDTH = 8
PAD = -9


@dataclass(frozen=True)
class Example:
    query: tuple[int, ...]
    target: tuple[float, ...]


@dataclass(frozen=True)
class MetaWorld:
    support: tuple[int, ...]
    examples: tuple[Example, ...]


@dataclass(frozen=True)
class TestWorld:
    slot: int
    support: tuple[int, ...]


@dataclass(frozen=True)
class PublicTraining:
    meta_worlds: tuple[MetaWorld, ...]
    test_worlds: tuple[TestWorld, ...]
    acquisition_ops: int


@dataclass(frozen=True)
class PublicQuery:
    slot: int
    tokens: tuple[int, ...]
    signature: int


@dataclass(frozen=True)
class PublicUpdate:
    query: PublicQuery
    target: tuple[float, ...]


@dataclass(frozen=True)
class NativeWorld:
    slot: int
    family: str
    public_fit: Any
    oracle_fit: Any


@dataclass(frozen=True)
class PrivilegedTraining:
    public: PublicTraining
    native_worlds: tuple[NativeWorld, ...]


@dataclass(frozen=True)
class PrivilegedQuery:
    public: PublicQuery
    family: str
    native: Any


@dataclass(frozen=True)
class PrivilegedUpdate:
    public: PublicUpdate
    family: str
    native: Any


def _walk(value: Any, output: list[int]) -> None:
    if is_dataclass(value):
        output.extend((-1, len(fields(value))))
        for field in fields(value):
            _walk(getattr(value, field.name), output)
    elif isinstance(value, dict):
        output.extend((-2, len(value)))
        for key in sorted(value, key=repr):
            _walk(key, output)
            _walk(value[key], output)
    elif isinstance(value, (tuple, list)):
        output.extend((-3, len(value)))
        for item in value:
            _walk(item, output)
    elif isinstance(value, bool):
        output.extend((-4, int(value)))
    elif isinstance(value, int):
        output.extend((-5, value))
    elif isinstance(value, float):
        output.extend((-6, int(round(value * 1_000_000))))
    elif value is None:
        output.append(-7)
    else:
        raise TypeError(f"unsupported public value: {type(value).__name__}")


def pack(value: Any, width: int) -> tuple[tuple[int, ...], int]:
    raw: list[int] = []
    _walk(value, raw)
    operations = len(raw)
    if len(raw) > width:
        last = len(raw) - 1
        raw = [raw[(index * last) // (width - 1)] for index in range(width)]
    elif len(raw) < width:
        raw.extend([PAD] * (width - len(raw)))
    return tuple(raw), operations
