from __future__ import annotations

import random
from dataclasses import dataclass

from nextai_autoresearch.attractor_core import ClassicalHopfield
from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


@dataclass(frozen=True)
class ParityQuery:
    state: tuple[int, ...]


def as_int(bits: tuple[int, ...]) -> int:
    return sum(int(bit) << index for index, bit in enumerate(bits))


def as_bits(value: int, width: int) -> tuple[int, ...]:
    return tuple((value >> index) & 1 for index in range(width))


class RandomParity(CandidateBase):
    metadata = CandidateMetadata("random_parity_guess", "random_control", "Seeded random bit-vector control.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.width, self.fit_ops = universe_size, 0

    def query(self, source: ParityQuery, steps: int) -> tuple[int, ...]:
        rng = random.Random(self.seed ^ as_int(source.state) ^ steps)
        self.last_ops, self.last_bytes_scanned = self.width, self.width
        self.last_iterations = self.last_active_updates = 0
        return tuple(rng.randrange(2) for _ in range(self.width))

    def update(self, source, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 128


class NearestCodeMemory(CandidateBase):
    metadata = CandidateMetadata("nearest_code_memory", "retrieval_control", "Nearest stored training codeword.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.width = universe_size
        self.codes = tuple(as_int(tuple(pattern)) for pattern in facts)
        self.fit_ops = len(self.codes) * self.width

    def query(self, source: ParityQuery, steps: int) -> tuple[int, ...]:
        value = as_int(source.state)
        answer = min(self.codes, key=lambda code: (code ^ value).bit_count())
        self.last_ops = 2 * len(self.codes) * self.width
        self.last_bytes_scanned = len(self.codes) * ((self.width + 7) // 8)
        self.last_iterations, self.last_active_updates = 1, 0
        return as_bits(answer, self.width)

    def update(self, source, target: int) -> None:
        self.codes += (as_int(tuple(source)),)
        self.update_ops = self.width

    def state_bytes(self) -> int:
        return 256 + len(self.codes) * ((self.width + 7) // 8)


class HopfieldParity(ClassicalHopfield):
    metadata = CandidateMetadata("classical_hopfield_parity", "hopfield_control", "Dense Hebbian retrieval on raw codewords.")


class ExactAffineSpan(CandidateBase):
    metadata = CandidateMetadata("exact_affine_span_decoder", "exact_constraint_control", "Learned affine span plus exact minimum-distance decoding.")

    def _insert(self, vector: int) -> int:
        operations = 0
        while vector:
            pivot = vector.bit_length() - 1
            if pivot not in self.basis:
                self.basis[pivot] = vector
                break
            vector ^= self.basis[pivot]
            operations += self.width
        return operations

    def _rebuild(self) -> int:
        self.codes = [self.origin]
        operations = 0
        for vector in self.basis.values():
            self.codes += [code ^ vector for code in self.codes]
            operations += len(self.codes) * self.width
        return operations

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.width = universe_size
        values = [as_int(tuple(pattern)) for pattern in facts]
        self.origin, self.basis = values[0], {}
        operations = len(values) * self.width
        for value in values[1:]:
            operations += self._insert(value ^ self.origin)
        self.fit_ops = operations + self._rebuild()
        self.affine_rank = len(self.basis)

    def query(self, source: ParityQuery, steps: int) -> tuple[int, ...]:
        value = as_int(source.state)
        answer = min(self.codes, key=lambda code: (code ^ value).bit_count())
        self.last_ops = len(self.codes) * (self.width + 2)
        self.last_bytes_scanned = len(self.codes) * ((self.width + 7) // 8)
        self.last_iterations, self.last_active_updates = 1, 0
        return as_bits(answer, self.width)

    def update(self, source, target: int) -> None:
        changed = len(self.basis)
        operations = self._insert(as_int(tuple(source)) ^ self.origin)
        if len(self.basis) != changed:
            operations += self._rebuild()
        self.affine_rank = len(self.basis)
        self.update_ops = operations + self.width

    def state_bytes(self) -> int:
        word = (self.width + 7) // 8
        return 256 + word * (len(self.codes) + len(self.basis) + 1)


def learn_factors(patterns: tuple[tuple[int, ...], ...]) -> tuple[tuple[tuple[int, int, int, int], ...], int]:
    width, factors, operations = len(patterns[0]), [], 0
    for left in range(width):
        for middle in range(left + 1, width):
            for right in range(middle + 1, width):
                parity = patterns[0][left] ^ patterns[0][middle] ^ patterns[0][right]
                stable = True
                for pattern in patterns[1:]:
                    stable &= (pattern[left] ^ pattern[middle] ^ pattern[right]) == parity
                    operations += 4
                if stable:
                    factors.append((left, middle, right, parity))
    return tuple(factors), operations


class FactorEnergyBase(CandidateBase):
    metadata = CandidateMetadata("factor_energy", "energy", "Learned overlapping parity energy.")

    def _prepare(self) -> None:
        self.degrees = [0] * self.width
        for left, middle, right, _ in self.factors:
            self.degrees[left] += 1
            self.degrees[middle] += 1
            self.degrees[right] += 1
        self.factor_count = len(self.factors)
        self.factor_signature = float(sum((left + 1) * 3 + (middle + 1) * 5 + (right + 1) * 7 + parity
                                          for left, middle, right, parity in self.factors))

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.width = universe_size
        self.factors, self.fit_ops = learn_factors(tuple(tuple(pattern) for pattern in facts))
        self._prepare()

    def _scan(self, state: list[int] | tuple[int, ...]):
        violations, energy, operations = [0] * self.width, 0, 0
        for left, middle, right, parity in self.factors:
            unsatisfied = state[left] ^ state[middle] ^ state[right] ^ parity
            operations += 4
            if unsatisfied:
                energy += 1
                violations[left] += 1
                violations[middle] += 1
                violations[right] += 1
                operations += 4
        return violations, energy, operations

    def update(self, source, target: int) -> None:
        pattern = tuple(source)
        kept = tuple(factor for factor in self.factors
                     if pattern[factor[0]] ^ pattern[factor[1]] ^ pattern[factor[2]] == factor[3])
        self.update_ops = 4 * len(self.factors)
        if len(kept) != len(self.factors):
            self.factors = kept
            self._prepare()

    def state_bytes(self) -> int:
        return 256 + 16 * len(self.factors) + 4 * len(self.degrees)


class SequentialFactorEnergy(FactorEnergyBase):
    metadata = CandidateMetadata("sequential_factor_energy", "classical_bitflip_control", "Greedy one-bit parity-energy descent.")

    def query(self, source: ParityQuery, steps: int) -> tuple[int, ...]:
        state, operations, path, updates = list(source.state), 0, [], 0
        for _ in range(steps):
            violations, current, extra = self._scan(state)
            operations += extra + 2 * self.width
            path.append(current)
            improvements = [2 * count - degree for count, degree in zip(violations, self.degrees)]
            best = max(range(self.width), key=improvements.__getitem__)
            if current == 0 or improvements[best] <= 0:
                break
            state[best] ^= 1
            updates += 1
            path.append(current - improvements[best])
        self.last_ops, self.last_bytes_scanned = operations, len(self.factors) * 3 * max(1, updates)
        self.last_iterations, self.last_active_updates, self.last_energy_path = updates, updates, tuple(path)
        return tuple(state)


class ParallelParityEnergy(FactorEnergyBase):
    metadata = CandidateMetadata("learned_parallel_parity_energy", "learned_energy", "One synchronous learned parity-energy relaxation.")

    def query(self, source: ParityQuery, steps: int) -> tuple[int, ...]:
        state = list(source.state)
        violations, current, operations = self._scan(state)
        flips = [index for index, (count, degree) in enumerate(zip(violations, self.degrees))
                 if 2 * count > degree]
        for index in flips:
            state[index] ^= 1
        self.last_ops = operations + 2 * self.width + len(flips)
        self.last_bytes_scanned = len(self.factors) * 3
        self.last_iterations, self.last_active_updates = 1, len(flips)
        self.last_energy_path = (current,)
        return tuple(state)


class OracleParallelParityEnergy(ParallelParityEnergy):
    metadata = CandidateMetadata("oracle_parallel_parity_energy", "oracle_control", "True-factor one-round parity relaxation.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.width = universe_size
        self.factors = tuple(tuple(map(int, factor)) for factor in tuple(facts)[0])
        self.fit_ops = 0
        self._prepare()
