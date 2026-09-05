from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .candidates.base import CandidateBase


Bytes = tuple[int, ...]
Labels = tuple[int, ...]


@dataclass(frozen=True)
class Demo:
    raw: Bytes
    labels: Labels


@dataclass(frozen=True)
class Episode:
    supports: tuple[Demo, ...]
    distractors: tuple[Bytes, ...]


@dataclass(frozen=True)
class OracleEpisode:
    episode: Episode
    motifs: tuple[tuple[int, Bytes], ...]


@dataclass(frozen=True)
class ByteQuery:
    raw: Bytes


def _corpus_bytes(episode: Episode) -> int:
    return sum(len(row.raw) for row in episode.supports) + sum(map(len, episode.distractors))


def _ngrams(raw: Bytes, low: int, high: int) -> Iterable[Bytes]:
    for size in range(low, min(high, len(raw)) + 1):
        for start in range(len(raw) - size + 1):
            yield raw[start : start + size]


def _presence(episode: Episode, phrases: set[Bytes] | None, low: int, high: int):
    masks: dict[Bytes, int] = {}
    distractor_hits: dict[Bytes, int] = {}
    ops = 0
    for index, demo in enumerate(episode.supports):
        if phrases is None:
            seen = set(_ngrams(demo.raw, low, high))
            ops += sum(max(0, len(demo.raw) - size + 1) for size in range(low, min(high, len(demo.raw)) + 1))
        else:
            seen = {p for p in phrases if _contains(demo.raw, p)}
            ops += sum(max(0, len(demo.raw) - len(item) + 1) for item in phrases)
        for item in seen:
            masks[item] = masks.get(item, 0) | (1 << index)
    for raw in episode.distractors:
        if phrases is None:
            seen = set(_ngrams(raw, low, high))
            ops += sum(max(0, len(raw) - size + 1) for size in range(low, min(high, len(raw)) + 1))
        else:
            seen = {p for p in phrases if _contains(raw, p)}
            ops += sum(max(0, len(raw) - len(item) + 1) for item in phrases)
        for item in seen:
            distractor_hits[item] = distractor_hits.get(item, 0) + 1
    return masks, distractor_hits, ops


def _contains(raw: Bytes, phrase: Bytes) -> bool:
    return any(raw[i : i + len(phrase)] == phrase for i in range(len(raw) - len(phrase) + 1))


def _label_masks(episode: Episode) -> dict[int, int]:
    labels = {label for demo in episode.supports for label in demo.labels}
    return {label: sum((1 << i) for i, demo in enumerate(episode.supports) if label in demo.labels) for label in labels}


def discover_exact(episode: Episode, low: int = 3, high: int = 7) -> tuple[dict[Bytes, int], int]:
    masks, distractors, ops = _presence(episode, None, low, high)
    full = (1 << len(episode.supports)) - 1
    result: dict[Bytes, int] = {}
    for label, positive in _label_masks(episode).items():
        negative = full ^ positive
        valid = [p for p, mask in masks.items() if mask & positive == positive and not mask & negative and not distractors.get(p)]
        ops += len(masks)
        if valid:
            best = max(valid, key=lambda p: (len(p), p))
            result[best] = label
    return result, ops


def discover_contrastive(episode: Episode) -> tuple[dict[Bytes, int], int]:
    masks, distractors, ops = _presence(episode, None, 2, 7)
    full = (1 << len(episode.supports)) - 1
    result: dict[Bytes, int] = {}
    for label, positive in _label_masks(episode).items():
        negative = full ^ positive
        positives, negatives = positive.bit_count(), max(1, negative.bit_count())
        ranked = []
        for phrase, mask in masks.items():
            recall = (mask & positive).bit_count() / positives
            leakage = (mask & negative).bit_count() / negatives + distractors.get(phrase, 0) / max(1, len(episode.distractors))
            ranked.append((recall - leakage + len(phrase) / 100.0, phrase, recall, leakage))
            ops += 6
        ranked.sort(reverse=True)
        if ranked and ranked[0][2] == 1.0 and ranked[0][3] == 0.0:
            result[ranked[0][1]] = label
    return result, ops


def _lz_phrases(streams: Iterable[Bytes]) -> tuple[set[Bytes], int]:
    phrases: set[Bytes] = set()
    ops = 0
    for raw in streams:
        current: Bytes = ()
        for value in raw:
            trial = current + (value,)
            ops += 1
            if trial in phrases:
                current = trial
            else:
                phrases.add(trial)
                current = ()
        if current:
            phrases.add(current)
    return {p for p in phrases if len(p) >= 2}, ops


