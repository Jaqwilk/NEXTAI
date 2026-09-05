from typing import Any

from .base import CandidateBase, CandidateMetadata
from ..mechanism_recombination_contract import PrivilegedQuery, PrivilegedTraining


class Candidate(CandidateBase):
    metadata = CandidateMetadata(
        "oracle_composition_graph", "privileged_oracle",
        "Evaluator-only exact lower bound for the held-out composition.",
    )

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, PrivilegedTraining):
            raise TypeError("oracle requires PrivilegedTraining")
        self.fit_ops = 0.0
        self.meta_fit_ops = 0.0

    def query(self, source: Any, steps: int) -> int:
        if not isinstance(source, PrivilegedQuery):
            raise TypeError("oracle requires PrivilegedQuery")
        self.last_ops = 1.0
        self.last_bytes_touched = 8.0
        return source.target

    def update(self, source: Any, target: Any) -> None:
        self.update_ops = 0.0

    def state_bytes(self) -> int:
        return 0
