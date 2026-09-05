from random import Random

from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


class Candidate(CandidateBase):
    metadata = CandidateMetadata(
        name="random_guess",
        family="negative_control",
        description="Uniform random answer; detects broken or trivial evaluation.",
    )

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.rng = Random(seed)
        self.universe_size = 0

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.universe_size = universe_size
        self.fit_ops = 0

    def query(self, source: int, steps: int) -> int | None:
        self.last_ops = 1
        if self.universe_size <= 0:
            return None
        return self.rng.randrange(self.universe_size)

    def update(self, source: int, target: int) -> None:
        self.universe_size = max(self.universe_size, source + 1, target + 1)
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64

