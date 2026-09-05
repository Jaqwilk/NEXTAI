from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


class Candidate(CandidateBase):
    metadata = CandidateMetadata(
        "fixed_short_indexed", "fixed_compute_control", "Always uses four steps."
    )

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.successor: dict[int, int] = {}

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.successor = dict(facts)
        self.fit_ops = len(self.successor)

    def query(self, source: int, steps: int) -> int | None:
        current = source
        for _ in range(4):
            current = self.successor.get(current)
            if current is None:
                break
        self.last_ops = 4
        return current

    def update(self, source: int, target: int) -> None:
        self.successor[source] = target
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 72 * len(self.successor) + 64
