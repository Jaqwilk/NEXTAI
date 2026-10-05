"""Frozen actual source features plus identical legal readout; native target controls."""
import hashlib
import time

import numpy as np
import torch
from torch.nn import functional as F
from torch.nn.attention import SDPBackend, sdpa_kernel

from .pvm01_core import Candidate as Reference, Transport, parameter_hash, unit, rbf
from .pvm01_optimized_core import CachedSession


def array_hash(value):
    return hashlib.sha256(value.tobytes()).hexdigest()


def ridge(inputs, targets, held, held_targets, grid, normalized=False):
    features = np.column_stack((inputs.astype(np.float64), np.ones(len(inputs))))
    validation = np.column_stack((held.astype(np.float64), np.ones(len(held))))
    targets, held_targets = targets.astype(np.float64), held_targets.astype(np.float64)
    covariance, cross = features.T @ features, features.T @ targets
    choices, best, selected = [], float("inf"), None
    for regularizer in grid:
        penalty = np.eye(features.shape[1]) * regularizer
        penalty[-1, -1] = 0
        weights = np.linalg.solve(covariance + penalty, cross)
        prediction = validation @ weights
        error = unit(prediction) - unit(held_targets) if normalized else prediction - held_targets
        score = float(np.mean(np.sum(error ** 2, axis=-1)))
        if not np.isfinite(score):
            raise ValueError("Nonfinite target readout/grid loss")
        choices.append({"ridge": regularizer, "validation_squared_l2": score})
        if score < best:
            best, selected = score, weights.copy()
    width, outputs = features.shape[1], targets.shape[1]
    operations = 2 * len(inputs) * width * (width + outputs) + len(grid) * width ** 3
    return selected, choices, operations


