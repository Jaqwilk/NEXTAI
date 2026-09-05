from .cross_family_specialist_core import SpecialistSuite
class Candidate(SpecialistSuite):
    def __init__(self, seed=0): super().__init__(seed, "joint")
