from .relation_fragment_core import RelationFragmentGraphLearner


class Candidate(RelationFragmentGraphLearner):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, mode="independent")
