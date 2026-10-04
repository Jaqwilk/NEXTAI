from .tensor_baseline_core import TensorBaseline


class Candidate(TensorBaseline):
    def __init__(self, seed: int) -> None:
        super().__init__(seed, "autoregressive")
