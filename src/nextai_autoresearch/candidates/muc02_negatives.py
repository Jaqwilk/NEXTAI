"""Same MUC v2 BM25 pair reader; only training mismatch distribution varies."""
from .muc02_core import LearnedSystem


class Candidate(LearnedSystem):
    mode = "bm25"

    def __init__(self, seed, protocol):
        self.negative_sampling = protocol["negative_arm"]
        if self.negative_sampling not in {"random", "hard"}:
            raise ValueError("Unregistered negative arm")
        super().__init__(seed, protocol)
