from .cross_family_pointer_core import PointerCrossFamilyLearner


class Candidate(PointerCrossFamilyLearner):
    def __init__(self, seed=0):
        super().__init__(seed, independent=True)
