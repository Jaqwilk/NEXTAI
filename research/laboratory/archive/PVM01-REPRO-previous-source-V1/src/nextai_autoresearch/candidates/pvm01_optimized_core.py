"""Same fitted controls with charged fp32/PCA/tree or dense KV-cache inference."""
import hashlib
import time

import numpy as np
import torch
from scipy.spatial import cKDTree
from torch.nn import functional as F

from .pvm01_core import Candidate as Reference, Session as ReferenceSession, unit


class Candidate(Reference):
    def __init__(self, seed, arm, recipe):
        self.optimized_arm = arm
        if arm.startswith("dense_cached_"):
            base_arm = "dense"
        elif arm == "exact_nn_cpu":
            base_arm = "exact_nn"
        elif arm in {"ridge32", "ridge_pca_scan", "ridge_pca_tree"}:
            base_arm = "ridge"
        else:
            raise ValueError("Unknown optimized control")
        super().__init__(seed, base_arm, recipe)
        self.projection = None

    def synchronize(self):
        if self.device.type == "cuda":
            torch.cuda.synchronize()

    def fit(self, writes, queries, validation_writes, validation_queries, sets=None):
        report = super().fit(writes, queries, validation_writes, validation_queries, sets)
        tick = time.perf_counter()
        self.arm = self.optimized_arm
        if self.arm in {"dense_cached_cpu", "exact_nn_cpu"}:
            self.model = self.model.to("cpu")
            if self.decoder is not None:
                self.decoder = self.decoder.to("cpu")
            self.device = torch.device("cpu")
        if self.arm.startswith("ridge"):
            predicted = np.column_stack([validation_queries, np.ones(len(validation_queries))]) @ self.weights
            if self.arm != "ridge32":
                _, singular, vectors = np.linalg.svd(unit(writes.astype(np.float64)), full_matrices=False)
                choices, best = [], float("inf")
                for rank in (16, 32, 64):
                    for exponent in (0., .5):
                        eigenvalues = np.maximum(singular[:rank] ** 2 / len(writes), 1e-6)
                        projection = vectors[:rank].T * eigenvalues ** (-exponent)
                        error = unit(predicted @ projection) - unit(validation_writes @ projection)
                        score = float(np.mean(np.sum(error ** 2, axis=1)))
                        choices.append({"rank": rank, "whitening_exponent": exponent,
                                        "validation_squared_l2": score})
                        if score < best:
                            best, self.projection = score, projection.astype(np.float32)
                report["pca_grid"] = choices
                report["pca_choice"] = min(choices, key=lambda row: row["validation_squared_l2"])
                report["pca_projection_sha256"] = hashlib.sha256(self.projection.tobytes()).hexdigest()
                self.fit_operations_estimate += 2 * len(writes) * 64 ** 2 + 64 ** 3
            self.weights = self.weights.astype(np.float32)
            report["fp32_ridge_weights_sha256"] = hashlib.sha256(self.weights.tobytes()).hexdigest()
        self.synchronize()
        self.fit_seconds += time.perf_counter() - tick
        report.update(arm=self.arm, fit_seconds=self.fit_seconds, inference_device=str(self.device),
                      precision="float32 inference; classical fit float64; cKDTree owns float64 copies",
                      fit_operations_estimate=self.fit_operations_estimate)
        return report

    def new_session(self, size):
        if self.arm.startswith("dense_cached_"):
            return CachedSession(self, size)
        if self.arm.startswith("ridge"):
            return RidgeSession(self, size)
        return ReferenceSession(self, size)

    def state_bytes(self):
        return super().state_bytes() + (0 if self.projection is None else self.projection.nbytes)


