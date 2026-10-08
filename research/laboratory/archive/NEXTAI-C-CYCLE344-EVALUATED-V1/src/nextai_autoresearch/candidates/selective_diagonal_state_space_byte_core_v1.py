from __future__ import annotations

import math
from typing import Any

import torch

from .base import CandidateBase, CandidateMetadata
from ..repository_sequence_contract import ByteContext, CompressionTraining


WIDTH, ALPHABET, CHUNK, EPOCHS = 16, 256, 64, 1
LEARNING_RATE, DECAY, GRADIENT_CLIP = 0.01, 0.9, 1.0
READOUT_OPS = 2 * WIDTH * ALPHABET + 4 * ALPHABET
PARAMETERS = 2 * ALPHABET * WIDTH + WIDTH + WIDTH * ALPHABET + ALPHABET


class SelectiveDiagonalStateSpaceByte(CandidateBase):
    ROLE = "selective_diagonal_state_space_byte_v1"
    SELECTION = "input"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        torch.set_num_threads(1)
        template = 0.05 * torch.linspace(-1.0, 1.0, WIDTH)
        self.input_map = torch.nn.Parameter(template.repeat(ALPHABET, 1))
        self.gate_map = torch.nn.Parameter(torch.zeros(ALPHABET, WIDTH))
        self.decay_logit = torch.nn.Parameter(
            torch.full((WIDTH,), math.log(DECAY / (1.0 - DECAY)))
        )
        self.readout = torch.nn.Parameter(torch.zeros(WIDTH, ALPHABET))
        self.bias = torch.nn.Parameter(torch.zeros(ALPHABET))
        self.parameters = [self.input_map, self.gate_map, self.decay_logit,
                           self.readout, self.bias]
        self.slots: dict[int, torch.Tensor] = {}
        self.meta_fit_ops = self.last_bytes_touched = self.last_update_bytes = 0
        self.metadata = CandidateMetadata(
            self.ROLE, "byte_compression", "source-identical selective diagonal state space"
        )

    def _transition_ops(self) -> int:
        return (13 if self.SELECTION == "input" else
                9 if self.SELECTION == "fixed" else 5) * WIDTH

    def _transition(self, state: torch.Tensor, byte: int) -> torch.Tensor:
        drive = torch.tanh(self.input_map[int(byte)])
        if self.SELECTION == "input":
            retain = torch.sigmoid(self.decay_logit + self.gate_map[int(byte)])
        elif self.SELECTION == "fixed":
            retain = torch.sigmoid(self.decay_logit)
        else:
            retain = torch.zeros_like(self.decay_logit)
        return retain * state + (1.0 - retain) * drive

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, CompressionTraining):
            raise TypeError("selective state space requires CompressionTraining")
        self.slots.clear()
        optimizer = torch.optim.Adam(
            self.parameters, lr=LEARNING_RATE, betas=(0.9, 0.999), eps=1e-8
        )
        self.fit_ops = 0
        step_ops = 3 * (READOUT_OPS + self._transition_ops())
        optimizer_ops = 10 * PARAMETERS
        for _ in range(EPOCHS):
            for item in facts.train_files:
                state = torch.zeros(WIDTH)
                for start in range(0, len(item.data), CHUNK):
                    optimizer.zero_grad(set_to_none=True)
                    losses = []
                    chunk = item.data[start:start + CHUNK]
                    for target in chunk:
                        logits = self.bias + state @ self.readout
                        losses.append(torch.nn.functional.cross_entropy(
                            logits.unsqueeze(0), torch.tensor([int(target)])
                        ))
                        state = self._transition(state, int(target))
                    torch.stack(losses).mean().backward()
                    torch.nn.utils.clip_grad_norm_(self.parameters, GRADIENT_CLIP)
                    optimizer.step()
                    state = state.detach()
                    self.fit_ops += len(chunk) * step_ops + optimizer_ops
        self.meta_fit_ops = self.fit_ops
        for parameter in self.parameters:
            parameter.requires_grad_(False)

    def _initial_state(self, source: ByteContext) -> tuple[torch.Tensor, int]:
        state = torch.zeros(WIDTH)
        with torch.no_grad():
            for byte in source.history:
                state = self._transition(state, int(byte))
        return state, len(source.history)

    def query(self, source: Any, steps: int) -> list[float]:
        if not isinstance(source, ByteContext):
            raise TypeError("selective state space requires ByteContext")
        state = self.slots.get(source.slot)
        folded = 0
        if state is None:
            state, folded = self._initial_state(source)
            self.slots[source.slot] = state
        with torch.no_grad():
            probabilities = torch.softmax(self.bias + state @ self.readout, dim=0)
        self.last_ops = READOUT_OPS + folded * self._transition_ops()
        transition_bytes = (3 if self.SELECTION == "input" else 2) * WIDTH * 4
        self.last_bytes_touched = (
            self.readout.numel() * 4 + self.bias.numel() * 4 + WIDTH * 4
            + folded * transition_bytes
        )
        return probabilities.tolist()

    def update(self, source: ByteContext, target: int) -> None:
        if not isinstance(source, ByteContext):
            raise TypeError("selective state space requires ByteContext")
        state = self.slots.get(source.slot)
        if state is None:
            state, _ = self._initial_state(source)
        with torch.no_grad():
            self.slots[source.slot] = self._transition(state, int(target))
        self.update_ops = self._transition_ops()
        self.last_update_bytes = 3 * WIDTH * 4

    def state_bytes(self) -> int:
        return 4 * (sum(parameter.numel() for parameter in self.parameters)
                    + len(self.slots) * WIDTH)


class Candidate(SelectiveDiagonalStateSpaceByte):
    pass
