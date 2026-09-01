from .invariant_residual_module_core import Candidate as Core


class Candidate(Core):
    def __init__(self, seed: int) -> None:
        super().__init__(seed, mode="pooled")
