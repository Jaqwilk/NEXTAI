from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


class Candidate(CandidateBase):
    metadata = CandidateMetadata(
        "fixed_max_indexed", "fixed_compute_control", "Always uses the maximum depth."
    )

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.successor: dict[int, int] = {}
        self.depth = 0

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.successor, self.depth = dict(facts), max_depth
        self.fit_ops = len(self.successor)

    def query(self, source: int, steps: int) -> int | None:
        current = source
        for _ in range(self.depth):
            current = self.successor.get(current)
            if current is None:
                break
        self.last_ops = self.depth
        return current

    def update(self, source: int, target: int) -> None:
        self.successor[source] = target
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 72 * len(self.successor) + 64
