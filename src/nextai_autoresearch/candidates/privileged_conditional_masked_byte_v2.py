from typing import Any

from .masked_byte_core import A, MaskedByteCandidate
from ..masked_refinement_contract import MASK, PrivilegedMaskedQuery


class Candidate(MaskedByteCandidate):
    MODE = "oracle"

    def query(self, source: Any, steps: int) -> list[list[float]]:
        if not isinstance(source, PrivilegedMaskedQuery):
            raise TypeError("privileged support control requires privileged query")
        if len(source.public.masked_positions) != len(source.target):
            raise ValueError("privileged targets must align with masked positions")
        output = []
        for position, target in zip(
            source.public.masked_positions, source.target, strict=True
        ):
            if source.public.snapshot[position] != MASK:
                raise ValueError("privileged target position is not masked")
            row = [0.0] * A
            row[target] = 1.0
            output.append(row)
        self.last_ops = self.last_bytes_touched = len(output)
        self.last_critical_path_steps = 1
        return output
