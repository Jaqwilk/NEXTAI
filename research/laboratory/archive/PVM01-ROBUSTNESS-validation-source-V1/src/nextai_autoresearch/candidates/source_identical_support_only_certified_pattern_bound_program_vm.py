from .certified_pattern_bound_program_vm_core import CertifiedPatternBoundProgramVM


class Candidate(CertifiedPatternBoundProgramVM):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, "support")
