from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


class Candidate(CandidateBase):
    metadata = CandidateMetadata(
        "adaptive_indexed", "adaptive_control", "Indexed traversal until a terminal."
    )

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.successor: dict[int, int] = {}
        self.terminals: set[int] = set()
        self.max_depth = 0

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.successor = dict(facts)
        self.terminals = {left for left, right in self.successor.items() if left == right}
        self.max_depth = max_depth
        self.fit_ops = len(self.successor)

    def query(self, source: int, steps: int) -> int | None:
        current = source
        for operations in range(self.max_depth + 1):
            if current in self.terminals:
                self.last_ops = operations
                return current
            current = self.successor.get(current)
            if current is None:
                break
        self.last_ops = self.max_depth
        return None

    def update(self, source: int, target: int) -> None:
        self.successor[source] = target
        self.terminals.discard(source)
        if source == target:
            self.terminals.add(source)
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 280 + 72 * len(self.successor) + 36 * len(self.terminals)
