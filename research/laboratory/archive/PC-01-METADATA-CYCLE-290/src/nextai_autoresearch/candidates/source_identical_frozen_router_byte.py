from .conditional_execution_byte_core import Candidate as CoreCandidate


class Candidate(CoreCandidate):
    ROLE = "source_identical_frozen_router_byte"
    LEARN_ROUTER = False
