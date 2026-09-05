from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable

import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


CHANNELS = 4
CHART_DIM = 2
TRANSITION_WIDTH = 28
DECODER_WIDTH = 6
RIDGE = 0.001
UPDATE_ETA = 0.05
OUTPUT_BOUND = 1.5
PAIRS = tuple(combinations(range(CHANNELS), CHART_DIM))
SCORE_PERMUTATION = (2, 5, 1, 4, 0, 3)


def _selected(values: tuple[float, ...], pair: tuple[int, int]) -> np.ndarray:
    return np.asarray((values[pair[0]], values[pair[1]]), dtype=float)


def transition_features(left: tuple[float, ...], center: tuple[float, ...],
                        right: tuple[float, ...], pair: tuple[int, int]) -> np.ndarray:
    raw = np.concatenate((_selected(left, pair), _selected(center, pair), _selected(right, pair)))
    return np.asarray((1.0, *raw, *(raw[i] * raw[j] for i in range(6) for j in range(i, 6))))


def decoder_features(chart: np.ndarray) -> np.ndarray:
    first, second = map(float, chart)
    return np.asarray((1.0, first, second, first * first, first * second, second * second))


def _ridge(design: np.ndarray, targets: np.ndarray) -> np.ndarray:
    return np.linalg.solve(
        design.T @ design + RIDGE * np.eye(design.shape[1]), design.T @ targets
    )


class PredictiveCoordinateChart(CandidateBase):
    metadata = CandidateMetadata(
        "predictive_coordinate_chart", "predictive_coordinates",
        "Source-identical two-coordinate predictive chart",
    )

    def __init__(self, seed: int = 0, *, mode: str = "aligned") -> None:
        super().__init__(seed)
        if mode not in {"aligned", "shuffled", "frozen"}:
            raise ValueError(mode)
        self.mode = mode
        self.selected_pair = PAIRS[0]
        self.pair_scores: tuple[float, ...] = ()
        self.transition_weights = np.zeros((TRANSITION_WIDTH, CHART_DIM))
        self.decoder_weights = np.zeros((DECODER_WIDTH, CHANNELS))
        self.last_bytes_touched = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        rows = tuple(facts)
        if not rows or not all(
            all(hasattr(row, field) for field in ("left", "center", "right", "target"))
            for row in rows
        ):
            raise TypeError("predictive chart requires anonymous Transition rows")
        full_targets = np.asarray([row.target for row in rows], dtype=float)
        models = []
        scores = []
        for pair in PAIRS:
            transition_design = np.asarray([
                transition_features(row.left, row.center, row.right, pair) for row in rows
            ])
            chart_targets = full_targets[:, pair]
            transition_weights = _ridge(transition_design, chart_targets)
            decoder_design = np.asarray([decoder_features(chart) for chart in chart_targets])
            decoder_weights = _ridge(decoder_design, full_targets)
            predicted_chart = transition_design @ transition_weights
            predicted_full = np.asarray([decoder_features(chart) for chart in predicted_chart]) @ decoder_weights
            reconstructed = decoder_design @ decoder_weights
            score = float(np.mean((predicted_full - full_targets) ** 2)
                          + np.mean((reconstructed - full_targets) ** 2))
            models.append((transition_weights, decoder_weights))
            scores.append(score)
        self.pair_scores = tuple(scores)
        assigned = scores if self.mode == "aligned" else [scores[index] for index in SCORE_PERMUTATION]
        selected = 0 if self.mode == "frozen" else min(range(len(PAIRS)), key=lambda index: (assigned[index], index))
        self.selected_pair = PAIRS[selected]
        self.transition_weights, self.decoder_weights = models[selected]
        rows_count = len(rows)
        transition_fit = rows_count * (TRANSITION_WIDTH ** 2 + TRANSITION_WIDTH * CHART_DIM) \
            + TRANSITION_WIDTH ** 3
        decoder_fit = rows_count * (DECODER_WIDTH ** 2 + DECODER_WIDTH * CHANNELS) \
            + DECODER_WIDTH ** 3
        feature_and_score = rows_count * (TRANSITION_WIDTH + DECODER_WIDTH * 2
                                          + TRANSITION_WIDTH * CHART_DIM
                                          + DECODER_WIDTH * CHANNELS * 2
                                          + CHANNELS * 4)
        self.fit_ops = len(PAIRS) * (transition_fit + decoder_fit + feature_and_score) + len(PAIRS)

    def _transition(self, left: tuple[float, ...], center: tuple[float, ...],
                    right: tuple[float, ...]) -> tuple[tuple[float, ...], int, int]:
        features = transition_features(left, center, right, self.selected_pair)
        chart = np.clip(features @ self.transition_weights, -OUTPUT_BOUND, OUTPUT_BOUND)
        decoded_features = decoder_features(chart)
        output = np.clip(decoded_features @ self.decoder_weights, -OUTPUT_BOUND, OUTPUT_BOUND)
        operations = TRANSITION_WIDTH + TRANSITION_WIDTH * CHART_DIM \
            + DECODER_WIDTH + DECODER_WIDTH * CHANNELS + CHART_DIM + CHANNELS
        touched = (3 * CHART_DIM + TRANSITION_WIDTH + self.transition_weights.size
                   + DECODER_WIDTH + self.decoder_weights.size + CHANNELS) * 8
        return tuple(map(float, output)), operations, touched

    def query(self, source: Any, steps: int) -> tuple[float, ...]:
        if not all(hasattr(source, field) for field in ("size", "target", "initial")):
            raise TypeError("predictive chart requires sparse Task")
        zero = (0.0,) * CHANNELS
        state = dict(source.initial)
        operations = 0
        touched = len(state) * CHANNELS * 8
        for _ in range(steps):
            active = set(state)
            positions = active | {(position - 1) % source.size for position in active} \
                | {(position + 1) % source.size for position in active}
            next_state = {}
            for position in positions:
                value, ops, byte_count = self._transition(
                    state.get((position - 1) % source.size, zero),
                    state.get(position, zero),
                    state.get((position + 1) % source.size, zero),
                )
                next_state[position] = value
                operations += ops
                touched += byte_count
            state = next_state
        self.last_ops = int(operations)
        self.last_bytes_touched = int(touched)
        return state.get(source.target, zero)

    def update(self, source: Any, target: Any) -> None:
        if not all(hasattr(source, field) for field in ("left", "center", "right", "target")):
            raise TypeError("predictive chart update requires Transition")
        features = transition_features(source.left, source.center, source.right, self.selected_pair)
        chart_target = _selected(source.target, self.selected_pair)
        chart_error = chart_target - features @ self.transition_weights
        self.transition_weights += UPDATE_ETA / (1.0 + float(features @ features)) \
            * np.outer(features, chart_error)
        decode = decoder_features(chart_target)
        output_error = np.asarray(source.target) - decode @ self.decoder_weights
        self.decoder_weights += UPDATE_ETA / (1.0 + float(decode @ decode)) \
            * np.outer(decode, output_error)
        self.update_ops = (TRANSITION_WIDTH + TRANSITION_WIDTH * CHART_DIM * 3
                           + DECODER_WIDTH + DECODER_WIDTH * CHANNELS * 3)

    def state_bytes(self) -> int:
        return int(self.transition_weights.nbytes + self.decoder_weights.nbytes
                   + len(self.pair_scores) * 8 + 128)


class Candidate(PredictiveCoordinateChart):
    """Auditable default entry for the shared implementation module."""

