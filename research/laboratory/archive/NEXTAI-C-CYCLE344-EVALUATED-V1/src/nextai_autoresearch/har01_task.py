"""Preregistered native physical windows; evaluator-only subject/split/answer access."""
from dataclasses import dataclass
import hashlib

import numpy as np

from .utils import load_json, sha256_file, sha256_json


CHANNELS = ("body_acc_x", "body_acc_y", "body_acc_z", "body_gyro_x", "body_gyro_y", "body_gyro_z")
SCREEN_SUBJECTS = tuple(range(1, 6)) + tuple(range(16, 21))


def arrays_hash(*arrays):
    digest = hashlib.sha256()
    for value in arrays:
        array = np.ascontiguousarray(value)
        digest.update(str((array.shape, array.dtype.str)).encode())
        digest.update(array.tobytes())
    return digest.hexdigest()


def rng_for(nonce, tag):
    return np.random.default_rng(int.from_bytes(hashlib.sha256(f"{nonce}|{tag}".encode()).digest()[:16], "big"))


def feature(window, view):
    """Only native time subsampling/block means, never a PVM latent/random map."""
    if window.shape != (6, 128) or window.dtype != np.float32 or view not in {"write", "nominal", "adverse"}:
        raise ValueError("Malformed native physical observation")
    indices = np.arange(0 if view == "write" else 1, 128, 2)
    if view == "adverse":
        indices = np.minimum(indices + 2, 127)
    selected = window[:, indices].copy()
    if view == "adverse":
        selected[4] = 0
    means = selected.reshape(6, 8, 8).mean(axis=-1)
    acceleration = np.linalg.norm(selected[:3], axis=0).reshape(8, 8).mean(axis=-1)
    gyroscope = np.linalg.norm(selected[3:], axis=0).reshape(8, 8).mean(axis=-1)
    result = np.concatenate((means.ravel(), acceleration, gyroscope)).astype(np.float32)
    if not np.isfinite(result).all():
        raise ValueError("Nonfinite native feature")
    return result


def transform(window, view, mean, scale):
    value = (feature(window.copy(), view) - mean) / scale
    return (value / max(float(np.linalg.norm(value)), 1e-12)).astype(np.float32)


def load_unit(root, index):
    if index not in range(5):
        raise ValueError("Only preregistered five screen pairs are accessible")
    manifest_path = root / "research/data_manifests/HAR01-ACQUISITION-V1.json"
    manifest = load_json(manifest_path)
    task = root / "research/plans/HAR01-NATIVE-TASK-CONTRACT-V1.json"
    if (manifest.get("complete") is not True or manifest["task_contract_sha256"] != sha256_file(task)
            or manifest["converted_subjects"] != list(SCREEN_SUBJECTS)
            or manifest.get("no_unselected_subject_signal_arrays") is not True):
        raise ValueError("Native acquisition/scope binding mismatch")
    path = (root / manifest["dataset_path"]).resolve()
    if not path.is_relative_to(root.resolve()) or sha256_file(path) != manifest["dataset_sha256"]:
        raise ValueError("Native screen payload changed or outside repository")
    publisher = root / "research/data/har01_native_v1/publisher.zip"
    if sha256_file(publisher) != manifest["publisher_sha256"]:
        raise ValueError("Preserved publisher archive changed")
    with np.load(path, allow_pickle=False) as archive:
        expected = {f"{prefix}_{s}" for s in SCREEN_SUBJECTS for prefix in ("subject", "rows")}
        if set(archive.files) != expected:
            raise ValueError("Unexpected reserved subject in screen payload")
        values = []
        for subject in (index + 1, index + 16):
            signals, rows = archive[f"subject_{subject}"].copy(), archive[f"rows_{subject}"].copy()
            if arrays_hash(signals, rows) != manifest["converted_subject_hashes"][str(subject)]:
                raise ValueError("Native subject arrays changed")
            values.append((signals, rows))
    train, dev = values
    fit, validation, calibration = train[0][0:128], train[0][130:178], train[0][180:260]
    if (len(fit), len(validation), len(calibration)) != (128, 48, 80) or len(dev[0][::2]) < 80:
        raise ValueError("Preregistered finite-data intake not feasible")
    raw_write = np.stack([feature(row, "write") for row in fit])
    mean = raw_write.mean(axis=0).astype(np.float32)
    scale = np.maximum(raw_write.std(axis=0), 1e-6).astype(np.float32)
    return {"T-fit": (fit, train[1][0:128]), "T-validation": (validation, train[1][130:178]),
            "T-calibration": (calibration, train[1][180:260]), "D": (dev[0][::2], dev[1][::2]),
            "mean": mean, "scale": scale, "train_subject": index + 1, "dev_subject": index + 16,
            "intake_sha256": sha256_file(manifest_path), "dataset_sha256": manifest["dataset_sha256"],
            "publisher_sha256": manifest["publisher_sha256"],
            "unique_counts": {"T-fit": 128, "T-validation": 48, "T-calibration": 80, "D": len(dev[0][::2])}}


