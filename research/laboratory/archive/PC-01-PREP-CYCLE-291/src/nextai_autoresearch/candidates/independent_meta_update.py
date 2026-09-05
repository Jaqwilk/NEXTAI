from .online_update_core import MetaUpdate


class Candidate(MetaUpdate):
    def __init__(self, seed=0):
        super().__init__(seed, independent=True)
