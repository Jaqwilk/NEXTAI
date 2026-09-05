from .tensor_indexed_local_operator_core import IndexedLocalOperator


class Candidate(IndexedLocalOperator):
    def __init__(self, seed: int) -> None:
        super().__init__(seed, "raw")

