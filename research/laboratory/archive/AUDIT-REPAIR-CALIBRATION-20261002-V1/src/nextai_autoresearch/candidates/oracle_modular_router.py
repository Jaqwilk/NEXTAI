from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


class Candidate(CandidateBase):
    metadata = CandidateMetadata(
        "oracle_modular_router",
        "sparse_modularity",
        "Perfect table router with one active constant-capacity expert per hop.",
    )
    capacity = 16

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.router: dict[int, int] = {}
        self.modules: list[dict[int, int]] = []
        self.terminals: set[int] = set()
        self.max_depth = 0

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.router, self.modules, self.terminals = {}, [], set()
        self.max_depth = max_depth
        for index, (source, target) in enumerate(facts):
            module_id = index // self.capacity
            if module_id == len(self.modules):
                self.modules.append({})
            self.router[source] = module_id
            self.modules[module_id][source] = target
            if source == target:
                self.terminals.add(source)
        self.fit_ops = 2 * len(self.router)

    def query(self, source: int, steps: int) -> int | None:
        current, operations = source, 0
        for _ in range(self.max_depth + 1):
            if current in self.terminals:
                self.last_ops = operations
                return current
            module_id = self.router.get(current)
            operations += 1
            if module_id is None:
                break
            current = self.modules[module_id].get(current)
            operations += 1
            if current is None:
                break
        self.last_ops = operations
        return None

    def update(self, source: int, target: int) -> None:
        module_id = self.router.get(source)
        if module_id is None:
            if not self.modules or len(self.modules[-1]) == self.capacity:
                self.modules.append({})
            module_id = len(self.modules) - 1
            self.router[source] = module_id
        self.modules[module_id][source] = target
        self.terminals.discard(source)
        if source == target:
            self.terminals.add(source)
        self.update_ops = 2

    def state_bytes(self) -> int:
        facts = sum(map(len, self.modules))
        return (
            280
            + 72 * len(self.router)
            + 72 * facts
            + 64 * len(self.modules)
            + 36 * len(self.terminals)
        )
