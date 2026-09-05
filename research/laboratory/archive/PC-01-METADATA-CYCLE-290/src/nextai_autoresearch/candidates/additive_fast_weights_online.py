from .online_update_core import LMS


class Candidate(LMS):
    def __init__(self, seed=0):
        super().__init__(seed, additive=True, polynomial=True)
