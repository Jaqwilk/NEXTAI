from .verified_incumbent_program_vm_core import VerifiedIncumbentProgramVM


class Candidate(VerifiedIncumbentProgramVM):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, "support")
