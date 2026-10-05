from .mechanism_recombination_core import RecombinationCandidate


class Candidate(RecombinationCandidate):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, mode="markov")
