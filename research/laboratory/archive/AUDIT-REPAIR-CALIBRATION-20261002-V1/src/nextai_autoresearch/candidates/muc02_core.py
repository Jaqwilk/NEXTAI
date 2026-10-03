"""Disclosed pair classifiers and classical readers; no private task imports."""
from __future__ import annotations

import math
import random
import re
import time
from collections import Counter, defaultdict

import torch
from torch import nn

from nextai_autoresearch.muc_contract import parse_question, parse_statement


def encoded_pair(query_key: str, document_key: str, length: int = 96):
    raw = (query_key + " | " + document_key).encode("utf-8")
    if len(raw) + 1 > length:
        raise ValueError("Pair encoding would truncate context")
    return [257, *(byte + 1 for byte in raw), *([0] * (length - len(raw) - 1))]


def training_pairs(worlds, limit, seed):
    groups, preprocessing = defaultdict(list), 0
    for index, world in enumerate(worlds):
        rows = []
        for text in world["statements"]:
            preprocessing += 2 * len(text.encode("utf-8")) + 3
            parsed = parse_statement(text)
            if parsed is None:
                raise ValueError("Malformed training statement")
            rows.append((parsed, text))
        keys = sorted({(row[0][1], row[0][2]) for row in rows})
        if len(keys) < 2:
            raise ValueError("Training world needs distinct keys for negative pairs")
        groups[(world["knowledge_size"], world["reasoning_depth"])].append((index, rows, keys))
    rng = random.Random(seed ^ 0x4D554332)
    cells = sorted(groups)
    rng.shuffle(cells)
    for cell in cells:
        rng.shuffle(groups[cell])
    pairs, visited, subjects, per_cell = [], set(), set(), Counter()
    if limit < 2 * len(worlds) or limit % 2:
        raise ValueError("Pair budget must cover every world and contain positive/negative pairs")
    for i in range(limit // 2):
        cell = cells[i % len(cells)]
        index, rows, keys = groups[cell][(i // len(cells)) % len(groups[cell])]
        parsed, text = rng.choice(rows)
        key = (parsed[1], parsed[2])
        negative = rng.choice([other for other in keys if other != key])
        doc = " ".join(key)
        pairs.extend([(" ".join(key), doc, 1.0), (" ".join(negative), doc, 0.0)])
        visited.add(index)
        subjects.add(key[0])
        per_cell[str(cell)] += 2
        preprocessing += 2 * 96 + 2 * len(doc) + len(" ".join(negative)) + len(" ".join(key))
    rng.shuffle(pairs)
    return pairs, {"worlds_covered":len(visited), "worlds_available":len(worlds), "cells_covered":len(per_cell),
                   "pairs_per_cell":dict(per_cell), "subjects_covered":len(subjects), "preprocessing_ops":preprocessing}


class Reader(nn.Module):
    def __init__(self, recipe):
        super().__init__()
        self.length, self.width, self.layers, self.ff = recipe["pair_bytes_cap"], recipe["width"], recipe["encoder_layers"], recipe["feedforward_width"]
        self.embedding = nn.Embedding(258, self.width, padding_idx=0)
        self.position = nn.Embedding(self.length, self.width)
        layer = nn.TransformerEncoderLayer(self.width, recipe["heads"], self.ff, recipe["dropout"], batch_first=True, norm_first=True)
        self.encoder = nn.TransformerEncoder(layer, self.layers, enable_nested_tensor=False)
        self.head = nn.Linear(self.width, 1)

    def forward(self, ids):
        positions = torch.arange(ids.shape[1], device=ids.device)
        hidden = self.embedding(ids) + self.position(positions)[None, :, :]
        return self.head(self.encoder(hidden, src_key_padding_mask=(ids == 0))[:, 0]).squeeze(-1)

    def estimated_forward_flops(self, examples):
        length, width = self.length, self.width
        return examples * (self.layers * (2 * (4*length*width*width + 2*length*width*self.ff + 2*length*length*width) + 10*length*width) + 2*width)


class BM25Index:
    """Raw word tokens, positive Lucene-style IDF, k1=1.2, b=0.75."""
    def __init__(self):
        self.postings, self.lengths, self.total_tokens = defaultdict(dict), [], 0
        self.build_ops, self.search_ops = 0, 0

    def add(self, text):
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        index = len(self.lengths)
        self.lengths.append(len(tokens))
        self.total_tokens += len(tokens)
        for term, frequency in Counter(tokens).items():
            self.postings[term][index] = frequency
        self.build_ops += 2 * len(text.encode("utf-8")) + 3 * len(tokens)

    def rank(self, terms, top_k=4):
        n = len(self.lengths)
        if not n:
            return []
        average = self.total_tokens / n
        scores = defaultdict(float)
        operations = 1
        for term in sorted(set(terms)):
            postings = self.postings.get(term.lower(), {})
            idf = math.log(1 + (n - len(postings) + .5) / (len(postings) + .5))
            operations += 5
            for index, frequency in postings.items():
                denominator = frequency + 1.2 * (1 - .75 + .75 * self.lengths[index] / average)
                scores[index] += idf * frequency * (1.2 + 1) / denominator
                operations += 12
        ordered = sorted(scores, key=lambda index: (-scores[index], index))
        self.search_ops += operations + len(scores) * max(1, math.ceil(math.log2(max(2,len(scores)))))
        return [(index, scores[index]) for index in ordered[:top_k]]

    def logical_bytes(self):
        return sum(len(term.encode("utf-8")) + 16 * len(rows) for term, rows in self.postings.items()) + 8 * len(self.lengths)


class SymbolicSystem:
    mode = "symbolic"
    def __init__(self, seed, protocol):
        self.seed, self.protocol = seed, protocol
        self.current_session = None
        self.parameter_bytes = 0
        self.fit_info = {"fit_ops":0, "preprocessing_ops":0, "fit_seconds":0., "fit_peak_bytes":0.,
                         "ops_kind":"estimated scalar operations; exact key lookup counts in world costs",
                         "counts_are_estimates":True}

    def fit(self, train, development):
        return {"optimizer_steps":0, "kind":"raw-text timestamped last-write map", "development":self._development(development)}

    def _development(self, worlds):
        correct, total, charged = 0, 0, 0
        for world in worlds:
            session = self.new_session()
            for statement in world["statements"]:
                session.ingest(statement)
            answers = session.answer_batch(tuple(q["text"] for q in world["questions"]))
            correct += sum(answer == q["answer"] for answer,q in zip(answers,world["questions"],strict=True))
            total += len(answers)
            report = session.cost_report()
            charged += sum(report[name] for name in ("input_ops","build_ops","update_ops","preprocessing_ops","query_ops"))
        self.fit_info["fit_ops"] += charged
        self.current_session = None
        return {"accuracy":correct/total if total else None, "queries":total, "charged_ops":charged}

    def new_session(self):
        self.current_session = Session(self)
        return self.current_session

    def synchronize(self):
        pass

    def warmup(self, session):
        previous = dict(session.counts)
        session.answer_batch(("Starting at EF000, follow amber. Which contact is reached now?",))
        warmup = session.counts["query_ops"] - previous["query_ops"]
        session.counts = previous
        session.counts["warmup_ops"] += warmup

    def record_fit_resources(self, seconds, peak):
        self.fit_info.update(fit_seconds=float(seconds), fit_peak_bytes=float(peak))

    def fit_cost_report(self):
        return dict(self.fit_info)


class LearnedSystem(SymbolicSystem):
    mode = "dense"
    learn = True
    def __init__(self, seed, protocol):
        super().__init__(seed, protocol)
        torch.set_num_threads(1)
        torch.manual_seed(seed)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = Reader(protocol["recipe"]).to(self.device)
        self.parameter_bytes = sum(p.numel()*p.element_size() for p in self.model.parameters())
        self.fit_info["ops_kind"] = "estimated scalar operations including dense FLOPs; raw GPU FLOPs kept separately"

    def synchronize(self):
        if self.device.type == "cuda":
            torch.cuda.synchronize()

    def scores(self, query_key, document_keys):
        result = []
        with torch.inference_mode():
            for start in range(0,len(document_keys),64):
                batch = document_keys[start:start+64]
                ids = torch.tensor([encoded_pair(query_key, key, self.model.length) for key in batch],dtype=torch.long,device=self.device)
                values = self.model(ids).sigmoid().cpu().tolist()
                if any(not math.isfinite(value) or not 0 <= value <= 1 for value in values):
                    raise ValueError("Nonfinite or invalid learned probability")
                result.extend(values)
        return result

    def fit(self, train, development):
        tick = time.monotonic()
        recipe = self.protocol["recipe"]
        pairs, coverage = training_pairs(train, recipe["training_pairs"], self.seed)
        self.fit_info["preprocessing_ops"] += coverage["preprocessing_ops"]
        encoded = torch.tensor([encoded_pair(q,d,self.model.length) for q,d,_ in pairs],dtype=torch.long,device=self.device)
        labels = torch.tensor([y for _,_,y in pairs],dtype=torch.float32,device=self.device)
        curve, updates = [], 0
        if self.learn:
            optimizer = torch.optim.AdamW(self.model.parameters(),lr=recipe["learning_rate"],weight_decay=recipe["weight_decay"])
            self.model.train()
            generator = torch.Generator().manual_seed(self.seed)
            order = torch.randperm(len(pairs),generator=generator).to(self.device)
            for step in range(self.protocol["fit_steps_cap"]):
                if time.monotonic()-tick > self.protocol["fit_seconds_cap"]:
                    raise TimeoutError("Fixed fit deadline exceeded")
                offset = (step*recipe["batch_size"]) % len(pairs)
                if offset == 0 and step:
                    order = torch.randperm(len(pairs),generator=generator).to(self.device)
                indices = order[offset:offset+recipe["batch_size"]]
                optimizer.zero_grad(set_to_none=True)
                loss = nn.functional.binary_cross_entropy_with_logits(self.model(encoded[indices]),labels[indices])
                if not bool(torch.isfinite(loss)):
                    raise ValueError("Nonfinite training loss")
                loss.backward()
                optimizer.step()
                curve.append(float(loss.detach().cpu()))
                updates += 1
                self.fit_info["fit_ops"] += 3*self.model.estimated_forward_flops(len(indices)) + 8*sum(p.numel() for p in self.model.parameters())
            del optimizer
        self.model.eval()
        hits = 0
        with torch.inference_mode():
            for start in range(0,len(pairs),64):
                hits += int(((self.model(encoded[start:start+64]) >= 0) == labels[start:start+64].bool()).sum().cpu())
                self.fit_info["fit_ops"] += self.model.estimated_forward_flops(len(encoded[start:start+64]))
        training_accuracy = hits/len(pairs)
        del encoded, labels, pairs
        development_report = self._development(development)
        return {"optimizer_steps":updates,"training_pair_accuracy":training_accuracy,"coverage":coverage,
                "loss_curve":curve,"development":development_report,"selection":"fixed final step; no dev selection",
                "model_kind":"byte-pair TransformerEncoder matcher with public grammar projection and explicit path loop"}


class Session:
    def __init__(self, system):
        self.system, self.rows, self.latest, self.seen = system, [], {}, set()
        self.index = BM25Index() if system.mode == "bm25" else None
        self.last_replaced = False
        self.payload_bytes = 0
        self.counts = {name:0 for name in ("input_ops","build_ops","update_ops","preprocessing_ops","query_ops","search_ops",
                                           "query_count","bytes_touched","parser_failures","warmup_ops","gpu_query_flops","key_lookups")}

    def ingest(self, text):
        parsed = parse_statement(text)
        self.counts["input_ops"] += 2*len(text.encode("utf-8"))+3
        if parsed is None:
            self.counts["parser_failures"] += 1
            raise ValueError("Malformed public statement")
        step, subject, relation, target = parsed
        key = subject, relation
        self.last_replaced = key in self.seen
        self.seen.add(key)
        self.counts["update_ops" if self.last_replaced else "build_ops"] += 2
        if self.system.mode == "symbolic":
            previous = self.latest.get(key)
            if previous is None or step >= previous[0]:
                self.latest[key] = step, target
        else:
            self.rows.append((parsed, " ".join(key), text))
            self.payload_bytes += len(text.encode("utf-8")) + len(subject)+len(relation)+len(target)+8
            if self.index:
                self.index.add(text)

    def answer_batch(self, questions):
        answers = []
        for text in questions:
            parsed = parse_question(text)
            self.counts["query_count"] += 1
            self.counts["query_ops"] += 2*len(text.encode("utf-8"))+3
            if parsed is None:
                self.counts["parser_failures"] += 1
                raise ValueError("Malformed public question")
            current, relations = parsed
            for relation in relations:
                if self.system.mode == "symbolic":
                    self.counts["key_lookups"] += 1
                    self.counts["query_ops"] += 1
                    current = self.latest.get((current,relation),(0,"UNKNOWN"))[1]
                    self.counts["bytes_touched"] += len(current)+len(relation)+8
                else:
                    query_key = f"{current} {relation}"
                    before = self.index.search_ops if self.index else 0
                    indices = [index for index,_ in self.index.rank((current,relation))] if self.index else list(range(len(self.rows)))
                    search = self.index.search_ops-before if self.index else len(self.rows)
                    self.counts["search_ops"] += search
                    self.counts["query_ops"] += search
                    keys = [self.rows[index][1] for index in indices]
                    probabilities = self.system.scores(query_key,keys)
                    flops = self.system.model.estimated_forward_flops(len(keys))
                    prep = sum(96+len(query_key)+len(key)+3 for key in keys)
                    self.counts["query_ops"] += flops+prep+3*len(keys)
                    self.counts["gpu_query_flops"] += flops if self.system.device.type == "cuda" else 0
                    self.counts["bytes_touched"] += len(keys)*self.system.parameter_bytes + sum(len(key)+len(query_key) for key in keys)
                    if not probabilities or max(probabilities) < .5:
                        current = "UNKNOWN"
                    else:
                        best = max(zip(indices,probabilities,strict=True),key=lambda pair:(pair[1],self.rows[pair[0]][0][0]))[0]
                        current = self.rows[best][0][3]
                if current == "UNKNOWN":
                    break
            answers.append(current)
        return tuple(answers)

    def cost_report(self):
        state = self.system.parameter_bytes+self.payload_bytes+sum(len(s)+len(r)+16 for s,r in self.seen)
        state += sum(len(s)+len(r)+len(target)+16 for (s,r),(_,target) in self.latest.items())
        if self.index:
            state += self.index.logical_bytes()
        return {**self.counts,"build_ops":self.counts["build_ops"]+(self.index.build_ops if self.index else 0),
                "state_bytes":state,"peak_state_bytes":state,"state_bytes_kind":"logical payload estimate; supervisor RSS includes Python/tensor/allocator overhead",
                "bytes_touched_kind":"logical upper bound; hardware memory traffic not measured",
                "cuda_peak_reserved_bytes":int(torch.cuda.max_memory_reserved()) if self.system.mode != "symbolic" and torch.cuda.is_available() else 0}


class Candidate(SymbolicSystem):
    """Core entry for source auditing; not an authorized experimental role."""
