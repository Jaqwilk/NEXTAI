"""Frozen support-size exposure contrast; unchanged Fourier/delta inference."""
import hashlib
import time

import numpy as np
import torch
from torch.nn import functional as F

from .pvm01_compact_core import Candidate as Compact, fourier, delta_unroll, training_loss
from .pvm01_core import Candidate as Reference


def common_draw(generator, device, batch, count, width):
    """Draw before truncation, so changing K cannot change the paired RNG stream."""
    indices = torch.randint(count, (batch,), generator=generator, device=device)
    labels = torch.randint(16, (batch, width), generator=generator, device=device)
    return indices, labels


class Candidate(Compact):
    def __init__(self, seed, arm, recipe):
        mapped = {"exposure_small": "compact_learned", "exposure_large": "compact_learned",
                  "exposure_frozen": "compact_frozen", "exposure_shuffled": "compact_shuffled",
                  "exposure_additive": "compact_additive"}
        if arm not in mapped:
            raise ValueError("Unknown support exposure arm")
        self.exposure_arm = arm
        super().__init__(seed, mapped[arm], recipe)

    def fit(self, writes, queries, validation_writes, validation_queries, sets=None):
        if sets is None or set(sets) != {32, 128, 512}:
            raise ValueError("Frozen exposure fit requires legal T-sets at K32/128/512")
        if len({len(group[0]) for group in sets.values()}) != 1:
            raise ValueError("Paired episode draw requires equal per-K train episode counts")
        report = Reference.fit(self, writes, queries, validation_writes, validation_queries, sets)
        started = time.perf_counter()
        self.model.eval().requires_grad_(False)
        tensors, precomputed = {}, hashlib.sha256()
        with torch.no_grad():
            for size, group in sets.items():
                support, question, targets = (torch.as_tensor(a, device=self.device) for a in group)
                keys, aligned = F.normalize(support, dim=-1), F.normalize(self.model(question), dim=-1)
                tensors[size] = keys, aligned, targets
                for value in (keys, aligned, targets):
                    array = value.cpu().numpy()
                    precomputed.update(str((array.shape, array.dtype.str)).encode())
                    precomputed.update(array.tobytes())
        projection = torch.nn.Parameter(torch.as_tensor(self.projection.copy(), device=self.device))
        self.feature_losses, self.feature_gradient_norms = [], []
        common_trace, sized_trace = hashlib.sha256(), hashlib.sha256()
        generator = torch.Generator(device=self.device).manual_seed(
            self.seed ^ self.recipe["compact_feature_batch_seed_xor"])
        shuffle = np.random.default_rng(self.seed ^ self.recipe["compact_feature_shuffle_seed_xor"])
        permutations = {size: torch.as_tensor(shuffle.permutation(len(tensors[size][0])), device=self.device)
                        for size in (32, 128, 512)}
        sizes = self.recipe["exposure_small_support_sizes"] if self.exposure_arm == "exposure_small" else self.recipe["exposure_large_support_sizes"]
        steps = 0 if self.exposure_arm == "exposure_frozen" else self.recipe["compact_feature_steps"]
        optimizer = torch.optim.AdamW([projection], lr=self.recipe["compact_feature_learning_rate"],
                                      weight_decay=self.recipe["compact_feature_weight_decay"])
        write_count = 0
        for step in range(steps):
            size = sizes[step % len(sizes)]
            support, questions, positions = tensors[size]
            indices, max_labels = common_draw(generator, self.device, self.recipe["compact_feature_batch"],
                                               len(support), self.recipe["exposure_common_value_draw_size"])
            labels = max_labels[:, :size]
            actual = positions[indices]
            target = labels.gather(1, actual.clamp(max=size - 1)).masked_fill(actual == size, 16)
            question_indices = permutations[size][indices] if self.exposure_arm == "exposure_shuffled" else indices
            keys, reads = fourier(support[indices], projection), fourier(questions[question_indices], projection)
            loss = training_loss(delta_unroll(keys, labels, reads), target, self.recipe)
            optimizer.zero_grad(set_to_none=True)
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite exposure feature loss")
            loss.backward()
            norm = torch.nn.utils.clip_grad_norm_([projection], self.recipe["compact_feature_gradient_clip"],
                                                  error_if_nonfinite=True)
            optimizer.step()
            self.feature_losses.append(float(loss.detach()))
            self.feature_gradient_norms.append(float(norm))
            common_trace.update(str(step).encode())
            sized_trace.update(str((step, size)).encode())
            for value in (indices, max_labels):
                common_trace.update(value.cpu().numpy().tobytes())
            for value in (indices, labels):
                sized_trace.update(value.cpu().numpy().tobytes())
            write_count += len(indices) * size
        self.projection = projection.detach().cpu().numpy().copy()
        if not np.isfinite(self.projection).all():
            raise ValueError("Nonfinite exposure projection")
        self.feature_hash = hashlib.sha256(self.projection.tobytes()).hexdigest()
        self.model = self.model.to("cpu").eval()
        self.synchronize()
        self.device = torch.device("cpu")
        self.arm = "additive" if self.exposure_arm == "exposure_additive" else "delta"
        self.fit_seconds += time.perf_counter() - started
        mean_support = sum(sizes) / len(sizes)
        self.fit_operations_estimate += steps * self.recipe["compact_feature_batch"] * (
            6 * mean_support * self.recipe["memory_feature_dimension"] * 16
            + 6 * (mean_support + 8) * 64 * self.recipe["memory_frequencies"])
        report.update(arm=self.exposure_arm, fit_seconds=self.fit_seconds, inference_device="cpu",
            compact_initial_features_sha256=self.initial_feature_hash, compact_final_features_sha256=self.feature_hash,
            compact_precomputed_sha256=precomputed.hexdigest(), exposure_common_draws_sha256=common_trace.hexdigest(),
            compact_batch_value_draws_sha256=sized_trace.hexdigest(), exposure_support_sizes=list(sizes),
            exposure_training_write_count=write_count, compact_feature_steps=steps,
            compact_feature_losses=self.feature_losses, compact_feature_gradient_norms=self.feature_gradient_norms,
            compact_shuffle_episode_permutations={str(k): v.cpu().tolist() for k, v in permutations.items()},
            memory_feature_dimension=self.recipe["memory_feature_dimension"], memory_update_is_classical=True,
            trained_memory_controller=False, trained_memory_feature_map=bool(steps),
            transport_frozen_during_feature_training=True, parameter_count=report["parameter_count"] + self.projection.size,
            fit_operations_estimate=self.fit_operations_estimate)
        return report
