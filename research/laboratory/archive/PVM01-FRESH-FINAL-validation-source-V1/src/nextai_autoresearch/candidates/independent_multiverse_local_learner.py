from .multiverse_local_core import MultiverseLocalLearner


class Candidate(MultiverseLocalLearner):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, mode="independent")
