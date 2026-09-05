from .population_local_rule_core import PopulationLocalRule


class Candidate(PopulationLocalRule):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, mode="true")