def _sequitur_phrases(streams: Iterable[Bytes]) -> tuple[set[Bytes], int]:
    sequences: list[list[Bytes]] = [[(value,) for value in raw] for raw in streams]
    phrases: set[Bytes] = set()
    ops = 0
    for _ in range(64):
        counts: dict[tuple[Bytes, Bytes], int] = {}
        for sequence in sequences:
            for pair in zip(sequence, sequence[1:]):
                counts[pair] = counts.get(pair, 0) + 1
                ops += 1
        repeated = [(count, left + right, (left, right)) for (left, right), count in counts.items() if count >= 2]
        if not repeated:
            break
        _, expansion, chosen = max(repeated, key=lambda row: (row[0], len(row[1]), row[1]))
        phrases.add(expansion)
        for sequence in sequences:
            rewritten: list[Bytes] = []
            index = 0
            while index < len(sequence):
                if index + 1 < len(sequence) and (sequence[index], sequence[index + 1]) == chosen:
                    rewritten.append(expansion)
                    index += 2
                else:
                    rewritten.append(sequence[index])
                    index += 1
                ops += 1
            sequence[:] = rewritten
    return phrases, ops


def discover_from_phrases(episode: Episode, kind: str) -> tuple[dict[Bytes, int], int]:
    streams = [demo.raw for demo in episode.supports] + list(episode.distractors)
    phrases, ops = (_lz_phrases(streams) if kind == "lz" else _sequitur_phrases(streams))
    phrases = {phrase for phrase in phrases if 2 <= len(phrase) <= 12}
    masks, distractors, presence_ops = _presence(episode, phrases, 2, 12)
    ops += presence_ops
    full = (1 << len(episode.supports)) - 1
    result: dict[Bytes, int] = {}
    for label, positive in _label_masks(episode).items():
        negative = full ^ positive
        valid = [p for p, mask in masks.items() if mask & positive == positive and not mask & negative and not distractors.get(p)]
        ops += len(phrases)
        if valid:
            result[max(valid, key=lambda p: (len(p), p))] = label
    return result, ops


class MotifCandidate(CandidateBase):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.fit_ops = self.update_ops = self.last_ops = 0
        self.last_input_ops = self.last_search_ops = self.last_execution_ops = 0
        self.last_memory_reads = self.last_bytes_loaded = 0
        self.last_cache_hit = False

    def _record(self, raw: Bytes, search: int, execution: int, hit: bool) -> None:
        self.last_input_ops = len(raw)
        self.last_search_ops = search
        self.last_execution_ops = execution
        self.last_memory_reads = len(raw) + search
        self.last_bytes_loaded = len(raw) + self.state_bytes()
        self.last_ops = len(raw) + search + execution
        self.last_cache_hit = hit


class SignatureComposer(MotifCandidate):
    method = "contrastive"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.signatures: dict[Bytes, int] = {}

    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        if self.method == "fixed":
            self.signatures, self.fit_ops = discover_exact(episode, 3, 3)
        elif self.method in {"lz", "sequitur"}:
            self.signatures, self.fit_ops = discover_from_phrases(episode, self.method)
        else:
            self.signatures, self.fit_ops = discover_contrastive(episode)

    def _decode(self, raw: Bytes, steps: int) -> tuple[Labels, int]:
        output, index, ops = [], 0, 0
        ordered = sorted(self.signatures.items(), key=lambda row: (-len(row[0]), row[0]))
        while index < len(raw) and len(output) < steps:
            match = None
            for phrase, label in ordered:
                ops += len(phrase)
                if raw[index : index + len(phrase)] == phrase:
                    match = (phrase, label)
                    break
            if match:
                output.append(match[1])
                index += len(match[0])
            else:
                index += 1
        return tuple(output), ops

    def query(self, query: ByteQuery, steps: int) -> Labels:
        answer, ops = self._decode(query.raw, steps)
        self._record(query.raw, ops, len(answer), len(answer) == steps)
        return answer

    def update(self, episode: Episode, target: object = None) -> None:
        self.fit(episode, 0, 0)
        self.update_ops = self.fit_ops

    def state_bytes(self) -> int:
        return 64 + sum(40 + len(phrase) for phrase in self.signatures)


class FixedTrigramComposer(SignatureComposer):
    method = "fixed"


class LZPhraseComposer(SignatureComposer):
    method = "lz"


class SequiturGrammarComposer(SignatureComposer):
    method = "sequitur"


class ContrastiveMotifComposer(SignatureComposer):
    method = "contrastive"


