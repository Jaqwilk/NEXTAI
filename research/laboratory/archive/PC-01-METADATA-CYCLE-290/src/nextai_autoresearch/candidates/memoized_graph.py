from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


class Candidate(CandidateBase):
    metadata = CandidateMetadata(
        name="memoized_graph",
        family="experience_compilation",
        description="Sparse graph that caches repeated complete reasoning paths.",
    )

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.successor: dict[int, int] = {}
        self.cache: dict[tuple[int, int], int | None] = {}

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.successor = dict(facts)
        self.cache = {}
        self.fit_ops = len(self.successor)

    def query(self, source: int, steps: int) -> int | None:
        key = (source, steps)
        if key in self.cache:
            self.last_ops = 1
            return self.cache[key]
        current = source
        operations = 0
        for _ in range(steps):
            operations += 1
            current = self.successor.get(current)
            if current is None:
                break
        self.cache[key] = current
        self.last_ops = operations
        return current

    def update(self, source: int, target: int) -> None:
        self.successor[source] = target
        # Conservative invalidation preserves correctness for arbitrary edge changes.
        invalidated = len(self.cache)
        self.cache = {}
        self.update_ops = 1 + invalidated

    def state_bytes(self) -> int:
        return 128 + len(self.successor) * 72 + len(self.cache) * 112

