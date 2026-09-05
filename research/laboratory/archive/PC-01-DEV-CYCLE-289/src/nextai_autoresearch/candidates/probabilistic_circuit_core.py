from __future__ import annotations

import math
from collections import Counter

import numpy as np

from .base import CandidateBase, CandidateMetadata


def _mi_matrix(data: np.ndarray) -> np.ndarray:
    count, width = data.shape
    if not count:
        return np.zeros((width, width))
    values = data.astype(np.int64)
    ones = values.mean(axis=0)
    both = values.T @ values / count
    result = np.zeros((width, width))
    for left in range(width):
        for right in range(left + 1, width):
            probabilities = (
                1 - ones[left] - ones[right] + both[left, right],
                ones[right] - both[left, right],
                ones[left] - both[left, right],
                both[left, right],
            )
            score = 0.0
            for state, joint in enumerate(probabilities):
                if joint > 0:
                    first, second = state // 2, state % 2
                    marginal = (ones[left] if first else 1 - ones[left]) * \
                               (ones[right] if second else 1 - ones[right])
                    if marginal > 0:
                        score += joint * math.log(joint / marginal)
            result[left, right] = result[right, left] = score
    return result


def _matching(matrix: np.ndarray, variables: list[int]) -> tuple[tuple[int, int], ...]:
    remaining, pairs = set(variables), []
    while remaining:
        left, right = max(
            ((a, b) for a in remaining for b in remaining if a < b),
            key=lambda pair: (matrix[pair], -pair[0], -pair[1]),
        )
        pairs.append((left, right))
        remaining.remove(left)
        remaining.remove(right)
    return tuple(pairs)


def _factor(samples: np.ndarray, left: int, right: int) -> np.ndarray:
    table = np.ones((2, 2), dtype=float)
    for row in samples:
        table[row[left], row[right]] += 1.0
    return table / table.sum()


