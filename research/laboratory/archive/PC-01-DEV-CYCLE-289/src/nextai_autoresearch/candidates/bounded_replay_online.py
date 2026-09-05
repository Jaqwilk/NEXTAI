from .online_update_core import KernelDictionary


class Candidate(KernelDictionary):
    def __init__(self, seed=0):
        super().__init__(seed, nearest=True)
