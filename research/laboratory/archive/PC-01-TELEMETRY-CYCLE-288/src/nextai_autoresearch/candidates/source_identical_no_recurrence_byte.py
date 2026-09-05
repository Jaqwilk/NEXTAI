from .orthogonal_reservoir_core import ReservoirByteLearner


class Candidate(ReservoirByteLearner):
    ROLE = "source_identical_no_recurrence_byte"
    RHO = 0.0
