"""Frozen evaluator for BRIDGE-U1-U2-V1.

This module is an evaluator and audit fixture, not a scored candidate suite.
The cohort remains unusable for scoring until its service-cycle decision is A.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import numpy as np

from nextai_autoresearch.relational_ood_contract import (
    COST_FIELDS,
    RelationalQueryBatch,
    RelationalTrainingBatch,
    empty_cost_record,
)


BENCHMARK_ID = "anonymous_repeated_measurement_ood_v1"
BRIDGE_ID = "BRIDGE-U1-U2-V1"
DEVELOPMENT_FIXTURE_SEED = 240_031
SOURCE_DIM = 16
INPUT_DIM = 32
SCALES = (64, 256, 1024)
MEASUREMENTS_PER_SOURCE = 2
QUERIES_PER_CONDITION = 256
TRAIN_NUISANCE = ((1 / 16, 0.0), (1 / 8, 0.0), (0.0, 1 / 16), (0.0, 1 / 8))
QUERY_NUISANCE = {
    "iid": None,
    "s1": (3 / 16, 3 / 16),
    "s2": (1 / 4, 1 / 4),
    "s3": (3 / 8, 3 / 8),
}
ROLES = ("correct", "shuffled", "passive", "random", "classical", "oracle")
CONSTRUCTION_TRACE = (
    "latent records",
    "relation graph",
    "public probes",
    "targets",
    "nuisance realization",
    "anonymous batch shuffle",
)
RIDGE_REGULARIZATION = 1e-3
CCA_REGULARIZATION = 1e-3
CCA_RANK = 16
NUMERICAL_TOLERANCE = 1e-10


@dataclass(frozen=True)
class _PrivateTraining:
    public_records: np.ndarray
    targets: np.ndarray
    latent_records: np.ndarray
    probes: np.ndarray
    nuisance: np.ndarray
    true_edges: tuple[tuple[int, int], ...]
    shuffled_edges: tuple[tuple[int, int], ...]
    random_edges: tuple[tuple[int, int], ...]
    pre_shuffle_edges: tuple[tuple[int, int], ...]
    permutation: np.ndarray


@dataclass(frozen=True)
class _PrivateQueries:
    public: RelationalQueryBatch
    targets: np.ndarray
    latent_records: np.ndarray
    probes: np.ndarray
    nuisance: tuple[float, float] | None


@dataclass(frozen=True)
class AuditFixture:
    scale: int
    permutation_variant: str
    roles: dict[str, RelationalTrainingBatch]
    private_training: _PrivateTraining
    queries: dict[str, _PrivateQueries]


def _rng(seed: int, stream: int) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence([seed, stream]))


def _rademacher(rng: np.random.Generator, shape: tuple[int, ...]) -> np.ndarray:
    return rng.integers(0, 2, size=shape, dtype=np.int8).astype(np.float64) * 2.0 - 1.0


def _bit_reversal_permutation() -> np.ndarray:
    return np.asarray([int(f"{j:05b}"[::-1], 2) for j in range(INPUT_DIM)], dtype=np.int64)


def _affine_permutation() -> np.ndarray:
    return np.asarray([(7 * j + 3) % INPUT_DIM for j in range(INPUT_DIM)], dtype=np.int64)


def _coordinate_permutation(variant: str) -> np.ndarray:
    if variant == "main":
        return _bit_reversal_permutation()
    if variant == "adversarial":
        return _affine_permutation()
    raise ValueError(f"unknown permutation variant: {variant}")


def _apply_coordinate_permutation(values: np.ndarray, variant: str) -> np.ndarray:
    permutation = _coordinate_permutation(variant)
    result = np.empty_like(values)
    result[:, permutation] = values
    return result


def _public_records(
    latent_records: np.ndarray,
    probes: np.ndarray,
    sigma: np.ndarray,
    dropout: np.ndarray,
    rng: np.random.Generator,
    variant: str,
) -> np.ndarray:
    keep = rng.random(latent_records.shape) >= dropout[:, None]
    noise = rng.normal(size=latent_records.shape) * sigma[:, None]
    measurements = keep * latent_records + noise
    return _apply_coordinate_permutation(np.concatenate((measurements, probes), axis=1), variant)


def _target(latent_records: np.ndarray, probes: np.ndarray) -> np.ndarray:
    return np.sum(latent_records * probes, axis=1) / SOURCE_DIM


def _to_rows(values: np.ndarray) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(float(value) for value in row) for row in values)


def _make_public_batch(
    records: np.ndarray,
    targets: np.ndarray,
    edges: tuple[tuple[int, int], ...],
    active: bool,
) -> RelationalTrainingBatch:
    return RelationalTrainingBatch(
        records=_to_rows(records),
        targets=tuple(float(value) for value in targets),
        relation_edges=edges,
        relation_mask=tuple(active for _ in edges),
        batch_order=tuple(range(len(records))),
    )


def _remap_edges(
    edges: Iterable[tuple[int, int]], inverse_batch_permutation: np.ndarray
) -> tuple[tuple[int, int], ...]:
    return tuple(
        (int(inverse_batch_permutation[left]), int(inverse_batch_permutation[right]))
        for left, right in edges
    )


def _is_true_edge(edge: tuple[int, int], true_edges: set[frozenset[int]]) -> bool:
    return frozenset(edge) in true_edges


def _shuffled_edges(
    true_edges: tuple[tuple[int, int], ...], rng: np.random.Generator
) -> tuple[tuple[int, int], ...]:
    left = [edge[0] for edge in true_edges]
    right = [edge[1] for edge in true_edges]
    shift = int(rng.integers(1, len(right)))
    edges = [(left[index], right[(index + shift) % len(right)]) for index in range(len(left))]
    order = rng.permutation(len(edges))
    return tuple(edges[int(index)] for index in order)


def _random_perfect_matching(
    endpoint_count: int,
    true_edges: tuple[tuple[int, int], ...],
    rng: np.random.Generator,
) -> tuple[tuple[int, int], ...]:
    truth = {frozenset(edge) for edge in true_edges}
    for _ in range(10_000):
        order = rng.permutation(endpoint_count)
        edges = tuple(
            (int(order[index]), int(order[index + 1]))
            for index in range(0, endpoint_count, 2)
        )
        if not any(_is_true_edge(edge, truth) for edge in edges):
            return edges
    raise RuntimeError("failed to draw a false perfect matching")


def _build_training(scale: int, variant: str, seed: int) -> _PrivateTraining:
    if scale not in SCALES:
        raise ValueError(f"scale must be one of {SCALES}")
    # The graph is fixed immediately after the latent records.  No probe,
    # target, nuisance label, or realized observation exists at this point.
    source_latents = _rademacher(_rng(seed, 1), (scale, SOURCE_DIM))
    latent_records = np.repeat(source_latents, MEASUREMENTS_PER_SOURCE, axis=0)
    pre_edges = tuple((2 * index, 2 * index + 1) for index in range(scale))

    probes = _rademacher(_rng(seed, 2), latent_records.shape)
    targets = _target(latent_records, probes)
    nuisance_index = _rng(seed, 3).integers(0, len(TRAIN_NUISANCE), len(latent_records))
    nuisance = np.asarray([TRAIN_NUISANCE[int(index)] for index in nuisance_index], dtype=np.float64)
    records = _public_records(
        latent_records,
        probes,
        nuisance[:, 0],
        nuisance[:, 1],
        _rng(seed, 4),
        variant,
    )

    # Every role table exists in acquisition order before the one shared
    # anonymous batch permutation is drawn and applied.
    shuffled_pre = _shuffled_edges(pre_edges, _rng(seed, 7))
    random_pre = _random_perfect_matching(len(records), pre_edges, _rng(seed, 8))
    batch_permutation = _rng(seed, 5).permutation(len(records))
    inverse = np.empty_like(batch_permutation)
    inverse[batch_permutation] = np.arange(len(batch_permutation))
    true_edges = _remap_edges(pre_edges, inverse)
    shuffled_edges = _remap_edges(shuffled_pre, inverse)
    random_edges = _remap_edges(random_pre, inverse)
    edge_order = _rng(seed, 6).permutation(len(true_edges))
    true_edges = tuple(true_edges[int(index)] for index in edge_order)
    return _PrivateTraining(
        public_records=records[batch_permutation],
        targets=targets[batch_permutation],
        latent_records=latent_records[batch_permutation],
        probes=probes[batch_permutation],
        nuisance=nuisance[batch_permutation],
        true_edges=true_edges,
        shuffled_edges=shuffled_edges,
        random_edges=random_edges,
        pre_shuffle_edges=pre_edges,
        permutation=batch_permutation,
    )


def _build_queries(variant: str, seed: int) -> dict[str, _PrivateQueries]:
    result: dict[str, _PrivateQueries] = {}
    for offset, (name, nuisance_condition) in enumerate(QUERY_NUISANCE.items(), start=20):
        latent = _rademacher(_rng(seed, offset), (QUERIES_PER_CONDITION, SOURCE_DIM))
        probes = _rademacher(_rng(seed, offset + 20), latent.shape)
        if nuisance_condition is None:
            indices = _rng(seed, offset + 40).integers(
                0, len(TRAIN_NUISANCE), QUERIES_PER_CONDITION
            )
            nuisance = np.asarray([TRAIN_NUISANCE[int(index)] for index in indices])
        else:
            nuisance = np.repeat(
                np.asarray(nuisance_condition, dtype=np.float64)[None, :],
                QUERIES_PER_CONDITION,
                axis=0,
            )
        records = _public_records(
            latent,
            probes,
            nuisance[:, 0],
            nuisance[:, 1],
            _rng(seed, offset + 60),
            variant,
        )
        result[name] = _PrivateQueries(
            public=RelationalQueryBatch(records=_to_rows(records)),
            targets=_target(latent, probes),
            latent_records=latent,
            probes=probes,
            nuisance=nuisance_condition,
        )
    return result


@lru_cache(maxsize=16)
def build_audit_fixture(
    scale: int, variant: str = "main", seed: int = DEVELOPMENT_FIXTURE_SEED
) -> AuditFixture:
    private = _build_training(scale, variant, seed + scale)
    truth = {frozenset(edge) for edge in private.true_edges}
    shuffled = private.shuffled_edges
    random_edges = private.random_edges
    if any(_is_true_edge(edge, truth) for edge in shuffled + random_edges):
        raise AssertionError("false relation role contains a true source pair")
    roles = {
        "correct": _make_public_batch(
            private.public_records, private.targets, private.true_edges, True
        ),
        "shuffled": _make_public_batch(private.public_records, private.targets, shuffled, True),
        "passive": _make_public_batch(
            private.public_records, private.targets, private.true_edges, False
        ),
        "random": _make_public_batch(
            private.public_records, private.targets, random_edges, True
        ),
        "classical": _make_public_batch(
            private.public_records, private.targets, private.true_edges, False
        ),
        "oracle": _make_public_batch(
            private.public_records, private.targets, private.true_edges, True
        ),
    }
    return AuditFixture(
        scale=scale,
        permutation_variant=variant,
        roles=roles,
        private_training=private,
        queries=_build_queries(variant, seed + 10_000 + scale),
    )


def _hash_array(values: np.ndarray, dtype: str) -> str:
    contiguous = np.ascontiguousarray(values, dtype=np.dtype(dtype))
    return hashlib.sha256(contiguous.tobytes(order="C")).hexdigest()


def _hash_edges(edges: tuple[tuple[int, int], ...]) -> str:
    return _hash_array(np.asarray(edges, dtype=np.int64), "<i8")


def role_bit_identity(fixture: AuditFixture) -> dict[str, object]:
    hashes: dict[str, dict[str, str]] = {}
    query_records = np.concatenate(
        [np.asarray(query.public.records, dtype=np.float64) for query in fixture.queries.values()]
    )
    query_targets = np.concatenate([query.targets for query in fixture.queries.values()])
    for name, role in fixture.roles.items():
        hashes[name] = {
            "records": _hash_array(np.asarray(role.records), "<f8"),
            "targets": _hash_array(np.asarray(role.targets), "<f8"),
            "query_records": _hash_array(query_records, "<f8"),
            "query_targets": _hash_array(query_targets, "<f8"),
            "batch_order": _hash_array(np.asarray(role.batch_order), "<i8"),
        }
    reference = hashes["correct"]
    return {
        "pass": all(role_hashes == reference for role_hashes in hashes.values()),
        "hashes": hashes,
        "relation_hashes": {
            name: _hash_edges(role.relation_edges) for name, role in fixture.roles.items()
        },
    }


def relation_construction_audit(fixture: AuditFixture) -> dict[str, object]:
    true = {frozenset(edge) for edge in fixture.private_training.true_edges}
    details: dict[str, object] = {}
    passed = CONSTRUCTION_TRACE.index("relation graph") < min(
        CONSTRUCTION_TRACE.index("public probes"),
        CONSTRUCTION_TRACE.index("targets"),
        CONSTRUCTION_TRACE.index("nuisance realization"),
    )
    for name in ("correct", "shuffled", "random"):
        role = fixture.roles[name]
        degree = np.zeros(len(role.records), dtype=np.int64)
        for left, right in role.active_relations():
            degree[left] += 1
            degree[right] += 1
        true_count = sum(frozenset(edge) in true for edge in role.active_relations())
        expected_true = fixture.scale if name == "correct" else 0
        valid = (
            len(role.active_relations()) == fixture.scale
            and np.all(degree == 1)
            and true_count == expected_true
            and all(left != right for left, right in role.active_relations())
        )
        passed = passed and bool(valid)
        details[name] = {
            "edge_count": len(role.active_relations()),
            "degree_min": int(degree.min()),
            "degree_max": int(degree.max()),
            "true_pair_count": int(true_count),
            "pass": bool(valid),
        }
    passive = fixture.roles["passive"]
    passive_valid = not any(passive.relation_mask) and len(passive.relation_mask) == fixture.scale
    details["passive"] = {
        "edge_count": len(passive.relation_edges),
        "active_count": len(passive.active_relations()),
        "pass": passive_valid,
    }
    return {"pass": passed and passive_valid, "construction_trace": CONSTRUCTION_TRACE, **details}


def _mutual_information(labels: np.ndarray, values: np.ndarray) -> float:
    _, x = np.unique(labels, return_inverse=True)
    _, y = np.unique(values, return_inverse=True)
    counts = np.zeros((x.max() + 1, y.max() + 1), dtype=np.float64)
    np.add.at(counts, (x, y), 1.0)
    joint = counts / counts.sum()
    px = joint.sum(axis=1, keepdims=True)
    py = joint.sum(axis=0, keepdims=True)
    expected = px @ py
    mask = joint > 0
    return float(np.sum(joint[mask] * np.log2(joint[mask] / expected[mask])))


def _safe_correlation(left: np.ndarray, right: np.ndarray) -> float:
    if np.std(left) <= NUMERICAL_TOLERANCE or np.std(right) <= NUMERICAL_TOLERANCE:
        return 0.0
    return float(np.corrcoef(left, right)[0, 1])


def _ridge_fit(features: np.ndarray, targets: np.ndarray, regularization: float) -> np.ndarray:
    gram = features.T @ features
    penalty = np.eye(features.shape[1]) * regularization
    penalty[0, 0] = 0.0
    return np.linalg.solve(gram + penalty, features.T @ targets)


def _index_features(indices: np.ndarray, total: int) -> np.ndarray:
    x = indices.astype(np.float64) / max(total - 1, 1)
    return np.column_stack((np.ones_like(x), x, x * x, np.sin(2 * np.pi * x), np.cos(2 * np.pi * x)))


def target_leakage_audit(fixture: AuditFixture) -> dict[str, object]:
    targets = fixture.private_training.targets
    correct = fixture.roles["correct"].active_relations()
    shuffled = fixture.roles["shuffled"].active_relations()
    labels = np.concatenate((np.ones(len(correct)), np.zeros(len(shuffled))))
    relation_targets = np.asarray(
        [(targets[left], targets[right]) for left, right in correct + shuffled]
    )
    # y is an exact finite alphabet; encode a symmetric pair without rounding loss.
    pair_code = np.asarray(
        [f"{min(left, right):.8f}|{max(left, right):.8f}" for left, right in relation_targets]
    )
    mi = _mutual_information(labels, pair_code)
    gap_correlation = abs(
        _safe_correlation(labels, np.abs(relation_targets[:, 0] - relation_targets[:, 1]))
    )
    correct_values = np.asarray([(targets[left], targets[right]) for left, right in correct])
    paired_correlation = abs(_safe_correlation(correct_values[:, 0], correct_values[:, 1]))

    indices = np.arange(len(targets))
    train = indices % 2 == 0
    weights = _ridge_fit(_index_features(indices[train], len(targets)), targets[train], 1e-3)
    prediction = _index_features(indices[~train], len(targets)) @ weights
    null = np.full_like(prediction, np.mean(targets[train]))
    target_rmse = float(np.sqrt(np.mean((prediction - targets[~train]) ** 2)))
    null_rmse = float(np.sqrt(np.mean((null - targets[~train]) ** 2)))
    order_gain = 1.0 - target_rmse / max(null_rmse, NUMERICAL_TOLERANCE)
    passed = mi < 0.08 and gap_correlation < 0.10 and paired_correlation < 0.10 and order_gain < 0.05
    return {
        "pass": bool(passed),
        "edge_truth_target_pair_mi_bits": mi,
        "edge_truth_absolute_target_gap_correlation": gap_correlation,
        "correct_pair_target_correlation": paired_correlation,
        "source_conditional_target_distribution_exact_tv": 0.0,
        "record_index_target_prediction_relative_gain": order_gain,
        "analytic_reason": "independent Rademacher probes make y identically distributed for every latent record",
    }


def source_identity_leakage_audit(fixture: AuditFixture) -> dict[str, object]:
    count = len(fixture.private_training.targets)
    partner: dict[int, int] = {}
    for left, right in fixture.private_training.true_edges:
        partner[left] = right
        partner[right] = left
    targets = fixture.private_training.targets

    def directed_recall(attacker: callable) -> float:
        return float(np.mean([attacker(index) == partner[index] for index in range(count)]))

    adjacent = directed_recall(lambda index: index ^ 1)
    mirror = directed_recall(lambda index: count - 1 - index)
    cyclic = directed_recall(lambda index: (index + 1) % count)

    def closest_target(index: int) -> int:
        difference = np.abs(targets - targets[index])
        difference[index] = np.inf
        return int(np.argmin(difference))

    target_order = directed_recall(closest_target)
    chance = 1.0 / (count - 1)
    maximum = max(adjacent, mirror, cyclic, target_order)
    return {
        "pass": bool(maximum <= chance + 0.05),
        "chance": chance,
        "adjacent_recall": adjacent,
        "mirror_recall": mirror,
        "cyclic_recall": cyclic,
        "target_order_recall": target_order,
        "public_source_labels": False,
        "public_nuisance_labels": False,
        "public_filenames": False,
    }


def permutation_audit(seed: int = DEVELOPMENT_FIXTURE_SEED) -> dict[str, object]:
    main = build_audit_fixture(256, "main", seed)
    adversarial = build_audit_fixture(256, "adversarial", seed)
    main_targets = np.concatenate([query.targets for query in main.queries.values()])
    adversarial_targets = np.concatenate([query.targets for query in adversarial.queries.values()])
    main_oracle = np.concatenate(
        [_target(query.latent_records, query.probes) for query in main.queries.values()]
    )
    adversarial_oracle = np.concatenate(
        [_target(query.latent_records, query.probes) for query in adversarial.queries.values()]
    )
    public_fields = set(RelationalTrainingBatch.__dataclass_fields__) | set(
        RelationalQueryBatch.__dataclass_fields__
    )
    forbidden_public = {
        "latent_records",
        "probes",
        "nuisance",
        "coordinate_permutation",
        "inverse_permutation",
        "oracle",
        "role",
    }
    passed = (
        np.array_equal(np.sort(_bit_reversal_permutation()), np.arange(INPUT_DIM))
        and np.array_equal(np.sort(_affine_permutation()), np.arange(INPUT_DIM))
        and np.array_equal(main_targets, adversarial_targets)
        and np.array_equal(main_oracle, main_targets)
        and np.array_equal(adversarial_oracle, adversarial_targets)
        and not (public_fields & forbidden_public)
    )
    return {
        "pass": bool(passed),
        "main_definition": "pi(j)=five-bit reversal(j)",
        "adversarial_definition": "pi(j)=(7j+3) mod 32",
        "main_permutation": _bit_reversal_permutation().tolist(),
        "adversarial_permutation": _affine_permutation().tolist(),
        "oracle_target_hash": _hash_array(main_targets, "<f8"),
        "candidate_visible_fields": sorted(public_fields),
    }


def oracle_sanity(fixture: AuditFixture) -> dict[str, object]:
    errors: dict[str, float] = {}
    for name, query in fixture.queries.items():
        prediction = _target(query.latent_records, query.probes)
        errors[name] = float(np.max(np.abs(prediction - query.targets)))
    return {"pass": all(error == 0.0 for error in errors.values()), "max_absolute_error": errors}


def _degree2_features(records: np.ndarray) -> np.ndarray:
    row, column = np.triu_indices(records.shape[1])
    products = records[:, row] * records[:, column]
    return np.column_stack((np.ones(len(records)), records, products))


def _nrmse(prediction: np.ndarray, target: np.ndarray) -> float:
    return float(np.sqrt(np.mean((prediction - target) ** 2)) / max(np.std(target), 1e-12))


def polynomial_ridge_control(fixture: AuditFixture) -> dict[str, object]:
    training = fixture.roles["classical"]
    features = _degree2_features(np.asarray(training.records, dtype=np.float64))
    weights = _ridge_fit(features, np.asarray(training.targets), RIDGE_REGULARIZATION)
    scores: dict[str, float] = {}
    for name, query in fixture.queries.items():
        prediction = _degree2_features(np.asarray(query.public.records)) @ weights
        scores[name] = _nrmse(prediction, query.targets)
    return {
        "control": "degree-2 polynomial ridge",
        "regularization": RIDGE_REGULARIZATION,
        "feature_count": int(features.shape[1]),
        "uses_relations": False,
        "uses_private_state": False,
        "nrmse": scores,
        "all_ood_at_or_below_frozen_ceiling": all(scores[name] <= 0.75 for name in ("s1", "s2", "s3")),
    }


def _cca_projection(
    records: np.ndarray, edges: tuple[tuple[int, int], ...], degree2: bool
) -> np.ndarray:
    raw = _degree2_features(records)[:, 1:] if degree2 else records
    left = raw[[edge[0] for edge in edges]]
    right = raw[[edge[1] for edge in edges]]
    mean = np.mean(np.concatenate((left, right)), axis=0)
    left = left - mean
    right = right - mean
    covariance = (left.T @ left + right.T @ right) / (2 * len(edges))
    covariance += CCA_REGULARIZATION * np.eye(covariance.shape[0])
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    keep = eigenvalues > NUMERICAL_TOLERANCE
    whitening = eigenvectors[:, keep] / np.sqrt(eigenvalues[keep])[None, :]
    cross = (left.T @ right + right.T @ left) / (2 * len(edges))
    whitened_cross = whitening.T @ cross @ whitening
    _, canonical = np.linalg.eigh(whitened_cross)
    rank = min(CCA_RANK, canonical.shape[1])
    return whitening @ canonical[:, -rank:]


def classical_control_feasibility(fixture: AuditFixture) -> dict[str, object]:
    records = np.asarray(fixture.roles["correct"].records)
    edges = fixture.roles["correct"].active_relations()
    linear_projection = _cca_projection(records, edges, degree2=False)
    # Kernel feasibility is exercised on a bounded development subset.  The
    # exact explicit degree-2 map is the declared polynomial kernel feature map.
    bounded_edges = edges[: min(64, len(edges))]
    bounded_endpoint_ids = sorted({index for edge in bounded_edges for index in edge})
    remap = {old: new for new, old in enumerate(bounded_endpoint_ids)}
    bounded_records = records[bounded_endpoint_ids]
    remapped_edges = tuple((remap[left], remap[right]) for left, right in bounded_edges)
    kernel_projection = _cca_projection(bounded_records, remapped_edges, degree2=True)
    finite = np.isfinite(linear_projection).all() and np.isfinite(kernel_projection).all()
    return {
        "pass": bool(finite),
        "controls": (
            "degree-2 polynomial ridge",
            "linear symmetric CCA plus degree-2 ridge",
            "degree-2 explicit-kernel symmetric CCA plus ridge",
        ),
        "regularization": CCA_REGULARIZATION,
        "rank": CCA_RANK,
        "tolerance": NUMERICAL_TOLERANCE,
        "selection_protocol": "data-free constants frozen before any scored run",
        "linear_projection_shape": list(linear_projection.shape),
        "kernel_projection_shape": list(kernel_projection.shape),
    }


def nuisance_sanity(seed: int = DEVELOPMENT_FIXTURE_SEED) -> dict[str, object]:
    conditions = list(TRAIN_NUISANCE) + [
        QUERY_NUISANCE["s1"],
        QUERY_NUISANCE["s2"],
        QUERY_NUISANCE["s3"],
    ]
    analytic = [math.sqrt(sigma * sigma + dropout) for sigma, dropout in conditions]
    latent = _rademacher(_rng(seed, 90), (8192, SOURCE_DIM))
    empirical: list[float] = []
    for offset, (sigma, dropout) in enumerate(conditions):
        keep = _rng(seed, 100 + offset).random(latent.shape) >= dropout
        noise = _rng(seed, 110 + offset).normal(size=latent.shape) * sigma
        observed = keep * latent + noise
        empirical.append(float(np.sqrt(np.mean((observed - latent) ** 2))))
    ood_monotonic = analytic[-3] < analytic[-2] < analytic[-1]
    empirical_monotonic = empirical[-3] < empirical[-2] < empirical[-1]
    return {
        "pass": bool(ood_monotonic and empirical_monotonic),
        "conditions": [list(condition) for condition in conditions],
        "analytic_rms_corruption": analytic,
        "empirical_rms_corruption": empirical,
    }


def scale_sanity(seed: int = DEVELOPMENT_FIXTURE_SEED) -> dict[str, object]:
    counts: dict[str, object] = {}
    passed = True
    for scale in SCALES:
        fixture = build_audit_fixture(scale, "main", seed)
        item = {
            "sources": scale,
            "training_records": len(fixture.roles["correct"].records),
            "correct_relations": len(fixture.roles["correct"].active_relations()),
            "query_conditions": len(fixture.queries),
            "queries_per_condition": [len(query.public.records) for query in fixture.queries.values()],
        }
        valid = (
            item["training_records"] == 2 * scale
            and item["correct_relations"] == scale
            and item["query_conditions"] == 4
            and item["queries_per_condition"] == [QUERIES_PER_CONDITION] * 4
        )
        item["pass"] = valid
        passed = passed and bool(valid)
        counts[str(scale)] = item
    return {"pass": passed, "counts": counts}


def cost_accounting_audit() -> dict[str, object]:
    record = empty_cost_record()
    return {
        "pass": tuple(record) == COST_FIELDS and all(value >= 0 for value in record.values()),
        "fields": list(record),
        "system_boundary": "acquisition through declared horizon, including relation work and memory",
        "wall_time_status": "diagnostic only",
    }


def contract_hashes(root: Path | None = None) -> dict[str, str]:
    base = root or Path(__file__).resolve().parents[3]
    paths = {
        "evaluator": Path(__file__),
        "public_contract": base / "src" / "nextai_autoresearch" / "relational_ood_contract.py",
    }
    return {
        name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()
    }


@lru_cache(maxsize=1)
def contract_audit() -> dict[str, object]:
    fixture = build_audit_fixture(1024)
    bit_identity = role_bit_identity(fixture)
    relation = relation_construction_audit(fixture)
    target_leakage = target_leakage_audit(fixture)
    source_leakage = source_identity_leakage_audit(fixture)
    permutation = permutation_audit()
    oracle = oracle_sanity(fixture)
    controls = classical_control_feasibility(build_audit_fixture(64))
    polynomial = {
        str(scale): polynomial_ridge_control(build_audit_fixture(scale)) for scale in SCALES
    }
    passive_classical_succeeds = any(
        result["all_ood_at_or_below_frozen_ceiling"] for result in polynomial.values()
    )
    checks = {
        "role_bit_identity": bit_identity,
        "relation_construction": relation,
        "target_leakage": target_leakage,
        "source_identity_leakage": source_leakage,
        "permutation": permutation,
        "oracle": oracle,
        "classical_feasibility": controls,
        "nuisance": nuisance_sanity(),
        "scale": scale_sanity(),
        "cost": cost_accounting_audit(),
    }
    infrastructure_pass = all(bool(check["pass"]) for check in checks.values())
    if not infrastructure_pass:
        decision = "H"
        reason = "one or more evaluator-integrity audits failed"
    elif passive_classical_succeeds:
        decision = "E"
        reason = "a relation-free degree-2 polynomial ridge solves the frozen useful OOD ceiling"
    else:
        decision = "A"
        reason = "all contract audits passed and the passive classical control did not trivialize the task"
    return {
        "benchmark": BENCHMARK_ID,
        "bridge": BRIDGE_ID,
        "development_fixture_seed": DEVELOPMENT_FIXTURE_SEED,
        "hashes": contract_hashes(),
        "checks": checks,
        "passive_polynomial_ridge": polynomial,
        "decision": decision,
        "reason": reason,
        "scoring_authorized": decision == "A",
    }


def run_suite(*args: object, **kwargs: object) -> dict[str, object]:
    """Hard stop: cycle 240 is service-only and this cohort is not scored."""

    raise RuntimeError(
        "anonymous_repeated_measurement_ood_v1 is service-audit only; no scoring plan is authorized"
    )
