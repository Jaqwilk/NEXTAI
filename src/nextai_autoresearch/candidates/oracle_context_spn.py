from .probabilistic_circuit_core import ProbabilisticCircuitCandidate

class Candidate(ProbabilisticCircuitCandidate):
    def __init__(self, seed: int): super().__init__(seed, "oracle")
