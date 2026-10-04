"""Legal paired-view controls; no private generator, plan, files or oracle access."""
import hashlib
import time

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


class Transport(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(64, 64)
        self.nonlin = nn.Sequential(nn.Linear(64, 128), nn.GELU(), nn.Linear(128, 64))

    def forward(self, inputs):
        return self.linear(inputs) + self.nonlin(inputs)


def parameter_hash(model):
    digest = hashlib.sha256()
    for value in model.state_dict().values():
        digest.update(value.detach().cpu().numpy().tobytes())
    return digest.hexdigest()


def unit(values):
    return values / np.maximum(np.linalg.norm(values, axis=-1, keepdims=True), 1e-12)


def rbf(left, right, bandwidth):
    distance = np.maximum(np.sum(left * left, axis=1)[:, None] + np.sum(right * right, axis=1) - 2 * left @ right.T, 0)
    return np.exp(-distance / (2 * bandwidth * bandwidth))


class Candidate:
    def __init__(self, seed, arm, recipe):
        self.seed, self.arm, self.recipe = seed, arm, recipe
        self.neural = arm in {"dense", "pointer", "untrained", "shuffled", "exact_nn"}
        self.device = torch.device("cuda" if self.neural else "cpu")
        torch.set_num_threads(recipe["threads"])
        torch.manual_seed(seed)
        self.model = Transport().to(self.device) if self.neural else None
        self.initial_hash = parameter_hash(self.model) if self.model is not None else None
        self.decoder = None
        if arm == "dense":
            layer = nn.TransformerDecoderLayer(64, 4, 256, dropout=0, activation="gelu", batch_first=True, norm_first=True)
            self.decoder = nn.TransformerDecoder(layer, 2).to(self.device)
            # Residual zero initialization preserves the supervised alignment at entry.
            for block in self.decoder.layers:
                for projection in (block.self_attn.out_proj, block.multihead_attn.out_proj, block.linear2):
                    nn.init.zeros_(projection.weight)
                    nn.init.zeros_(projection.bias)
        self.threshold = .85
        self.weights = self.landmarks = None
        self.grid = []
        self.losses = []
        self.fit_seconds = 0.
        self.report = {}
        self.fit_operations_estimate = 0.

    def synchronize(self):
        if self.neural:
            torch.cuda.synchronize()

    def fit(self, writes, queries, validation_writes, validation_queries, sets=None):
        started = time.perf_counter()
        if self.neural and self.arm != "untrained":
            inputs = torch.as_tensor(queries, device=self.device)
            targets = torch.as_tensor(writes, device=self.device)
            if self.arm == "shuffled":
                permutation = np.random.default_rng(self.seed ^ 0x53485546).permutation(len(writes))
                targets = targets[torch.as_tensor(permutation, device=self.device)]
            batches = torch.Generator(device=self.device).manual_seed(self.seed ^ 0x42415443)
            optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.recipe["learning_rate"], weight_decay=self.recipe["weight_decay"])
            self.model.train()
            for _ in range(self.recipe["alignment_steps"]):
                indices = torch.randint(len(inputs), (self.recipe["alignment_batch"],), generator=batches, device=self.device)
                optimizer.zero_grad(set_to_none=True)
                loss = F.mse_loss(self.model(inputs[indices]), targets[indices])
                if not torch.isfinite(loss):
                    raise ValueError("Nonfinite alignment loss")
                loss.backward()
                optimizer.step()
                self.losses.append(float(loss.detach()))
            self.model.eval()
            if self.decoder is not None:
                self.model.requires_grad_(False)
                tensors = {size: tuple(torch.as_tensor(a, device=self.device) for a in group) for size, group in sets.items()}
                optimizer = torch.optim.AdamW(self.decoder.parameters(), lr=self.recipe["learning_rate"], weight_decay=self.recipe["weight_decay"])
                self.decoder.train()
                self.set_losses = []
                for step in range(self.recipe["dense_set_steps"]):
                    size = (32, 128)[step % 2]
                    support, question, labels = tensors[size]
                    indices = torch.randint(len(support), (4,), generator=batches, device=self.device)
                    keys = F.normalize(support[indices], dim=-1)
                    with torch.no_grad():
                        embedded = F.normalize(self.model(question[indices]), dim=-1)
                    decoded = self.refine(embedded, keys)
                    scores = decoded @ keys.transpose(-1, -2)
                    scores = torch.cat([scores, torch.full((*scores.shape[:-1], 1), .85, device=self.device)], dim=-1) * 20
                    actual = labels[indices]
                    loss = F.cross_entropy(scores.flatten(0, 1), actual.flatten())
                    known = actual < size
                    target = keys.gather(1, actual.clamp(max=size - 1)[..., None].expand(-1, -1, 64))
                    loss = loss + .1 * F.mse_loss(decoded[known], target[known])
                    optimizer.zero_grad(set_to_none=True)
                    if not torch.isfinite(loss):
                        raise ValueError("Nonfinite set loss")
                    loss.backward()
                    optimizer.step()
                    self.set_losses.append(float(loss.detach()))
                self.decoder.eval()
        elif self.arm in {"ridge", "kernel"}:
            inputs, targets = queries.astype(np.float64), writes.astype(np.float64)
            validation = validation_queries.astype(np.float64)
            best = float("inf")
            combinations = [(None, r) for r in self.recipe["ridge_grid"]] if self.arm == "ridge" else [(h, r) for h in (.25, .5, 1.) for r in (.0001, .01)]
            for bandwidth, regularizer in combinations:
                landmarks = inputs[:512] if bandwidth is not None else None
                features = rbf(inputs, landmarks, bandwidth) if bandwidth else inputs
                held = rbf(validation, landmarks, bandwidth) if bandwidth else validation
                if bandwidth is not None:
                    # Nyström whitening makes primal L2 ridge the RKHS penalty.
                    lower = np.linalg.cholesky(rbf(landmarks, landmarks, bandwidth) + np.eye(len(landmarks)) * 1e-10)
                    features = np.linalg.solve(lower, features.T).T
                    held = np.linalg.solve(lower, held.T).T
                features = np.column_stack([features, np.ones(len(features))])
                held = np.column_stack([held, np.ones(len(held))])
                penalty = np.eye(features.shape[1]) * regularizer
                penalty[-1, -1] = 0
                weights = np.linalg.solve(features.T @ features + penalty, features.T @ targets)
                width = features.shape[1]
                self.fit_operations_estimate += 2 * len(inputs) * width * (width + 64) + width ** 3
                score = float(np.mean((held @ weights - validation_writes) ** 2))
                self.grid.append({"bandwidth": bandwidth, "ridge": regularizer, "validation_mse": score})
                if score < best:
                    best = score
                    if bandwidth is not None:
                        weights = np.vstack([np.linalg.solve(lower.T, weights[:-1]), weights[-1:]])
                    self.weights, self.bandwidth, self.landmarks = weights, bandwidth, landmarks
        self.synchronize()
        self.fit_seconds = time.perf_counter() - started
        self.report = {"arm": self.arm, "seed": self.seed, "fit_seconds": self.fit_seconds,
                       "initial_parameters_sha256": self.initial_hash,
                       "final_encoder_sha256": parameter_hash(self.model) if self.neural else None,
                       "optimizer_steps": len(self.losses), "alignment_losses": self.losses,
                       "dense_set_losses": getattr(self, "set_losses", []), "classical_grid": self.grid,
                       "device": str(self.device), "precision": "float32 neural / float64 classical",
                       "parameter_count": sum(p.numel() for m in (self.model, self.decoder) if m is not None for p in m.parameters())}
        self.fit_operations_estimate += len(self.losses) * 6 * self.recipe["alignment_batch"] * sum(p.numel() for p in self.model.parameters()) if self.model is not None else 0
        if self.decoder is not None:
            self.fit_operations_estimate += self.recipe["dense_set_steps"] * 6 * 4 * 8 * sum(p.numel() for p in self.decoder.parameters())
        self.report["fit_operations_estimate"] = self.fit_operations_estimate
        return self.report

    def calibrate(self, legal_episodes):
        # Receives only declared train calibration inputs and supervised train labels.
        samples = []
        for writes, queries, labels in legal_episodes:
            session = self.new_session(len({row[1] for row in writes}))
            for row in writes:
                session.ingest(row)
            for query, label in zip(queries, labels, strict=True):
                _, score, value = session.read(query)
                samples.append((score, value, label))
        choices = []
        for threshold in self.recipe["threshold_grid"]:
            answers = [v if score >= threshold else -1 for score, v, _ in samples]
            accuracy = sum(a == item[2] for a, item in zip(answers, samples, strict=True)) / len(samples)
            known = [i for i, item in enumerate(samples) if item[2] != -1]
            absent = [i for i, item in enumerate(samples) if item[2] == -1]
            false_abstention = sum(answers[i] == -1 for i in known) / len(known)
            rejection = sum(answers[i] == -1 for i in absent) / len(absent)
            choices.append({"threshold": threshold, "accuracy": accuracy, "known_false_abstention": false_abstention, "absent_rejection": rejection})
        eligible = [c for c in choices if c["known_false_abstention"] <= .02 and c["absent_rejection"] >= .95]
        chosen = max(eligible or choices, key=lambda c: (c["accuracy"], c["absent_rejection"], -c["threshold"]))
        self.threshold = chosen["threshold"]
        self.report.update(calibration_grid=choices, calibration_choice=chosen, calibration_feasible=bool(eligible))

    def refine(self, embedded, keys):
        # Query batching supplies no peer context unavailable to a single query.
        count = embedded.shape[1]
        mask = ~torch.eye(count, dtype=torch.bool, device=embedded.device) if count > 1 else None
        return F.normalize(self.decoder(embedded, keys, tgt_mask=mask), dim=-1)

    def new_session(self, size):
        return Session(self, size)

    def state_bytes(self):
        total = sum(p.numel() * p.element_size() for m in (self.model, self.decoder) if m is not None for p in m.parameters())
        return total + sum(a.nbytes for a in (self.weights, self.landmarks) if a is not None)


