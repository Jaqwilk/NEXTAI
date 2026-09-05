from .local_expert_tree_core import LocalExpertTree


class Candidate(LocalExpertTree):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, mode="frozen")
