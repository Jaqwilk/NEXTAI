from __future__ import annotations

from dataclasses import dataclass


DIMENSION, LATENT = 12, 6
View = tuple[float, ...]
ViewPair = tuple[View, View]


@dataclass(frozen=True)
class BindingFact:
    source: ViewPair
    target: ViewPair
    value: int


@dataclass(frozen=True)
class ViewQuery:
    view: View
    signature: int


@dataclass(frozen=True)
class OracleQuery(ViewQuery):
    entity: int


@dataclass(frozen=True)
class OracleSpec:
    transitions: dict[int, int]
    values: dict[int, int]


@dataclass(frozen=True)
class OracleUpdate:
    entity: int
    target: int
    value: int
