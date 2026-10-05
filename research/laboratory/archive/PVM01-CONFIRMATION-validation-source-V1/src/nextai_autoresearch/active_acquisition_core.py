from __future__ import annotations

import random
from dataclasses import dataclass

from .candidates.base import CandidateBase


@dataclass(frozen=True)
class Codebook:
    rows: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class CodebookUpdate:
    changes: tuple[tuple[int, tuple[int, ...]], ...]


class ProbeSession:
    __slots__ = ("__row", "calls")

    def __init__(self, row: tuple[int, ...]) -> None:
        self.__row, self.calls = row, 0

    def probe(self, column: int) -> int:
        self.calls += 1
        return self.__row[column]


@dataclass(frozen=True)
class ProbeBatch:
    sessions: tuple[ProbeSession, ...]


@dataclass(frozen=True)
class OracleBatch:
    batch: ProbeBatch
    targets: tuple[int, ...]


class AcquisitionCandidate(CandidateBase):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.rows: list[tuple[int, ...]] = []
        self.policy_build_ops = 0
        self.last_input_ops = self.last_search_ops = self.last_execution_ops = 0
        self.last_memory_reads = self.last_bytes_loaded = self.last_probe_count = 0
        self.last_cache_hit = False

    @property
    def width(self) -> int:
        return len(self.rows[0]) if self.rows else 0

    def fit(self, codebook: Codebook, universe_size: int, max_depth: int) -> None:
        self.rows = list(codebook.rows)
        self.fit_ops = len(self.rows) * self.width
        self.policy_build_ops = 0

    def _record(self, probes: int, search: int, execution: int, hit: bool) -> None:
        self.last_probe_count = probes
        self.last_input_ops = 2 * probes  # address plus delivered binary outcome
        self.last_search_ops, self.last_execution_ops = search, execution
        self.last_memory_reads = search + execution + probes
        self.last_bytes_loaded = 8 * self.last_memory_reads + self.state_bytes()
        self.last_ops = self.last_input_ops + search + execution
        self.last_cache_hit = hit

    def _apply(self, update: CodebookUpdate) -> int:
        for label, row in update.changes:
            self.rows[label] = row
        return len(update.changes) * self.width

    def update(self, update: CodebookUpdate, target: object = None) -> None:
        self.update_ops = self._apply(update)

    def state_bytes(self) -> int:
        return 64 + len(self.rows) * self.width


class NoProbeGuess(AcquisitionCandidate):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.size = 1

    def fit(self, codebook: Codebook, universe_size: int, max_depth: int) -> None:
        self.size, self.fit_ops = universe_size, 0

    def query(self, wrapped: ProbeBatch, steps: int) -> tuple[int, ...]:
        batch = wrapped.batch if isinstance(wrapped, OracleBatch) else wrapped
        answer = tuple((self.seed + index) % self.size for index in range(len(batch.sessions)))
        self._record(0, 0, len(answer), False)
        return answer

    def update(self, update: CodebookUpdate, target: object = None) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64


class PassiveObserveAll(AcquisitionCandidate):
    def query(self, batch: ProbeBatch, steps: int) -> tuple[int, ...]:
        answers, probes, search = [], 0, 0
        for session in batch.sessions:
            observed = tuple(session.probe(column) for column in range(self.width))
            probes += self.width
            answer = next((label for label, row in enumerate(self.rows) if row == observed), 0)
            search += len(self.rows) * self.width
            answers.append(answer)
        self._record(probes, search, len(answers), True)
        return tuple(answers)


