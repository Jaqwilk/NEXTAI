from .continuous_local_rule_core import ContinuousLocalRule


class Candidate(ContinuousLocalRule):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, mode="dense")
