from __future__ import annotations

from typing import Any

import numpy as np

from .base import CandidateBase, CandidateMetadata
from ..repository_sequence_contract import ByteContext, ByteFile, CompressionTraining


ALPHABET = 256
STATE_WIDTH = 64
SIGNATURE_DEPTH = 8
SURPRISE_BITS = 6.0
STATE_PSEUDOCOUNT = 16.0


def equality_state(history: tuple[int, ...] | list[int]) -> int:
    labels: dict[int, int] = {}
    code = 0
    for value in history[-SIGNATURE_DEPTH:]:
        symbol = int(value)
        if symbol not in labels:
            labels[symbol] = len(labels)
        code = (code * 9 + labels[symbol] + 1) % STATE_WIDTH
    return code


class Candidate(CandidateBase):
    ROLE = "surprise_gated_transition_machine_byte"
    CLOCK = "surprise"
    LEARN_TRANSITIONS = True

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.transitions = np.repeat(
            np.arange(STATE_WIDTH, dtype=np.uint8)[:, None], ALPHABET, axis=1
        )
        self.transition_votes = np.ones((STATE_WIDTH, ALPHABET), dtype=np.uint8)
        self.emissions = np.zeros((STATE_WIDTH, ALPHABET), dtype=np.uint32)
        self.emission_totals = np.zeros(STATE_WIDTH, dtype=np.uint64)
        self.unigram = np.ones(ALPHABET, dtype=np.uint64)
        self.slots: dict[int, int] = {}
        self.pending: dict[int, tuple[tuple[int, ...], int, np.ndarray]] = {}
        self.meta_fit_ops = self.last_bytes_touched = self.last_update_bytes = 0
        self.metadata = CandidateMetadata(
            self.ROLE, "byte_compression", "source-identical event-driven transition machine"
        )

    def _distribution(self, state: int) -> np.ndarray:
        prior = self.unigram.astype(np.float64)
        prior /= float(prior.sum())
        row = self.emissions[state].astype(np.float64)
        return (row + STATE_PSEUDOCOUNT * prior) / (
            float(self.emission_totals[state]) + STATE_PSEUDOCOUNT
        )

    def _event(self, probability: float) -> bool:
        return self.CLOCK == "dense" or probability <= 2.0 ** -SURPRISE_BITS

    def _learn_transition(self, state: int, symbol: int, desired: int) -> None:
        current = int(self.transitions[state, symbol])
        votes = int(self.transition_votes[state, symbol])
        if current == desired:
            self.transition_votes[state, symbol] = min(255, votes + 1)
        elif votes > 1:
            self.transition_votes[state, symbol] = votes - 1
        else:
            self.transitions[state, symbol] = desired
            self.transition_votes[state, symbol] = 1

    def _advance(self, state: int, symbol: int, history: list[int], learn: bool) -> int:
        probability = float(self._distribution(state)[symbol])
        event = self._event(probability)
        if learn and self.LEARN_TRANSITIONS and event:
            self._learn_transition(state, symbol, equality_state([*history, symbol]))
        self.unigram[symbol] += 1
        self.emissions[state, symbol] += 1
        self.emission_totals[state] += 1
        history.append(symbol)
        if event:
            state = int(self.transitions[state, symbol])
        return state

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, CompressionTraining):
            raise TypeError("transition machine requires CompressionTraining")
        self.fit_ops = 0
        for item in facts.train_files:
            state, history = 0, []
            for raw in item.data:
                symbol = int(raw)
                before = len(history)
                state = self._advance(state, symbol, history, True)
                self.fit_ops += 12 + min(before + 1, SIGNATURE_DEPTH)
        self.meta_fit_ops = self.fit_ops

    def _replay(self, history: tuple[int, ...]) -> tuple[int, int]:
        state, ops = 0, 0
        prefix: list[int] = []
        for symbol in history:
            probability = float(self._distribution(state)[int(symbol)])
            if self._event(probability):
                state = int(self.transitions[state, int(symbol)])
            prefix.append(int(symbol))
            ops += 4
        return state, ops

    def query(self, source: Any, steps: int) -> list[float]:
        if not isinstance(source, ByteContext):
            raise TypeError("transition machine requires ByteContext")
        if source.slot in self.slots:
            state, replay_ops = self.slots[source.slot], 0
        else:
            state, replay_ops = self._replay(source.history)
        probabilities = self._distribution(state)
        self.pending[source.slot] = (source.history, state, probabilities.copy())
        self.last_ops = replay_ops + 4 * ALPHABET
        self.last_bytes_touched = replay_ops * 2 + 2 * ALPHABET * 8
        return probabilities.tolist()

    def update(self, source: Any, target: int) -> None:
        if not isinstance(source, ByteContext):
            raise TypeError("transition machine requires ByteContext")
        pending = self.pending.pop(source.slot, None)
        if pending is None or pending[0] != source.history:
            raise RuntimeError("update requires the matching prereveal query artifact")
        _, state, probabilities = pending
        symbol = int(target)
        event = self._event(float(probabilities[symbol]))
        self.slots[source.slot] = (
            int(self.transitions[state, symbol]) if event else state
        )
        self.update_ops = 5 if event else 2
        self.last_update_bytes = 11 if event else 8

    def state_bytes(self) -> int:
        arrays = (
            self.transitions.nbytes + self.transition_votes.nbytes
            + self.emissions.nbytes + self.emission_totals.nbytes + self.unigram.nbytes
        )
        return int(arrays + 16 * len(self.slots))


