from .surprise_transition_machine_byte_core import Candidate as CoreCandidate


class Candidate(CoreCandidate):
    ROLE = "source_identical_dense_transition_machine_byte"
    CLOCK = "dense"
