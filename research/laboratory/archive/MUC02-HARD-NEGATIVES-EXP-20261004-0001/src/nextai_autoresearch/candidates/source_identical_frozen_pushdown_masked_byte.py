from .learned_pushdown_masked_byte_core import Candidate as _Core


class Candidate(_Core):
    ROLE = "source_identical_frozen_pushdown_masked_byte"
    MODE = "frozen"
