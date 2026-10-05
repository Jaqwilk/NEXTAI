"""Source-shared, raw-text MUC-01 calibration baselines.

The learned controls train a six-layer transformer lexical reader from scratch.
The calibration deliberately exposes its generic iterative control loop: it is
not evidence for a new memory architecture and cannot receive generator state.
"""
from __future__ import annotations

import math
import re
import time
from collections import Counter

import torch
from torch import nn


STATEMENT = re.compile(r"At step (\d+), (E[A-Z]\d{3})'s ([a-z]+) contact became (E[A-Z]\d{3})\.")
QUESTION = re.compile(r"Starting at (E[A-Z]\d{3}), follow ([a-z, ]+)\. Which contact is reached now\?")


def parse_statement(text):
    match = STATEMENT.fullmatch(text)
    if match is None:
        return None
    stamp, subject, relation, value = match.groups()
    return int(stamp), subject, relation, value


def parse_question(text):
    match = QUESTION.fullmatch(text)
    if match is None:
        return None
    start, chain = match.groups()
    return start, tuple(part.strip() for part in chain.split(", then "))


class Reader(nn.Module):
    def __init__(self):
        super().__init__()
        width = 384
        self.embedding = nn.Embedding(2048, width)
        self.position = nn.Embedding(64, width)
        layer = nn.TransformerEncoderLayer(width, 6, 1536, 0.0, "gelu", batch_first=True, norm_first=True)
        self.blocks = nn.TransformerEncoder(layer, 6, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(width)
        self.head = nn.Linear(width, 1)

    def forward(self, tokens):
        positions = torch.arange(tokens.shape[1], device=tokens.device)
        hidden = self.blocks(self.embedding(tokens) + self.position(positions))
        return self.head(self.norm(hidden[:, 0])).squeeze(-1)


def encode_pair(subject, relation, row_subject, row_relation):
    raw = f"{subject}|{relation}|{row_subject}|{row_relation}".encode("utf-8")[:61]
    return [1] + [3 + value for value in raw] + [2]


def _batch(rows, device):
    width = max(len(row) for row in rows)
    tensor = torch.zeros((len(rows), width), dtype=torch.long, device=device)
    for index, row in enumerate(rows):
        tensor[index, :len(row)] = torch.tensor(row, dtype=torch.long, device=device)
    return tensor


class LearnedSystem:
    def __init__(self, seed, protocol, retrieval=False):
        self.seed = int(seed)
        self.protocol = protocol
        self.retrieval = retrieval
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        torch.manual_seed(self.seed)
        if self.device.type == "cuda":
            torch.cuda.manual_seed_all(self.seed)
        self.model = Reader().to(self.device)
        self.fit_ops = 0.0
        self.preprocess_ops = 0.0
        self.fit_peak = 0
        self.training_accuracy = 0.0
        self.parser_failures = 0
        self.fit_seconds = 0.0
        self.sessions = []

    def fit(self, train_worlds, development_worlds):
        started = time.monotonic()
        pairs = []
        for world in train_worlds:
            parsed = [parse_statement(row) for row in world["statements"]]
            parsed = [row for row in parsed if row is not None]
            for _, subject, relation, _ in parsed:
                pairs.append((encode_pair(subject, relation, subject, relation), 1.0))
                negative = parsed[(len(pairs) * 17) % len(parsed)]
                if negative[1] == subject and negative[2] == relation:
                    negative = parsed[(len(pairs) * 17 + 1) % len(parsed)]
                pairs.append((encode_pair(subject, relation, negative[1], negative[2]), 0.0))
                if len(pairs) >= 4096:
                    break
            if len(pairs) >= 4096:
                break
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=3e-4, weight_decay=0.01)
        order = torch.randperm(len(pairs), generator=torch.Generator().manual_seed(self.seed)).tolist()
        cap = min(192, int(self.protocol["fit_steps_cap"]))
        correct = 0
        seen = 0
        self.model.train()
        if self.device.type == "cuda":
            torch.cuda.reset_peak_memory_stats()
        for step in range(cap):
            if time.monotonic() - started >= float(self.protocol["fit_seconds_cap"]):
                break
            indices = [order[(step * 32 + j) % len(order)] for j in range(32)]
            tokens = _batch([pairs[i][0] for i in indices], self.device)
            targets = torch.tensor([pairs[i][1] for i in indices], device=self.device)
            logits = self.model(tokens)
            loss = nn.functional.binary_cross_entropy_with_logits(logits, targets)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            correct += int(((logits.detach() >= 0) == (targets >= .5)).sum().item())
            seen += len(indices)
            self.fit_ops += float(sum(parameter.numel() for parameter in self.model.parameters()) * 6 * len(indices))
        if self.device.type == "cuda":
            torch.cuda.synchronize()
            self.fit_peak = int(torch.cuda.max_memory_reserved())
        self.model.eval()
        self.training_accuracy = correct / max(1, seen)
        return {"optimizer_steps": step + 1, "lexical_training_accuracy": self.training_accuracy, "development_worlds_received": len(development_worlds), "fit_seconds_cap": self.protocol["fit_seconds_cap"]}

    def new_session(self):
        session = LearnedSession(self)
        self.sessions.append(session)
        return session

    def record_fit_resources(self, seconds, traced_peak):
        self.fit_seconds = float(seconds)
        self.fit_peak = max(self.fit_peak, int(traced_peak))

    def cost_report(self):
        parameters = sum(parameter.numel() * parameter.element_size() for parameter in self.model.parameters())
        query_ops = [value for session in self.sessions for value in session.query_ops]
        search_ops = [value for session in self.sessions for value in session.search_ops]
        input_ops = [value for session in self.sessions for value in session.input_ops]
        build_ops = sum(session.build_ops for session in self.sessions)
        mean = lambda values: sum(values) / len(values) if values else 0.0
        return {"fit_seconds": self.fit_seconds, "fit_ops": self.fit_ops, "preprocessing_ops": self.preprocess_ops, "fit_peak_bytes": self.fit_peak, "state_bytes": parameters, "peak_state_bytes": max(parameters, self.fit_peak), "mean_query_ops": mean(query_ops), "mean_search_ops": mean(search_ops), "mean_input_ops": mean(input_ops), "mean_bytes_touched": parameters + mean(input_ops), "update_ops": 1, "build_ops": build_ops, "parser_failures": self.parser_failures}


