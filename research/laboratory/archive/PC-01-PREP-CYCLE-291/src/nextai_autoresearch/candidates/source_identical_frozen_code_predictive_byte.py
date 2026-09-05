from .local_sparse_predictive_code_core import Candidate as CoreCandidate


class Candidate(CoreCandidate):
    ROLE = "source_identical_frozen_code_predictive_byte"
    LEARN_CODE = False
