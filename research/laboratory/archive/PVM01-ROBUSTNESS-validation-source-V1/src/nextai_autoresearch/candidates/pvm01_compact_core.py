"""Preregistered feature learning through a fixed classical delta memory."""
import hashlib
import time

import numpy as np
import torch
from torch.nn import functional as F

from .pvm01_core import Candidate as Reference
from .pvm01_delta_core import Candidate as FixedFeatures, Session


def fourier(inputs, projection):
    angles = F.normalize(inputs, dim=-1) @ projection
    return torch.cat((torch.cos(angles), torch.sin(angles)), dim=-1) / np.sqrt(projection.shape[1])


def delta_unroll(keys, labels, questions):
    """Same beta=1 write algebra as inference, with an untruncated gradient."""
    memory = keys.new_zeros((keys.shape[0], keys.shape[-1], 16))
    for position in range(keys.shape[1]):
        key = keys[:, position]
        correction = F.one_hot(labels[:, position], 16).to(keys.dtype) - torch.bmm(
            key[:, None], memory)[:, 0]
        memory = memory + key[:, :, None] * correction[:, None, :]
    return torch.bmm(questions, memory)


def training_loss(values, targets, recipe):
    null = torch.full((*values.shape[:-1], 1), recipe["compact_null_score"],
                      device=values.device, dtype=values.dtype)
    logits = torch.cat((values, null), dim=-1) * recipe["compact_logit_scale"]
    return F.cross_entropy(logits.flatten(0, 1), targets.flatten())


class Candidate(FixedFeatures):
    def __init__(self, seed, arm, recipe):
        if arm not in {"compact_learned", "compact_frozen", "compact_shuffled", "compact_additive"}:
            raise ValueError("Unknown compact feature arm")
        self.compact_arm = arm
        compact = {**recipe, "memory_frequencies": recipe["compact_frequencies"],
                   "memory_feature_dimension": recipe["compact_feature_dimension"]}
        super().__init__(seed, "delta", compact)
        self.initial_feature_hash = self.feature_hash

    def fit(self, writes, queries, validation_writes, validation_queries, sets=None):
        if sets is None or set(sets) != {32, 128}:
            raise ValueError("Frozen compact fit requires legal training sets at K32/128")
        # Exact source-identical transport; no gradient or feature signal changes it.
        report = Reference.fit(self, writes, queries, validation_writes, validation_queries, sets)
        started = time.perf_counter()
        self.model.eval().requires_grad_(False)
        tensors, precomputed = {}, hashlib.sha256()
        with torch.no_grad():
            for size, group in sets.items():
                support, question, targets = (torch.as_tensor(a, device=self.device) for a in group)
                keys = F.normalize(support, dim=-1)
                aligned = F.normalize(self.model(question), dim=-1)
                tensors[size] = keys, aligned, targets
                for value in (keys, aligned, targets):
                    array = value.cpu().numpy()
                    precomputed.update(str((array.shape, array.dtype.str)).encode())
                    precomputed.update(array.tobytes())
        projection = torch.nn.Parameter(torch.as_tensor(self.projection.copy(), device=self.device))
        self.feature_losses, self.feature_gradient_norms = [], []
        trace = hashlib.sha256()
        generator = torch.Generator(device=self.device).manual_seed(
            self.seed ^ self.recipe["compact_feature_batch_seed_xor"])
        permutations = {}
        shuffle = np.random.default_rng(self.seed ^ self.recipe["compact_feature_shuffle_seed_xor"])
        for size in (32, 128):
            order = shuffle.permutation(len(tensors[size][0]))
            permutations[size] = torch.as_tensor(order, device=self.device)
        steps = 0 if self.compact_arm == "compact_frozen" else self.recipe["compact_feature_steps"]
        optimizer = torch.optim.AdamW([projection], lr=self.recipe["compact_feature_learning_rate"],
                                      weight_decay=self.recipe["compact_feature_weight_decay"])
        for step in range(steps):
            size = (32, 128)[step % 2]
            support, questions, positions = tensors[size]
            indices = torch.randint(len(support), (self.recipe["compact_feature_batch"],),
                                    generator=generator, device=self.device)
            labels = torch.randint(16, (len(indices), size), generator=generator, device=self.device)
            actual = positions[indices]
            target = labels.gather(1, actual.clamp(max=size - 1)).masked_fill(actual == size, 16)
            question_indices = permutations[size][indices] if self.compact_arm == "compact_shuffled" else indices
            keys = fourier(support[indices], projection)
            reads = fourier(questions[question_indices], projection)
            loss = training_loss(delta_unroll(keys, labels, reads), target, self.recipe)
            optimizer.zero_grad(set_to_none=True)
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite compact feature loss")
            loss.backward()
            norm = torch.nn.utils.clip_grad_norm_([projection], self.recipe["compact_feature_gradient_clip"],
                                                  error_if_nonfinite=True)
            optimizer.step()
            self.feature_losses.append(float(loss.detach()))
            self.feature_gradient_norms.append(float(norm))
            trace.update(str((step, size)).encode())
            for value in (indices, labels):
                trace.update(value.cpu().numpy().tobytes())
        self.projection = projection.detach().cpu().numpy().copy()
        if not np.isfinite(self.projection).all():
            raise ValueError("Nonfinite feature projection")
        self.feature_hash = hashlib.sha256(self.projection.tobytes()).hexdigest()
        self.model = self.model.to("cpu").eval()
        self.synchronize()
        self.device = torch.device("cpu")
        self.arm = "additive" if self.compact_arm == "compact_additive" else "delta"
        self.fit_seconds += time.perf_counter() - started
        # Coarse estimate only; every precomputation, draw, unroll and optimizer is timed.
        self.fit_operations_estimate += steps * self.recipe["compact_feature_batch"] * (
            6 * 80 * self.recipe["memory_feature_dimension"] * 16 + 6 * 88 * 64 * self.recipe["memory_frequencies"])
        report.update(arm=self.compact_arm, fit_seconds=self.fit_seconds, inference_device="cpu",
                      compact_initial_features_sha256=self.initial_feature_hash,
                      compact_final_features_sha256=self.feature_hash, compact_precomputed_sha256=precomputed.hexdigest(),
                      compact_batch_value_draws_sha256=trace.hexdigest(), compact_feature_steps=steps,
                      compact_feature_losses=self.feature_losses, compact_feature_gradient_norms=self.feature_gradient_norms,
                      compact_shuffle_episode_permutations={str(k): v.cpu().tolist() for k, v in permutations.items()},
                      memory_feature_dimension=self.recipe["memory_feature_dimension"],
                      memory_update_is_classical=True, trained_memory_controller=False,
                      trained_memory_feature_map=bool(steps), transport_frozen_during_feature_training=True,
                      parameter_count=report["parameter_count"] + self.projection.size,
                      fit_operations_estimate=self.fit_operations_estimate)
        return report

    def new_session(self, size):
        return Session(self, size)
