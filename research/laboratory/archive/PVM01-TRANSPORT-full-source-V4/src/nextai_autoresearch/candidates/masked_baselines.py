from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .base import CandidateBase, CandidateMetadata
from ..masked_refinement_contract import MASK, MaskedQuery, MaskedTraining


ALPHABET = 256


class PPMDModel:
    """PPM-D, full exclusion, order 5, frozen inference."""

    def __init__(self, maximum_order: int = 5) -> None:
        self.maximum_order = maximum_order
        self.unigram: dict[int, int] = {}
        self.contexts: dict[tuple[int, ...], dict[int, int]] = {}

    def update(self, history: tuple[int, ...], target: int) -> None:
        for order in range(1, min(self.maximum_order, len(history)) + 1):
            node = self.contexts.setdefault(history[-order:], {})
            node[target] = node.get(target, 0) + 1
        self.unigram[target] = self.unigram.get(target, 0) + 1

    def prune(self, maximum_contexts: int = 4_000) -> None:
        if len(self.contexts) <= maximum_contexts:
            return
        ranked = sorted(
            self.contexts.items(),
            key=lambda item: (sum(item[1].values()), -len(item[0])),
            reverse=True,
        )
        self.contexts = dict(ranked[:maximum_contexts])

    def distribution(self, history: tuple[int, ...]) -> list[float]:
        answer = [0.0] * ALPHABET
        excluded: set[int] = set()
        remaining = 1.0
        nodes = [
            self.contexts.get(history[-order:], {})
            for order in range(min(self.maximum_order, len(history)), 0, -1)
        ]
        nodes.append(self.unigram)
        for node in nodes:
            active = {value: count for value, count in node.items() if value not in excluded}
            total = sum(active.values())
            distinct = len(active)
            if not total or not distinct:
                excluded.update(node)
                continue
            denominator = total + distinct  # PPM-D escape estimate.
            for value, count in active.items():
                answer[value] += remaining * count / denominator
            remaining *= distinct / denominator
            excluded.update(node)
        unseen = [value for value in range(ALPHABET) if value not in excluded]
        if unseen:
            share = remaining / len(unseen)
            for value in unseen:
                answer[value] += share
        else:
            scale = sum(answer)
            answer = [value / scale for value in answer]
        return answer

    def state_bytes(self) -> int:
        return 512 + 72 * len(self.unigram) + sum(
            96 + 8 * len(context) + 72 * len(node)
            for context, node in self.contexts.items()
        )


@dataclass
class _CTWNode:
    counts: dict[int, int] = field(default_factory=dict)
    children: dict[int, "_CTWNode"] = field(default_factory=dict)
    local_weight: float = 1.0

    def update(self, context: tuple[int, ...], target: int) -> None:
        self.counts[target] = self.counts.get(target, 0) + 1
        if context:
            self.children.setdefault(context[0], _CTWNode()).update(context[1:], target)

    def _log_kt(self) -> float:
        total = sum(self.counts.values())
        answer = math.lgamma(ALPHABET / 2) - math.lgamma(total + ALPHABET / 2)
        answer += sum(math.lgamma(count + 0.5) - math.lgamma(0.5)
                      for count in self.counts.values())
        return answer

    def finalize(self) -> float:
        local = self._log_kt()
        if not self.children:
            self.local_weight = 1.0
            return local
        children = sum(child.finalize() for child in self.children.values())
        maximum = max(local, children)
        normalizer = maximum + math.log(math.exp(local - maximum) + math.exp(children - maximum))
        self.local_weight = math.exp(local - normalizer)
        return normalizer - math.log(2.0)

    def distribution(self, context: tuple[int, ...]) -> list[float]:
        total = sum(self.counts.values()) + ALPHABET / 2
        local = [(self.counts.get(value, 0) + 0.5) / total
                 for value in range(ALPHABET)]
        if not context or not self.children:
            return local
        child = self.children.get(context[0])
        deeper = ([1.0 / ALPHABET] * ALPHABET if child is None
                  else child.distribution(context[1:]))
        return [self.local_weight * first + (1.0 - self.local_weight) * second
                for first, second in zip(local, deeper)]

    def state_bytes(self) -> int:
        return 128 + 72 * len(self.counts) + sum(
            64 + child.state_bytes() for child in self.children.values()
        )


class CTWByteModel:
    """Generalized 256-ary CTW with KT(1/2), default depth 2."""

    def __init__(self, depth: int = 2) -> None:
        self.depth = depth
        self.root = _CTWNode()

    def fit_file(self, data: tuple[int, ...]) -> None:
        for index in range(self.depth, len(data)):
            context = tuple(reversed(data[index - self.depth:index]))
            self.root.update(context, data[index])  # Update only after context is fixed.

    def finalize(self) -> None:
        self.root.finalize()

    def distribution(self, history: tuple[int, ...]) -> list[float]:
        context = tuple(reversed(history[-self.depth:]))
        return self.root.distribution(context)

    def state_bytes(self) -> int:
        return self.root.state_bytes()


class _SequentialMaskedBaseline(CandidateBase):
    def update(self, source: Any, target: int) -> None:
        self.update_ops = 0

    def _query(self, source: MaskedQuery, distribution) -> list[list[float]]:
        snapshot = list(source.snapshot)
        output = []
        for position in source.masked_positions:
            history = tuple(value for value in snapshot[:position] if value != MASK)
            row = distribution(history)
            output.append(row)
            snapshot[position] = max(range(ALPHABET), key=row.__getitem__)
        self.last_ops = len(output) * ALPHABET * 18
        self.last_bytes_touched = self.last_ops * 8
        self.last_critical_path_steps = max(1, len(output))
        return output


class PPMMaskedCandidate(_SequentialMaskedBaseline):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.metadata = CandidateMetadata("ppm_d_order5", "masked_byte", "PPM-D order 5")
        self.model = PPMDModel(5)
        self.meta_fit_ops = 0

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, MaskedTraining):
            raise TypeError("PPM baseline requires MaskedTraining")
        self.fit_ops = 0
        for item in facts.train_files:
            history: tuple[int, ...] = ()
            for target in item.data:
                self.model.update(history, target)
                history = (*history[-4:], target)
                self.fit_ops += min(5, len(history)) + 1
        self.model.prune()
        self.meta_fit_ops = self.fit_ops

    def query(self, source: Any, steps: int) -> list[list[float]]:
        if not isinstance(source, MaskedQuery):
            raise TypeError("PPM baseline requires MaskedQuery")
        return self._query(source, self.model.distribution)

    def state_bytes(self) -> int:
        return self.model.state_bytes()


class CTWMaskedCandidate(_SequentialMaskedBaseline):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.metadata = CandidateMetadata("ctw_byte_depth2", "masked_byte", "256-ary CTW depth 2")
        self.model = CTWByteModel(2)
        self.meta_fit_ops = 0

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, MaskedTraining):
            raise TypeError("CTW baseline requires MaskedTraining")
        self.fit_ops = 0
        for item in facts.train_files:
            self.model.fit_file(item.data)
            self.fit_ops += max(0, len(item.data) - self.model.depth) * (self.model.depth + 1)
        self.model.finalize()
        self.meta_fit_ops = self.fit_ops

    def query(self, source: Any, steps: int) -> list[list[float]]:
        if not isinstance(source, MaskedQuery):
            raise TypeError("CTW baseline requires MaskedQuery")
        return self._query(source, self.model.distribution)

    def state_bytes(self) -> int:
        return self.model.state_bytes()


class Candidate(PPMMaskedCandidate):
    pass
