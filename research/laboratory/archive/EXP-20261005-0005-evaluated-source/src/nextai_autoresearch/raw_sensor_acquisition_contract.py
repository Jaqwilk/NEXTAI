from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RawSensorWorld:
    samples: tuple[tuple[tuple[float, ...], ...], ...]


@dataclass(frozen=True)
class RawSensorTraining:
    meta_worlds: tuple[RawSensorWorld, ...]
    support: RawSensorWorld


class RawProbeSession:
    __slots__ = ("__values", "calls", "used")

    def __init__(self, values: tuple[float, ...]) -> None:
        self.__values = values
        self.calls = 0
        self.used: set[int] = set()

    def probe(self, sensor: int) -> float:
        if sensor < 0 or sensor >= len(self.__values):
            raise IndexError("raw sensor index outside public width")
        if sensor in self.used:
            raise ValueError("the same raw sensor may not be charged twice")
        self.used.add(sensor)
        self.calls += 1
        return self.__values[sensor]


class PrivilegedRawProbeSession(RawProbeSession):
    __slots__ = ("target",)

    def __init__(self, values: tuple[float, ...], target: int) -> None:
        super().__init__(values)
        self.target = target
