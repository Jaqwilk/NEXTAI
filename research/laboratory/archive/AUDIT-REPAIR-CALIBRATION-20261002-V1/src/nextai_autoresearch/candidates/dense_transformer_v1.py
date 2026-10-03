from nextai_autoresearch.muc01_baseline_core import LearnedSystem


class Candidate(LearnedSystem):
    def __init__(self, seed, protocol):
        super().__init__(seed, protocol, retrieval=False)
