"""Preregistered learned transport with classical RFF delta/additive memory."""
import hashlib
import time

import numpy as np
import torch
from torch.nn import functional as F

from .pvm01_core import Candidate as Reference, unit


class Candidate(Reference):
    def __init__(self, seed, arm, recipe):
        self.memory_arm = arm
        transport_arm = {"delta_untrained": "untrained",
                         "delta_shuffled": "shuffled"}.get(arm, "pointer")
        if arm not in {"delta", "additive", "delta_untrained", "delta_shuffled"}:
            raise ValueError("Unknown compact memory arm")
        super().__init__(seed, transport_arm, recipe)
        count = recipe["memory_frequencies"]
        if recipe["memory_feature_dimension"] != 2 * count:
            raise ValueError("RFF dimension mismatch")
        rng = np.random.default_rng(seed ^ recipe["memory_projection_seed_xor"])
        self.projection = rng.normal(
            0, 1 / recipe["memory_bandwidth"], (64, count)).astype(np.float32)
        self.feature_scale = np.float32(1 / np.sqrt(count))
        self.feature_hash = hashlib.sha256(self.projection.tobytes()).hexdigest()

    def synchronize(self):
        if self.device.type == "cuda":
            torch.cuda.synchronize()

    def fit(self, *args, **kwargs):
        report = super().fit(*args, **kwargs)
        tick = time.perf_counter()
        self.model = self.model.to("cpu").eval()
        self.model.requires_grad_(False)
        self.device = torch.device("cpu")
        self.arm = self.memory_arm
        self.fit_seconds += time.perf_counter() - tick
        report.update(arm=self.arm, fit_seconds=self.fit_seconds,
                      inference_device="cpu", memory_projection_sha256=self.feature_hash,
                      memory_feature_dimension=self.recipe["memory_feature_dimension"],
                      memory_update_is_classical=True, trained_memory_controller=False)
        return report

    def feature(self, observation):
        angles = unit(observation) @ self.projection
        return np.concatenate((np.cos(angles), np.sin(angles))) * self.feature_scale

    def new_session(self, size):
        return Session(self, size)

    def state_bytes(self):
        return super().state_bytes() + self.projection.nbytes


class Session:
    def __init__(self, system, size):
        self.system, self.size = system, size
        self.timestamps = {}
        self.memory = np.zeros(
            (system.recipe["memory_feature_dimension"], 16), dtype=np.float32)

    def ingest(self, row):
        timestamp, handle, observation, value = row
        if (not isinstance(handle, int) or observation.shape != (64,)
                or observation.dtype != np.float32 or not 0 <= value < 16):
            raise ValueError("Malformed legal write")
        if handle in self.timestamps and timestamp <= self.timestamps[handle]:
            return
        if handle not in self.timestamps and len(self.timestamps) >= self.size:
            raise ValueError("Session capacity exceeded")
        key = self.system.feature(observation)
        target = np.zeros(16, dtype=np.float32)
        target[value] = 1
        # This subtraction is the only delta/additive causal intervention.
        correction = target if self.system.arm == "additive" else target - key @ self.memory
        self.memory += self.system.recipe["memory_write_strength"] * key[:, None] * correction[None]
        self.timestamps[handle] = timestamp

    def read(self, observation):
        if observation.shape != (64,) or observation.dtype != np.float32:
            raise ValueError("Malformed legal query")
        with torch.inference_mode():
            transported = F.normalize(
                self.system.model(torch.as_tensor(observation)), dim=-1).numpy()
        values = self.system.feature(transported) @ self.memory
        value = int(np.argmax(values))
        # No record handle can be reconstructed from this compact value memory.
        return None, float(values[value]), value

    def answer(self, observation):
        handle, score, value = self.read(observation)
        return value if score >= self.system.threshold else -1, handle, score, value

    def state_bytes(self):
        # Metadata is an explicit logical estimate; RSS is measured by the parent.
        return self.system.state_bytes() + self.memory.nbytes + len(self.timestamps) * 16
