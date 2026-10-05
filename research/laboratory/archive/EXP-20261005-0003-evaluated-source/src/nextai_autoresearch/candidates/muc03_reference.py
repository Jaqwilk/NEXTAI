"""Unchanged MUC v2 transformer and hard sampler; fit length is bound by runner."""
from .muc02_core import LearnedSystem


class Candidate(LearnedSystem):
    mode = "bm25"
    negative_sampling = "hard"
