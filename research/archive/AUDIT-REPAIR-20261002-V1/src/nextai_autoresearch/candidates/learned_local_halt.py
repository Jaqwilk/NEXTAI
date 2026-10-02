from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


class Candidate(CandidateBase):
    metadata = CandidateMetadata(
        "learned_local_halt",
        "adaptive_recurrence",
        "Indexed recurrence with a one-feature perceptron halt policy.",
    )

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.successor: dict[int, int] = {}
        self.max_depth = 0
        self.weight = 0.0
        self.bias = 0.0

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.successor = dict(facts)
        self.max_depth = max_depth
        terminal = next(left for left, right in self.successor.items() if left == right)
        predecessor = {
            right: left for left, right in self.successor.items() if left != right
        }
        examples = [(1.0, 1)]
        current = terminal
        for _ in range(4):
            current = predecessor.get(current)
            if current is None:
                break
            examples.append((0.0, 0))

        self.weight = self.bias = 0.0
        self.fit_ops = 2 * len(self.successor)
        for _ in range(8):
            mistakes = 0
            for feature, target in examples:
                prediction = int(self.bias + self.weight * feature >= 0.0)
                error = target - prediction
                self.fit_ops += 5
                if error:
                    self.weight += error * feature
                    self.bias += error
                    self.fit_ops += 3
                    mistakes += 1
            if not mistakes:
                break

    def query(self, source: int, steps: int) -> int | None:
        current = source
        operations = 0
        for _ in range(self.max_depth + 1):
            following = self.successor.get(current)
            if following is None:
                self.last_ops = operations + 1
                return None
            feature = float(following == current)
            halt = self.bias + self.weight * feature >= 0.0
            operations += 5  # lookup, feature, multiply, add, threshold
            if halt:
                self.last_ops = operations
                return current
            current = following
        self.last_ops = operations
        return None

    def update(self, source: int, target: int) -> None:
        self.successor[source] = target
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 96 + 72 * len(self.successor)
