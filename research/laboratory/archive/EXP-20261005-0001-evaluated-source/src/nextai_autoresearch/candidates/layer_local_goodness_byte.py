from .layer_local_goodness_core import GoodnessByteLearner


class Candidate(GoodnessByteLearner):
    ROLE = "layer_local"