class ProbabilisticCircuitCandidate(CandidateBase):
    metadata = CandidateMetadata("probabilistic-circuit", "probabilistic", "Conditional circuit controls")

    def __init__(self, seed: int = 0, mode: str = "uniform") -> None:
        super().__init__(seed)
        self.mode = mode
        self.samples = np.empty((0, 0), dtype=np.uint8)
        self.selector = -1
        self.matchings: tuple[tuple[tuple[int, int], ...], ...] = ((), ())
        self.factors: tuple[tuple[np.ndarray, ...], ...] = ((), ())
        self.prior = (0.5, 0.5)
        self.tree: list[list[int]] = []
        self.root_probability = 0.5
        self.conditionals: dict[tuple[int, int], np.ndarray] = {}
        self.joint = Counter()
        self.edges: tuple[tuple[int, int], ...] = ()
        self.edge_factors: dict[tuple[int, int], np.ndarray] = {}
        self.node_probabilities = np.empty(0)
        self.last_comparisons = self.last_bytes_touched = self.rebuilt_nodes = 0

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        del universe_size, max_depth
        oracle = self.mode == "oracle"
        public = facts.public if oracle else facts
        self.samples = np.asarray(public.samples, dtype=np.uint8)
        rows, width = self.samples.shape
        self.fit_ops = rows * width
        self.rebuilt_nodes = 0
        if self.mode == "uniform":
            return
        if self.mode == "joint":
            self.joint = Counter(map(tuple, self.samples.tolist()))
            self.fit_ops += rows
            return
        if self.mode == "autoregressive":
            return
        if oracle:
            self.selector, self.matchings = facts.selector, facts.matchings
            self.prior = (0.5, 0.5)
            self.factors = tuple(tuple(np.array([[(1-e)/2, e/2], [e/2, (1-e)/2]])
                                       for e in eps) for eps in facts.epsilons)
            self.fit_ops = 0
            return
        if self.mode == "tree":
            self._fit_tree(self.samples)
        elif self.mode == "pairwise":
            self._fit_pairwise(self.samples)
        elif self.mode == "fixed":
            self.selector = 0
            variables = [index for index in range(width) if index != self.selector]
            fixed = tuple(zip(variables[::2], variables[1::2]))
            self.matchings = (fixed, fixed)
            self._fit_context_factors(self.samples)
        else:
            self._discover_context(self.samples, learned=self.mode == "learned")

    def _discover_context(self, samples: np.ndarray, *, learned: bool) -> None:
        rows, width = samples.shape
        best = None
        for selector in range(width):
            variables = [index for index in range(width) if index != selector]
            score, matchings = 0.0, []
            for value in (0, 1):
                matrix = _mi_matrix(samples[samples[:, selector] == value])
                matching = _matching(matrix, variables)
                score += sum(matrix[left, right] for left in variables for right in variables if left < right)
                score -= sum(matrix[pair] for pair in matching)
                matchings.append(matching)
            proposal = (score, selector, tuple(matchings))
            if best is None or proposal[:2] < best[:2]:
                best = proposal
        assert best is not None
        _, self.selector, self.matchings = best
        self.fit_ops += width * 2 * rows * (width - 1) ** 2
        if learned:
            self.fit_ops += rows * width
        self._fit_context_factors(samples)

    def _fit_context_factors(self, samples: np.ndarray) -> None:
        counts = [int(np.sum(samples[:, self.selector] == value)) for value in (0, 1)]
        self.prior = ((counts[0] + 1) / (len(samples) + 2), (counts[1] + 1) / (len(samples) + 2))
        self.factors = tuple(
            tuple(_factor(samples[samples[:, self.selector] == context], *pair)
                  for pair in self.matchings[context]) for context in (0, 1)
        )
        self.fit_ops += len(samples) * sum(len(matching) for matching in self.matchings)

    def _fit_tree(self, samples: np.ndarray) -> None:
        width = samples.shape[1]
        matrix = _mi_matrix(samples)
        chosen, edges = {0}, []
        while len(chosen) < width:
            edge = max(((left, right) for left in chosen for right in range(width) if right not in chosen),
                       key=lambda pair: matrix[pair])
            edges.append(edge)
            chosen.add(edge[1])
        self.tree = [[] for _ in range(width)]
        self.root_probability = (float(samples[:, 0].sum()) + 1) / (len(samples) + 2)
        for parent, child in edges:
            self.tree[parent].append(child)
            table = np.ones((2, 2), dtype=float)
            for row in samples:
                table[row[parent], row[child]] += 1
            self.conditionals[parent, child] = table / table.sum(axis=1, keepdims=True)
        self.fit_ops += len(samples) * width * width + len(samples) * len(edges)

    def _fit_pairwise(self, samples: np.ndarray) -> None:
        width = samples.shape[1]
        matrix = _mi_matrix(samples)
        degrees = [0] * width
        edges = []
        for left, right in sorted(((a, b) for a in range(width) for b in range(a + 1, width)),
                                  key=lambda pair: matrix[pair], reverse=True):
            if degrees[left] < 1 and degrees[right] < 1:
                edges.append((left, right))
                degrees[left] += 1
                degrees[right] += 1
            if len(edges) == width // 2:
                break
        self.edges = tuple(edges)
        self.edge_factors = {}
        self.node_probabilities = (samples.sum(axis=0) + 1) / (len(samples) + 2)
        for edge in self.edges:
            table = _factor(samples, *edge)
            marginals = np.outer([1-self.node_probabilities[edge[0]], self.node_probabilities[edge[0]]],
                                 [1-self.node_probabilities[edge[1]], self.node_probabilities[edge[1]]])
            self.edge_factors[edge] = table / marginals
        self.fit_ops += len(samples) * width * width + len(samples) * len(edges)

    @staticmethod
    def _context_likelihood(evidence: dict[int, int], context: int, selector: int,
                            prior: tuple[float, float], matching, factors) -> float:
        if selector in evidence and evidence[selector] != context:
            return 0.0
        result = prior[context]
        for (left, right), table in zip(matching, factors):
            if left in evidence and right in evidence:
                result *= table[evidence[left], evidence[right]]
            elif left in evidence:
                result *= table[evidence[left], :].sum()
            elif right in evidence:
                result *= table[:, evidence[right]].sum()
        return float(result)

    def _context_probability(self, query) -> float:
        evidence = dict(query.evidence)
        denominator = sum(self._context_likelihood(evidence, c, self.selector, self.prior,
                          self.matchings[c], self.factors[c]) for c in (0, 1))
        evidence[query.target] = 1
        numerator = sum(self._context_likelihood(evidence, c, self.selector, self.prior,
                        self.matchings[c], self.factors[c]) for c in (0, 1))
        self.last_ops = 4 + sum(len(matching) for matching in self.matchings) * 2
        return numerator / denominator

    def _tree_likelihood(self, evidence: dict[int, int]) -> float:
        operations = 0
        def message(node: int, parent_value: int | None = None) -> float:
            nonlocal operations
            values = (evidence[node],) if node in evidence else (0, 1)
            total = 0.0
            for value in values:
                weight = ((self.root_probability if value else 1-self.root_probability)
                          if parent_value is None else self.conditionals[parent[node], node][parent_value, value])
                for child in self.tree[node]:
                    weight *= message(child, value)
                total += weight
                operations += 1
            return total
        parent = {child: node for node, children in enumerate(self.tree) for child in children}
        result = message(0)
        self.last_ops += operations
        return result

    def _pairwise_likelihood(self, evidence: dict[int, int]) -> float:
        width = len(self.node_probabilities)
        adjacency = [[] for _ in range(width)]
        for left, right in self.edges:
            adjacency[left].append(right); adjacency[right].append(left)
        seen, total = set(), 1.0
        for start in range(width):
            if start in seen:
                continue
            component, stack = [], [start]
            while stack:
                node = stack.pop()
                if node in seen: continue
                seen.add(node); component.append(node); stack.extend(adjacency[node])
            assignments = itertools_product(component, evidence)
            subtotal = 0.0
            for assignment in assignments:
                weight = 1.0
                for node, value in assignment.items():
                    probability = self.node_probabilities[node]
                    weight *= probability if value else 1-probability
                for edge in self.edges:
                    if edge[0] in assignment and edge[1] in assignment:
                        weight *= self.edge_factors[edge][assignment[edge[0]], assignment[edge[1]]]
                subtotal += weight
                self.last_ops += len(assignment) + len(self.edges)
            total *= subtotal
        return total

    def query(self, source, steps: int):
        del steps
        evidence = dict(source.evidence)
        self.last_ops = self.last_comparisons = 0
        self.last_bytes_touched = 8 * (len(evidence) + 1)
        if self.mode == "uniform":
            self.last_ops = 1
            return 0.5
        if self.mode == "joint":
            matches = total = positive = 0
            for row, count in self.joint.items():
                self.last_ops += len(evidence) + 1
                if all(row[index] == value for index, value in evidence.items()):
                    matches += count
                    positive += count * row[source.target]
                total += count
            return (positive + 1) / (matches + 2) if matches else (sum(c*r[source.target] for r,c in self.joint.items()) + 1) / (total + 2)
        if self.mode == "autoregressive":
            prefix = {index: value for index, value in evidence.items() if index < source.target}
            selected = self.samples
            for index, value in prefix.items():
                selected = selected[selected[:, index] == value]
                self.last_ops += len(selected)
            return (float(selected[:, source.target].sum()) + 1) / (len(selected) + 2)
        if self.mode == "tree":
            denominator = self._tree_likelihood(evidence)
            evidence[source.target] = 1
            return self._tree_likelihood(evidence) / denominator
        if self.mode == "pairwise":
            denominator = self._pairwise_likelihood(evidence)
            evidence[source.target] = 1
            return self._pairwise_likelihood(evidence) / denominator
        return self._context_probability(source)

    def update(self, source, target) -> None:
        del target
        public = source.public if self.mode == "oracle" else source
        new_samples = np.asarray(public.samples, dtype=np.uint8)
        self.update_ops = int(new_samples.size)
        self.rebuilt_nodes = 0
        if self.mode == "uniform":
            return
        if self.mode == "joint":
            self.joint.update(map(tuple, new_samples.tolist()))
            return
        if self.mode == "autoregressive":
            self.samples = np.concatenate((self.samples, new_samples))
            return
        if self.mode in {"tree", "pairwise"}:
            self.rebuilt_nodes = self.circuit_nodes()
            self.fit_ops = 0
            (self._fit_tree if self.mode == "tree" else self._fit_pairwise)(new_samples)
            self.update_ops += self.fit_ops
            return
        if self.mode == "oracle":
            self.factors = tuple(tuple(np.array([[(1-e)/2, e/2], [e/2, (1-e)/2]])
                                       for e in eps) for eps in source.epsilons)
            self.rebuilt_nodes = 1
            return
        proposals = []
        for context in (0, 1):
            subset = new_samples[new_samples[:, self.selector] == context]
            for index, pair in enumerate(self.matchings[context]):
                table = _factor(subset, *pair)
                proposals.append((float(np.abs(table - self.factors[context][index]).sum()), context, index, table))
        _, context, index, table = max(proposals, key=lambda item: item[0])
        factors = [list(group) for group in self.factors]
        factors[context][index] = table
        self.factors = tuple(tuple(group) for group in factors)
        self.rebuilt_nodes = 1
        self.update_ops += len(proposals) * 4

    def circuit_nodes(self) -> int:
        width = self.samples.shape[1] if self.samples.ndim == 2 else 0
        if self.mode == "uniform": return 1
        if self.mode == "joint": return len(self.joint)
        if self.mode == "autoregressive": return width
        if self.mode == "tree": return max(1, 2 * width - 1)
        if self.mode == "pairwise": return width + len(self.edges)
        return 3 + sum(len(matching) for matching in self.matchings)

    def state_bytes(self) -> int:
        if self.mode == "joint": return len(self.joint) * (self.samples.shape[1] + 8)
        if self.mode == "autoregressive": return int(self.samples.size)
        if self.mode == "tree": return 8 * (1 + 4 * len(self.conditionals))
        if self.mode == "pairwise": return int(8 * (len(self.node_probabilities) + 4 * len(self.edges)))
        if self.mode == "uniform": return 8
        return 24 + 8 * sum(4 * len(group) for group in self.factors)


def itertools_product(component: list[int], evidence: dict[int, int]):
    free = [node for node in component if node not in evidence]
    for mask in range(1 << len(free)):
        assignment = {node: evidence[node] for node in component if node in evidence}
        assignment.update({node: (mask >> index) & 1 for index, node in enumerate(free)})
        yield assignment


class Candidate(ProbabilisticCircuitCandidate):
    def __init__(self, seed: int):
        super().__init__(seed, "uniform")
