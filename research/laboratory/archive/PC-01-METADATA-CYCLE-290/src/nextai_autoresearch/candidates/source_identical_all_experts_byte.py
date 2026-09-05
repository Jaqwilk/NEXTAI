from .conditional_execution_byte_core import EXPERTS, Candidate as CoreCandidate


class Candidate(CoreCandidate):
    ROLE = "source_identical_all_experts_byte"
    ACTIVE_EXPERTS = EXPERTS
