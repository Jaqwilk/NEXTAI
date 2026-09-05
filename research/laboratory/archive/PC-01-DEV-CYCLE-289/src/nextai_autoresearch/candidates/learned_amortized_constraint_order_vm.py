from .amortized_constraint_order_vm_core import AmortizedConstraintOrderVM


class Candidate(AmortizedConstraintOrderVM):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, "meta")