class ExactSuffixComposer(SignatureComposer):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.trie: dict[int, dict] = {}

    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        self.signatures, self.fit_ops = discover_exact(episode)
        self.trie = {}
        for phrase, label in self.signatures.items():
            node = self.trie
            for value in phrase:
                node = node.setdefault(value, {})
            node[-1] = label
            self.fit_ops += len(phrase)

    def _decode(self, raw: Bytes, steps: int) -> tuple[Labels, int]:
        output, start, ops = [], 0, 0
        while start < len(raw) and len(output) < steps:
            node, end, found = self.trie, start, None
            while end < len(raw) and raw[end] in node:
                node = node[raw[end]]
                end += 1
                ops += 1
                if -1 in node:
                    found = (end, node[-1])
            ops += 1
            if found:
                start, label = found
                output.append(label)
            else:
                start += 1
        return tuple(output), ops

    def state_bytes(self) -> int:
        return 64 + sum(48 + len(phrase) * 16 for phrase in self.signatures)


class RawSupportRescan(ExactSuffixComposer):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.episode = Episode((), ())

    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        self.episode = episode
        self.fit_ops = _corpus_bytes(episode)
        self.signatures = {}
        self.trie = {}

    def query(self, query: ByteQuery, steps: int) -> Labels:
        signatures, discovery = discover_exact(self.episode)
        self.signatures = signatures
        self.trie = {}
        for phrase, label in signatures.items():
            node = self.trie
            for value in phrase:
                node = node.setdefault(value, {})
            node[-1] = label
        answer, search = self._decode(query.raw, steps)
        self._record(query.raw, discovery + search, len(answer), False)
        self.signatures = {}
        self.trie = {}
        return answer

    def update(self, episode: Episode, target: object = None) -> None:
        self.episode = episode
        self.update_ops = _corpus_bytes(episode)

    def state_bytes(self) -> int:
        return 64 + _corpus_bytes(self.episode)


class OracleMotifComposer(ExactSuffixComposer):
    def fit(self, wrapped: OracleEpisode, universe_size: int, max_depth: int) -> None:
        self.signatures = {motif: label for label, motif in wrapped.motifs}
        self.fit_ops = sum(len(motif) for motif in self.signatures)
        self.trie = {}
        for phrase, label in self.signatures.items():
            node = self.trie
            for value in phrase:
                node = node.setdefault(value, {})
            node[-1] = label

    def update(self, wrapped: OracleEpisode, target: object = None) -> None:
        self.fit(wrapped, 0, 0)
        self.update_ops = self.fit_ops


class RandomByteGuess(MotifCandidate):
    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0

    def query(self, query: ByteQuery, steps: int) -> Labels:
        answer = tuple(1 + ((self.seed + len(query.raw) + i * 3) % 4) for i in range(steps))
        self._record(query.raw, 0, steps, False)
        return answer

    def update(self, episode: Episode, target: object = None) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64


class DenseRecurrentComposer(MotifCandidate):
    hidden = 12
    classes = 9

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        rng = np.random.default_rng(seed)
        self.embedding = rng.normal(0, 0.25, (256, self.hidden))
        self.recurrent = rng.normal(0, 0.18, (self.hidden, self.hidden))
        self.output = np.zeros((self.hidden + 1, 1))
        self.max_depth = 1

    def _encode(self, raw: Bytes) -> np.ndarray:
        state = np.zeros(self.hidden)
        for value in raw:
            state = np.tanh(state @ self.recurrent + self.embedding[value])
        return np.r_[state, 1.0]

    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        self.max_depth = max_depth
        x = np.vstack([self._encode(demo.raw) for demo in episode.supports])
        y = np.zeros((len(episode.supports), max_depth * self.classes))
        for row, demo in enumerate(episode.supports):
            for position, label in enumerate(demo.labels[:max_depth]):
                y[row, position * self.classes + label] = 1.0
        gram = x.T @ x + np.eye(x.shape[1]) * 1e-3
        self.output = np.linalg.solve(gram, x.T @ y)
        support_bytes = sum(len(demo.raw) for demo in episode.supports)
        background_bytes = sum(map(len, episode.distractors))
        self.fit_ops = support_bytes * (self.hidden * self.hidden + self.hidden) + background_bytes + x.shape[0] * x.shape[1] * y.shape[1] + x.shape[1] ** 3

    def query(self, query: ByteQuery, steps: int) -> Labels:
        scores = self._encode(query.raw) @ self.output
        answer = tuple(int(np.argmax(scores[i * self.classes : (i + 1) * self.classes])) for i in range(steps))
        search = len(query.raw) * (self.hidden * self.hidden + self.hidden) + steps * self.classes * (self.hidden + 1)
        self._record(query.raw, search, steps, False)
        return answer

    def update(self, episode: Episode, target: object = None) -> None:
        self.fit(episode, 0, self.max_depth)
        self.update_ops = self.fit_ops

    def state_bytes(self) -> int:
        return int(self.embedding.nbytes + self.recurrent.nbytes + self.output.nbytes + 64)
