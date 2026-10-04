from .online_update_core import RLS


class Candidate(RLS):
    def __init__(self, seed=0):
        super().__init__(seed, polynomial=True)