def pairs(unit, nonce, split, count):
    if split not in {"T-fit", "T-validation"}:
        raise ValueError("No evaluation pairs may enter target adaptation")
    windows, _ = unit[split]
    selected = rng_for(nonce, split).integers(len(windows), size=count)
    writes = np.stack([transform(windows[i], "write", unit["mean"], unit["scale"]) for i in selected])
    queries = np.stack([transform(windows[i], "nominal", unit["mean"], unit["scale"]) for i in selected])
    return writes, queries


@dataclass(frozen=True)
class Episode:
    writes: tuple
    queries: np.ndarray
    answers: tuple
    target_handles: tuple
    target_sources: tuple
    strata: tuple
    condition: str


def episode(unit, nonce, split, size, updates, index, query_count=64, condition="nominal"):
    if split not in {"T-fit", "T-calibration", "D"} or size not in {16, 32, 64} or updates not in {0, 1, 4}:
        raise ValueError("Native study has no reserved replication/final access")
    if condition not in {"nominal", "adverse"} or (split != "D" and condition != "nominal"):
        raise ValueError("No adverse training/calibration")
    windows, row_ids = unit[split]
    rng = rng_for(nonce, f"episode|{split}|{size}|{updates}|{index}|{query_count}")
    known = query_count * 3 // 4
    absent = query_count - known
    selection = rng.choice(len(windows), size + absent, replace=False)
    present, unknown = selection[:size], selection[size:]
    handles = rng.permutation(size) + int(rng.integers(100000, 1000000000))
    values = rng.integers(0, 16, size=size)
    subject = unit["dev_subject"] if split == "D" else unit["train_subject"]

    def source(i, tick):
        publisher_split, row = row_ids[present[i]]
        return f"uci-har:{('train', 'test')[int(publisher_split)]}:{int(row)+1}:subject{subject}:version{tick}"

    sources = [source(i, i) for i in range(size)]
    writes = [(i, int(handles[i]), windows[present[i]].copy(), int(values[i]), sources[i]) for i in range(size)]
    first_writes = tuple(writes)
    changed = rng.choice(size, size // 4, replace=False) if updates else np.array([], dtype=int)
    tick = size
    for _ in range(updates):
        for i in changed:
            values[i] = (values[i] + int(rng.integers(1, 16))) % 16
            sources[i] = source(i, tick)
            writes.append((tick, int(handles[i]), windows[present[i]].copy(), int(values[i]), sources[i]))
            tick += 1
    if updates:
        # Public stale arrivals must never overwrite the latest value OR source.
        writes.extend(first_writes[i] for i in changed)
        keep = np.setdiff1d(np.arange(size), changed)
        chosen = np.concatenate((rng.choice(changed, known // 2), rng.choice(keep, known - known // 2)))
        strata = ["updated"] * (known // 2) + ["retained"] * (known - known // 2)
    else:
        chosen = rng.choice(size, known)
        strata = ["retained"] * known
    queries = np.concatenate((windows[present[chosen]], windows[unknown])).copy()
    answers = [int(values[i]) for i in chosen] + [-1] * absent
    targets = [int(handles[i]) for i in chosen] + [None] * absent
    actual_sources = [sources[i] for i in chosen] + [None] * absent
    strata += ["absent"] * absent
    order = rng.permutation(query_count)
    return Episode(tuple(writes), queries[order], tuple(answers[i] for i in order),
                   tuple(targets[i] for i in order), tuple(actual_sources[i] for i in order),
                   tuple(strata[i] for i in order), condition)


def prepared_calibration(unit, item):
    writes = tuple((t, h, transform(w, "write", unit["mean"], unit["scale"]), v, s)
                   for t, h, w, v, s in item.writes)
    queries = np.stack([transform(w, item.condition, unit["mean"], unit["scale"]) for w in item.queries])
    return writes, queries, tuple(zip(item.answers, item.target_sources, strict=True))


def training_sets(unit, nonce):
    result = {}
    for size in (16, 32):
        contexts, queries, targets = [], [], []
        for index in range(128):
            item = episode(unit, nonce, "T-fit", size, 0, index, 8)
            writes, observations, _ = prepared_calibration(unit, item)
            contexts.append(np.stack([row[2] for row in writes]))
            queries.append(observations)
            lookup = {row[1]: i for i, row in enumerate(writes)}
            targets.append([lookup.get(handle, size) for handle in item.target_handles])
        result[size] = np.array(contexts), np.array(queries), np.array(targets, dtype=np.int64)
    return result


def episode_hash(item):
    return sha256_json({"writes": [(t, h, arrays_hash(w), v, s) for t, h, w, v, s in item.writes],
                        "queries": arrays_hash(item.queries), "answers": item.answers,
                        "handles": item.target_handles, "sources": item.target_sources,
                        "strata": item.strata, "condition": item.condition})
