from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

from .base import CandidateBase, CandidateMetadata


CHANNELS = 4
RAW_WIDTH = 12
FEATURES = RAW_WIDTH + 1
RIDGE = 0.001
MAX_LEAVES = 8
MIN_LEAF = 48
MIN_CHILD = 24
NOVELTY_SPAN = 0.20
MIN_RELATIVE_GAIN = 0.05
UPDATE_ETA = 0.05
OUTPUT_BOUND = 1.5
SHUFFLE_SALT = 0x51E17


@dataclass
class Node:
    path: tuple[int, ...]
    weights: np.ndarray
    feature: int | None = None
    threshold: float = 0.0
    left: "Node | None" = None
    right: "Node | None" = None


@dataclass(frozen=True)
class Proposal:
    leaf: Node
    feature: int
    threshold: float
    gain: float
    left_indices: np.ndarray
    right_indices: np.ndarray


def _raw(row: Any) -> tuple[float, ...]:
    return tuple((*row.left, *row.center, *row.right))


def _ridge(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float, int]:
    gram = x.T @ x + RIDGE * np.eye(FEATURES)
    weights = np.linalg.solve(gram, x.T @ y)
    residual = y - x @ weights
    sse = float(np.sum(residual * residual))
    operations = int(len(x) * (FEATURES * FEATURES + FEATURES * CHANNELS + FEATURES * CHANNELS)
                     + FEATURES ** 3 + FEATURES)
    return weights, sse, operations


