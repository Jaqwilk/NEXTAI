from __future__ import annotations

import random
from typing import Any, Iterable

from .candidates.base import CandidateBase, CandidateMetadata


def neighbors(cell: int, side: int) -> tuple[int, ...]:
    row, column = divmod(cell, side)
    return tuple(
        next_row * side + next_column
        for next_row in range(max(0, row - 1), min(side, row + 2))
        for next_column in range(max(0, column - 1), min(side, column + 2))
        if (next_row, next_column) != (row, column)
    )


class LearnedRule(CandidateBase):
    metadata = CandidateMetadata("learned_local_rule", "cellular", "Learned local AND rule")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.weights = [0, 0, 0]
        self.peak_work_items = 0
        self.last_cell_updates = 0

    def _prediction(self, features: tuple[int, int]) -> int:
        vector = (1, *features)
        return int(sum(weight * value for weight, value in zip(self.weights, vector)) >= 0)

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        cases = tuple(facts)
        self.fit_ops = 0
        for _ in range(32):
            errors = 0
            for features, target in cases:
                prediction = self._prediction(features)
                self.fit_ops += 6
                delta = int(target) - prediction
                if delta:
                    vector = (1, *features)
                    self.weights = [
                        weight + delta * value
                        for weight, value in zip(self.weights, vector)
                    ]
                    self.fit_ops += 3
                    errors += 1
            if errors == 0:
                return
        raise RuntimeError("local rule did not converge")

    def update(self, source: Any, target: int) -> None:
        features = tuple(source)
        delta = int(target) - self._prediction(features)
        self.update_ops = 6
        if delta:
            vector = (1, *features)
            self.weights = [
                weight + delta * value for weight, value in zip(self.weights, vector)
            ]
            self.update_ops += 3

    def state_bytes(self) -> int:
        return 88 + 16 * self.peak_work_items

    def _fires(self, open_cell: int, active_neighbor: int) -> bool:
        return bool(self._prediction((open_cell, active_neighbor)))


class LearnedSynchronous(LearnedRule):
    def query(self, source: Any, steps: int) -> bool:
        task = source
        active = {task.source}
        operations = 0
        self.last_cell_updates = 0
        for _ in range(steps):
            next_active = set(active)
            for cell, open_cell in enumerate(task.cells):
                operations += 1
                self.last_cell_updates += 1
                if not open_cell or cell in active:
                    continue
                active_neighbor = 0
                for neighbor in neighbors(cell, task.side):
                    operations += 1
                    if neighbor in active:
                        active_neighbor = 1
                        break
                operations += 6
                if self._fires(1, active_neighbor):
                    next_active.add(cell)
            active = next_active
            self.peak_work_items = max(self.peak_work_items, len(active) + len(next_active))
        self.last_ops = operations
        return any(goal in active for goal in task.goals)


def _event_query(candidate: Any, task: Any, steps: int, *, learned: bool) -> bool:
    active = {task.source}
    frontier = {task.source}
    operations = 0
    candidate.last_cell_updates = 0
    for _ in range(steps):
        pending: set[int] = set()
        for cell in frontier:
            operations += 1
            candidate.last_cell_updates += 1
            for neighbor in neighbors(cell, task.side):
                operations += 3
                if not task.cells[neighbor] or neighbor in active or neighbor in pending:
                    continue
                if learned:
                    operations += 6
                    if not candidate._fires(1, 1):
                        continue
                pending.add(neighbor)
        active.update(pending)
        frontier = pending
        candidate.peak_work_items = max(
            candidate.peak_work_items, len(active) + len(frontier)
        )
        if not frontier:
            break
    candidate.last_ops = operations
    return any(goal in active for goal in task.goals)


class LearnedEventQueue(LearnedRule):
    def query(self, source: Any, steps: int) -> bool:
        return _event_query(self, source, steps, learned=True)


class OracleEventQueue(CandidateBase):
    metadata = CandidateMetadata("oracle_event_queue", "cellular", "Oracle local event queue")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.peak_work_items = 0
        self.last_cell_updates = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0

    def query(self, source: Any, steps: int) -> bool:
        return _event_query(self, source, steps, learned=False)

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64 + 16 * self.peak_work_items


class SparseGridBFS(OracleEventQueue):
    metadata = CandidateMetadata("sparse_grid_bfs", "graph", "Sparse causal-region BFS")


class RandomCellularGuess(CandidateBase):
    metadata = CandidateMetadata("random_cellular_guess", "random", "Random Boolean control")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.rng = random.Random(seed)
        self.last_cell_updates = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0

    def query(self, source: Any, steps: int) -> bool:
        self.last_ops = 1
        self.last_cell_updates = 0
        return bool(self.rng.randrange(2))

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64