class RidgeSession:
    def __init__(self, system, size):
        self.system, self.size = system, size
        self.slots, self.times, self.handles = {}, {}, []
        width = 64 if system.projection is None else system.projection.shape[1]
        self.keys = np.empty((size, width), dtype=np.float32)
        self.values = np.zeros(size, dtype=np.int64)
        self.tree = None
        self.dirty = True

    def ingest(self, row):
        timestamp, handle, observation, value = row
        if (not isinstance(handle, int) or observation.shape != (64,)
                or observation.dtype != np.float32 or not 0 <= value < 16):
            raise ValueError("Malformed legal write")
        if handle in self.times and timestamp <= self.times[handle]:
            return
        if handle not in self.slots:
            if len(self.handles) >= self.size:
                raise ValueError("Session capacity exceeded")
            self.slots[handle] = len(self.handles)
            self.handles.append(handle)
        index = self.slots[handle]
        transformed = observation if self.system.projection is None else observation @ self.system.projection
        self.keys[index] = unit(transformed)
        self.values[index], self.times[handle] = value, timestamp
        self.dirty = True

    def read(self, observation):
        if observation.shape != (64,) or observation.dtype != np.float32:
            raise ValueError("Malformed legal query")
        projected = observation @ self.system.weights[:-1] + self.system.weights[-1]
        if self.system.projection is not None:
            projected = projected @ self.system.projection
        embedded = unit(projected)
        if self.system.arm == "ridge_pca_tree":
            if self.dirty:
                self.tree = cKDTree(self.keys[:len(self.handles)], leafsize=16,
                                    copy_data=True, balanced_tree=True, compact_nodes=True)
                self.dirty = False
            _, index = self.tree.query(embedded, k=1, eps=0, p=2, workers=1)
            index = int(index)
        else:
            index = int(np.argmax(self.keys[:len(self.handles)] @ embedded))
        return self.handles[index], float(self.keys[index] @ embedded), int(self.values[index])

    def answer(self, observation):
        handle, score, value = self.read(observation)
        return value if score >= self.system.threshold else -1, handle, score, value

    def state_bytes(self):
        tree = 0 if self.tree is None else (
            self.tree.data.nbytes + self.tree.indices.nbytes
            + self.tree.maxes.nbytes + self.tree.mins.nbytes + self.tree.size * 64)
        return self.system.state_bytes() + self.keys.nbytes + self.values.nbytes + self.size * 24 + tree


class CachedSession(ReferenceSession):
    def __init__(self, system, size):
        super().__init__(system, size)
        self.cache = [(torch.empty_like(self.keys), torch.empty_like(self.keys))
                      for _ in system.decoder.layers]

    def ingest(self, row):
        previous = self.times.get(row[1])
        super().ingest(row)
        if previous is not None and row[0] <= previous:
            return
        slot = self.slots[row[1]]
        with torch.inference_mode():
            for layer, (keys, values) in zip(self.system.decoder.layers, self.cache, strict=True):
                attention = layer.multihead_attn
                keys[slot] = F.linear(self.keys[slot], attention.in_proj_weight[64:128],
                                      attention.in_proj_bias[64:128])
                values[slot] = F.linear(self.keys[slot], attention.in_proj_weight[128:],
                                        attention.in_proj_bias[128:])

    def decoded(self, embedded):
        """One query: self-attention has one token; cross-attention remains dense."""
        value = embedded.reshape(1, 64)
        for layer, (keys, values) in zip(self.system.decoder.layers, self.cache, strict=True):
            attention = layer.self_attn
            normalized = layer.norm1(value)
            single_value = F.linear(normalized, attention.in_proj_weight[128:],
                                    attention.in_proj_bias[128:])
            value = value + F.linear(single_value, attention.out_proj.weight, attention.out_proj.bias)
            attention = layer.multihead_attn
            question = F.linear(layer.norm2(value), attention.in_proj_weight[:64],
                                attention.in_proj_bias[:64]).reshape(4, 1, 16)
            cached_keys = keys[:len(self.handles)].reshape(-1, 4, 16).transpose(0, 1)
            cached_values = values[:len(self.handles)].reshape(-1, 4, 16).transpose(0, 1)
            probabilities = torch.softmax(question @ cached_keys.transpose(-1, -2) / 4, dim=-1)
            attended = (probabilities @ cached_values).reshape(1, 64)
            value = value + F.linear(attended, attention.out_proj.weight, attention.out_proj.bias)
            value = value + layer.linear2(layer.activation(layer.linear1(layer.norm3(value))))
        if self.system.decoder.norm is not None:
            value = self.system.decoder.norm(value)
        return F.normalize(value[0], dim=-1)

    def read(self, observation):
        if observation.shape != (64,) or observation.dtype != np.float32:
            raise ValueError("Malformed legal query")
        with torch.inference_mode():
            embedded = F.normalize(self.system.model(
                torch.as_tensor(observation, device=self.system.device)), dim=-1)
            decoded = self.decoded(embedded)
            scores = self.keys[:len(self.handles)] @ decoded
            index = int(torch.argmax(scores))
            return self.handles[index], float(scores[index]), int(self.labels[index])

    def state_bytes(self):
        return super().state_bytes() + sum(t.numel() * t.element_size() for pair in self.cache for t in pair)
