from .cross_family_learner_core import CrossFamilyLearner
class Candidate(CrossFamilyLearner):
    def __init__(self, seed=0): super().__init__(seed, "independent")
