from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Iterable

from .candidates.base import CandidateBase, CandidateMetadata


@dataclass(frozen=True)
class AttractorQuery:
    state: tuple[int, ...]


def _patterns(facts: Iterable[Any]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(bit) for bit in pattern) for pattern in facts)


class AttractorBase(CandidateBase):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.last_iterations = self.last_active_updates = self.last_bytes_scanned = 0
        self.last_energy_path: tuple[int, ...] = ()

    def _record(self, ops: int, reads: int = 0, iterations: int = 0, updates: int = 0, path: tuple[int, ...] = ()) -> None:
        self.last_ops, self.last_bytes_scanned = ops, reads
        self.last_iterations, self.last_active_updates = iterations, updates
        self.last_energy_path = path


class RandomAttractor(AttractorBase):
    metadata = CandidateMetadata("random_attractor_guess", "random", "Independent random output bits")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.rng = random.Random(self.seed)
        self.width, self.fit_ops = universe_size, 0

    def query(self, source: AttractorQuery, steps: int) -> tuple[int, ...]:
        answer = tuple(self.rng.randrange(2) for _ in source.state)
        self._record(len(answer))
        return answer

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64


class BitMajority(AttractorBase):
    metadata = CandidateMetadata("bit_majority_attractor", "heuristic", "Per-position training majority")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        patterns = _patterns(facts)
        self.count = len(patterns)
        self.ones = [sum(pattern[index] for pattern in patterns) for index in range(universe_size)]
        self.majority = tuple(int(2 * value > self.count) for value in self.ones)
        self.fit_ops = self.count * universe_size

    def query(self, source: AttractorQuery, steps: int) -> tuple[int, ...]:
        self._record(len(self.majority), len(self.majority))
        return self.majority

    def update(self, source: Any, target: int) -> None:
        pattern = tuple(source)
        self.count += 1
        for index, bit in enumerate(pattern):
            self.ones[index] += bit
        self.majority = tuple(int(2 * value > self.count) for value in self.ones)
        self.update_ops = 2 * len(pattern)

    def state_bytes(self) -> int:
        return 8 * len(self.ones) + len(self.majority)


class NearestStored(AttractorBase):
    metadata = CandidateMetadata("nearest_stored_attractor", "retrieval", "Exact whole-pattern nearest neighbour")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.patterns = _patterns(facts)
        self.fit_ops = len(self.patterns) * universe_size

    def query(self, source: AttractorQuery, steps: int) -> tuple[int, ...]:
        best = min(self.patterns, key=lambda pattern: sum(left != right for left, right in zip(source.state, pattern)))
        count = len(self.patterns) * len(source.state)
        self._record(2 * count, count)
        return best

    def update(self, source: Any, target: int) -> None:
        pattern = tuple(source)
        self.patterns += (pattern,)
        self.update_ops = len(pattern)

    def state_bytes(self) -> int:
        return sum(len(pattern) for pattern in self.patterns)


class ClassicalHopfield(AttractorBase):
    metadata = CandidateMetadata("classical_hopfield_attractor", "hopfield", "Dense Hebbian Hopfield relaxation")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        patterns = _patterns(facts)
        self.weights = [[0] * universe_size for _ in range(universe_size)]
        operations = 0
        for pattern in patterns:
            bipolar = [2 * bit - 1 for bit in pattern]
            operations += universe_size
            for left in range(universe_size):
                for right in range(left + 1, universe_size):
                    value = bipolar[left] * bipolar[right]
                    self.weights[left][right] += value
                    self.weights[right][left] += value
                    operations += 3
        self.fit_ops = operations

    def query(self, source: AttractorQuery, steps: int) -> tuple[int, ...]:
        bipolar = [2 * bit - 1 for bit in source.state]
        answer, operations = [], len(bipolar)
        for index, row in enumerate(self.weights):
            field = 0
            for other, weight in enumerate(row):
                field += weight * bipolar[other]
                operations += 2
            answer.append(int(field > 0) if field else source.state[index])
            operations += 1
        result = tuple(answer)
        updates = sum(left != right for left, right in zip(source.state, result))
        self._record(operations, 8 * len(bipolar) ** 2, 1, updates)
        return result

    def update(self, source: Any, target: int) -> None:
        pattern = tuple(source)
        bipolar = [2 * bit - 1 for bit in pattern]
        operations = len(pattern)
        for left in range(len(pattern)):
            for right in range(left + 1, len(pattern)):
                value = bipolar[left] * bipolar[right]
                self.weights[left][right] += value
                self.weights[right][left] += value
                operations += 3
        self.update_ops = operations

    def state_bytes(self) -> int:
        return 8 * sum(len(row) for row in self.weights)


def learn_components(patterns: tuple[tuple[int, ...], ...]) -> tuple[tuple[tuple[int, int], ...], int]:
    width, operations = len(patterns[0]), 0
    neighbours = [[] for _ in range(width)]
    for left in range(width):
        for right in range(left + 1, width):
            parity = patterns[0][left] ^ patterns[0][right]
            stable = True
            for pattern in patterns:
                stable &= (pattern[left] ^ pattern[right]) == parity
                operations += 2
            if stable:
                neighbours[left].append(right)
                neighbours[right].append(left)
    components, seen = [], set()
    for root in range(width):
        if root in seen:
            continue
        stack, members = [root], []
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            members.append(node)
            stack.extend(neighbours[node])
        components.append(tuple((node, patterns[0][root] ^ patterns[0][node]) for node in sorted(members)))
    return tuple(components), operations


