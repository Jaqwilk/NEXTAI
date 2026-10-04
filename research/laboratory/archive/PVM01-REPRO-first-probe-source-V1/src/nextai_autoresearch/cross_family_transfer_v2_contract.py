from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Any


@dataclass(frozen=True)
class Example:
    query: tuple[int, ...]
    target: tuple[float, ...]


@dataclass(frozen=True)
class TrainingWorld:
    support: tuple[int, ...]
    examples: tuple[Example, ...]


@dataclass(frozen=True)
class TestWorld:
    slot: int
    support: tuple[int, ...]


@dataclass(frozen=True)
class PublicTraining:
    training_worlds: tuple[TrainingWorld, ...]
    test_worlds: tuple[TestWorld, ...]
    acquisition_ops: int


@dataclass(frozen=True)
class PublicQuery:
    slot: int
    tokens: tuple[int, ...]


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


def encode(value: Any) -> tuple[tuple[int, ...], int]:
    """Lossless, family-neutral structural encoding; names and native types are omitted."""
    output: list[int] = []

    def walk(item: Any) -> None:
        if is_dataclass(item):
            output.extend((-1, len(fields(item))))
            for field in fields(item):
                walk(getattr(item, field.name))
        elif isinstance(item, dict):
            output.extend((-2, len(item)))
            for key in sorted(item, key=repr):
                walk(key)
                walk(item[key])
        elif isinstance(item, (tuple, list)):
            output.extend((-3, len(item)))
            for child in item:
                walk(child)
        elif isinstance(item, bool):
            output.extend((-4, int(item)))
        elif isinstance(item, int):
            output.extend((-5, item))
        elif isinstance(item, float):
            output.extend((-6, int(round(item * 1_000_000))))
        elif item is None:
            output.append(-7)
        else:
            raise TypeError(f"unsupported public value: {type(item).__name__}")

    walk(value)
    return tuple(output), len(output)
