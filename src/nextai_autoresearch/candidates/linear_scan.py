from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


class Candidate(CandidateBase):
    metadata = CandidateMetadata(
        name="linear_scan",
        family="unindexed_memory",
        description="Stores facts in a list and scans all knowledge for every reasoning hop.",
    )

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.facts: list[tuple[int, int]] = []

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.facts = list(facts)
        self.fit_ops = len(self.facts)

    def query(self, source: int, steps: int) -> int | None:
        current = source
        operations = 0
        for _ in range(steps):
            found = None
            for left, right in self.facts:
                operations += 1
                if left == current:
                    found = right
                    break
            if found is None:
                self.last_ops = operations
                return None
            current = found
        self.last_ops = operations
        return current

    def update(self, source: int, target: int) -> None:
        operations = 0
        for index, (left, _) in enumerate(self.facts):
            operations += 1
            if left == source:
                self.facts[index] = (source, target)
                self.update_ops = operations
                return
        self.facts.append((source, target))
        self.update_ops = operations + 1

    def state_bytes(self) -> int:
        return 56 + len(self.facts) * 112