def learn_robust_components(
    patterns: tuple[tuple[int, ...], ...], threshold: float = 0.70
) -> tuple[tuple[tuple[int, int], ...], int]:
    """Cluster bits whose majority parity clears a preregistered noise gap."""
    width, count, operations = len(patterns[0]), len(patterns), 0
    neighbours = [[] for _ in range(width)]
    parities: dict[tuple[int, int], int] = {}
    for left in range(width):
        for right in range(left + 1, width):
            different = sum(pattern[left] ^ pattern[right] for pattern in patterns)
            agreement = max(different, count - different) / count
            operations += 3 * count + 2
            if agreement >= threshold:
                parity = int(2 * different > count)
                neighbours[left].append(right)
                neighbours[right].append(left)
                parities[left, right] = parity
    components, seen = [], set()
    for root in range(width):
        if root in seen:
            continue
        stack, members = [root], []
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            members.append(node)
            stack.extend(neighbours[node])
        members.sort()
        anchor = members[0]
        component = [(anchor, 0)]
        for node in members[1:]:
            component.append((node, parities[min(anchor, node), max(anchor, node)]))
        components.append(tuple(component))
    return tuple(components), operations


def energy(state: list[int] | tuple[int, ...], components: tuple[tuple[tuple[int, int], ...], ...]) -> tuple[int, int, int]:
    total = operations = reads = 0
    for component in components:
        ones = 0
        for position, parity in component:
            ones += state[position] ^ parity
            operations += 2
            reads += 2
        total += min(ones, len(component) - ones)
        operations += 2
    return total, operations, reads


class LearnedEnergyBase(AttractorBase):
    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        patterns = _patterns(facts)
        self.components, self.fit_ops = learn_components(patterns)

    def update(self, source: Any, target: int) -> None:
        pattern = tuple(source)
        self.update_ops = sum(2 * len(component) for component in self.components)
        for component in self.components:
            root, root_parity = component[0]
            root_value = pattern[root] ^ root_parity
            if any((pattern[position] ^ parity) != root_value for position, parity in component):
                self.update_ops += len(component)

    def state_bytes(self) -> int:
        return 16 * sum(len(component) for component in self.components)


class SequentialEnergy(LearnedEnergyBase):
    metadata = CandidateMetadata("sequential_energy_repair", "energy", "Greedy one-bit energy descent")

    def query(self, source: AttractorQuery, steps: int) -> tuple[int, ...]:
        state = list(source.state)
        current, operations, reads = energy(state, self.components)
        path, updates = [current], 0
        while current and updates < len(state):
            best_index, best_energy = None, current
            for index in range(len(state)):
                state[index] ^= 1
                candidate, extra_ops, extra_reads = energy(state, self.components)
                operations += extra_ops + 2
                reads += extra_reads + 1
                state[index] ^= 1
                if candidate < best_energy:
                    best_index, best_energy = index, candidate
            if best_index is None:
                break
            state[best_index] ^= 1
            current, updates = best_energy, updates + 1
            path.append(current)
        self._record(operations, reads, updates, updates, tuple(path))
        return tuple(state)


class ParallelEnergy(LearnedEnergyBase):
    metadata = CandidateMetadata("learned_parallel_energy", "energy", "Learned factored energy with synchronous component cleanup")

    def query(self, source: AttractorQuery, steps: int) -> tuple[int, ...]:
        answer, operations, reads, before = list(source.state), 0, 0, 0
        for component in self.components:
            normalized = []
            for position, parity in component:
                normalized.append(source.state[position] ^ parity)
                operations += 2
                reads += 2
            latent = int(2 * sum(normalized) > len(normalized))
            before += min(sum(normalized), len(normalized) - sum(normalized))
            operations += len(normalized) + 4
            for position, parity in component:
                answer[position] = latent ^ parity
                operations += 2
                reads += 1
        result = tuple(answer)
        updates = sum(left != right for left, right in zip(source.state, result))
        self._record(operations, reads, int(bool(before)), updates, (before, 0))
        return result


class OracleEnergy(ParallelEnergy):
    metadata = CandidateMetadata("oracle_relational_energy", "oracle", "True latent component energy")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.components = tuple(tuple((int(position), int(parity)) for position, parity in component) for component in tuple(facts)[0])
        self.fit_ops = 0


class RobustParallelEnergy(ParallelEnergy):
    metadata = CandidateMetadata("robust_parallel_energy", "energy", "Robust factored energy with synchronous cleanup")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.components, self.fit_ops = learn_robust_components(_patterns(facts))


class IncrementalSequentialEnergy(RobustParallelEnergy):
    metadata = CandidateMetadata("incremental_sequential_energy", "energy", "Incremental one-bit schedule on robust factored energy")

    def query(self, source: AttractorQuery, steps: int) -> tuple[int, ...]:
        answer, mismatches, operations, reads = list(source.state), [], 0, 0
        for component in self.components:
            normalized = []
            for position, parity in component:
                normalized.append(source.state[position] ^ parity)
                operations += 2
                reads += 2
            latent = int(2 * sum(normalized) > len(normalized))
            operations += len(normalized) + 4
            for (position, parity), value in zip(component, normalized):
                operations += 1
                if value != latent:
                    mismatches.append((position, latent ^ parity))
        path = [len(mismatches)]
        for position, value in mismatches:
            answer[position] = value
            operations += 2
            reads += 1
            path.append(path[-1] - 1)
        self._record(operations, reads, len(mismatches), len(mismatches), tuple(path))
        return tuple(answer)
