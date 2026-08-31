from __future__ import annotations

from typing import Any

from .base import CandidateBase, CandidateMetadata
from .masked_baselines import CTWByteModel, PPMDModel
from ..repository_sequence_contract import ByteContext, CompressionTraining


class FrozenRepositoryCoder(CandidateBase):
    MODEL = "ppm_d_order5"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.model = PPMDModel(5) if self.MODEL == "ppm_d_order5" else CTWByteModel(2)
        self.metadata = CandidateMetadata(self.MODEL, "byte_compression", self.MODEL)
        self.meta_fit_ops = self.last_bytes_touched = self.last_update_bytes = 0

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, CompressionTraining):
            raise TypeError("repository coder requires CompressionTraining")
        self.fit_ops = 0
        for item in facts.train_files:
            if self.MODEL == "ppm_d_order5":
                history: tuple[int, ...] = ()
                for target in item.data:
                    self.model.update(history, target)
                    history = (*history[-4:], target)
                    self.fit_ops += min(5, len(history)) + 1
            else:
                self.model.fit_file(item.data)
                self.fit_ops += max(0, len(item.data) - 2) * 3
        if self.MODEL == "ppm_d_order5":
            self.model.prune()
        else:
            self.model.finalize()
        self.meta_fit_ops = self.fit_ops

    def query(self, source: Any, steps: int) -> list[float]:
        if not isinstance(source, ByteContext):
            raise TypeError("repository coder requires ByteContext")
        self.last_ops = 256 * (7 if self.MODEL == "ppm_d_order5" else 3)
        self.last_bytes_touched = self.last_ops * 8
        return self.model.distribution(source.history)

    def update(self, source: ByteContext, target: int) -> None:
        self.update_ops = self.last_update_bytes = 0

    def state_bytes(self) -> int:
        return self.model.state_bytes()


class Candidate(FrozenRepositoryCoder):
    pass