class Session:
    def __init__(self, system, size):
        self.system, self.size = system, size
        self.slots, self.times, self.handles = {}, {}, []
        self.labels = np.zeros(size, dtype=np.int64)
        self.keys = torch.empty((size, 64), device=system.device) if system.neural else np.empty((size, 64), dtype=np.float64)

    def ingest(self, row):
        timestamp, handle, observation, value = row
        if not isinstance(handle, int) or observation.shape != (64,) or observation.dtype != np.float32 or not 0 <= value < 16:
            raise ValueError("Malformed legal write")
        if handle in self.times and timestamp <= self.times[handle]:
            return
        if handle not in self.slots:
            if len(self.handles) >= self.size:
                raise ValueError("Session capacity exceeded")
            self.slots[handle] = len(self.handles)
            self.handles.append(handle)
        slot = self.slots[handle]
        self.times[handle] = timestamp
        self.labels[slot] = value
        self.keys[slot] = F.normalize(torch.as_tensor(observation, device=self.system.device), dim=-1) if self.system.neural else unit(observation.astype(np.float64))

    def read(self, observation):
        if observation.shape != (64,) or observation.dtype != np.float32:
            raise ValueError("Malformed legal query")
        system = self.system
        if system.neural:
            with torch.inference_mode():
                embedded = F.normalize(system.model(torch.as_tensor(observation, device=system.device)), dim=-1)
                if system.decoder is not None:
                    embedded = system.refine(embedded[None, None], self.keys[None])[0, 0]
                scores = self.keys @ embedded
                if system.arm in {"pointer", "untrained", "shuffled", "dense"}:
                    # A dense softmax pointer over records and a NULL entry, no shortlist.
                    probabilities = torch.softmax(torch.cat([scores, torch.tensor([system.threshold], device=system.device)]) * 20, dim=0)
                    index = int(torch.argmax(probabilities[:-1]))
                else:
                    index = int(torch.argmax(scores))
                score = float(scores[index])
        else:
            projected = observation.astype(np.float64)
            if system.weights is not None:
                features = rbf(projected[None], system.landmarks, system.bandwidth)[0] if system.landmarks is not None else projected
                projected = np.append(features, 1.) @ system.weights
            scores = self.keys @ unit(projected)
            index = int(np.argmax(scores))
            score = float(scores[index])
        return self.handles[index], score, int(self.labels[index])

    def answer(self, observation):
        handle, score, value = self.read(observation)
        return (value if score >= self.system.threshold else -1), handle, score, value

    def state_bytes(self):
        # Explicit logical storage, including dictionary entries; not measured allocator traffic.
        return self.system.state_bytes() + self.size * (64 * (4 if self.system.neural else 8) + 8 + 3 * 8)
