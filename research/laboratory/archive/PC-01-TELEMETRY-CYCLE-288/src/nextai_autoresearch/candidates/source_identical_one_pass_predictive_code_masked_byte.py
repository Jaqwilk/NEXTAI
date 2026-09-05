from .local_sparse_predictive_code_core import Candidate as CoreCandidate


class Candidate(CoreCandidate):
    ROLE = "source_identical_one_pass_predictive_code_masked_byte"
