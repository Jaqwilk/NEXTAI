"""Protected paired-view generator. Never imported or exposed by candidates."""
from dataclasses import dataclass
import hashlib

import numpy as np


def rng_for(nonce, tag):
    return np.random.default_rng(int.from_bytes(hashlib.sha256(f"{nonce}|{tag}".encode()).digest()[:16], "big"))


def maps(nonce):
    rng = rng_for(nonce, "maps")
    return tuple(np.linalg.qr(rng.normal(size=(64, 16)))[0].astype(np.float32) for _ in range(2))


def identities(rng, count):
    values = rng.normal(size=(count, 16))
    return (values / np.linalg.norm(values, axis=1, keepdims=True)).astype(np.float32)


def views(first, second, values, rng):
    return ((np.tanh(1.5 * values) @ first.T + rng.normal(0, .02, (len(values), 64))).astype(np.float32),
            (np.tanh(.8 * values) @ second.T + rng.normal(0, .02, (len(values), 64))).astype(np.float32))


def pairs(nonce, split, count):
    if split not in {"T-fit", "T-validation"}:
        raise ValueError("Reference fit uses only reserved training splits")
    rng = rng_for(nonce, split)
    return views(*maps(nonce), identities(rng, count), rng)


@dataclass(frozen=True)
class Episode:
    writes: tuple
    queries: np.ndarray
    answers: tuple
    target_handles: tuple
    strata: tuple


def episode(nonce, split, size, updates, index, query_count=64):
    if split not in {"T-calibration", "T-sets", "D"} or updates not in {0, 1, 4}:
        raise ValueError("Reference study has no final access")
    rng = rng_for(nonce, f"{split}|{size}|{updates}|{index}")
    first, second = maps(nonce)
    values = identities(rng, size)
    handles = rng.permutation(size) + int(rng.integers(100000, 1000000000))
    labels = rng.integers(0, 16, size=size)
    observations, _ = views(first, second, values, rng)
    writes = [(i, int(handles[i]), observations[i].copy(), int(labels[i])) for i in range(size)]
    changed = rng.choice(size, size // 4, replace=False) if updates else np.array([], dtype=int)
    tick = size
    for _ in range(updates):
        for i in changed:
            labels[i] = (labels[i] + int(rng.integers(1, 16))) % 16
            write, _ = views(first, second, values[i:i + 1], rng)
            writes.append((tick, int(handles[i]), write[0], int(labels[i])))
            tick += 1
    known = query_count * 3 // 4
    if updates:
        keep = np.setdiff1d(np.arange(size), changed)
        chosen = np.concatenate([rng.choice(changed, known // 2), rng.choice(keep, known - known // 2)])
        strata = ["updated"] * (known // 2) + ["retained"] * (known - known // 2)
    else:
        chosen = rng.choice(size, known)
        strata = ["retained"] * known
    query_values = np.concatenate([values[chosen], identities(rng, query_count - known)])
    _, queries = views(first, second, query_values, rng)
    answers = [int(labels[i]) for i in chosen] + [-1] * (query_count - known)
    targets = [int(handles[i]) for i in chosen] + [None] * (query_count - known)
    strata += ["absent"] * (query_count - known)
    order = rng.permutation(query_count)
    return Episode(tuple(writes), queries[order], tuple(answers[i] for i in order),
                   tuple(targets[i] for i in order), tuple(strata[i] for i in order))


def training_sets(nonce, count=128):
    result = {}
    for size in (32, 128):
        contexts, queries, targets = [], [], []
        for index in range(count):
            item = episode(nonce, "T-sets", size, 0, index, 8)
            contexts.append(np.stack([row[2] for row in item.writes]))
            queries.append(item.queries)
            lookup = {row[1]: i for i, row in enumerate(item.writes)}
            targets.append([lookup.get(handle, size) for handle in item.target_handles])
        result[size] = (np.array(contexts), np.array(queries), np.array(targets, dtype=np.int64))
    return result


def arrays_hash(*arrays):
    digest = hashlib.sha256()
    for value in arrays:
        a = np.ascontiguousarray(value)
        digest.update(str((a.shape, a.dtype.str)).encode())
        digest.update(a.tobytes())
    return digest.hexdigest()


def episode_hash(item):
    return arrays_hash(np.array([(r[0], r[1], r[3]) for r in item.writes], dtype=np.int64),
                       np.stack([r[2] for r in item.writes]), item.queries,
                       np.array(item.answers), np.array([h if h is not None else -1 for h in item.target_handles]))
