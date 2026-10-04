from __future__ import annotations

import numpy as np
import torch

from .candidates.base import CandidateBase, CandidateMetadata
from .entity_addressing_contract import OBSERVATION_DIMENSION, PrivateQuery, PrivateSpec, RawQuery, TransitionBurst
from .local_torch import deterministic_device, gru_cost, parameter_bytes


def split_burst(record: TransitionBurst) -> tuple[np.ndarray, np.ndarray]:
    rows = np.asarray(record.observations, dtype=np.float64)
    jumps = np.square(rows[1:] - rows[:-1]).sum(axis=1)
    cut = int(np.argmax(jumps)) + 1
    return rows[:cut].mean(axis=0), rows[cut:].mean(axis=0)


class RawNearestNeighbour(CandidateBase):
    metadata = CandidateMetadata("raw_nearest_neighbour_scan_v1", "nearest_neighbour", "Full raw-observation scan.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        pairs = [split_burst(record) for record in facts]
        self.sources = np.stack([pair[0] for pair in pairs])
        self.targets = np.stack([pair[1] for pair in pairs])
        self.values = tuple(record.value for record in facts)
        self.fit_ops = len(pairs) * OBSERVATION_DIMENSION * 16

    def query(self, source: RawQuery, steps: int) -> int:
        view = np.asarray(source.observation)
        answer = -1
        for _ in range(steps):
            index = int(np.argmin(np.square(self.sources - view).sum(axis=1)))
            view, answer = self.targets[index], self.values[index]
        comparisons = len(self.values) * steps
        self.last_comparisons = comparisons
        self.last_ops = OBSERVATION_DIMENSION + comparisons * OBSERVATION_DIMENSION * 3
        self.last_bytes_touched = OBSERVATION_DIMENSION * 8 * (1 + 2 * comparisons)
        return answer

    def update(self, source: TransitionBurst, target: int) -> None:
        left, right = split_burst(source)
        self.sources = np.vstack((self.sources, left))
        self.targets = np.vstack((self.targets, right))
        self.values += (target,)
        self.update_ops = OBSERVATION_DIMENSION * 16

    def state_bytes(self) -> int:
        return int(self.sources.nbytes + self.targets.nbytes + 8 * len(self.values))


class DenseGRUNet(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.gru = torch.nn.GRU(OBSERVATION_DIMENSION, 32, batch_first=True)
        self.head = torch.nn.Linear(32, OBSERVATION_DIMENSION + 1)

    def forward(self, inputs, hidden=None):
        output, hidden = self.gru(inputs[:, None, :], hidden)
        return self.head(output[:, -1, :]), hidden


class DenseTransitionGRU(CandidateBase):
    metadata = CandidateMetadata("local_dense_transition_gru_v1", "dense_neural_control", "Local dense transition GRU without external memory.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        pairs = [split_burst(record) for record in facts]
        device = deterministic_device(self.seed)
        x = torch.tensor(np.stack([pair[0] for pair in pairs]), dtype=torch.float32, device=device)
        values = np.asarray([record.value for record in facts], dtype=np.float64)
        self.value_center, self.value_scale = float(values.mean()), float(max(values.std(), 1.0))
        y_view = torch.tensor(np.stack([pair[1] for pair in pairs]), dtype=torch.float32, device=device)
        y_value = torch.tensor((values - self.value_center) / self.value_scale, dtype=torch.float32, device=device)[:, None]
        y = torch.cat((y_view, y_value), dim=1)
        self.model = DenseGRUNet().to(device)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
        for _ in range(32):
            optimizer.zero_grad(set_to_none=True)
            prediction, _ = self.model(x)
            torch.square(prediction - y).mean().backward()
            optimizer.step()
        self.model.eval()
        self.device = device
        cost = gru_cost(self.model, OBSERVATION_DIMENSION, 32, OBSERVATION_DIMENSION + 1,
                        len(facts), 32, 1)
        self.fit_ops = cost.encoding_ops + cost.fit_ops
        self._per_query_ops = cost.query_ops

    def query(self, source: RawQuery, steps: int) -> int:
        current = torch.tensor(source.observation, dtype=torch.float32, device=self.device)[None]
        output, hidden = None, None
        with torch.no_grad():
            for _ in range(steps):
                output, hidden = self.model(current, hidden)
                current = output[:, :OBSERVATION_DIMENSION]
        assert output is not None
        self.last_ops = OBSERVATION_DIMENSION + steps * self._per_query_ops
        self.last_comparisons = 0
        self.last_bytes_touched = OBSERVATION_DIMENSION * 4 + steps * parameter_bytes(self.model)
        return int(round(float(output[0, -1].cpu()) * self.value_scale + self.value_center))

    def update(self, source: TransitionBurst, target: int) -> None:
        self.update_ops = 0

    def state_bytes(self) -> int:
        return parameter_bytes(self.model) + 16


class PrivilegedExactEntityKey(CandidateBase):
    metadata = CandidateMetadata("privileged_exact_entity_key_v1", "privileged_control", "Evaluator-private exact entity key.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        spec = tuple(facts)[0]
        if not isinstance(spec, PrivateSpec):
            raise TypeError("privileged control requires PrivateSpec")
        self.transitions, self.values = dict(spec.transitions), dict(spec.values)
        self.fit_ops = 0

    def query(self, source: PrivateQuery, steps: int) -> int:
        entity = source.entity
        for _ in range(steps):
            entity = self.transitions[entity]
        self.last_ops = OBSERVATION_DIMENSION + steps
        self.last_comparisons = 0
        self.last_bytes_touched = OBSERVATION_DIMENSION * 8 + steps * 16
        return self.values[entity]

    def update(self, source, target: int) -> None:
        entity, successor = source
        self.transitions[entity] = successor
        self.values[successor] = target
        self.update_ops = 2

    def state_bytes(self) -> int:
        return 24 * len(self.transitions)
