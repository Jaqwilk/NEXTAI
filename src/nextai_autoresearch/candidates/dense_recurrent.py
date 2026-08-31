import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata, UnsupportedScale


class Candidate(CandidateBase):
    metadata = CandidateMetadata(
        name="dense_recurrent",
        family="dense_recurrent_control",
        description="Dense one-hot recurrent transition; exact but touches the full state matrix per hop.",
    )

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.matrix = np.zeros((0, 0), dtype=np.float32)

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        if universe_size > 4096:
            raise UnsupportedScale("dense_recurrent caps universe_size at 4096")
        self.matrix = np.zeros((universe_size, universe_size), dtype=np.float32)
        count = 0
        for source, target in facts:
            self.matrix[source, target] = 1.0
            count += 1
        self.fit_ops = universe_size * universe_size + count

    def query(self, source: int, steps: int) -> int | None:
        size = int(self.matrix.shape[0])
        if source < 0 or source >= size:
            self.last_ops = 1
            return None
        state = np.zeros(size, dtype=np.float32)
        state[source] = 1.0
        for _ in range(steps):
            state = state @ self.matrix
        self.last_ops = max(1, 2 * size * size * steps)
        if not bool(np.any(state)):
            return None
        return int(np.argmax(state))

    def update(self, source: int, target: int) -> None:
        old_size = int(self.matrix.shape[0])
        new_size = max(old_size, source + 1, target + 1)
        operations = 1
        if new_size > old_size:
            expanded = np.zeros((new_size, new_size), dtype=np.float32)
            expanded[:old_size, :old_size] = self.matrix
            self.matrix = expanded
            operations += new_size * new_size
        self.matrix[source, :] = 0.0
        self.matrix[source, target] = 1.0
        self.update_ops = operations + new_size

    def state_bytes(self) -> int:
        return int(self.matrix.nbytes)

