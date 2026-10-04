from .operator_algebra_core import OperatorAlgebraCandidate


class Candidate(OperatorAlgebraCandidate):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, mode="relations")
