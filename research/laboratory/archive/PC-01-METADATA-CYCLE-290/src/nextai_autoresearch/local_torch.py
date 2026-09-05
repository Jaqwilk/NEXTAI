from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np
import torch


@dataclass(frozen=True)
class TorchCost:
    encoding_ops: int
    fit_ops: int
    query_ops: int
    state_bytes: int
    bytes_touched: int


def deterministic_device(seed: int, device: str = "auto") -> torch.device:
    target = "cuda" if device == "auto" and torch.cuda.is_available() else device
    target = "cpu" if target == "auto" else target
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    return torch.device(target)


def parameter_bytes(module: torch.nn.Module) -> int:
    tensors = tuple(module.parameters()) + tuple(module.buffers())
    return sum(t.numel() * t.element_size() for t in tensors)


def mlp_cost(module: torch.nn.Module, examples: int, fit_steps: int, queries: int) -> TorchCost:
    linears = [layer for layer in module.modules() if isinstance(layer, torch.nn.Linear)]
    per_item = sum(2 * layer.in_features * layer.out_features + layer.out_features for layer in linears)
    state = parameter_bytes(module)
    return TorchCost(
        encoding_ops=examples * per_item,
        fit_ops=fit_steps * examples * 3 * per_item,
        query_ops=queries * per_item,
        state_bytes=state,
        bytes_touched=(examples + queries) * state,
    )


def gru_cost(module: torch.nn.Module, input_size: int, hidden_size: int,
             output_size: int, examples: int, fit_steps: int, queries: int) -> TorchCost:
    gate_ops = 3 * (2 * input_size * hidden_size + 2 * hidden_size * hidden_size + 6 * hidden_size)
    per_step = gate_ops + 2 * hidden_size * output_size + output_size
    state = parameter_bytes(module)
    return TorchCost(
        encoding_ops=examples * per_step,
        fit_ops=fit_steps * examples * 3 * per_step,
        query_ops=queries * per_step,
        state_bytes=state,
        bytes_touched=(examples + queries) * state,
    )
