from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


class Candidate(CandidateBase):
    metadata = CandidateMetadata(
        name="compiled_jump",
        family="compiled_reasoning",
        description="Binary-lifting table compiles repeated paths into logarithmic-depth queries.",
    )

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.levels: list[dict[int, int]] = []
        self.max_depth = 1

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        level_zero = dict(facts)
        self.levels = [level_zero]
        self.max_depth = max(1, max_depth)
        operations = len(level_zero)
        while (1 << len(self.levels)) <= self.max_depth:
            previous = self.levels[-1]
            current: dict[int, int] = {}
            for source, middle in previous.items():
                operations += 1
                target = previous.get(middle)
                if target is not None:
                    current[source] = target
            self.levels.append(current)
        self.fit_ops = operations

    def query(self, source: int, steps: int) -> int | None:
        current = source
        operations = 0
        bit = 0
        remaining = steps
        while remaining:
            if remaining & 1:
                operations += 1
                if bit >= len(self.levels):
                    self.last_ops = operations
                    return None
                current = self.levels[bit].get(current)
                if current is None:
                    self.last_ops = operations
                    return None
            remaining >>= 1
            bit += 1
        self.last_ops = operations
        return current

    def update(self, source: int, target: int) -> None:
        if not self.levels:
            self.levels = [{}]
        self.levels[0][source] = target
        operations = 1
        # Rebuild all compiled levels to preserve correctness after an arbitrary update.
        for level_index in range(1, len(self.levels)):
            previous = self.levels[level_index - 1]
            current: dict[int, int] = {}
            for left, middle in previous.items():
                operations += 1
                right = previous.get(middle)
                if right is not None:
                    current[left] = right
            self.levels[level_index] = current
        self.update_ops = operations

    def state_bytes(self) -> int:
        entries = sum(len(level) for level in self.levels)
        return 64 + entries * 72

