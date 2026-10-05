from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .candidates.base import CandidateBase


Signature = tuple[int, int, int]


@dataclass(frozen=True, order=True)
class Event:
    time: int
    channel: int


@dataclass(frozen=True)
class Demo:
    events: tuple[Event, ...]
    labels: tuple[int, ...]


@dataclass(frozen=True)
class Episode:
    supports: tuple[Demo, ...]


@dataclass(frozen=True)
class OracleEpisode:
    episode: Episode
    active_channel: int
    motifs: tuple[tuple[int, Signature], ...]


@dataclass(frozen=True)
class TimedQuery:
    events: tuple[Event, ...]


def _times(events: tuple[Event, ...], channel: int) -> tuple[int, ...]:
    return tuple(event.time for event in events if event.channel == channel)


def _groups(times: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    groups: list[list[int]] = []
    for value in times:
        if not groups or value - groups[-1][-1] > 8:
            groups.append([value])
        else:
            groups[-1].append(value)
    return tuple(tuple(group) for group in groups)


def _signature(times: tuple[int, ...]) -> Signature | None:
    if len(times) != 4:
        return None
    return tuple(right - left for left, right in zip(times, times[1:]))  # type: ignore[return-value]


def _decode(times: tuple[int, ...], motifs: dict[Signature, int], steps: int) -> tuple[int, ...]:
    output = []
    for group in _groups(times):
        label = motifs.get(_signature(group))
        if label is not None:
            output.append(label)
        if len(output) == steps:
            break
    return tuple(output)


def discover(episode: Episode, width: int):
    expected = tuple(4 * len(demo.labels) for demo in episode.supports)
    penalties = []
    for channel in range(width):
        counts = tuple(len(_times(demo.events, channel)) for demo in episode.supports)
        penalties.append((sum(abs(a - b) for a, b in zip(counts, expected)), channel))
    active = min(penalties)[1]
    motifs: dict[Signature, int] = {}
    for demo in episode.supports:
        if len(demo.labels) == 1:
            signature = _signature(_times(demo.events, active))
            if signature is not None:
                motifs[signature] = demo.labels[0]
    events = sum(len(demo.events) for demo in episode.supports)
    return active, motifs, events + width * len(episode.supports) * 2


class TemporalCandidate(CandidateBase):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.last_input_ops = self.last_search_ops = self.last_execution_ops = 0
        self.last_memory_reads = self.last_bytes_loaded = 0
        self.last_cache_hit = False

    def _record(self, query: TimedQuery, search: int, execution: int, hit: bool, input_ops: int | None = None) -> None:
        self.last_input_ops = len(query.events) if input_ops is None else input_ops
        self.last_search_ops = search
        self.last_execution_ops = execution
        self.last_memory_reads = self.last_input_ops + search
        self.last_bytes_loaded = len(query.events) * 16 + self.state_bytes()
        self.last_ops = self.last_input_ops + search + execution
        self.last_cache_hit = hit


class TimedAutomatonMatcher(TemporalCandidate):
    query_overhead = 0
    update_overhead = 0

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.active = 0
        self.motifs: dict[Signature, int] = {}

    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        self.active, self.motifs, self.fit_ops = discover(episode, universe_size)

    def _answer(self, query: TimedQuery, steps: int) -> tuple[tuple[int, ...], int]:
        times = _times(query.events, self.active)
        return _decode(times, self.motifs, steps), len(times)

    def query(self, query: TimedQuery, steps: int) -> tuple[int, ...]:
        answer, relevant = self._answer(query, steps)
        self._record(query, relevant + self.query_overhead, relevant + len(answer), len(answer) == steps)
        return answer

    def update(self, episode: Episode, target: object = None) -> None:
        demo = episode.supports[0]
        label = demo.labels[0]
        self.motifs = {signature: value for signature, value in self.motifs.items() if value != label}
        signature = _signature(_times(demo.events, self.active))
        if signature is not None:
            self.motifs[signature] = label
        self.update_ops = len(demo.events) + self.update_overhead

    def state_bytes(self) -> int:
        return 80 + len(self.motifs) * 48


class LearnedPolychronousBinder(TimedAutomatonMatcher):
    query_overhead = 8
    update_overhead = 24

    def query(self, query: TimedQuery, steps: int) -> tuple[int, ...]:
        answer, relevant = self._answer(query, steps)
        delay_trace_ops = relevant * 3 + self.query_overhead
        self._record(query, delay_trace_ops, relevant + len(answer), len(answer) == steps)
        return answer

    def state_bytes(self) -> int:
        return super().state_bytes() + 96


class HeapEventTransducer(TimedAutomatonMatcher):
    def query(self, query: TimedQuery, steps: int) -> tuple[int, ...]:
        answer, relevant = self._answer(query, steps)
        queue_ops = int(len(query.events) * math.log2(max(2, len(query.events))))
        self._record(query, queue_ops + relevant, relevant + len(answer), len(answer) == steps)
        return answer


class CalendarEventTransducer(TimedAutomatonMatcher):
    def query(self, query: TimedQuery, steps: int) -> tuple[int, ...]:
        answer, relevant = self._answer(query, steps)
        bucket_scans = (query.events[-1].time // 8 + 1) if query.events else 0
        self._record(query, len(query.events) + bucket_scans + relevant, relevant + len(answer), len(answer) == steps)
        return answer

    def state_bytes(self) -> int:
        return super().state_bytes() + 64


class OracleTemporalBinder(TimedAutomatonMatcher):
    def fit(self, wrapped: OracleEpisode, universe_size: int, max_depth: int) -> None:
        self.active = wrapped.active_channel
        self.motifs = {signature: label for label, signature in wrapped.motifs}
        self.fit_ops = len(self.motifs)

    def update(self, wrapped: OracleEpisode, target: object = None) -> None:
        self.fit(wrapped, 0, 0)
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 80


class RandomEventGuess(TemporalCandidate):
    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0

    def query(self, query: TimedQuery, steps: int) -> tuple[int, ...]:
        answer = tuple(1 + ((self.seed + index * 7919) % 4) for index in range(steps))
        self._record(query, 0, steps, False)
        return answer

    def update(self, episode: Episode, target: object = None) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64


class RateCodeClassifier(RandomEventGuess):
    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        self.fit_ops = sum(len(demo.events) for demo in episode.supports)

    def query(self, query: TimedQuery, steps: int) -> tuple[int, ...]:
        label = 1 + ((len(query.events) + self.seed) % 4)
        answer = (label,) * steps
        self._record(query, len(query.events), steps, False)
        return answer

    def state_bytes(self) -> int:
        return 80


class NearestTimedTrace(TemporalCandidate):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.rows: tuple[tuple[int, int, tuple[int, ...]], ...] = ()

    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        self.rows = tuple((len(demo.events), demo.events[-1].time, demo.labels) for demo in episode.supports)
        self.fit_ops = sum(row[0] for row in self.rows)

    def query(self, query: TimedQuery, steps: int) -> tuple[int, ...]:
        count, horizon = len(query.events), query.events[-1].time
        row = min(self.rows, key=lambda value: abs(value[0] - count) + abs(value[1] - horizon))
        self._record(query, len(self.rows) * 3, len(row[2]), False)
        return row[2]

    def update(self, episode: Episode, target: object = None) -> None:
        self.fit(episode, 0, 0)
        self.update_ops = self.fit_ops

    def state_bytes(self) -> int:
        return 64 + len(self.rows) * 48


class ClockedSpikeReservoir(TemporalCandidate):
    hidden = 12
    classes = 5

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.width = self.max_depth = 1
        self.input_weights = self.recurrent = self.readout = np.zeros((1, 1))

    def _encode(self, events: tuple[Event, ...]) -> tuple[np.ndarray, int]:
        horizon = events[-1].time + 1 if events else 1
        state, index = np.zeros(self.hidden), 0
        for tick in range(horizon):
            vector = np.zeros(self.width)
            while index < len(events) and events[index].time == tick:
                vector[events[index].channel] = 1.0
                index += 1
            state = np.tanh(vector @ self.input_weights + state @ self.recurrent)
        return np.r_[state, 1.0], horizon * (self.width * self.hidden + self.hidden ** 2)

    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        self.width, self.max_depth = universe_size, max_depth
        rng = np.random.default_rng(self.seed)
        self.input_weights = rng.normal(0, 0.2, (self.width, self.hidden))
        self.recurrent = rng.normal(0, 0.08, (self.hidden, self.hidden))
        encoded = [self._encode(demo.events) for demo in episode.supports]
        design = np.vstack([row[0] for row in encoded])
        targets = np.zeros((len(encoded), max_depth * self.classes))
        for row, demo in enumerate(episode.supports):
            for position, label in enumerate(demo.labels[:max_depth]):
                targets[row, position * self.classes + label] = 1.0
        self.readout = np.linalg.solve(design.T @ design + np.eye(self.hidden + 1) * 1e-3, design.T @ targets)
        self.fit_ops = sum(row[1] for row in encoded) + len(encoded) * (self.hidden + 1) ** 2

    def query(self, query: TimedQuery, steps: int) -> tuple[int, ...]:
        encoded, ops = self._encode(query.events)
        scores = encoded @ self.readout
        answer = tuple(int(np.argmax(scores[i * self.classes:(i + 1) * self.classes])) for i in range(steps))
        self._record(query, ops, steps * self.classes * (self.hidden + 1), False, input_ops=ops)
        return answer

    def update(self, episode: Episode, target: object = None) -> None:
        self.fit(episode, self.width, self.max_depth)
        self.update_ops = self.fit_ops

    def state_bytes(self) -> int:
        return 96 + self.input_weights.nbytes + self.recurrent.nbytes + self.readout.nbytes
