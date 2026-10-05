import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


class Candidate(CandidateBase):
    metadata = CandidateMetadata(
        name="vsa_superposition",
        family="hyperdimensional_computing",
        description=(
            "Fixed-width bipolar VSA: directed successor bindings are superposed "
            "and recovered by exhaustive codebook cleanup."
        ),
    )

    dimension = 2048

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.rng = np.random.default_rng(seed)
        self.codebook = np.zeros((0, self.dimension), dtype=np.int8)
        self.memory = np.zeros(self.dimension, dtype=np.int32)

    def _generate_codes(self, count: int) -> np.ndarray:
        if count <= 0:
            return np.zeros((0, self.dimension), dtype=np.int8)
        bits = self.rng.integers(
            0, 2, size=(count, self.dimension), dtype=np.int8
        )
        return bits * np.int8(2) - np.int8(1)

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.rng = np.random.default_rng(self.seed)
        self.codebook = self._generate_codes(universe_size)
        self.memory = np.zeros(self.dimension, dtype=np.int32)
        fact_list = list(facts)
        if fact_list:
            sources = np.fromiter(
                (source for source, _ in fact_list), dtype=np.int64
            )
            targets = np.fromiter(
                (target for _, target in fact_list), dtype=np.int64
            )
            # Rolling the source vector creates a role-specific code so that
            # directed (a -> b) and (b -> a) bindings are not identical.
            source_roles = np.roll(self.codebook[sources], 1, axis=1)
            bindings = source_roles * self.codebook[targets]
            self.memory = bindings.sum(axis=0, dtype=np.int32)
        count = len(fact_list)
        self.fit_ops = universe_size * self.dimension + 3 * count * self.dimension

    def query(self, source: int, steps: int) -> int | None:
        size = int(self.codebook.shape[0])
        if source < 0 or source >= size or steps < 0:
            self.last_ops = 1
            return None
        current = int(source)
        operations = 0
        for _ in range(steps):
            source_role = np.roll(self.codebook[current], 1).astype(
                np.int32, copy=False
            )
            retrieved = source_role * self.memory
            scores = self.codebook @ retrieved
            current = int(np.argmax(scores))
            # Role construction + unbinding + K dot products + argmax.
            operations += (
                2 * self.dimension
                + size * (2 * self.dimension - 1)
                + size
            )
        self.last_ops = operations
        return current

    def update(self, source: int, target: int) -> None:
        old_size = int(self.codebook.shape[0])
        new_size = max(old_size, source + 1, target + 1)
        generated = new_size - old_size
        if generated:
            self.codebook = np.vstack(
                (self.codebook, self._generate_codes(generated))
            )
        source_role = np.roll(self.codebook[source], 1).astype(
            np.int32, copy=False
        )
        binding = source_role * self.codebook[target].astype(
            np.int32, copy=False
        )
        # This prototype supports append-only superposition. Replacing an old
        # fact would require subtracting its old binding, tested in a later
        # dependency/update benchmark rather than hidden in this candidate.
        self.memory += binding
        self.update_ops = generated * self.dimension + 3 * self.dimension

    def state_bytes(self) -> int:
        return int(self.codebook.nbytes + self.memory.nbytes + 256)

