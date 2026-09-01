from .dyadic_lifted_local_core import DyadicLiftedLocal


class Candidate(DyadicLiftedLocal):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, mode="dyadic")