class LocalExpertTree(CandidateBase):
    metadata = CandidateMetadata(
        "local_expert_tree", "continuous_cellular",
        "Source-identical error/novelty split local affine experts",
    )

    def __init__(self, seed: int = 0, *, mode: str = "aligned") -> None:
        super().__init__(seed)
        if mode not in {"aligned", "shuffled", "frozen"}:
            raise ValueError(mode)
        self.mode = mode
        self.root = Node((), np.zeros((FEATURES, CHANNELS)))
        self.leaves: list[Node] = [self.root]
        self._leaf_indices: dict[tuple[int, ...], np.ndarray] = {}
        self.last_bytes_touched = 0

    @staticmethod
    def _design(rows: Iterable[Any]) -> tuple[np.ndarray, np.ndarray]:
        items = tuple(rows)
        if not items or not all(all(hasattr(row, field) for field in ("left", "center", "right", "target")) for row in items):
            raise TypeError("local expert tree requires Transition rows")
        x = np.asarray([(1.0, *_raw(row)) for row in items], dtype=float)
        y = np.asarray([row.target for row in items], dtype=float)
        return x, y

    def _proposals(self, x: np.ndarray, y: np.ndarray) -> tuple[list[Proposal], int]:
        proposals: list[Proposal] = []
        operations = 0
        for leaf in sorted(self.leaves, key=lambda item: item.path):
            indices = self._leaf_indices[leaf.path]
            if len(indices) < MIN_LEAF:
                continue
            for feature in range(RAW_WIDTH):
                values = x[indices, feature + 1]
                operations += len(indices)
                if float(np.max(values) - np.min(values)) < NOVELTY_SPAN:
                    continue
                ordered = np.sort(values)
                operations += int(len(values) * max(1, math.ceil(math.log2(len(values)))))
                threshold = float((ordered[(len(ordered) - 1) // 2] + ordered[len(ordered) // 2]) / 2)
                left_indices = indices[values <= threshold]
                right_indices = indices[values > threshold]
                operations += len(indices)
                if len(left_indices) < MIN_CHILD or len(right_indices) < MIN_CHILD:
                    continue
                _, parent_sse, parent_ops = _ridge(x[indices], y[indices])
                _, left_sse, left_ops = _ridge(x[left_indices], y[left_indices])
                _, right_sse, right_ops = _ridge(x[right_indices], y[right_indices])
                gain = (parent_sse - left_sse - right_sse) / max(parent_sse, 1e-12)
                operations += parent_ops + left_ops + right_ops + 5
                proposals.append(Proposal(
                    leaf, feature, threshold, float(gain), left_indices, right_indices,
                ))
        return proposals, operations

    def assigned_gains(self, proposals: list[Proposal]) -> tuple[float, ...]:
        gains = [proposal.gain for proposal in proposals]
        if self.mode == "shuffled":
            order = list(range(len(gains)))
            random.Random(self.seed ^ SHUFFLE_SALT).shuffle(order)
            gains = [gains[index] for index in order]
        return tuple(gains)

    def _choose(self, proposals: list[Proposal]) -> Proposal | None:
        if not proposals or self.mode == "frozen":
            return None
        assigned = self.assigned_gains(proposals)
        selected = max(range(len(proposals)), key=lambda index: (assigned[index], -index))
        return proposals[selected] if assigned[selected] >= MIN_RELATIVE_GAIN else None

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        del universe_size
        if max_depth != 16:
            raise ValueError("local expert tree requires frozen maximum depth 16")
        x, y = self._design(facts)
        root_weights, _, operations = _ridge(x, y)
        self.root = Node((), root_weights)
        self.leaves = [self.root]
        self._leaf_indices = {(): np.arange(len(x))}
        while len(self.leaves) < MAX_LEAVES:
            proposals, proposal_ops = self._proposals(x, y)
            operations += proposal_ops
            selected = self._choose(proposals)
            operations += max(0, len(proposals) - 1)
            if selected is None:
                break
            left_weights, _, left_ops = _ridge(x[selected.left_indices], y[selected.left_indices])
            right_weights, _, right_ops = _ridge(x[selected.right_indices], y[selected.right_indices])
            operations += left_ops + right_ops
            leaf = selected.leaf
            leaf.feature = selected.feature
            leaf.threshold = selected.threshold
            leaf.left = Node((*leaf.path, 0), left_weights)
            leaf.right = Node((*leaf.path, 1), right_weights)
            self.leaves.remove(leaf)
            self.leaves.extend((leaf.left, leaf.right))
            del self._leaf_indices[leaf.path]
            self._leaf_indices[leaf.left.path] = selected.left_indices
            self._leaf_indices[leaf.right.path] = selected.right_indices
        self.leaves.sort(key=lambda item: item.path)
        self.fit_ops = int(operations)

    def _route(self, raw: np.ndarray) -> tuple[Node, int]:
        node = self.root
        comparisons = 0
        while node.feature is not None:
            comparisons += 1
            node = node.left if raw[node.feature] <= node.threshold else node.right
            if node is None:
                raise RuntimeError("incomplete local expert tree")
        return node, comparisons

    def _transition(self, left: tuple[float, ...], center: tuple[float, ...],
                    right: tuple[float, ...]) -> tuple[tuple[float, ...], int, int]:
        raw = np.asarray((*left, *center, *right), dtype=float)
        leaf, comparisons = self._route(raw)
        features = np.asarray((1.0, *raw), dtype=float)
        value = np.clip(features @ leaf.weights, -OUTPUT_BOUND, OUTPUT_BOUND)
        operations = RAW_WIDTH + comparisons + FEATURES * CHANNELS + CHANNELS
        touched = int((RAW_WIDTH + leaf.weights.size + comparisons * 2) * 8)
        return tuple(map(float, value)), int(operations), touched

    def query(self, source: Any, steps: int) -> tuple[float, ...]:
        if not all(hasattr(source, field) for field in ("size", "target", "initial")):
            raise TypeError("local expert tree requires sparse public Task")
        zero = (0.0,) * CHANNELS
        state = dict(source.initial)
        operations = len(state) * CHANNELS
        touched = len(state) * CHANNELS * 8
        for _ in range(steps):
            active = set(state)
            positions = active | {(position - 1) % source.size for position in active} \
                | {(position + 1) % source.size for position in active}
            updated = {}
            for position in positions:
                value, work, byte_count = self._transition(
                    state.get((position - 1) % source.size, zero),
                    state.get(position, zero),
                    state.get((position + 1) % source.size, zero),
                )
                updated[position] = value
                operations += work
                touched += byte_count
            state = updated
        self.last_ops = int(operations)
        self.last_bytes_touched = int(touched)
        return state.get(source.target, zero)

    def update(self, source: Any, target: Any) -> None:
        del target
        raw = np.asarray(_raw(source), dtype=float)
        features = np.asarray((1.0, *raw), dtype=float)
        leaf, comparisons = self._route(raw)
        error = np.asarray(source.target, dtype=float) - features @ leaf.weights
        leaf.weights += UPDATE_ETA / (1.0 + float(features @ features)) * np.outer(features, error)
        self.update_ops = int(comparisons + FEATURES * CHANNELS * 3 + FEATURES)
        self.last_update_bytes = int(leaf.weights.nbytes + features.nbytes)

    def state_bytes(self) -> int:
        nodes: list[Node] = []
        stack = [self.root]
        while stack:
            node = stack.pop()
            nodes.append(node)
            if node.left is not None:
                stack.extend((node.left, node.right))
        return int(sum(node.weights.nbytes + 48 for node in nodes) + 64)


class Candidate(LocalExpertTree):
    pass
