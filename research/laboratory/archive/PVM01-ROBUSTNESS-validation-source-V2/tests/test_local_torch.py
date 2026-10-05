import os
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import pytest
import torch

from nextai_autoresearch.local_torch import deterministic_device, gru_cost, mlp_cost, parameter_bytes


def _development_fit(device: str) -> tuple[torch.Tensor, int]:
    target = deterministic_device(1103, device)
    x = torch.arange(24, dtype=torch.float32, device=target).reshape(6, 4) / 24
    y = torch.stack((x[:, 0] - x[:, 1], x[:, 2] + x[:, 3]), dim=1)
    model = torch.nn.Sequential(torch.nn.Linear(4, 5), torch.nn.Tanh(), torch.nn.Linear(5, 2)).to(target)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.05)
    for _ in range(8):
        optimizer.zero_grad(set_to_none=True)
        torch.square(model(x) - y).mean().backward()
        optimizer.step()
    return torch.cat([p.detach().cpu().flatten() for p in model.parameters()]), parameter_bytes(model)


def test_development_training_is_deterministic_on_cpu() -> None:
    left, left_bytes = _development_fit("cpu")
    right, right_bytes = _development_fit("cpu")
    assert torch.equal(left, right)
    assert left_bytes == right_bytes == 148


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_development_training_is_deterministic_on_cuda() -> None:
    left, _ = _development_fit("cuda")
    right, _ = _development_fit("cuda")
    assert torch.equal(left, right)


def test_accounting_is_explicit_and_positive() -> None:
    model = torch.nn.Sequential(torch.nn.Linear(4, 5), torch.nn.Tanh(), torch.nn.Linear(5, 2))
    cost = mlp_cost(model, examples=6, fit_steps=8, queries=3)
    assert cost.encoding_ops == 6 * (45 + 22)
    assert cost.fit_ops == 8 * 6 * 3 * (45 + 22)
    assert cost.query_ops == 3 * (45 + 22)
    assert cost.state_bytes == 148
    assert cost.bytes_touched > cost.state_bytes
    gru = torch.nn.Sequential(torch.nn.GRU(4, 5, batch_first=True), torch.nn.Linear(5, 2))
    recurrent = gru_cost(gru, 4, 5, 2, examples=6, fit_steps=8, queries=3)
    assert recurrent.fit_ops > recurrent.encoding_ops > recurrent.query_ops > 0
    assert recurrent.state_bytes == parameter_bytes(gru)


def test_local_torch_interface_has_no_model_api_or_pretrained_loader() -> None:
    source = (Path(__file__).parents[1] / "src/nextai_autoresearch/local_torch.py").read_text(encoding="utf-8")
    forbidden = ("torch.hub", "from_pretrained", "requests", "http://", "https://", "openai")
    assert not any(token in source for token in forbidden)
