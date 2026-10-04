from .orthogonal_reservoir_core import ReservoirByteLearner


class Candidate(ReservoirByteLearner):
    ROLE = "source_identical_frozen_readout_reservoir_byte"
    TRAIN_READOUT = False
