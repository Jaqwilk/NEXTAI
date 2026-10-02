from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np

from .base import CandidateBase, CandidateMetadata
from ..repository_sequence_contract import (
    ByteContext, CompressionTraining, PrivilegedByteContext,
)


ALPHABET = 256
MAX_CONTEXTS = 4_000


def _increment(table: dict[tuple[int, ...], dict[int, int]],
               context: tuple[int, ...], target: int) -> None:
    node = table.get(context)
    if node is None:
        node = {}
        table[context] = node
    node[target] = node.get(target, 0) + 1


def _prune(table: dict[tuple[int, ...], dict[int, int]]) -> dict[tuple[int, ...], dict[int, int]]:
    if len(table) <= MAX_CONTEXTS:
        return table
    ranked = sorted(table.items(), key=lambda item: (sum(item[1].values()), -len(item[0])), reverse=True)
    kept = dict(ranked[:MAX_CONTEXTS])
    kept[()] = table[()]
    return kept


class CompressorCandidate(CandidateBase):
    MODE = "uniform"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.metadata = CandidateMetadata(self.MODE, "byte_compression", self.MODE)
        self.depth = 1
        self.table: dict[tuple[int, ...], dict[int, int]] = {}
        self.local: dict[int, dict[tuple[int, ...], dict[int, int]]] = defaultdict(dict)
        self.weights = (1.0,)
        self.phrases: set[tuple[int, ...]] = set()
        self.slot_phrases: dict[int, tuple[int, ...]] = {}
        self.dense: np.ndarray | None = None
        self.base = np.ones(ALPHABET, dtype=np.float32)
        self.meta_fit_ops = 0
        self.last_bytes_touched = 0
        self.last_update_bytes = 0

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, CompressionTraining):
            raise TypeError("compression candidate requires CompressionTraining")
        self.depth = max(1, int(max_depth))
        self.fit_ops = self.meta_fit_ops = 0
        if self.MODE in {"uniform", "oracle"}:
            return
        if self.MODE == "dense":
            self._fit_dense(facts)
            return
        raw: dict[tuple[int, ...], dict[int, int]] = {}
        if self.MODE == "lz":
            for item in facts.train_files:
                self._fit_lz(item.data, raw)
        else:
            maximum = 0 if self.MODE == "unigram" else self.depth
            for item in facts.train_files:
                data = item.data
                for index, target in enumerate(data):
                    for order in range(min(maximum, index) + 1):
                        _increment(raw, tuple(data[index - order:index]), target)
                        self.fit_ops += 1
        self.fit_ops += int(len(raw) * math.log2(max(2, len(raw))))
        self.table = _prune(raw)
        self.meta_fit_ops = self.fit_ops
        if self.MODE == "hierarchical":
            self._select_weights(facts)

    def _fit_dense(self, facts: CompressionTraining) -> None:
        self.dense = np.full((self.depth, ALPHABET, ALPHABET), 0.25, dtype=np.float32)
        self.base = np.full(ALPHABET, 0.5, dtype=np.float32)
        for item in facts.train_files:
            data = item.data
            for index, target in enumerate(data):
                self.base[target] += 1
                self.fit_ops += 1
                for lag in range(min(self.depth, index)):
                    self.dense[lag, data[index - lag - 1], target] += 1
                    self.fit_ops += 1
        self.meta_fit_ops = self.fit_ops

    def _fit_lz(self, data: tuple[int, ...], table: dict[tuple[int, ...], dict[int, int]]) -> None:
        phrase: tuple[int, ...] = ()
        self.phrases.add(())
        for target in data:
            _increment(table, (), target)
            extension = (*phrase, target)
            self.fit_ops += len(phrase) + 2
            if extension in self.phrases and len(extension) < self.depth:
                phrase = extension
                continue
            _increment(table, phrase[-self.depth:], target)
            if len(self.phrases) < MAX_CONTEXTS:
                self.phrases.add(extension[-self.depth:])
            phrase = ()

    def _select_weights(self, facts: CompressionTraining) -> None:
        losses = [0.0] * (self.depth + 1)
        count = 0
        for item in facts.validation_files:
            for index, target in enumerate(item.data):
                count += 1
                for order in range(self.depth + 1):
                    context = tuple(item.data[max(0, index - order):index])
                    node = self.table.get(context, {})
                    total = sum(node.values())
                    probability = (node.get(target, 0) + 0.5) / (total + 0.5 * ALPHABET)
                    losses[order] -= math.log(max(probability, 2.0 ** -52))
                    self.meta_fit_ops += ALPHABET
        if not count:
            self.weights = tuple(1.0 / (self.depth + 1) for _ in losses)
            return
        per_byte = [value / count for value in losses]
        best = min(per_byte)
        raw = [math.exp(-4.0 * (value - best)) for value in per_byte]
        total = sum(raw)
        self.weights = tuple(value / total for value in raw)

    def _counts(self, context: tuple[int, ...], slot: int) -> tuple[dict[int, int], dict[int, int]]:
        return self.table.get(context, {}), self.local.get(slot, {}).get(context, {})

    def _kt(self, context: tuple[int, ...], slot: int) -> list[float]:
        global_node, local_node = self._counts(context, slot)
        total = sum(global_node.values()) + sum(local_node.values()) + 0.5 * ALPHABET
        return [(global_node.get(value, 0) + local_node.get(value, 0) + 0.5) / total
                for value in range(ALPHABET)]

    def _context_distributions(self, source: ByteContext) -> list[list[float]]:
        history = source.history
        return [self._kt(tuple(history[-order:]) if order else (), source.slot)
                for order in range(min(self.depth, len(history)) + 1)]

    def query(self, source: Any, steps: int) -> list[float]:
        if self.MODE == "oracle":
            if not isinstance(source, PrivilegedByteContext):
                raise TypeError("oracle requires privileged context")
            total = sum(source.file_histogram) + 0.5 * ALPHABET
            self.last_ops = self.last_bytes_touched = ALPHABET
            return [(count + 0.5) / total for count in source.file_histogram]
        if not isinstance(source, ByteContext):
            raise TypeError("public compressor requires ByteContext")
        if self.MODE == "uniform":
            self.last_ops = self.last_bytes_touched = 1
            return [1.0 / ALPHABET] * ALPHABET
        if self.MODE == "dense":
            return self._query_dense(source)
        if self.MODE == "lz":
            history = source.history
            context = ()
            for order in range(min(self.depth, len(history)), 0, -1):
                candidate = tuple(history[-order:])
                if candidate in self.table:
                    context = candidate
                    break
            self.last_ops = ALPHABET + self.depth
            self.last_bytes_touched = self.last_ops * 8
            return self._kt(context, source.slot)
        distributions = self._context_distributions(source)
        if self.MODE == "unigram":
            answer = distributions[0]
        elif self.MODE == "ppm":
            answer = distributions[0]
            for order, current in enumerate(distributions[1:], 1):
                node, local = self._counts(tuple(source.history[-order:]), source.slot)
                total = sum(node.values()) + sum(local.values())
                weight = total / (total + len(node) + len(local) + 1)
                answer = [weight * value + (1.0 - weight) * prior
                          for value, prior in zip(current, answer)]
        elif self.MODE == "ctw":
            answer = distributions[0]
            for order, current in enumerate(distributions[1:], 1):
                node, local = self._counts(tuple(source.history[-order:]), source.slot)
                total = sum(node.values()) + sum(local.values())
                weight = total / (total + ALPHABET)
                answer = [(1.0 - weight) * prior + weight * value
                          for prior, value in zip(answer, current)]
        else:
            weights = self.weights[:len(distributions)]
            scale = sum(weights)
            answer = [sum(weight * distribution[value]
                          for weight, distribution in zip(weights, distributions)) / scale
                      for value in range(ALPHABET)]
        self.last_ops = len(distributions) * ALPHABET * 2
        self.last_bytes_touched = self.last_ops * 8
        return answer

    def _query_dense(self, source: ByteContext) -> list[float]:
        assert self.dense is not None
        base_logits = np.log(self.base.astype(np.float64)) - math.log(float(self.base.sum()))
        logits = base_logits.copy()
        lag_count = min(self.depth, len(source.history))
        for lag in range(lag_count):
            row = self.dense[lag, source.history[-lag - 1]].astype(np.float64)
            logits += (np.log(row) - math.log(float(row.sum())) - base_logits) / (lag_count + 1)
        logits -= float(logits.max())
        probabilities = np.exp(logits)
        probabilities /= probabilities.sum()
        local = self.local.get(source.slot, {}).get((), {})
        if local:
            local_total = sum(local.values())
            weight = local_total / (local_total + 256.0)
            probabilities = (1.0 - weight) * probabilities
            for value, count in local.items():
                probabilities[value] += weight * count / local_total
        self.last_ops = (min(self.depth, len(source.history)) * 4 + 5) * ALPHABET
        self.last_bytes_touched = self.last_ops * 8
        return probabilities.tolist()

    def update(self, source: ByteContext, target: int) -> None:
        self.update_ops = self.last_update_bytes = 0
        if self.MODE in {"uniform", "oracle"}:
            return
        slot_table = self.local[source.slot]
        _increment(slot_table, (), int(target))
        self.update_ops = 1
        if source.history and self.MODE not in {"unigram", "dense"}:
            _increment(slot_table, (source.history[-1],), int(target))
            self.update_ops += 1
        if self.MODE == "lz":
            phrase = self.slot_phrases.get(source.slot, ())
            extension = (*phrase, int(target))
            if extension in self.phrases and len(extension) < self.depth:
                self.slot_phrases[source.slot] = extension
            else:
                self.slot_phrases[source.slot] = ()
            self.update_ops += len(phrase) + 1
        self.last_update_bytes = self.update_ops * 16

    def state_bytes(self) -> int:
        local_nodes = sum(len(table) for table in self.local.values())
        local_pairs = sum(len(node) for table in self.local.values() for node in table.values())
        if self.dense is not None:
            core = int(self.dense.nbytes + self.base.nbytes)
        else:
            pairs = sum(len(node) for node in self.table.values())
            core = sum(512 + 8 * len(context) for context in self.table) + 72 * pairs
            core += sum(128 + 8 * len(phrase) for phrase in self.phrases)
        return core + 512 * local_nodes + 72 * local_pairs + 128 * len(self.slot_phrases) + 256


class Candidate(CompressorCandidate):
    MODE = "uniform"