class Candidate(Reference):
    def __init__(self, seed, arm, recipe, source_arrays=None):
        if arm not in {"source_trained", "source_untrained", "source_shuffled", "source_ridge",
                       "target_dense", "target_ridge_pca", "target_kernel", "native_raw", "native_shift"}:
            raise ValueError("Unknown preregistered native arm")
        super().__init__(seed, "dense" if arm == "target_dense" else "raw", recipe)
        self.route, self.arm = arm, arm
        self.projection = self.source_weights = self.adapter = None
        self.source_before = None
        if arm.startswith("source_"):
            if source_arrays is None or "projection" not in source_arrays:
                raise ValueError("Missing actual frozen source state")
            self.projection = source_arrays["projection"].copy()
            if arm == "source_ridge":
                self.source_weights = source_arrays["weights"].copy()
            else:
                self.model = Transport().to("cpu")
                expected = {"model." + key for key in self.model.state_dict()} | {"projection"}
                if set(source_arrays) != expected:
                    raise ValueError("Unexpected original encoder fields")
                self.model.load_state_dict({key: torch.as_tensor(source_arrays["model." + key].copy())
                                            for key in self.model.state_dict()}, strict=True)
                self.model.eval().requires_grad_(False)
            self.device = torch.device("cpu")
            self.source_before = self.source_identity()
        elif source_arrays is not None:
            raise ValueError("Target-only control cannot receive source state")

    def source_identity(self):
        return {"encoder_sha256": parameter_hash(self.model) if self.model is not None else None,
                "ridge_sha256": array_hash(self.source_weights) if self.source_weights is not None else None,
                "projection_sha256": array_hash(self.projection) if self.projection is not None else None}

    def source_features(self, queries):
        if self.source_weights is not None:
            return (queries @ self.source_weights[:-1] + self.source_weights[-1]) @ self.projection
        with torch.inference_mode():
            return self.model(torch.as_tensor(queries)).numpy().copy()

    def synchronize(self):
        if self.device.type == "cuda":
            torch.cuda.synchronize()

    def _dense_fit(self, writes, queries, validation_writes, validation_queries, sets):
        decoder, self.decoder = self.decoder, None
        self.arm = "pointer"
        super().fit(writes, queries, validation_writes, validation_queries)
        self.decoder = decoder
        self.model.requires_grad_(False)
        self.set_losses = []
        tensors = {size: tuple(torch.as_tensor(a, device=self.device) for a in group)
                   for size, group in sets.items()}
        if set(tensors) != {16, 32}:
            raise ValueError("Native training contexts must be K16/32")
        generator = torch.Generator(device=self.device).manual_seed(self.seed ^ 0x42415443)
        optimizer = torch.optim.AdamW(self.decoder.parameters(), lr=self.recipe["learning_rate"],
                                     weight_decay=self.recipe["weight_decay"])
        self.decoder.train()
        for step in range(self.recipe["dense_set_steps"]):
            size = (16, 32)[step % 2]
            support, questions, labels = tensors[size]
            indices = torch.randint(len(support), (4,), generator=generator, device=self.device)
            keys = F.normalize(support[indices], dim=-1)
            with torch.no_grad():
                embedded = F.normalize(self.model(questions[indices]), dim=-1)
            decoded = self.refine(embedded, keys)
            scores = decoded @ keys.transpose(-1, -2)
            scores = torch.cat((scores, torch.full((*scores.shape[:-1], 1), .85, device=self.device)), dim=-1) * 20
            actual = labels[indices]
            loss = F.cross_entropy(scores.flatten(0, 1), actual.flatten())
            known = actual < size
            targets = keys.gather(1, actual.clamp(max=size - 1)[..., None].expand(-1, -1, 64))
            loss = loss + .1 * F.mse_loss(decoded[known], targets[known])
            optimizer.zero_grad(set_to_none=True)
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite native dense loss")
            loss.backward()
            optimizer.step()
            self.set_losses.append(float(loss.detach()))
        self.decoder.eval()
        self.synchronize()
        self.fit_operations_estimate += self.recipe["dense_set_steps"] * 6 * 4 * 8 * sum(p.numel() for p in self.decoder.parameters())
        self.model, self.decoder = self.model.to("cpu"), self.decoder.to("cpu")
        self.device, self.arm = torch.device("cpu"), "dense_cached_cpu"

    def fit(self, writes, queries, validation_writes, validation_queries, sets=None):
        started = time.perf_counter()
        self.grid = []
        if self.route.startswith("source_"):
            targets, held_targets = writes @ self.projection, validation_writes @ self.projection
            self.adapter, self.grid, self.fit_operations_estimate = ridge(
                self.source_features(queries), targets, self.source_features(validation_queries), held_targets,
                self.recipe["ridge_grid"], normalized=True)
            self.adapter = self.adapter.astype(np.float32)
            if self.source_before != self.source_identity():
                raise ValueError("Frozen source altered by target adaptation")
        elif self.route == "target_dense":
            deterministic = torch.are_deterministic_algorithms_enabled()
            warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
            try:
                torch.use_deterministic_algorithms(True)
                with sdpa_kernel(SDPBackend.MATH):
                    self._dense_fit(writes, queries, validation_writes, validation_queries, sets)
            finally:
                torch.use_deterministic_algorithms(deterministic, warn_only=warn_only)
        elif self.route == "target_ridge_pca":
            self.weights, self.grid, self.fit_operations_estimate = ridge(
                queries, writes, validation_queries, validation_writes, self.recipe["ridge_grid"])
            self.weights = self.weights.astype(np.float32)
            predicted = validation_queries @ self.weights[:-1] + self.weights[-1]
            _, singular, vectors = np.linalg.svd(unit(writes.astype(np.float64)), full_matrices=False)
            choices, best = [], float("inf")
            for rank in self.recipe["pca_rank_grid"]:
                for exponent in self.recipe["pca_whitening_grid"]:
                    variance = np.maximum(singular[:rank] ** 2 / len(writes), 1e-6)
                    projection = vectors[:rank].T * variance ** (-exponent)
                    error = unit(predicted @ projection) - unit(validation_writes @ projection)
                    score = float(np.mean(np.sum(error ** 2, axis=-1)))
                    choices.append({"rank": rank, "whitening_exponent": exponent, "validation_squared_l2": score})
                    if score < best:
                        best, self.projection = score, projection.astype(np.float32).copy()
            self.pca_grid = choices
            self.fit_operations_estimate += 2 * len(writes) * 64 ** 2 + 64 ** 3
        elif self.route == "target_kernel":
            inputs, held = queries.astype(np.float64), validation_queries.astype(np.float64)
            self.landmarks = inputs[:self.recipe["kernel_landmarks"]].copy()
            best = float("inf")
            for bandwidth in self.recipe["kernel_bandwidth_grid"]:
                lower = np.linalg.cholesky(rbf(self.landmarks, self.landmarks, bandwidth) + np.eye(len(self.landmarks)) * 1e-10)
                features = np.linalg.solve(lower, rbf(inputs, self.landmarks, bandwidth).T).T
                validation = np.linalg.solve(lower, rbf(held, self.landmarks, bandwidth).T).T
                weights, choices, operations = ridge(features, writes, validation, validation_writes,
                                                     self.recipe["kernel_ridge_grid"])
                self.fit_operations_estimate += operations + 4 * len(inputs) * 64 * len(self.landmarks)
                for choice in choices:
                    self.grid.append(dict(choice, bandwidth=bandwidth))
                chosen = min(choices, key=lambda row: row["validation_squared_l2"])
                if chosen["validation_squared_l2"] < best:
                    best, self.bandwidth = chosen["validation_squared_l2"], bandwidth
                    self.weights = np.vstack((np.linalg.solve(lower.T, weights[:-1]), weights[-1:])).astype(np.float32)
            self.landmarks = self.landmarks.astype(np.float32)
        self.synchronize()
        self.fit_seconds = time.perf_counter() - started
        self.report = {"arm": self.route, "seed": self.seed, "fit_seconds": self.fit_seconds,
                       "initial_parameters_sha256": self.initial_hash,
                       "final_encoder_sha256": parameter_hash(self.model) if self.model is not None else None,
                       "source_before": self.source_before,
                       "source_after": self.source_identity() if self.route.startswith("source_") else None,
                       "source_frozen": self.source_before == self.source_identity() if self.source_before else None,
                       "source_replayed": False, "optimizer_steps": len(self.losses), "alignment_losses": self.losses,
                       "dense_set_losses": getattr(self, "set_losses", []), "classical_grid": self.grid,
                       "pca_grid": getattr(self, "pca_grid", []), "device": str(self.device),
                       "parameter_count": sum(p.numel() for m in (self.model, self.decoder) if m is not None for p in m.parameters()),
                       "fit_operations_estimate": self.fit_operations_estimate,
                       "adapter_sha256": array_hash(self.adapter) if self.adapter is not None else None,
                       "precision": "FP32 source/target service and state; FP64 ridge/kernel/PCA fits"}
        return self.report

    def new_session(self, size):
        return Session(self, size)

    def calibrate(self, legal_episodes):
        samples = []
        for writes, queries, labels in legal_episodes:
            session = self.new_session(len({row[1] for row in writes}))
            for row in writes:
                session.ingest(row)
            for query, (truth, target_source) in zip(queries, labels, strict=True):
                handle, score, value = session.read(query)
                if not np.isfinite(score):
                    raise ValueError("Nonfinite native train-calibration score")
                samples.append((score, value, session.sources[handle], truth, target_source))
        choices = []
        for threshold in self.recipe["threshold_grid"]:
            outputs = [(value, source) if score >= threshold else (-1, None)
                       for score, value, source, _, _ in samples]
            correct = sum(output == (row[3], row[4]) for output, row in zip(outputs, samples, strict=True))
            known = [i for i, row in enumerate(samples) if row[3] != -1]
            absent = [i for i, row in enumerate(samples) if row[3] == -1]
            choices.append({"threshold": threshold, "accuracy": correct / len(samples),
                            "known_false_abstention": sum(outputs[i][0] == -1 for i in known) / len(known),
                            "absent_rejection": sum(outputs[i] == (-1, None) for i in absent) / len(absent)})
        eligible = [choice for choice in choices if choice["known_false_abstention"] <= .02
                    and choice["absent_rejection"] >= .95]
        selected = max(eligible or choices, key=lambda row: (row["accuracy"], row["absent_rejection"], -row["threshold"]))
        self.threshold = selected["threshold"]
        self.report.update(calibration_grid=choices, calibration_choice=selected, calibration_feasible=bool(eligible),
                           calibration_answer_semantics="value AND current source; UNKNOWN-1/None")

    def state_bytes(self):
        total = sum(p.numel() * p.element_size() for m in (self.model, self.decoder) if m is not None for p in m.parameters())
        # T-fitted64means/scales are part of the service even though evaluator transforms inputs.
        return total + 512 + sum(a.nbytes for a in (self.weights, self.landmarks, self.projection,
                                                   self.source_weights, self.adapter) if a is not None)


