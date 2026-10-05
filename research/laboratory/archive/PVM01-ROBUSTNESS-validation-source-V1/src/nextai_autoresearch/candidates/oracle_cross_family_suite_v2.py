from .cross_family_specialist_v2_core import SpecialistSuiteV2


class Candidate(SpecialistSuiteV2):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, probability_mode="oracle")