class SequentialPolicy(AcquisitionCandidate):
    def _select(self, version: tuple[int, ...], unused: tuple[int, ...]) -> tuple[int, int]:
        raise NotImplementedError

    def query(self, batch: ProbeBatch, steps: int) -> tuple[int, ...]:
        answers, probes, search, execution, exact = [], 0, 0, 0, True
        for session in batch.sessions:
            version, unused = tuple(range(len(self.rows))), tuple(range(self.width))
            while len(version) > 1 and unused:
                column, cost = self._select(version, unused)
                value = session.probe(column)
                probes, search = probes + 1, search + cost
                execution += len(version)
                version = tuple(label for label in version if self.rows[label][column] == value)
                unused = tuple(item for item in unused if item != column)
            exact &= len(version) == 1
            answers.append(version[0] if version else 0)
        self._record(probes, search, execution, exact)
        return tuple(answers)


class FixedProbeOrder(SequentialPolicy):
    def _select(self, version: tuple[int, ...], unused: tuple[int, ...]) -> tuple[int, int]:
        return unused[0], 1


class RandomProbePolicy(SequentialPolicy):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.rng = random.Random(seed)

    def _select(self, version: tuple[int, ...], unused: tuple[int, ...]) -> tuple[int, int]:
        return unused[self.rng.randrange(len(unused))], 1


class EntropyGreedyProbe(SequentialPolicy):
    def _select(self, version: tuple[int, ...], unused: tuple[int, ...]) -> tuple[int, int]:
        best, cost = (len(version) + 1, unused[0]), 0
        for column in unused:
            ones = sum(self.rows[label][column] for label in version)
            best = min(best, (abs(len(version) - 2 * ones), column))
            cost += len(version) + 1
        return best[1], cost


class RankedProbePolicy(SequentialPolicy):
    select_cost = 1

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.order: tuple[int, ...] = ()
        self.values: tuple[int, ...] = ()

    def _select(self, version: tuple[int, ...], unused: tuple[int, ...]) -> tuple[int, int]:
        available = set(unused)
        return next(column for column in self.order if column in available), self.select_cost

    def state_bytes(self) -> int:
        return super().state_bytes() + len(self.order) * 8


class CertifiedDecisionTree(RankedProbePolicy):
    def _build(self) -> int:
        scores = []
        for column in range(self.width):
            ones = sum(row[column] for row in self.rows)
            scores.append((min(ones, len(self.rows) - ones), column))
        self.order = tuple(column for _, column in sorted(scores, reverse=True))
        signature_count = len({tuple(row[column] for column in self.order) for row in self.rows})
        if signature_count != len(self.rows):
            raise ValueError("codebook is not identifiable")
        return len(self.rows) * (self.width + len(self.order))

    def fit(self, codebook: Codebook, universe_size: int, max_depth: int) -> None:
        super().fit(codebook, universe_size, max_depth)
        self.policy_build_ops = self._build()
        self.fit_ops += self.policy_build_ops

    def update(self, update: CodebookUpdate, target: object = None) -> None:
        changed = self._apply(update)
        self.policy_build_ops = self._build()
        self.update_ops = changed + self.policy_build_ops


class LearnedValueProbePolicy(CertifiedDecisionTree):
    select_cost = 2

    def _build(self) -> int:
        rewards = [0] * self.width
        for row in self.rows:  # simulated target episodes teach expected split reward
            for column, value in enumerate(row):
                rewards[column] += value
        self.values = tuple(min(value, len(self.rows) - value) for value in rewards)
        self.order = tuple(sorted(range(self.width), key=lambda col: (self.values[col], col), reverse=True))
        if len({tuple(row[column] for column in self.order) for row in self.rows}) != len(self.rows):
            raise ValueError("learned policy cannot identify the codebook")
        return 2 * len(self.rows) * self.width + self.width * self.width

    def state_bytes(self) -> int:
        return super().state_bytes() + len(self.values) * 8


class OracleTargetReader(NoProbeGuess):
    def query(self, wrapped: OracleBatch, steps: int) -> tuple[int, ...]:
        if not isinstance(wrapped, OracleBatch):
            raise TypeError("oracle requires hidden targets")
        self._record(0, 0, len(wrapped.targets), True)
        return wrapped.targets