class Session:
    def __init__(self, system, size):
        self.system, self.size = system, size
        self.sources, self.times, self.slots, self.handles = {}, {}, {}, []
        self.cached = CachedSession(system, size) if system.route == "target_dense" else None
        width = 64 if system.projection is None else system.projection.shape[1]
        self.keys = np.empty((size, width), dtype=np.float32) if self.cached is None else None
        self.values = np.zeros(size, dtype=np.int64) if self.cached is None else None

    def ingest(self, row):
        timestamp, handle, observation, value, source = row
        if (not isinstance(handle, int) or observation.shape != (64,) or observation.dtype != np.float32
                or not 0 <= value < 16 or not isinstance(source, str) or not source):
            raise ValueError("Malformed public fact/source write")
        if handle in self.times and timestamp <= self.times[handle]:
            return
        if self.cached is not None:
            self.cached.ingest((timestamp, handle, observation, value))
        else:
            if handle not in self.slots:
                if len(self.handles) >= self.size:
                    raise ValueError("Native memory capacity exceeded")
                self.slots[handle] = len(self.handles)
                self.handles.append(handle)
            slot = self.slots[handle]
            projected = observation if self.system.projection is None else observation @ self.system.projection
            self.keys[slot] = unit(projected)
            self.values[slot] = value
        self.times[handle], self.sources[handle] = timestamp, source

    def read(self, observation):
        if observation.shape != (64,) or observation.dtype != np.float32:
            raise ValueError("Native query exposes only its64observation")
        if self.cached is not None:
            return self.cached.read(observation)
        system = self.system
        if system.route.startswith("source_"):
            features = system.source_features(observation[None])[0]
            projected = features @ system.adapter[:-1] + system.adapter[-1]
        elif system.route == "target_kernel":
            features = rbf(observation[None], system.landmarks, system.bandwidth)[0]
            projected = features @ system.weights[:-1] + system.weights[-1]
        elif system.route == "target_ridge_pca":
            projected = (observation @ system.weights[:-1] + system.weights[-1]) @ system.projection
        else:
            projected = observation
        keys = self.keys[:len(self.handles)]
        if system.route == "native_shift":
            series, query = keys.reshape(-1, 8, 8), projected.reshape(8, 8)
            scores = []
            for offset in (-1, 0, 1):
                left = series[:, :, max(0, offset):min(8, 8 + offset)].reshape(len(keys), -1)
                right = query[:, max(0, -offset):min(8, 8 - offset)].ravel()
                scores.append(unit(left) @ unit(right))
            similarity = np.max(scores, axis=0)
        else:
            similarity = keys @ unit(projected)
        index = int(np.argmax(similarity))
        return self.handles[index], float(similarity[index]), int(self.values[index])

    def answer(self, observation):
        handle, score, value = self.read(observation)
        accepted = score >= self.system.threshold
        return value if accepted else -1, handle, score, value, self.sources[handle] if accepted else None

    def state_bytes(self):
        sources = sum(len(source.encode("utf-8")) for source in self.sources.values())
        metadata = self.size * 48 + sources
        if self.cached is not None:
            return self.cached.state_bytes() + metadata
        return self.system.state_bytes() + self.keys.nbytes + self.values.nbytes + metadata
