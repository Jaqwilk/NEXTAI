from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


class Candidate(CandidateBase):
    metadata = CandidateMetadata(
        "adaptive_linear_scan", "adaptive_control", "Linear scans until a terminal."
    )

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.facts: list[tuple[int, int]] = []
        self.terminals: set[int] = set()
        self.max_depth = 0

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.facts = list(facts)
        self.terminals = {left for left, right in self.facts if left == right}
        self.max_depth = max_depth
        self.fit_ops = len(self.facts)

    def query(self, source: int, steps: int) -> int | None:
        current, operations = source, 0
        for _ in range(self.max_depth + 1):
            if current in self.terminals:
                self.last_ops = operations
                return current
            for left, right in self.facts:
                operations += 1
                if left == current:
                    current = right
                    break
            else:
                self.last_ops = operations
                return None
        self.last_ops = operations
        return None

    def update(self, source: int, target: int) -> None:
        self.facts.append((source, target))
        if source == target:
            self.terminals.add(source)
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 280 + 112 * len(self.facts) + 36 * len(self.terminals)
