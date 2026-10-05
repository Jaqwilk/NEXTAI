"""Training observation-noise intervention over the frozen dense implementation."""
import hashlib
import time

import numpy as np

from .pvm01_core import parameter_hash
from .pvm01_repro_core import Candidate as Reference


def arrays_hash(*arrays):
    digest = hashlib.sha256()
    for value in arrays:
        array = np.ascontiguousarray(value)
        digest.update(str((array.shape, array.dtype.str)).encode())
        digest.update(array.tobytes())
    return digest.hexdigest()


def mixed_training_sets(sets, seed, policy):
    if set(sets or {}) != {32, 128}:
        raise ValueError("Mixed noise requires both unchanged training support sizes")
    rng = np.random.default_rng(seed ^ policy["noise_rng_seed_xor"])
    result = {}
    for size in sorted(sets):
        support, queries, targets = sets[size]
        if (support.shape != (128, size, 64) or queries.shape != (128, 8, 64)
                or targets.shape != (128, 8) or support.dtype != np.float32
                or queries.dtype != np.float32 or targets.dtype != np.int64
                or not np.isfinite(support).all() or not np.isfinite(queries).all()):
            raise ValueError("Malformed unchanged dense training sets")
        copied = [array.copy() for array in (support, queries, targets)]
        for array in copied[:2]:
            selected = array[policy["augmented_episode_parity"]::2]
            selected += rng.normal(0, policy["independent_added_gaussian_std"], selected.shape).astype(np.float32)
        result[size] = tuple(copied)
    return result


class Candidate(Reference):
    def __init__(self, seed, arm, recipe):
        if arm not in {"dense_mixed", "dense_cached_cpu_mixed", "dense_cached_cuda_mixed"}:
            raise ValueError("Only preregistered mixed-noise dense roles")
        self.noise_arm = arm
        super().__init__(seed, arm.removesuffix("_mixed"), recipe)

    def fit(self, writes, queries, validation_writes, validation_queries, sets=None):
        tick = time.perf_counter()
        initial_decoder = parameter_hash(self.decoder)
        effective = mixed_training_sets(sets, self.seed, self.recipe["dense_noise_augmentation"])
        augmentation_seconds = time.perf_counter() - tick
        report = super().fit(writes, queries, validation_writes, validation_queries, effective)
        self.fit_seconds += augmentation_seconds
        report.update(arm=self.noise_arm, fit_seconds=self.fit_seconds,
                      initial_decoder_sha256=initial_decoder,
                      base_dense_sets_sha256={str(k): arrays_hash(*v) for k, v in sets.items()},
                      effective_dense_sets_sha256={str(k): arrays_hash(*v) for k, v in effective.items()},
                      augmentation_seconds_included_in_fit=augmentation_seconds,
                      augmentation_copied_bytes=sum(a.nbytes for v in effective.values() for a in v),
                      augmentation_noise_scalar_samples=sum(a[1::2].size for v in effective.values() for a in v[:2]),
                      augmentation_policy=self.recipe["dense_noise_augmentation"])
        return report
