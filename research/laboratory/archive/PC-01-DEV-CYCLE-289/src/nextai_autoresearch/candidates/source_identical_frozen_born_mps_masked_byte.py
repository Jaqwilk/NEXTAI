from .born_mps_masked_byte_core import Candidate as CoreCandidate


class Candidate(CoreCandidate):
    ROLE = "source_identical_frozen_born_mps_masked_byte"
    LEARN_TENSOR = False
