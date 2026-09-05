from .sparse_set_memory_core_v1 import SparseSetMemoryLearner


class Candidate(SparseSetMemoryLearner):
    MODE = "pooled_sparse_frozen_router"
