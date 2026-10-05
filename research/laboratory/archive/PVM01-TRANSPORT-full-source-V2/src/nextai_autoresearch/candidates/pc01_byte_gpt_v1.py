"""Conventional byte GPT; preregistered in EXP-20260905-0001 before implementation.

Architecture only. The trusted worker owns initialization, optimizer, sampling,
selection and all data. Forward receives integer contexts, never targets/paths.
Layout follows the frozen PC-01 nanoGPT-shaped recipe; no novelty is claimed.
"""
from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F


class CausalAttention(nn.Module):
    def __init__(self, width: int, heads: int, dropout: float):
        super().__init__()
        self.n_head = heads
        self.c_attn = nn.Linear(width, 3 * width, bias=False)
        self.c_proj = nn.Linear(width, width, bias=False)
        self.attn_dropout = nn.Dropout(dropout)
        self.resid_dropout = nn.Dropout(dropout)

    def forward(self, x):
        batch, length, width = x.shape
        q, k, v = self.c_attn(x).split(width, dim=2)
        q = q.view(batch, length, self.n_head, width // self.n_head).transpose(1, 2)
        k = k.view(batch, length, self.n_head, width // self.n_head).transpose(1, 2)
        v = v.view(batch, length, self.n_head, width // self.n_head).transpose(1, 2)
        y = F.scaled_dot_product_attention(
            q, k, v, attn_mask=None, is_causal=True,
            dropout_p=self.attn_dropout.p if self.training else 0.0,
        )
        y = y.transpose(1, 2).contiguous().view(batch, length, width)
        return self.resid_dropout(self.c_proj(y))


class MLP(nn.Module):
    def __init__(self, width: int, hidden: int, dropout: float):
        super().__init__()
        self.c_fc = nn.Linear(width, hidden, bias=False)
        self.gelu = nn.GELU(approximate="none")
        self.c_proj = nn.Linear(hidden, width, bias=False)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        return self.dropout(self.c_proj(self.gelu(self.c_fc(x))))


class Block(nn.Module):
    def __init__(self, width: int, hidden: int, heads: int, dropout: float, epsilon: float):
        super().__init__()
        self.ln_1 = nn.LayerNorm(width, eps=epsilon, bias=False)
        self.attn = CausalAttention(width, heads, dropout)
        self.ln_2 = nn.LayerNorm(width, eps=epsilon, bias=False)
        self.mlp = MLP(width, hidden, dropout)

    def forward(self, x):
        x = x + self.attn(self.ln_1(x))
        return x + self.mlp(self.ln_2(x))


class Candidate(nn.Module):
    def __init__(self, *, model_config: dict):
        super().__init__()
        width = model_config["embedding_width"]
        epsilon = model_config["layernorm_epsilon"]
        dropout = model_config["dropout"]
        self.context_bytes = model_config["context_bytes"]
        self.transformer = nn.ModuleDict({
            "wte": nn.Embedding(model_config["vocab_size"], width),
            "wpe": nn.Embedding(self.context_bytes, width),
            "drop": nn.Dropout(dropout),
            "h": nn.ModuleList([
                Block(width, model_config["feedforward_width"], model_config["heads"], dropout, epsilon)
                for _ in range(model_config["layers"])
            ]),
            "ln_f": nn.LayerNorm(width, eps=epsilon, bias=False),
        })
        self.lm_head = nn.Linear(width, model_config["vocab_size"], bias=False)
        self.lm_head.weight = self.transformer.wte.weight

    def forward(self, tokens):
        if tokens.ndim != 2 or not 1 <= tokens.shape[1] <= self.context_bytes:
            raise ValueError("Expected BxT integer tokens within the fixed context")
        positions = torch.arange(tokens.shape[1], device=tokens.device, dtype=torch.long)
        x = self.transformer.drop(self.transformer.wte(tokens) + self.transformer.wpe(positions))
        for block in self.transformer.h:
            x = block(x)
        return self.lm_head(self.transformer.ln_f(x))
