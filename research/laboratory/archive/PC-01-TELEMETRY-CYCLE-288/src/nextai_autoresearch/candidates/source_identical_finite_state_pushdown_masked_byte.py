from .learned_pushdown_masked_byte_core import BOUNDED_DEPTH, Candidate as _Core


class Candidate(_Core):
    ROLE = "source_identical_finite_state_pushdown_masked_byte"
    STACK_LIMIT = BOUNDED_DEPTH