def semantic_fixtures() -> dict[str, bool]:
    context = ByteContext(7, (4, 4, 9, 4))
    sparse = Candidate(0)
    sparse.slots[7] = 3
    common = np.zeros(ALPHABET, dtype=np.float64)
    common[4] = 0.5
    sparse.pending[7] = (context.history, 3, common)
    sparse.update(context, 4)
    no_event_preserves_state = sparse.slots[7] == 3 and sparse.update_ops == 2

    rare = np.zeros(ALPHABET, dtype=np.float64)
    rare[9] = 1.0 / 128.0
    sparse.transitions[3, 9] = 11
    sparse.pending[7] = (context.history, 3, rare)
    sparse.update(context, 9)
    rare_event_transitions = sparse.slots[7] == 11 and sparse.update_ops == 5

    dense = Candidate(0)
    dense.CLOCK = "dense"
    dense.transitions[3, 4] = 12
    dense.pending[7] = (context.history, 3, common)
    dense.update(context, 4)
    dense_updates_every_reveal = dense.slots[7] == 12 and dense.update_ops == 5

    prereveal = Candidate(0)
    try:
        prereveal.update(context, 4)
        predict_before_reveal = False
    except RuntimeError:
        predict_before_reveal = True

    permutation = tuple((73 * value + 19) % ALPHABET for value in range(ALPHABET))
    original = (1, 2, 1, 3, 2, 4, 1, 4)
    relabeled = tuple(permutation[value] for value in original)
    first, second = Candidate(0), Candidate(0)
    first.fit(CompressionTraining((ByteFile(1, original * 4),), (), 0), 8, 4)
    second.fit(CompressionTraining((ByteFile(1, relabeled * 4),), (), 0), 8, 4)
    first_row = first.query(ByteContext(20, original[-4:]), 1)
    second_row = second.query(ByteContext(20, relabeled[-4:]), 1)
    relabeling_equivariant = (
        equality_state(original) == equality_state(relabeled)
        and all(abs(first_row[value] - second_row[permutation[value]]) < 1e-12
                for value in range(ALPHABET))
    )

    slow_before = sparse.transitions.copy(), sparse.emissions.copy(), sparse.unigram.copy()
    other = ByteContext(8, context.history)
    sparse.slots[8] = 6
    sparse.pending[7] = (context.history, sparse.slots[7], common)
    sparse.update(context, 4)
    slot_local_and_slow_frozen = (
        sparse.slots[8] == 6
        and np.array_equal(slow_before[0], sparse.transitions)
        and np.array_equal(slow_before[1], sparse.emissions)
        and np.array_equal(slow_before[2], sparse.unigram)
    )
    checks = {
        "predict_before_reveal": predict_before_reveal,
        "byte_relabeling_equivariance": relabeling_equivariant,
        "sparse_no_event_state_preservation": no_event_preserves_state,
        "rare_event_transition": rare_event_transitions,
        "dense_every_reveal": dense_updates_every_reveal,
        "slot_local_test_update_and_frozen_slow_state": slot_local_and_slow_frozen,
        "explicit_event_dense_cost": sparse.update_ops < dense.update_ops,
    }
    if not all(checks.values()):
        raise AssertionError(checks)
    return checks
