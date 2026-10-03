from .conjugacy_library_core import ConjugacyCandidate
class Candidate(ConjugacyCandidate):
    def __init__(self, seed=0): super().__init__(seed, "primitive")
