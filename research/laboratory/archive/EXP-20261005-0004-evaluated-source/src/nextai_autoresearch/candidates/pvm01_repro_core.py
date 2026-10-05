"""Explicit reproducible FIT execution policy; the existing model is unchanged."""
import torch
from torch.nn.attention import SDPBackend, sdpa_kernel

from .pvm01_core import Candidate as Reference
from .pvm01_optimized_core import Candidate as Optimized


class Candidate(Optimized):
    def __init__(self, seed, arm, recipe):
        if arm not in {"dense", "dense_cached_cpu", "dense_cached_cuda"}:
            raise ValueError("Only existing dense and cached roles are supported")
        if arm == "dense":
            Reference.__init__(self, seed, arm, recipe)
            self.optimized_arm, self.projection = arm, None
        else:
            super().__init__(seed, arm, recipe)

    def fit(self, writes, queries, validation_writes, validation_queries, sets=None):
        deterministic = torch.are_deterministic_algorithms_enabled()
        warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
        try:
            torch.use_deterministic_algorithms(True)
            with sdpa_kernel(SDPBackend.MATH):
                if self.optimized_arm == "dense":
                    return Reference.fit(self, writes, queries, validation_writes, validation_queries, sets)
                return super().fit(writes, queries, validation_writes, validation_queries, sets)
        finally:
            torch.use_deterministic_algorithms(deterministic, warn_only=warn_only)
