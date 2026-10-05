"""Existing learned transport, training-only PCA, and exact CPU record reads."""
import hashlib
import time

import numpy as np
import torch
from torch.nn.attention import SDPBackend, sdpa_kernel

from .pvm01_core import Candidate as Reference, unit
from .pvm01_optimized_core import RidgeSession


class Candidate(Reference):
    def __init__(self, seed, arm, recipe):
        base = {"transport_pca": "exact_nn", "transport_full": "exact_nn",
                "transport_pca_untrained": "untrained", "transport_pca_shuffled": "shuffled"}
        if arm not in base:
            raise ValueError("Unknown transport compression arm")
        self.transport_arm, self.projection = arm, None
        super().__init__(seed, base[arm], recipe)

    def synchronize(self):
        if self.device.type == "cuda":
            torch.cuda.synchronize()

    def fit(self, writes, queries, validation_writes, validation_queries, sets=None):
        deterministic = torch.are_deterministic_algorithms_enabled()
        warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
        try:
            torch.use_deterministic_algorithms(True)
            with sdpa_kernel(SDPBackend.MATH):
                report = super().fit(writes, queries, validation_writes, validation_queries, sets)
        finally:
            torch.use_deterministic_algorithms(deterministic, warn_only=warn_only)
        tick = time.perf_counter()
        self.model = self.model.to("cpu")
        self.device, self.arm = torch.device("cpu"), self.transport_arm
        if self.arm != "transport_full":
            _, singular, vectors = np.linalg.svd(unit(writes.astype(np.float64)), full_matrices=False)
            energy = np.cumsum(singular ** 2) / np.sum(singular ** 2)
            grid = [{"rank": rank, "retained_variance": float(energy[rank - 1])}
                    for rank in self.recipe["transport_pca_rank_grid"]]
            chosen = next((row for row in grid if row["retained_variance"] >= self.recipe["transport_pca_variance_fraction"]), grid[-1])
            self.projection = vectors[:chosen["rank"]].T.astype(np.float32).copy()
            report.update(pca_grid=grid, pca_choice=chosen,
                          pca_projection_sha256=hashlib.sha256(self.projection.tobytes()).hexdigest())
            self.fit_operations_estimate += 2 * len(writes) * 64 ** 2 + 64 ** 3
        self.fit_seconds += time.perf_counter() - tick
        report.update(arm=self.arm, fit_seconds=self.fit_seconds, inference_device="cpu",
                      precision="float32 neural/records/projection; float64 PCA fit",
                      fit_operations_estimate=self.fit_operations_estimate)
        return report

    def new_session(self, size):
        return TransportSession(self, size)

    def state_bytes(self):
        return super().state_bytes() + (0 if self.projection is None else self.projection.nbytes)


class TransportSession(RidgeSession):
    def read(self, observation):
        if observation.shape != (64,) or observation.dtype != np.float32:
            raise ValueError("Malformed legal query")
        with torch.inference_mode():
            projected = self.system.model(torch.as_tensor(observation)).numpy()
        if self.system.projection is not None:
            projected = projected @ self.system.projection
        embedded = unit(projected)
        index = int(np.argmax(self.keys[:len(self.handles)] @ embedded))
        return self.handles[index], float(self.keys[index] @ embedded), int(self.values[index])
