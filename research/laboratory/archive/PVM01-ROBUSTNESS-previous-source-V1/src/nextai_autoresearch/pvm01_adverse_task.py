"""New adverse cohort: same latent/truth draws, fixed noise magnitude interaction."""
import numpy as np
from .pvm01_task import Episode, rng_for, maps, identities


def views(first, second, values, rng, noise):
    return ((np.tanh(1.5 * values) @ first.T + rng.normal(0, noise, (len(values), 64))).astype(np.float32),
            (np.tanh(.8 * values) @ second.T + rng.normal(0, noise, (len(values), 64))).astype(np.float32))



def episode(nonce, split, size, updates, index, query_count=64, *, noise=.02):
    if noise not in (.02, .04):
        raise ValueError("Only preregistered observation noise conditions")
    if split not in {"T-calibration", "T-sets", "D"} or updates not in {0, 1, 4}:
        raise ValueError("Reference study has no final access")
    rng = rng_for(nonce, f"{split}|{size}|{updates}|{index}")
    first, second = maps(nonce)
    values = identities(rng, size)
    handles = rng.permutation(size) + int(rng.integers(100000, 1000000000))
    labels = rng.integers(0, 16, size=size)
    observations, _ = views(first, second, values, rng, noise)
    writes = [(i, int(handles[i]), observations[i].copy(), int(labels[i])) for i in range(size)]
    changed = rng.choice(size, size // 4, replace=False) if updates else np.array([], dtype=int)
    tick = size
    for _ in range(updates):
        for i in changed:
            labels[i] = (labels[i] + int(rng.integers(1, 16))) % 16
            write, _ = views(first, second, values[i:i + 1], rng, noise)
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
    _, queries = views(first, second, query_values, rng, noise)
    answers = [int(labels[i]) for i in chosen] + [-1] * (query_count - known)
    targets = [int(handles[i]) for i in chosen] + [None] * (query_count - known)
    strata += ["absent"] * (query_count - known)
    order = rng.permutation(query_count)
    return Episode(tuple(writes), queries[order], tuple(answers[i] for i in order),
                   tuple(targets[i] for i in order), tuple(strata[i] for i in order))