class LearnedSession:
    def __init__(self, system):
        self.system = system
        self.rows = []
        self.last_replaced = False
        self.keys = set()
        self.query_ops = []
        self.search_ops = []
        self.input_ops = []
        self.build_ops = 0

    def ingest(self, text):
        parsed = parse_statement(text)
        if parsed is None:
            self.system.parser_failures += 1
            return
        key = parsed[1:3]
        self.last_replaced = key in self.keys
        self.keys.add(key)
        self.rows.append(parsed)
        self.build_ops += len(text.encode("utf-8"))

    def _rank(self, subject, relation):
        candidates = self.rows
        if self.system.retrieval:
            terms = Counter((subject.lower(), relation.lower()))
            scored = []
            for row in self.rows:
                overlap = int(row[1].lower() in terms) * 3 + int(row[2].lower() in terms) * 2
                scored.append((overlap, row[0], row))
            candidates = [item[2] for item in sorted(scored, reverse=True)[:4]]
            self.search_ops.append(float(len(self.rows)))
        else:
            self.search_ops.append(float(len(self.rows)))
        encoded = [encode_pair(subject, relation, row[1], row[2]) for row in candidates]
        with torch.inference_mode():
            logits = self.system.model(_batch(encoded, self.system.device)).detach().cpu().tolist()
        matching = [(score, row[0], row[3]) for score, row in zip(logits, candidates)]
        self.query_ops.append(float(len(candidates) * 6 * 384 * 384))
        self.input_ops.append(float(sum(len(item) for item in encoded)))
        if not matching:
            return "UNKNOWN"
        best_score = max(score for score, _, _ in matching)
        if best_score < 0:
            return "UNKNOWN"
        near = [item for item in matching if item[0] >= best_score - 0.25]
        return max(near, key=lambda item: item[1])[2]

    def answer_batch(self, questions):
        answers = []
        for question in questions:
            parsed = parse_question(question)
            if parsed is None:
                self.system.parser_failures += 1
                answers.append("UNKNOWN")
                continue
            current, relations = parsed
            for relation in relations:
                current = self._rank(current, relation)
                if current == "UNKNOWN":
                    break
            answers.append(current)
        if self.query_ops:
            self.system.preprocess_ops += sum(self.input_ops)
        return tuple(answers)


class SymbolicSystem:
    def __init__(self, seed, protocol):
        self.parser_failures = 0
        self.total_build = 0
        self.total_queries = 0
        self.total_input = 0
        self.total_updates = 0
        self.max_state = 0

    def fit(self, train_worlds, development_worlds):
        return {"optimizer_steps": 0, "development_worlds_received": len(development_worlds)}

    def new_session(self):
        return SymbolicSession(self)

    def record_fit_resources(self, seconds, traced_peak):
        self.fit_seconds = float(seconds)
        self.fit_peak = int(traced_peak)

    def cost_report(self):
        return {"fit_seconds": getattr(self, "fit_seconds", 0), "fit_ops": 0, "preprocessing_ops": self.total_input, "fit_peak_bytes": getattr(self, "fit_peak", 0), "state_bytes": self.max_state, "peak_state_bytes": max(self.max_state, getattr(self, "fit_peak", 0)), "mean_query_ops": self.total_queries, "mean_search_ops": 0, "mean_input_ops": self.total_input, "mean_bytes_touched": self.max_state, "update_ops": self.total_updates, "build_ops": self.total_build, "parser_failures": self.parser_failures}


class SymbolicSession:
    def __init__(self, system):
        self.system = system
        self.graph = {}
        self.last_replaced = False

    def ingest(self, text):
        parsed = parse_statement(text)
        self.system.total_input += len(text.encode("utf-8"))
        if parsed is None:
            self.system.parser_failures += 1
            return
        stamp, subject, relation, value = parsed
        key = (subject, relation)
        self.last_replaced = key in self.graph
        self.system.total_updates += 1
        previous = self.graph.get(key)
        if previous is None or stamp > previous[0]:
            self.graph[key] = (stamp, value)
        self.system.total_build += 1
        self.system.max_state = max(self.system.max_state, len(self.graph) * 96)

    def answer_batch(self, questions):
        answers = []
        for question in questions:
            parsed = parse_question(question)
            if parsed is None:
                self.system.parser_failures += 1
                answers.append("UNKNOWN")
                continue
            current, relations = parsed
            for relation in relations:
                self.system.total_queries += 1
                item = self.graph.get((current, relation))
                if item is None:
                    current = "UNKNOWN"
                    break
                current = item[1]
            answers.append(current)
        return tuple(answers)
