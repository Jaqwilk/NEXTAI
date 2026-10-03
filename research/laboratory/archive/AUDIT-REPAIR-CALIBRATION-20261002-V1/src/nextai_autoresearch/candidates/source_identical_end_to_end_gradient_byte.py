from .layer_local_goodness_core import GoodnessByteLearner


class Candidate(GoodnessByteLearner):
    ROLE = "global_credit"
