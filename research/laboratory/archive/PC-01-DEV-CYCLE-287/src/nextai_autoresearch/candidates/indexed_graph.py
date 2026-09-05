from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


class Candidate(CandidateBase):
    metadata = CandidateMetadata(
        name="indexed_graph",
        family="sparse_structured_memory",
        description="Hash-indexed successor memory with one local lookup per reasoning hop.",
    )

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.successor: dict[int, int] = {}

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.successor = dict(facts)
        self.fit_ops = len(self.successor)

    def query(self, source: int, steps: int) -> int | None:
        current = source
        operations = 0
        for _ in range(steps):
            operations += 1
            current = self.successor.get(current)
            if current is None:
                self.last_ops = operations
                return None
        self.last_ops = operations
        return current

    def update(self, source: int, target: int) -> None:
        self.successor[source] = target
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64 + len(self.successor) * 72

